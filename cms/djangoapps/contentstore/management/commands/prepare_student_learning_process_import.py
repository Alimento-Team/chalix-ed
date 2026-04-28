"""Prepare learner accounts and normalized staging CSV for LMS learning-process import."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.functions import Lower

from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole
from common.djangoapps.student.models import UserProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Command(BaseCommand):
    help = 'Prepare student learning-process data in CMS and write a normalized CSV for LMS import.'
    DEFAULT_EMAIL_DOMAIN = 'itg-acst.edu.vn'
    DEFAULT_IMPORTED_USER_PASSWORD = 'Itg@cst2025'

    REQUIRED_COLUMNS = [
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
    OUTPUT_HEADERS = [
        'course_id',
        'student_id',
        'external_user_id',
        'position',
        'gender',
        'location',
        'age',
        'job_title',
        'experience',
        'week_1',
        'week_2',
        'week_3',
        'vle_1',
        'vle_2',
        'vle_3',
        'total_studied_time',
        'completed_percentage',
        'status',
        'final_score',
        'source_row_number',
    ]
    DEFAULT_DOB = '01/01/1870'

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', required=True, help='Path to the raw source CSV file.')
        parser.add_argument('--output-path', required=True, help='Path to write the normalized staging CSV.')
        parser.add_argument(
            '--courses-mapping-path',
            required=False,
            help='Optional path to courses_mapping.csv for validating enrolled course IDs.',
        )
        parser.add_argument(
            '--course-id-mapping-output-path',
            required=False,
            help='Optional path to write resolved source->actual course id mapping CSV.',
        )
        parser.add_argument(
            '--create-missing-users',
            action='store_true',
            help='Create auth users when the learner username is missing.',
        )
        parser.add_argument(
            '--sync-user-credentials',
            action='store_true',
            help='Update processed users to use import email (or username@itg-acst.edu.vn) and default password.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path']).expanduser().resolve()
        output_path = Path(options['output_path']).expanduser().resolve()
        courses_mapping_path_option = options.get('courses_mapping_path')
        courses_mapping_path = (
            Path(courses_mapping_path_option).expanduser().resolve()
            if courses_mapping_path_option else None
        )
        mapping_output_path_option = options.get('course_id_mapping_output_path')
        mapping_output_path = (
            Path(mapping_output_path_option).expanduser().resolve()
            if mapping_output_path_option else None
        )
        create_missing_users = options['create_missing_users']
        sync_user_credentials = options['sync_user_credentials']

        if not csv_path.exists():
            raise CommandError(f'CSV file does not exist: {csv_path}')
        if courses_mapping_path is not None and not courses_mapping_path.exists():
            raise CommandError(f'Courses mapping file does not exist: {courses_mapping_path}')

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if mapping_output_path is not None:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)

        courses_mapping, resolved_mapping_rows = self._load_courses_mapping(courses_mapping_path)
        if mapping_output_path is not None:
            self._write_resolved_mapping_csv(mapping_output_path, resolved_mapping_rows)

        unresolved_count = sum(
            1 for row in resolved_mapping_rows if not row.get('actual_course_id')
        )

        prepared_rows = []
        failed_count = 0
        error_examples = []

        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, skipinitialspace=True)
            self._validate_header(reader.fieldnames)

            for row_number, row in enumerate(reader, start=2):
                try:
                    prepared_rows.extend(
                        self._prepare_rows(
                            row,
                            row_number,
                            courses_mapping=courses_mapping,
                            create_missing_users=create_missing_users,
                            sync_user_credentials=sync_user_credentials,
                        )
                    )
                except ValueError as exc:
                    failed_count += 1
                    if len(error_examples) < 10:
                        error_examples.append(f'row {row_number}: {exc}')

        with output_path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=self.OUTPUT_HEADERS)
            writer.writeheader()
            writer.writerows(prepared_rows)

        self.stdout.write(self.style.SUCCESS('CMS PREP complete'))
        self.stdout.write(f'Prepared rows: {len(prepared_rows)}')
        self.stdout.write(f'Failed: {failed_count}')
        self.stdout.write(f'Output: {output_path}')
        if mapping_output_path is not None:
            self.stdout.write(f'Course ID Mapping Output: {mapping_output_path}')
        if unresolved_count:
            self.stdout.write(
                self.style.WARNING(
                    f'Course mapping unresolved: {unresolved_count} row(s); '
                    'source course_id will be used for those entries.'
                )
            )
        for msg in error_examples:
            self.stdout.write(self.style.WARNING(msg))

    def _validate_header(self, fieldnames):
        if not fieldnames:
            raise CommandError('CSV header is missing.')

        missing = [name for name in self.REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise CommandError(f'CSV is missing required columns: {missing}')

        if not any(name in fieldnames for name in self.IDENTITY_COLUMNS):
            raise CommandError(
                f'CSV must include at least one identity column from: {self.IDENTITY_COLUMNS}'
            )
        if 'course_id' not in fieldnames and 'enrolled_courses' not in fieldnames:
            raise CommandError('CSV must include either course_id or enrolled_courses.')

        has_legacy_vle = all(name in fieldnames for name in self.LEGACY_VLE_COLUMNS)
        has_activity_columns = all(name in fieldnames for name in self.ACTIVITY_COLUMNS)
        if not has_legacy_vle and not has_activity_columns:
            raise CommandError(
                'CSV must include either legacy vle_1..vle_3 columns or activity columns '
                'video_n/quiz_n/resource_n for n=1..3.'
            )

    def _prepare_rows(
        self,
        row,
        row_number,
        courses_mapping=None,
        create_missing_users=False,
        sync_user_credentials=False,
    ):
        student_id = self._first_present_value(row, self.IDENTITY_COLUMNS)
        if not student_id:
            raise ValueError('student identifier is empty')

        user = self._get_or_create_user(
            student_id,
            email=(row.get('email') or '').strip(),
            create_missing_users=create_missing_users,
        )
        if user is None:
            raise ValueError(f'user not found for student_id {student_id}')

        with transaction.atomic():
            self._sync_user_account(
                user,
                (row.get('email') or '').strip(),
                sync_user_credentials=sync_user_credentials,
            )
            organization_name = self._resolve_organization_name(row)
            self._sync_user_profile(
                user=user,
                profile_name=(row.get('name') or '').strip() or student_id,
                profile_name_was_provided=bool((row.get('name') or '').strip()),
                raw_date_of_birth=(row.get('date_of_birth') or '').strip(),
                organization_name=organization_name,
            )
            self._sync_user_organization(user, organization_name)

        vle_1, vle_2, vle_3 = self._resolve_vle_values(row)

        course_ids = self._resolve_course_ids(row, courses_mapping)
        per_course_total_studied_time = self._resolve_per_course_total_studied_time(
            row.get('total_studied_time'),
            len(course_ids),
        )
        rows = []
        for course_id in course_ids:
            rows.append(
                {
                    'course_id': course_id,
                    'student_id': student_id,
                    'external_user_id': (row.get('id') or '').strip(),
                    'position': (row.get('position') or '').strip(),
                    'gender': (row.get('gender') or '').strip(),
                    'location': (row.get('location') or '').strip(),
                    'age': (row.get('age') or '').strip(),
                    'job_title': (row.get('job_title') or '').strip(),
                    'experience': (row.get('experience') or '').strip(),
                    'week_1': (row.get('week_1') or '').strip(),
                    'week_2': (row.get('week_2') or '').strip(),
                    'week_3': (row.get('week_3') or '').strip(),
                    'vle_1': vle_1,
                    'vle_2': vle_2,
                    'vle_3': vle_3,
                    'total_studied_time': per_course_total_studied_time,
                    'completed_percentage': self._format_optional_percentage(row.get('completed_percentage')),
                    'status': (row.get('status') or '').strip(),
                    'final_score': (row.get('final_score') or '').strip(),
                    'source_row_number': row_number,
                }
            )
        return rows

    def _resolve_organization_name(self, row):
        return (row.get('co_quan') or row.get('department') or '').strip()

    def _load_courses_mapping(self, mapping_path):
        if mapping_path is None:
            return {}, []

        mapping = {}
        resolved_rows = []
        with mapping_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                course_id = (row.get('course_id') or '').strip()
                course_name = (row.get('course_name') or '').strip()
                if not course_id:
                    continue

                if not course_name:
                    mapping[course_id] = {
                        'course_name': course_name,
                        'actual_course_id': '',
                    }
                    resolved_rows.append(
                        {
                            'source_course_id': course_id,
                            'course_name': course_name,
                            'actual_course_id': '',
                            'status': 'unresolved',
                            'note': 'missing course_name',
                        }
                    )
                    continue

                actual_course_id = self._lookup_actual_course_id(course_name)
                if not actual_course_id:
                    mapping[course_id] = {
                        'course_name': course_name,
                        'actual_course_id': '',
                    }
                    resolved_rows.append(
                        {
                            'source_course_id': course_id,
                            'course_name': course_name,
                            'actual_course_id': '',
                            'status': 'unresolved',
                            'note': 'course_name not found in CourseOverview',
                        }
                    )
                    continue

                mapping[course_id] = {
                    'course_name': course_name,
                    'actual_course_id': actual_course_id,
                }
                resolved_rows.append(
                    {
                        'source_course_id': course_id,
                        'course_name': course_name,
                        'actual_course_id': actual_course_id,
                        'status': 'resolved',
                        'note': '',
                    }
                )

        return mapping, resolved_rows

    def _write_resolved_mapping_csv(self, output_path, rows):
        headers = ['source_course_id', 'course_name', 'actual_course_id', 'status', 'note']
        with output_path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def _lookup_actual_course_id(self, course_name):
        normalized_name = self._normalize_text(course_name)
        if not normalized_name:
            return ''

        overview = (
            CourseOverview.objects
            .annotate(normalized_display_name=Lower('display_name'))
            .filter(normalized_display_name=normalized_name)
            .order_by('id')
            .first()
        )
        return str(overview.id) if overview else ''

    def _normalize_text(self, value):
        return ' '.join(str(value).strip().split()).lower()

    def _resolve_course_ids(self, row, courses_mapping):
        course_ids = []

        single_course = (row.get('course_id') or '').strip()
        if single_course:
            course_ids.append(single_course)

        enrolled_courses = (row.get('enrolled_courses') or '').strip()
        if enrolled_courses:
            for course_id in enrolled_courses.split(';'):
                cleaned = course_id.strip()
                if cleaned:
                    course_ids.append(cleaned)

        unique_course_ids = []
        seen = set()
        for course_id in course_ids:
            if course_id not in seen:
                seen.add(course_id)
                unique_course_ids.append(course_id)

        if not unique_course_ids:
            raise ValueError('course_id/enrolled_courses is empty')

        if courses_mapping:
            resolved_course_ids = []
            for course_id in unique_course_ids:
                mapping_entry = courses_mapping.get(course_id)
                if mapping_entry and mapping_entry.get('actual_course_id'):
                    resolved_course_ids.append(mapping_entry['actual_course_id'])
                else:
                    resolved_course_ids.append(course_id)
            return resolved_course_ids

        return unique_course_ids

    def _resolve_vle_values(self, row):
        has_activity_columns = all(str(row.get(name, '')).strip() != '' for name in self.ACTIVITY_COLUMNS)

        if has_activity_columns:
            return (
                self._parse_int(row['video_1'], 'video_1') + self._parse_int(row['quiz_1'], 'quiz_1') + self._parse_int(row['resource_1'], 'resource_1'),
                self._parse_int(row['video_2'], 'video_2') + self._parse_int(row['quiz_2'], 'quiz_2') + self._parse_int(row['resource_2'], 'resource_2'),
                self._parse_int(row['video_3'], 'video_3') + self._parse_int(row['quiz_3'], 'quiz_3') + self._parse_int(row['resource_3'], 'resource_3'),
            )

        return (
            self._parse_int(row['vle_1'], 'vle_1'),
            self._parse_int(row['vle_2'], 'vle_2'),
            self._parse_int(row['vle_3'], 'vle_3'),
        )

    def _parse_int(self, value, field_name):
        try:
            parsed = int(str(value).strip())
        except (ValueError, TypeError):
            raise ValueError(f'invalid integer for {field_name}: {value}')
        if parsed < 0:
            raise ValueError(f'{field_name} must be >= 0: {parsed}')
        return parsed

    def _format_optional_decimal(self, value):
        if value is None or str(value).strip() == '':
            return ''
        try:
            return str(Decimal(str(value).strip()))
        except (InvalidOperation, AttributeError):
            raise ValueError(f'invalid decimal value: {value}')

    def _format_optional_percentage(self, value):
        if value is None:
            return ''
        raw_value = str(value).strip()
        if not raw_value:
            return ''
        if raw_value.endswith('%'):
            raw_value = raw_value[:-1].strip()
        try:
            parsed = int(Decimal(raw_value))
        except (InvalidOperation, ValueError):
            raise ValueError(f'invalid completed_percentage: {value}')
        if parsed < 0 or parsed > 100:
            raise ValueError(f'completed_percentage out of range: {parsed}')
        return str(parsed)

    def _resolve_per_course_total_studied_time(self, value, course_count):
        if value is None or str(value).strip() == '':
            return ''
        if course_count <= 0:
            raise ValueError('course_count must be > 0 when total_studied_time is provided')

        try:
            total_hours = Decimal(str(value).strip())
        except (InvalidOperation, AttributeError):
            raise ValueError(f'invalid decimal value: {value}')

        per_course_hours = total_hours / Decimal(course_count)
        normalized = per_course_hours.normalize()

        # Keep plain decimal formatting without scientific notation for CSV output.
        as_text = format(normalized, 'f')
        if '.' in as_text:
            as_text = as_text.rstrip('0').rstrip('.')
        return as_text

    def _first_present_value(self, row, column_names):
        for name in column_names:
            value = row.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ''

    def _get_or_create_user(self, username, email='', create_missing_users=False):
        user = User.objects.filter(username=username).first()
        if user:
            return user
        if not create_missing_users:
            return None
        return User.objects.create_user(
            username=username,
            email=email or f'{username}@{self.DEFAULT_EMAIL_DOMAIN}',
            password=self.DEFAULT_IMPORTED_USER_PASSWORD,
        )

    def _sync_user_account(self, user, email, sync_user_credentials=False):
        desired_email = email or f'{user.username}@{self.DEFAULT_EMAIL_DOMAIN}'
        update_fields = []

        if desired_email and user.email != desired_email:
            user.email = desired_email
            update_fields.append('email')

        if sync_user_credentials:
            user.set_password(self.DEFAULT_IMPORTED_USER_PASSWORD)
            update_fields.append('password')

        if update_fields:
            user.save(update_fields=list(dict.fromkeys(update_fields)))

    def _sync_user_profile(self, user, profile_name, profile_name_was_provided, raw_date_of_birth, organization_name):
        year_of_birth = self._resolve_birth_year(raw_date_of_birth)
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

        if raw_date_of_birth:
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

    def _sync_user_organization(self, user, organization_name):
        if not organization_name:
            raise ValueError('co_quan is empty')

        organization = ChalixOrganization.objects.filter(name=organization_name).first()
        if organization is None:
            organization = ChalixOrganization.objects.filter(name__iexact=organization_name).first()
        if organization is None:
            organization = ChalixOrganization.objects.filter(display_name__iexact=organization_name).first()
        if organization is None:
            raise ValueError(f'unmapped co_quan: {organization_name}')

        ChalixUserRole.objects.filter(
            user=user,
            role='cong_chuc',
            is_active=True,
        ).exclude(organization=organization).update(is_active=False)

        role, created = ChalixUserRole.objects.get_or_create(
            user=user,
            role='cong_chuc',
            organization=organization,
            defaults={'is_active': True},
        )
        if not created and not role.is_active:
            role.is_active = True
            role.save(update_fields=['is_active', 'updated_at'])

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