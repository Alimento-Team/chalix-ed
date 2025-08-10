"""
Signal handlers to set Vietnamese as default language for new users.
ALL SIGNAL HANDLERS DISABLED - Using alternative approaches to avoid IntegrityError
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, has_user_preference
import logging

log = logging.getLogger(__name__)


@receiver(user_logged_in)  # RE-ENABLED - Safe now that admin email validation is fixed
def set_vietnamese_on_first_login(sender, request, user, **kwargs):
    """
    Set Vietnamese as default language preference when user logs in.
    This is now safe to use since we've fixed the admin interface to prevent empty emails.
    """
    try:
        from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
        from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, has_user_preference

        # Only set if user doesn't already have a language preference
        if not has_user_preference(user, LANGUAGE_KEY):
            set_user_preference(user, LANGUAGE_KEY, 'vi')
            log.info(f"Set Vietnamese as default language for user on login: {user.username}")

    except Exception as e:
        # Log but don't re-raise to prevent login issues
        log.warning(f"Failed to set Vietnamese language preference on login for user {user.username}: {e}")


# Keep the old function but completely disabled for reference
# @receiver(post_save, sender=User)  # Completely disabled - was causing IntegrityError
def set_default_language_for_new_user(sender, instance, created, **kwargs):
    """
    DISABLED: This signal handler was causing IntegrityError: (1062, "Duplicate entry '' for key 'auth_user.email'")
    Replaced with user_logged_in signal approach above.
    """
    return  # Completely disabled

    if not hasattr(instance, 'username') or not instance.username:
        return

    if not hasattr(instance, 'email') or not instance.email:
        return

    # Skip if user is not active
    if not instance.is_active:
        return

    # Skip if email is empty or whitespace only (critical for MySQL duplicate key prevention)
    if not instance.email.strip():
        return

    def safe_set_language_preference():
        """
        Safely set the language preference with comprehensive error handling
        to prevent any interference with user creation.
        """
        try:
            # Re-fetch the user to ensure it still exists and get latest state
            user = User.objects.get(pk=instance.pk)

            # Validate the user still has required data
            if not user.email or not user.email.strip() or not user.is_active:
                return

            # Only set if user doesn't already have a language preference
            if not has_user_preference(user, LANGUAGE_KEY):
                set_user_preference(user, LANGUAGE_KEY, 'vi')
                log.info(f"Set Vietnamese as default language for user: {user.username}")

        except User.DoesNotExist:
            # User was deleted between signal and this execution, ignore
            pass
        except Exception as e:
            # Log but don't re-raise to prevent interfering with user creation
            log.error(f"Error setting language preference for user {instance.username}: {e}")

    try:
        # Execute after transaction commit to ensure user creation is complete
        transaction.on_commit(safe_set_language_preference)
    except Exception:
        # If we can't schedule the preference setting, just skip it silently
        # to avoid any interference with the user creation process
        pass
