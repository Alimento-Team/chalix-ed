"""Import predicted scores into existing StudentLearningProcessSnapshot rows.

CSV must contain at minimum: student_id, course_id, predicted_result_1
Optional columns: predicted_result_2, predicted_result_3

Only updates rows that already exist (students previously imported via
import_student_learning_process).  No user creation, no org lookup, no CMS
prep step required.

Usage:
    ./manage.py lms import_prediction_scores --csv-path /path/to/file.csv
    ./manage.py lms import_prediction_scores --csv-path /path/to/file.csv --dry-run
"""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot

REQUIRED_COLUMNS = {'student_id', 'course_id', 'predicted_result_1'}
PREDICTION_COLUMNS = ['predicted_result_1', 'predicted_result_2', 'predicted_result_3']


def _to_decimal(value):
    """Return Decimal or None; None if blank/invalid."""
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    try:
        return Decimal(v)
    except InvalidOperation:
        return None


class Command(BaseCommand):
    help = 'Update predicted scores on existing StudentLearningProcessSnapshot rows from CSV.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            required=True,
            help='Path to the CSV file containing prediction columns.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Validate and report without writing to the database.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        dry_run = options['dry_run']

        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN – no changes will be written.'))

        updated = 0
        skipped_missing = 0
        skipped_invalid = 0
        now = timezone.now()

        with csv_path.open(newline='', encoding='utf-8-sig') as fh:
            reader = csv.DictReader(fh)
            headers = set(reader.fieldnames or [])

            missing_required = REQUIRED_COLUMNS - headers
            if missing_required:
                raise CommandError(
                    f'CSV is missing required columns: {", ".join(sorted(missing_required))}'
                )

            for row_num, row in enumerate(reader, start=2):
                student_id = str(row.get('student_id', '')).strip()
                course_id = str(row.get('course_id', '')).strip()

                if not student_id or not course_id:
                    self.stderr.write(f'Row {row_num}: blank student_id or course_id – skipped.')
                    skipped_invalid += 1
                    continue

                pred_1 = _to_decimal(row.get('predicted_result_1'))
                pred_2 = _to_decimal(row.get('predicted_result_2')) if 'predicted_result_2' in headers else None
                pred_3 = _to_decimal(row.get('predicted_result_3')) if 'predicted_result_3' in headers else None

                if pred_1 is None:
                    self.stderr.write(
                        f'Row {row_num}: invalid predicted_result_1 for student {student_id} – skipped.'
                    )
                    skipped_invalid += 1
                    continue

                try:
                    snapshot = StudentLearningProcessSnapshot.objects.get(
                        student_id=student_id,
                        course_id=course_id,
                    )
                except StudentLearningProcessSnapshot.DoesNotExist:
                    self.stderr.write(
                        f'Row {row_num}: no snapshot for student={student_id} course={course_id} – skipped.'
                    )
                    skipped_missing += 1
                    continue

                # Map predicted_result_N → estimated_week_N
                snapshot.estimated_week_1 = pred_1
                snapshot.estimated_week_2 = pred_2
                snapshot.estimated_week_3 = pred_3

                # Use the last available prediction as the predicted final score
                predicted_final = pred_3 if pred_3 is not None else (pred_2 if pred_2 is not None else pred_1)
                snapshot.predicted_final_score = predicted_final

                # Determine which week the latest prediction came from
                if pred_3 is not None:
                    prediction_week = 3
                elif pred_2 is not None:
                    prediction_week = 2
                else:
                    prediction_week = 1

                snapshot.prediction_source = 'imported'
                snapshot.prediction_week = prediction_week
                snapshot.prediction_updated_at = now

                if not dry_run:
                    snapshot.save(update_fields=[
                        'estimated_week_1',
                        'estimated_week_2',
                        'estimated_week_3',
                        'predicted_final_score',
                        'prediction_source',
                        'prediction_week',
                        'prediction_updated_at',
                    ])

                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Done. '
                f'Updated: {updated} | Skipped (no snapshot): {skipped_missing} | '
                f'Skipped (invalid): {skipped_invalid}'
            )
        )
