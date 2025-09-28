import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.models.course_enrollment import CourseEnrollment, AlreadyEnrolledError

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Enroll all users into the specified course key. Usage: manage.py enroll_all_users_in_course <course_key> [--skip-staff]"

    def add_arguments(self, parser):
        parser.add_argument('course_key', type=str, help='Opaque course key (e.g., course-v1:Org+Num+Run)')
        parser.add_argument('--skip-staff', action='store_true', default=False, help='Skip staff and superusers')
        parser.add_argument('--batch-size', type=int, default=500, help='Batch size for processing users')

    def handle(self, *args, **options):
        try:
            course_key = CourseKey.from_string(options['course_key'])
        except Exception as exc:
            raise CommandError(f"Invalid course key: {options['course_key']}: {exc}")

        skip_staff = options['skip_staff']
        batch_size = options['batch_size']

        User = get_user_model()
        users_qs = User.objects.all()
        if skip_staff:
            users_qs = users_qs.filter(is_staff=False, is_superuser=False)

        total = users_qs.count()
        self.stdout.write(self.style.NOTICE(f"Enrolling {total} users into {course_key} (skip_staff={skip_staff})"))

        offset = 0
        enrolled = 0
        while True:
            batch = list(users_qs[offset:offset + batch_size])
            if not batch:
                break

            with transaction.atomic():
                for user in batch:
                    try:
                        CourseEnrollment.enroll(user, course_key, check_access=False)
                        enrolled += 1
                    except AlreadyEnrolledError:
                        continue
                    except Exception as exc:  # pragma: no cover - defensive
                        log.exception('Failed to enroll %s into %s: %s', user.username, course_key, exc)

            offset += batch_size

        self.stdout.write(self.style.SUCCESS(f"Completed. Newly enrolled: {enrolled}"))
