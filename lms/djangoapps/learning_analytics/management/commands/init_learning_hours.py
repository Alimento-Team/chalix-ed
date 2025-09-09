"""
Management command to initialize learning hours requirements for users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from lms.djangoapps.learning_analytics.models import LearningHoursRequirement
from lms.djangoapps.learning_analytics.services import LearningHoursService


class Command(BaseCommand):
    help = 'Initialize learning hours requirements for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year for which to create requirements (default: current year)'
        )
        parser.add_argument(
            '--required-hours',
            type=int,
            default=40,
            help='Default required hours (default: 40)'
        )
        parser.add_argument(
            '--users',
            nargs='+',
            help='Specific user IDs to initialize (default: all active users)'
        )

    def handle(self, *args, **options):
        year = options['year']
        required_hours = options['required_hours']
        user_ids = options.get('users')

        # Get users to process
        if user_ids:
            users = User.objects.filter(id__in=user_ids, is_active=True)
        else:
            users = User.objects.filter(is_active=True)

        created_count = 0
        updated_count = 0

        self.stdout.write(f"Processing {users.count()} users for year {year}")

        for user in users:
            requirement, created = LearningHoursRequirement.objects.get_or_create(
                user=user,
                current_year=year,
                defaults={
                    'required_hours': required_hours,
                    'status': 'in_progress'
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f"Created requirement for user {user.username}")
            else:
                # Update existing requirement if needed
                if requirement.required_hours != required_hours:
                    requirement.required_hours = required_hours
                    requirement.save()
                    updated_count += 1
                    self.stdout.write(f"Updated requirement for user {user.username}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully initialized learning hours requirements:\n"
                f"- Created: {created_count}\n"
                f"- Updated: {updated_count}\n"
                f"- Total processed: {created_count + updated_count}"
            )
        )
