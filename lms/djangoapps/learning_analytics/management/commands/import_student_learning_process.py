"""Import student learning-process snapshots from CSV."""

import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.models import UserProfile
from common.djangoapps.student.models.course_enrollment import AlreadyEnrolledError, CourseEnrollment
from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot


class Command(BaseCommand):
    help = 'One-time import for student learning-process snapshots.'

    REQUIRED_BASE_COLUMNS = [
        'course_id',
        'student_id',
        'position',
        'gender',
        'location',
        'age',
        'job_title',
        'experience',
        'week_1',
        'week_2',
        'week_3',
        'final_score',
    ]
    LEGACY_VLE_COLUMNS = ['vle_1', 'vle_2', 'vle_3']
    ACTIVITY_COLUMNS = [
        'video_1',
        'quiz_1',
        'resource_1',
        'video_2',
        'quiz_2',
        'resource_2',
        'video_3',
        'quiz_3',
        'resource_3',
    ]
    DEFAULT_DOB = '01/01/1870'

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', required=True, help='Path to source CSV file.')
        parser.add_argument('--schema-path', required=True, help='Path to dataset description JSON file.')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate and parse data without writing rows.',
        )
        parser.add_argument(
            '--create-missing-users',
            action='store_true',
            help='Create auth users when student_id username is missing.',
        )
        parser.add_argument(
            '--replace-existing',
            action='store_true',
            help='Replace existing snapshot rows for students found in the input CSV.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path']).expanduser().resolve()
        schema_path = Path(options['schema_path']).expanduser().resolve()
        dry_run = options['dry_run']
        create_missing_users = options['create_missing_users']
        replace_existing = options['replace_existing']

        if not csv_path.exists():
            raise CommandError(f'CSV file does not exist: {csv_path}')
        if not schema_path.exists():
            raise CommandError(f'Schema file does not exist: {schema_path}')

        codebooks = self._load_codebooks(schema_path)

        created_count = 0
        updated_count = 0
        replaced_count = 0
        failed_count = 0
        error_examples = []
        parsed_rows = []
        imported_student_ids = set()

        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, skipinitialspace=True)
            self._validate_header(reader.fieldnames)

            for row_number, row in enumerate(reader, start=2):
                try:
                    parsed_row = self._parse_row(
                        row,
                        row_number,
                        codebooks,
                        create_missing_users=create_missing_users,
                    )
                except ValueError as exc:
                    failed_count += 1
                    if len(error_examples) < 10:
                        error_examples.append(f'row {row_number}: {exc}')
                    continue

                parsed_rows.append(parsed_row)
                imported_student_ids.add(parsed_row['snapshot']['student_id'])

        if dry_run:
            created_count = len(parsed_rows)
        else:
            if replace_existing and imported_student_ids:
                replaced_count, _ = StudentLearningProcessSnapshot.objects.filter(
                    student_id__in=imported_student_ids,
                ).delete()

            for parsed_row in parsed_rows:
                try:
                    with transaction.atomic():
                        self._sync_user_profile(parsed_row)
                        self._ensure_enrollment(parsed_row['user'], parsed_row['course_key'], parsed_row['normalized_course_id'])

                        payload = parsed_row['snapshot']
                        _, created = StudentLearningProcessSnapshot.objects.update_or_create(
                            student_id=payload['student_id'],
                            course_id=payload['course_id'],
                            defaults=payload,
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                except ValueError as exc:
                    failed_count += 1
                    if len(error_examples) < 10:
                        error_examples.append(f'row {parsed_row["snapshot"]["source_row_number"]}: {exc}')

        mode = 'DRY RUN' if dry_run else 'IMPORT'
        self.stdout.write(self.style.SUCCESS(f'{mode} complete'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Replaced: {replaced_count}')
        self.stdout.write(f'Failed: {failed_count}')
        for msg in error_examples:
            self.stdout.write(self.style.WARNING(msg))

    def _load_codebooks(self, schema_path):
        with schema_path.open('r', encoding='utf-8') as handle:
            schema = json.load(handle)

        fields = {entry['name']: entry for entry in schema.get('fields', []) if 'name' in entry}

        def make_reverse_map(field_name, value_key='values'):
            source = fields.get(field_name, {}).get(value_key, {})
            reverse_map = {}
            for code, label in source.items():
                reverse_map[self._normalize_text(label)] = int(code)
            return reverse_map

        return {
            'position': make_reverse_map('position'),
            'gender': make_reverse_map('gender'),
            'location': make_reverse_map('location', value_key='all_possible_values'),
            'age': make_reverse_map('age'),
            'job_title': make_reverse_map('job_title'),
            'experience': make_reverse_map('experience'),
        }

    def _validate_header(self, fieldnames):
        if not fieldnames:
            raise CommandError('CSV header is missing.')
        missing = [name for name in self.REQUIRED_BASE_COLUMNS if name not in fieldnames]
        if missing:
            raise CommandError(f'CSV is missing required columns: {missing}')

        has_legacy_vle = all(name in fieldnames for name in self.LEGACY_VLE_COLUMNS)
        has_activity_columns = all(name in fieldnames for name in self.ACTIVITY_COLUMNS)
        if not has_legacy_vle and not has_activity_columns:
            raise CommandError(
                'CSV must include either legacy vle_1..vle_3 columns or activity columns '
                'video_n/quiz_n/resource_n for n=1..3.'
            )

    def _parse_row(self, row, row_number, codebooks, create_missing_users=False):
        raw_course_id = row['course_id'].strip()
        if not raw_course_id:
            raise ValueError('course_id is empty')
        course_id, course_key = self._normalize_course_id(raw_course_id)
        if course_key is None:
            raise ValueError(f'invalid course_id for enrollment: {raw_course_id}')

        student_id = row['student_id'].strip()
        if not student_id:
            raise ValueError('student_id is empty')

        user = self._get_or_create_user(student_id, create_missing_users=create_missing_users)
        if user is None:
            raise ValueError(f'user not found for student_id {student_id}')

        position_text, position_code = self._map_category('position', row['position'], codebooks)
        gender_text, gender_code = self._map_category('gender', row['gender'], codebooks)
        location_text, location_code = self._map_category('location', row['location'], codebooks)
        age_text, age_code = self._map_category('age', row['age'], codebooks)
        job_title_text, job_title_code = self._map_category('job_title', row['job_title'], codebooks)
        experience_text, experience_code = self._map_category('experience', row['experience'], codebooks)

        week_1 = self._parse_decimal(row['week_1'], 'week_1', Decimal('0.0'), Decimal('10.0'))
        week_2 = self._parse_decimal(row['week_2'], 'week_2', Decimal('0.0'), Decimal('10.0'))
        week_3 = self._parse_decimal(row['week_3'], 'week_3', Decimal('0.0'), Decimal('10.0'))
        final_score = self._parse_decimal(row['final_score'], 'final_score', Decimal('0.0'), Decimal('10.0'))

        vle_1, vle_2, vle_3 = self._resolve_vle_values(row)

        parsed_name = (row.get('name') or '').strip()
        parsed_dob = (row.get('date_of_birth') or '').strip()

        return {
            'user': user,
            'course_key': course_key,
            'normalized_course_id': course_id,
            'profile_name': parsed_name or student_id,
            'profile_name_was_provided': bool(parsed_name),
            'year_of_birth': self._resolve_birth_year(parsed_dob),
            'dob_was_provided': bool(parsed_dob),
            'snapshot': {
                'user': user,
                'student_id': student_id,
                'course_id': course_id,
                'position_code': position_code,
                'position_text': position_text,
                'gender_code': gender_code,
                'gender_text': gender_text,
                'location_code': location_code,
                'location_text': location_text,
                'age_code': age_code,
                'age_text': age_text,
                'job_title_code': job_title_code,
                'job_title_text': job_title_text,
                'experience_code': experience_code,
                'experience_text': experience_text,
                'week_1': week_1,
                'week_2': week_2,
                'week_3': week_3,
                'vle_1': vle_1,
                'vle_2': vle_2,
                'vle_3': vle_3,
                'final_score': final_score,
                'source_file': 'dataset/log.csv',
                'source_row_number': row_number,
            },
        }

    def _resolve_vle_values(self, row):
        has_activity_columns = all(str(row.get(name, '')).strip() != '' for name in self.ACTIVITY_COLUMNS)

        if has_activity_columns:
            video_1 = self._parse_int(row['video_1'], 'video_1', minimum=0)
            quiz_1 = self._parse_int(row['quiz_1'], 'quiz_1', minimum=0)
            resource_1 = self._parse_int(row['resource_1'], 'resource_1', minimum=0)
            video_2 = self._parse_int(row['video_2'], 'video_2', minimum=0)
            quiz_2 = self._parse_int(row['quiz_2'], 'quiz_2', minimum=0)
            resource_2 = self._parse_int(row['resource_2'], 'resource_2', minimum=0)
            video_3 = self._parse_int(row['video_3'], 'video_3', minimum=0)
            quiz_3 = self._parse_int(row['quiz_3'], 'quiz_3', minimum=0)
            resource_3 = self._parse_int(row['resource_3'], 'resource_3', minimum=0)
            return (
                video_1 + quiz_1 + resource_1,
                video_2 + quiz_2 + resource_2,
                video_3 + quiz_3 + resource_3,
            )

        try:
            return (
                self._parse_int(row['vle_1'], 'vle_1', minimum=0),
                self._parse_int(row['vle_2'], 'vle_2', minimum=0),
                self._parse_int(row['vle_3'], 'vle_3', minimum=0),
            )
        except KeyError as exc:
            raise ValueError(f'missing VLE column: {exc}')

    def _map_category(self, field_name, value, codebooks):
        text_value = value.strip()
        code = codebooks[field_name].get(self._normalize_text(text_value))
        if code is None:
            raise ValueError(f'unmapped {field_name}: {text_value}')
        return text_value, code

    def _parse_decimal(self, value, field_name, minimum, maximum):
        try:
            parsed = Decimal(value.strip())
        except (InvalidOperation, AttributeError):
            raise ValueError(f'invalid decimal for {field_name}: {value}')

        if parsed < minimum or parsed > maximum:
            raise ValueError(f'{field_name} out of range: {parsed}')
        return parsed

    def _parse_int(self, value, field_name, minimum=0):
        try:
            parsed = int(str(value).strip())
        except (ValueError, TypeError):
            raise ValueError(f'invalid integer for {field_name}: {value}')
        if parsed < minimum:
            raise ValueError(f'{field_name} must be >= {minimum}: {parsed}')
        return parsed

    def _normalize_text(self, value):
        return ' '.join(str(value).strip().split()).lower()

    def _normalize_course_id(self, raw_course_id):
        candidates = [raw_course_id]
        if not raw_course_id.startswith('course-v1:'):
            candidates.append(f'course-v1:{raw_course_id}')

        for candidate in candidates:
            try:
                course_key = CourseKey.from_string(candidate)
                return str(course_key), course_key
            except Exception:
                continue
        return raw_course_id, None

    def _resolve_birth_year(self, raw_date_of_birth):
        date_value = raw_date_of_birth or self.DEFAULT_DOB
        parsed_year = None
        for date_format in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y'):
            try:
                parsed_year = datetime.strptime(date_value, date_format).year
                break
            except ValueError:
                continue

        if parsed_year is None:
            parsed_year = datetime.strptime(self.DEFAULT_DOB, '%d/%m/%Y').year

        min_year = min(UserProfile.VALID_YEARS)
        max_year = max(UserProfile.VALID_YEARS)
        if parsed_year < min_year:
            return min_year
        if parsed_year > max_year:
            return max_year
        return parsed_year

    def _get_or_create_user(self, student_id, create_missing_users=False):
        user = User.objects.filter(username=student_id).first()
        if user:
            return user

        if not create_missing_users:
            return user

        # This import is one-time bootstrap data; set unusable password to prevent unknown credentials.
        user = User.objects.create_user(
            username=student_id,
            email=f'{student_id}@example.local',
            password=None,
        )
        return user

    def _sync_user_profile(self, parsed_row):
        user = parsed_row['user']
        profile_name = parsed_row['profile_name']
        profile_name_was_provided = parsed_row['profile_name_was_provided']
        year_of_birth = parsed_row['year_of_birth']
        dob_was_provided = parsed_row['dob_was_provided']

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': profile_name,
                'year_of_birth': year_of_birth,
            },
        )

        update_fields = []
        if profile_name_was_provided:
            if profile.name != profile_name:
                profile.name = profile_name
                update_fields.append('name')
        elif not profile.name:
            profile.name = profile_name
            update_fields.append('name')

        if dob_was_provided:
            if profile.year_of_birth != year_of_birth:
                profile.year_of_birth = year_of_birth
                update_fields.append('year_of_birth')
        elif profile.year_of_birth is None:
            profile.year_of_birth = year_of_birth
            update_fields.append('year_of_birth')

        if update_fields:
            profile.save(update_fields=update_fields)

    def _ensure_enrollment(self, user, course_key, course_id):
        try:
            CourseEnrollment.enroll(user, course_key, check_access=False)
        except AlreadyEnrolledError:
            CourseEnrollment.objects.filter(user=user, course_id=course_key).update(is_active=True)
        except Exception as exc:
            raise ValueError(f'failed to enroll user {user.username} to {course_id}: {exc}')

