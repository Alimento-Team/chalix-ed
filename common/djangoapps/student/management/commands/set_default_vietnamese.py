"""
Management command to set Vietnamese as the default language for new user registrations.
"""
from django.core.management.base import BaseCommand
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from django.contrib.auth.models import User


class Command(BaseCommand):
    """
    Set Vietnamese as default language for all users who don't have a language preference set.
    """
    help = 'Set Vietnamese as default language for users without language preference'

    def handle(self, *args, **options):
        """
        Main command logic
        """
        from openedx.core.djangoapps.user_api.models import UserPreference

        # Get users without language preference
        users_with_lang_pref = UserPreference.objects.filter(key=LANGUAGE_KEY).values_list('user_id', flat=True)
        users_without_lang_pref = User.objects.exclude(id__in=users_with_lang_pref)

        count = 0
        for user in users_without_lang_pref:
            try:
                set_user_preference(user, LANGUAGE_KEY, 'vi')
                count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to set language preference for user {user.username}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully set Vietnamese as default language for {count} users')
        )
