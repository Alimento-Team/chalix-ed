"""Import student learning-process snapshots from CSV."""

import csv
import json
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.models import UserProfile
from common.djangoapps.student.models.course_enrollment import AlreadyEnrolledError, CourseEnrollment
from lms.djangoapps.learning_analytics.models import LearnerBehavior, StudentLearningProcessSnapshot


class Command(BaseCommand):
    help = 'One-time import for student learning-process snapshots.'

    DEFAULT_CODEBOOKS = {
        'position': {
            'nhan vien': 0,
            'chuyen vien': 1,
            'chuyen vien chinh': 2,
            'lanh dao': 3,
        },
        'gender': {
            'nam': 0,
            'nu': 1,
        },
        'age': {
            'tu 20 den 25 tuoi': 1,
            'tren 25 tuoi': 2,
        },
        'job_title': {
            'cong chuc': 0,
            'vien chuc': 1,
        },
        'experience': {
            'duoi 5 nam': 0,
            'tu 5 den 10 nam': 1,
            'tren 10 nam': 2,
        },
        'location': {
            'ha noi': 1,
            'bac ninh': 2,
            'nam dinh': 3,
            'bac giang': 4,
            'quang ninh': 5,
            'hai phong': 6,
            'hai duong': 7,
            'hung yen': 8,
            'thai binh': 9,
            'ninh binh': 10,
            'ha nam': 11,
            'ha giang': 12,
            'cao bang': 13,
            'lao cai': 14,
            'son la': 15,
            'lai chau': 16,
            'bac can': 17,
            'lang son': 18,
            'tuyen quang': 19,
            'yen bai': 20,
            'thai nguyen': 21,
            'dien bien': 22,
            'phu tho': 23,
            'vinh phuc': 24,
            'hoa binh': 25,
            'thanh hoa': 26,
            'nghe an': 27,
            'ha tinh': 28,
            'quang binh': 29,
            'quang tri': 30,
            'thua thien hue': 31,
            'da nang': 32,
            'quang nam': 33,
            'quang ngai': 34,
            'kon tum': 35,
            'gia lai': 36,
            'binh dinh': 37,
            'phu yen': 38,
            'dak lak': 39,
            'khanh hoa': 40,
            'dak nong': 41,
            'lam dong': 42,
            'ninh thuan': 43,
            'binh phuoc': 44,
            'dong nai': 45,
            'binh thuan': 46,
            'tp ho chi minh': 47,
            'long an': 48,
            'ba ria-vung tau': 49,
            'dong thap': 50,
            'an giang': 51,
            'tien giang': 52,
            'vinh long': 53,
            'ben tre': 54,
            'can tho': 55,
            'kien giang': 56,
            'tra vinh': 57,
            'hau giang': 58,
            'soc trang': 59,
            'bac lieu': 60,
            'ca mau': 61,
            'tay ninh': 62,
            'binh duong': 63,
        },
    }

    REQUIRED_BASE_COLUMNS = [
        'course_id',
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
    IDENTITY_COLUMNS = ['username', 'student_id', 'id']
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
        parser.add_argument('--schema-path', required=False, help='Optional path to dataset description JSON file.')
        parser.add_argument(
            '--prepared-input',
            action='store_true',
            help='Treat the CSV as normalized CMS staging output and skip user/profile/org sync.',
        )
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
        schema_path_option = options.get('schema_path')
        schema_path = Path(schema_path_option).expanduser().resolve() if schema_path_option else None
        prepared_input = options['prepared_input']
        dry_run = options['dry_run']
        create_missing_users = options['create_missing_users']
        replace_existing = options['replace_existing']

        if not csv_path.exists():
            raise CommandError(f'CSV file does not exist: {csv_path}')

        codebooks = self._default_codebooks()
        if schema_path is not None:
            if not schema_path.exists():
                raise CommandError(f'Schema file does not exist: {schema_path}')
            codebooks = self._load_codebooks(schema_path, base_codebooks=codebooks)

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
                        source_file=csv_path.name,
                        prepared_input=prepared_input,
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
                        if not prepared_input:
                            self._sync_user_account(parsed_row)
                            self._sync_user_profile(parsed_row)
                            self._sync_user_organization(parsed_row)
                        self._ensure_enrollment(parsed_row['user'], parsed_row['course_key'], parsed_row['normalized_course_id'])

                        payload = parsed_row['snapshot']
                        _, created = StudentLearningProcessSnapshot.objects.update_or_create(
                            student_id=payload['student_id'],
                            course_id=payload['course_id'],
                            defaults=payload,
                        )

                        behavior_payload = parsed_row.get('behavior')
                        if behavior_payload:
                            LearnerBehavior.objects.update_or_create(
                                user=behavior_payload['user'],
                                course_id=behavior_payload['course_id'],
                                defaults=behavior_payload['defaults'],
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

    def _default_codebooks(self):
        return {field: dict(entries) for field, entries in self.DEFAULT_CODEBOOKS.items()}

    def _load_codebooks(self, schema_path, base_codebooks=None):
        with schema_path.open('r', encoding='utf-8') as handle:
            schema = json.load(handle)

        fields = {entry['name']: entry for entry in schema.get('fields', []) if 'name' in entry}

        def make_reverse_map(field_name, value_key='values'):
            source = fields.get(field_name, {}).get(value_key, {})
            reverse_map = {}
            if isinstance(source, dict):
                for code, label in source.items():
                    reverse_map[self._normalize_text(label)] = int(code)
            elif isinstance(source, list):
                for index, label in enumerate(source):
                    reverse_map[self._normalize_text(label)] = index
            return reverse_map

        codebooks = base_codebooks or self._default_codebooks()
        schema_books = {
            'position': make_reverse_map('position'),
            'gender': make_reverse_map('gender'),
            'location': make_reverse_map('location', value_key='all_possible_values'),
            'age': make_reverse_map('age'),
            'job_title': make_reverse_map('job_title'),
            'experience': make_reverse_map('experience'),
        }
        for key, reverse_map in schema_books.items():
            if reverse_map:
                codebooks[key] = reverse_map
        return codebooks

    def _validate_header(self, fieldnames):
        if not fieldnames:
            raise CommandError('CSV header is missing.')
        missing = [name for name in self.REQUIRED_BASE_COLUMNS if name not in fieldnames]
        if missing:
            raise CommandError(f'CSV is missing required columns: {missing}')
        if not any(name in fieldnames for name in self.IDENTITY_COLUMNS):
            raise CommandError(
                f'CSV must include at least one identity column from: {self.IDENTITY_COLUMNS}'
            )

        has_legacy_vle = all(name in fieldnames for name in self.LEGACY_VLE_COLUMNS)
        has_activity_columns = all(name in fieldnames for name in self.ACTIVITY_COLUMNS)
        if not has_legacy_vle and not has_activity_columns:
            raise CommandError(
                'CSV must include either legacy vle_1..vle_3 columns or activity columns '
                'video_n/quiz_n/resource_n for n=1..3.'
            )

    def _parse_row(self, row, row_number, codebooks, create_missing_users=False, source_file='', prepared_input=False):
        raw_course_id = row['course_id'].strip()
        if not raw_course_id:
            raise ValueError('course_id is empty')
        course_id, course_key = self._normalize_course_id(raw_course_id)
        if course_key is None:
            raise ValueError(f'invalid course_id for enrollment: {raw_course_id}')

        student_id = self._first_present_value(row, self.IDENTITY_COLUMNS)
        if not student_id:
            raise ValueError('student identifier is empty')

        external_user_id = (row.get('external_user_id') or row.get('id') or '').strip()
        email = (row.get('email') or '').strip()
        organization_name = (row.get('co_quan') or '').strip()
        raw_status = (row.get('status') or '').strip()

        user = self._get_or_create_user(
            student_id,
            email=email,
            create_missing_users=create_missing_users,
        )
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
        total_studied_time = self._parse_optional_decimal(
            row.get('total_studied_time'),
            'total_studied_time',
            minimum=Decimal('0.0'),
        )
        completed_percentage = self._parse_optional_percentage(row.get('completed_percentage'))
        source_row_number = self._parse_optional_int(row.get('source_row_number'), 'source_row_number') or row_number
        activity_totals = self._resolve_activity_totals(row)

        behavior_payload = None
        if activity_totals:
            behavior_payload = {
                'user': user,
                'course_id': course_id,
                'defaults': {
                    'videos_watched': activity_totals['videos_watched'],
                    'problems_attempted': activity_totals['problems_attempted'],
                    'completion_percentage': float(completed_percentage or 0),
                },
            }

        return {
            'user': user,
            'course_key': course_key,
            'normalized_course_id': course_id,
            'email': email,
            'organization_name': organization_name,
            'profile_name': parsed_name or student_id,
            'profile_name_was_provided': bool(parsed_name),
            'raw_date_of_birth': parsed_dob,
            'year_of_birth': self._resolve_birth_year(parsed_dob),
            'dob_was_provided': bool(parsed_dob),
            'snapshot': {
                'user': user,
                'student_id': student_id,
                'course_id': course_id,
                'external_user_id': external_user_id,
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
                'total_studied_time': total_studied_time,
                'completed_percentage': completed_percentage,
                'status': raw_status,
                'final_score': final_score,
                'source_file': source_file or 'dataset/log.csv',
                'source_row_number': source_row_number,
            },
            'behavior': behavior_payload,
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

    def _resolve_activity_totals(self, row):
        has_activity_columns = all(str(row.get(name, '')).strip() != '' for name in self.ACTIVITY_COLUMNS)
        if not has_activity_columns:
            return None

        return {
            'videos_watched': (
                self._parse_int(row['video_1'], 'video_1', minimum=0)
                + self._parse_int(row['video_2'], 'video_2', minimum=0)
                + self._parse_int(row['video_3'], 'video_3', minimum=0)
            ),
            'problems_attempted': (
                self._parse_int(row['quiz_1'], 'quiz_1', minimum=0)
                + self._parse_int(row['quiz_2'], 'quiz_2', minimum=0)
                + self._parse_int(row['quiz_3'], 'quiz_3', minimum=0)
            ),
        }

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

    def _parse_optional_decimal(self, value, field_name, minimum=None, maximum=None):
        if value is None or str(value).strip() == '':
            return None

        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, AttributeError):
            raise ValueError(f'invalid decimal for {field_name}: {value}')

        if minimum is not None and parsed < minimum:
            raise ValueError(f'{field_name} out of range: {parsed}')
        if maximum is not None and parsed > maximum:
            raise ValueError(f'{field_name} out of range: {parsed}')
        return parsed

    def _parse_optional_percentage(self, value):
        if value is None:
            return None

        raw_value = str(value).strip()
        if not raw_value:
            return None

        if raw_value.endswith('%'):
            raw_value = raw_value[:-1].strip()

        try:
            parsed = int(Decimal(raw_value))
        except (InvalidOperation, ValueError):
            raise ValueError(f'invalid completed_percentage: {value}')

        if parsed < 0 or parsed > 100:
            raise ValueError(f'completed_percentage out of range: {parsed}')
        return parsed

    def _parse_int(self, value, field_name, minimum=0):
        try:
            parsed = int(str(value).strip())
        except (ValueError, TypeError):
            raise ValueError(f'invalid integer for {field_name}: {value}')
        if parsed < minimum:
            raise ValueError(f'{field_name} must be >= {minimum}: {parsed}')
        return parsed

    def _parse_optional_int(self, value, field_name, minimum=0):
        if value is None or str(value).strip() == '':
            return None
        return self._parse_int(value, field_name, minimum=minimum)

    def _normalize_text(self, value):
        text = ' '.join(str(value).strip().split()).lower()
        # đ/Đ (d-with-stroke, U+0111/U+0110) does not decompose via NFKD; replace manually first
        text = text.replace('\u0111', 'd').replace('\u0110', 'D')
        # Strip all remaining Vietnamese (and other) diacritics via NFKD decomposition
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    def _first_present_value(self, row, column_names):
        for name in column_names:
            value = row.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ''

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

    def _get_or_create_user(self, student_id, email='', create_missing_users=False):
        user = User.objects.filter(username=student_id).first()
        if user:
            return user

        if not create_missing_users:
            return user

        # This import is one-time bootstrap data; set unusable password to prevent unknown credentials.
        user = User.objects.create_user(
            username=student_id,
            email=email or f'{student_id}@example.local',
            password=None,
        )
        return user

    def _sync_user_account(self, parsed_row):
        user = parsed_row['user']
        email = parsed_row['email']
        update_fields = []

        if email and user.email != email:
            user.email = email
            update_fields.append('email')

        if update_fields:
            user.save(update_fields=update_fields)

    def _sync_user_profile(self, parsed_row):
        user = parsed_row['user']
        profile_name = parsed_row['profile_name']
        profile_name_was_provided = parsed_row['profile_name_was_provided']
        year_of_birth = parsed_row['year_of_birth']
        dob_was_provided = parsed_row['dob_was_provided']
        raw_date_of_birth = parsed_row['raw_date_of_birth']
        organization_name = parsed_row['organization_name']

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

        meta = profile.get_meta()
        meta_changed = False
        if raw_date_of_birth and meta.get('ngay_sinh') != raw_date_of_birth:
            meta['ngay_sinh'] = raw_date_of_birth
            meta_changed = True
        if organization_name:
            if meta.get('ten_co_quan') != organization_name:
                meta['ten_co_quan'] = organization_name
                meta_changed = True
            if meta.get('don_vi_cong_tac') != organization_name:
                meta['don_vi_cong_tac'] = organization_name
                meta_changed = True
        if meta_changed:
            profile.set_meta(meta)
            update_fields.append('meta')

        if update_fields:
            profile.save(update_fields=update_fields)

    def _sync_user_organization(self, parsed_row):
        organization_name = parsed_row['organization_name']
        if not organization_name:
            return

        organization_id = self._get_chalix_organization_id(organization_name)
        if organization_id is None:
            raise ValueError(f'unmapped co_quan: {organization_name}')

        now = timezone.now()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE contentstore_chalixuserrole
                SET is_active = FALSE, updated_at = %s
                WHERE user_id = %s AND role = %s AND is_active = TRUE AND organization_id <> %s
                """,
                [now, parsed_row['user'].id, 'cong_chuc', organization_id],
            )

            cursor.execute(
                """
                SELECT id
                FROM contentstore_chalixuserrole
                WHERE user_id = %s AND role = %s AND organization_id = %s
                LIMIT 1
                """,
                [parsed_row['user'].id, 'cong_chuc', organization_id],
            )
            existing_row = cursor.fetchone()

            if existing_row:
                cursor.execute(
                    """
                    UPDATE contentstore_chalixuserrole
                    SET is_active = TRUE, updated_at = %s
                    WHERE id = %s
                    """,
                    [now, existing_row[0]],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO contentstore_chalixuserrole
                        (user_id, role, organization_id, is_active, created_at, updated_at, created_by_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [parsed_row['user'].id, 'cong_chuc', organization_id, True, now, now, None],
                )

    def _get_chalix_organization_id(self, organization_name):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM contentstore_chalixorganization
                    WHERE name = %s OR LOWER(name) = LOWER(%s) OR LOWER(display_name) = LOWER(%s)
                    ORDER BY id ASC
                    LIMIT 1
                    """,
                    [organization_name, organization_name, organization_name],
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as exc:
            raise ValueError(f'failed to resolve co_quan {organization_name}: {exc}')

    def _ensure_enrollment(self, user, course_key, course_id):
        try:
            CourseEnrollment.enroll(user, course_key, check_access=False)
        except AlreadyEnrolledError:
            CourseEnrollment.objects.filter(user=user, course_id=course_key).update(is_active=True)
        except Exception as exc:
            raise ValueError(f'failed to enroll user {user.username} to {course_id}: {exc}')

