"""
Management command to migrate existing course completion data to learning hours.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from lms.djangoapps.learning_analytics.services import LearningHoursService
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.courseware.models import StudentModule


class Command(BaseCommand):
    help = 'Migrate existing course completion data to learning hours tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year to migrate data for (default: current year)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making changes'
        )

    def handle(self, *args, **options):
        year = options['year']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write("DRY RUN MODE - No data will be modified")

        # Get all course enrollments for the year
        enrollments = CourseEnrollment.objects.filter(
            created__year=year,
            is_active=True
        )

        total_processed = 0
        total_hours_tracked = 0

        for enrollment in enrollments:
            user = enrollment.user
            course_id = enrollment.course_id

            # Check if user has completed modules in this course
            completed_modules = StudentModule.objects.filter(
                student=user,
                course_id=course_id,
                grade__isnull=False,
                grade__gt=0
            ).count()

            if completed_modules > 0:
                # Estimate hours based on completed modules
                estimated_minutes = completed_modules * 20  # 20 minutes per module average
                estimated_hours = round(estimated_minutes / 60, 1)

                self.stdout.write(
                    f"User: {user.username}, Course: {course_id}, "
                    f"Modules: {completed_modules}, Estimated hours: {estimated_hours}"
                )

                if not dry_run:
                    # Track the estimated time
                    LearningHoursService.track_time_spent(
                        user=user,
                        course_id=course_id,
                        minutes_spent=estimated_minutes
                    )

                total_processed += 1
                total_hours_tracked += estimated_hours

                # Check if user has a certificate for additional hours
                certificate = GeneratedCertificate.objects.filter(
                    user=user,
                    course_id=course_id,
                    status='downloadable'
                ).first()

                if certificate and not dry_run:
                    # Add bonus hours for course completion
                    LearningHoursService.track_time_spent(
                        user=user,
                        course_id=course_id,
                        minutes_spent=60  # 1 hour bonus for completion
                    )
                    total_hours_tracked += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration complete:\n"
                f"- Processed enrollments: {total_processed}\n"
                f"- Total estimated hours: {total_hours_tracked:.1f}\n"
                f"- Mode: {'DRY RUN' if dry_run else 'LIVE'}"
            )
        )
