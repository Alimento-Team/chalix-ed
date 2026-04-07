"""Import student learning-process snapshots from CSV."""

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot


class Command(BaseCommand):
    help = 'One-time import for student learning-process snapshots.'

    REQUIRED_COLUMNS = [
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
        'vle_1',
        'vle_2',
        'vle_3',
        'final_score',
    ]

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', required=True, help='Path to source CSV file.')
        parser.add_argument('--schema-path', required=True, help='Path to dataset description JSON file.')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate and parse data without writing rows.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path']).expanduser().resolve()
        schema_path = Path(options['schema_path']).expanduser().resolve()
        dry_run = options['dry_run']

        if not csv_path.exists():
            raise CommandError(f'CSV file does not exist: {csv_path}')
        if not schema_path.exists():
            raise CommandError(f'Schema file does not exist: {schema_path}')

        codebooks = self._load_codebooks(schema_path)

        created_count = 0
        skipped_count = 0
        failed_count = 0
        error_examples = []

        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            self._validate_header(reader.fieldnames)

            for row_number, row in enumerate(reader, start=2):
                try:
                    payload = self._parse_row(row, row_number, codebooks)
                except ValueError as exc:
                    failed_count += 1
                    if len(error_examples) < 10:
                        error_examples.append(f'row {row_number}: {exc}')
                    continue

                if dry_run:
                    created_count += 1
                    continue

                with transaction.atomic():
                    obj, created = StudentLearningProcessSnapshot.objects.get_or_create(
                        student_id=payload['student_id'],
                        defaults=payload,
                    )
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1
                        self._update_user_link_if_missing(obj, payload['user'])

        mode = 'DRY RUN' if dry_run else 'IMPORT'
        self.stdout.write(self.style.SUCCESS(f'{mode} complete'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Skipped (already exists): {skipped_count}')
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
        missing = [name for name in self.REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise CommandError(f'CSV is missing required columns: {missing}')

    def _parse_row(self, row, row_number, codebooks):
        student_id = row['student_id'].strip()
        if not student_id:
            raise ValueError('student_id is empty')

        user = User.objects.filter(username=student_id).first()
        if not user:
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

        vle_1 = self._parse_int(row['vle_1'], 'vle_1', minimum=0)
        vle_2 = self._parse_int(row['vle_2'], 'vle_2', minimum=0)
        vle_3 = self._parse_int(row['vle_3'], 'vle_3', minimum=0)

        return {
            'user': user,
            'student_id': student_id,
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

    def _parse_int(self, value, field_name, minimum=0):
        try:
            parsed = int(value)
        except (ValueError, TypeError):
            raise ValueError(f'invalid integer for {field_name}: {value}')
        if parsed < minimum:
            raise ValueError(f'{field_name} must be >= {minimum}: {parsed}')
        return parsed

    def _normalize_text(self, value):
        return ' '.join(str(value).strip().split()).lower()

    def _update_user_link_if_missing(self, obj, user):
        if obj.user_id is None and user:
            obj.user = user
            obj.save(update_fields=['user', 'updated_at'])
