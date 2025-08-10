"""
Management command to set Vietnamese as default language for users who don't have a language preference.
This is a safer alternative to using post_save signals.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, has_user_preference
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set Vietnamese as default language for users who do not have a language preference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write(f"Looking for users without language preference...")

        # Find active users who don't have a language preference and have valid emails
        users_processed = 0
        users_updated = 0

        # Process users in batches to avoid memory issues
        user_queryset = User.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(email__exact='').exclude(email__exact='').order_by('id')

        total_users = user_queryset.count()
        self.stdout.write(f"Found {total_users} active users with emails to check")

        for offset in range(0, total_users, batch_size):
            batch = user_queryset[offset:offset + batch_size]

            for user in batch:
                users_processed += 1

                try:
                    # Check if user already has a language preference
                    if not has_user_preference(user, LANGUAGE_KEY):
                        if dry_run:
                            self.stdout.write(f"[DRY RUN] Would set Vietnamese for user: {user.username}")
                            users_updated += 1
                        else:
                            set_user_preference(user, LANGUAGE_KEY, 'vi')
                            self.stdout.write(f"Set Vietnamese for user: {user.username}")
                            users_updated += 1

                except Exception as e:
                    logger.error(f"Error processing user {user.username}: {e}")
                    self.stderr.write(f"Error processing user {user.username}: {e}")

                # Progress indicator
                if users_processed % 100 == 0:
                    self.stdout.write(f"Processed {users_processed}/{total_users} users...")

        action = "Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Complete! {action} {users_updated} out of {users_processed} users with Vietnamese language preference"
            )
        )
