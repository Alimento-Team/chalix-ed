"""
Management command to sync learning hours with external LMS data.
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

from lms.djangoapps.learning_analytics.models import LearnerBehavior
from lms.djangoapps.learning_analytics.services import LearningHoursService


class Command(BaseCommand):
    help = 'Sync learning hours data with external LMS or import from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            help='Path to JSON file containing learning hours data'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['simple', 'detailed'],
            default='simple',
            help='Format of the JSON data (simple or detailed)'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        data_format = options['format']

        if not json_file:
            self.stdout.write(self.style.ERROR("Please provide --json-file argument"))
            return

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {json_file}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON format: {e}"))
            return

        if data_format == 'simple':
            self._process_simple_format(data)
        else:
            self._process_detailed_format(data)

    def _process_simple_format(self, data):
        """
        Process simple format:
        {
            "username": minutes_spent,
            "user2": minutes_spent,
            ...
        }
        """
        processed = 0
        errors = 0

        for username, minutes in data.items():
            try:
                user = User.objects.get(username=username)
                
                # Create or update learning behavior
                behavior, created = LearnerBehavior.objects.get_or_create(
                    user=user,
                    defaults={
                        'total_time_spent_minutes': minutes,
                        'last_activity': timezone.now()
                    }
                )
                
                if not created:
                    behavior.total_time_spent_minutes = minutes
                    behavior.last_activity = timezone.now()
                    behavior.save()

                self.stdout.write(f"✓ Updated {username}: {minutes} minutes")
                processed += 1

            except User.DoesNotExist:
                self.stdout.write(f"✗ User not found: {username}")
                errors += 1
            except Exception as e:
                self.stdout.write(f"✗ Error processing {username}: {e}")
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nProcessed: {processed}, Errors: {errors}")
        )

    def _process_detailed_format(self, data):
        """
        Process detailed format:
        {
            "users": [
                {
                    "username": "user1",
                    "sessions": [
                        {
                            "date": "2024-01-15",
                            "minutes": 45,
                            "course_id": "course-v1:org+course+run"
                        }
                    ]
                }
            ]
        }
        """
        processed = 0
        errors = 0

        for user_data in data.get('users', []):
            username = user_data.get('username')
            sessions = user_data.get('sessions', [])

            try:
                user = User.objects.get(username=username)
                
                total_minutes = 0
                for session in sessions:
                    minutes = session.get('minutes', 0)
                    course_id = session.get('course_id')
                    session_date = session.get('date')

                    # Parse date
                    if session_date:
                        session_datetime = datetime.strptime(session_date, '%Y-%m-%d')
                        session_datetime = timezone.make_aware(session_datetime)
                    else:
                        session_datetime = timezone.now()

                    # Track the session time
                    if course_id:
                        LearningHoursService.track_time_spent(
                            user=user,
                            course_id=course_id,
                            minutes_spent=minutes
                        )
                    
                    total_minutes += minutes

                self.stdout.write(
                    f"✓ Updated {username}: {len(sessions)} sessions, {total_minutes} total minutes"
                )
                processed += 1

            except User.DoesNotExist:
                self.stdout.write(f"✗ User not found: {username}")
                errors += 1
            except Exception as e:
                self.stdout.write(f"✗ Error processing {username}: {e}")
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nProcessed: {processed}, Errors: {errors}")
        )
