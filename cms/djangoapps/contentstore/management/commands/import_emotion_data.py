import csv
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Q, Sum

from cms.djangoapps.contentstore.models import (
    ChalixStudentEmotion,
    ChalixTopicEmotionAggregate,
)


class Command(BaseCommand):
    help = "Import emotion_data.csv and recompute topic adjustment aggregates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            dest="file_path",
            default="",
            help="Path to emotion_data.csv. Defaults to <workspace>/dataset/emo/emotion_data.csv.",
        )
        parser.add_argument(
            "--batch",
            dest="batch_name",
            default="",
            help="Optional source batch label for traceability.",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            dest="truncate",
            default=True,
            help="Replace all existing imported emotion data before import (default).",
        )
        parser.add_argument(
            "--no-truncate",
            action="store_false",
            dest="truncate",
            help="Keep existing rows and upsert by (student_id, course_id, topic_number).",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file_path"]).expanduser() if options["file_path"] else self._default_csv_path()
        if not csv_path.exists() or not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        batch_name = options["batch_name"].strip() or datetime.utcnow().strftime("seed_%Y%m%d_%H%M%S")
        truncate = bool(options["truncate"])

        required_columns = {
            "student_id",
            "course_id",
            "course_name",
            "topic_number",
            "topic_name",
            "emotion",
        }

        valid_rows = []
        invalid_rows = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV file has no header row")

            missing_columns = required_columns.difference(set(reader.fieldnames))
            if missing_columns:
                raise CommandError(
                    "CSV missing required columns: " + ", ".join(sorted(missing_columns))
                )

            for row_number, row in enumerate(reader, start=2):
                student_id = (row.get("student_id") or "").strip()
                course_id = (row.get("course_id") or "").strip()
                course_name = (row.get("course_name") or "").strip()
                topic_number = (row.get("topic_number") or "").strip()
                topic_name = (row.get("topic_name") or "").strip()
                emotion_raw = (row.get("emotion") or "").strip()

                if not all([student_id, course_id, topic_number]):
                    invalid_rows += 1
                    self.stderr.write(
                        f"Skip row {row_number}: missing student_id/course_id/topic_number"
                    )
                    continue

                try:
                    emotion = int(emotion_raw)
                except (TypeError, ValueError):
                    invalid_rows += 1
                    self.stderr.write(f"Skip row {row_number}: invalid emotion '{emotion_raw}'")
                    continue

                if emotion not in {1, 0, -1}:
                    invalid_rows += 1
                    self.stderr.write(f"Skip row {row_number}: emotion must be one of 1, 0, -1")
                    continue

                valid_rows.append(
                    ChalixStudentEmotion(
                        student_id=student_id,
                        course_id=course_id,
                        course_name=course_name,
                        topic_number=topic_number,
                        topic_name=topic_name,
                        emotion=emotion,
                        source_batch=batch_name,
                    )
                )

        if not valid_rows:
            raise CommandError("No valid rows found in CSV; import aborted")

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            if truncate:
                ChalixStudentEmotion.objects.all().delete()
                ChalixStudentEmotion.objects.bulk_create(valid_rows, batch_size=2000)
                created_count = len(valid_rows)
            else:
                for item in valid_rows:
                    defaults = {
                        "course_name": item.course_name,
                        "topic_name": item.topic_name,
                        "emotion": item.emotion,
                        "source_batch": batch_name,
                    }
                    _, created = ChalixStudentEmotion.objects.update_or_create(
                        student_id=item.student_id,
                        course_id=item.course_id,
                        topic_number=item.topic_number,
                        defaults=defaults,
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            ChalixTopicEmotionAggregate.objects.all().delete()
            aggregate_rows = (
                ChalixStudentEmotion.objects.values(
                    "course_id",
                    "course_name",
                    "topic_number",
                    "topic_name",
                )
                .annotate(
                    like_count=Count("id", filter=Q(emotion=1)),
                    neutral_count=Count("id", filter=Q(emotion=0)),
                    dislike_count=Count("id", filter=Q(emotion=-1)),
                    score_sum=Sum("emotion"),
                )
                .order_by("course_id", "topic_number")
            )

            aggregate_objects = []
            for row in aggregate_rows:
                score_sum = int(row.get("score_sum") or 0)
                aggregate_objects.append(
                    ChalixTopicEmotionAggregate(
                        course_id=row["course_id"],
                        course_name=row.get("course_name") or "",
                        topic_number=row["topic_number"],
                        topic_name=row.get("topic_name") or "",
                        like_count=int(row.get("like_count") or 0),
                        neutral_count=int(row.get("neutral_count") or 0),
                        dislike_count=int(row.get("dislike_count") or 0),
                        score_sum=score_sum,
                        adjust_required=score_sum < 0,
                        source_batch=batch_name,
                    )
                )

            ChalixTopicEmotionAggregate.objects.bulk_create(aggregate_objects, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("Emotion import completed"))
        self.stdout.write(f"File: {csv_path}")
        self.stdout.write(f"Batch: {batch_name}")
        self.stdout.write(f"Valid rows: {len(valid_rows)}")
        self.stdout.write(f"Invalid rows: {invalid_rows}")
        self.stdout.write(f"Inserted student rows: {created_count}")
        if not truncate:
            self.stdout.write(f"Updated student rows: {updated_count}")
        self.stdout.write(f"Aggregate rows: {len(aggregate_objects)}")

    @staticmethod
    def _default_csv_path() -> Path:
        base_dir = Path(getattr(settings, "BASE_DIR", ".")).resolve()
        return base_dir.parent / "dataset" / "emo" / "emotion_data.csv"
