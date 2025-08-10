"""
Middleware to set Vietnamese as default language for new users.
This is a safer alternative to using post_save signals that can interfere with user creation.
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, has_user_preference
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class VietnameseDefaultLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to set Vietnamese as default language for authenticated users
    who don't have a language preference set.

    This runs during request processing rather than during user creation,
    which avoids interfering with the user creation process.
    """

    def process_request(self, request):
        """
        Check if the authenticated user needs Vietnamese set as default language.
        """
        # Only process for authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        user = request.user

        # Skip if user doesn't have valid email
        if not user.email or not user.email.strip():
            return None

        # Skip if user is not active
        if not user.is_active:
            return None

        # Check if this user has been processed in this session
        session_key = f'vi_lang_set_for_user_{user.id}'
        if request.session.get(session_key, False):
            return None

        try:
            # Only set if user doesn't already have a language preference
            if not has_user_preference(user, LANGUAGE_KEY):
                set_user_preference(user, LANGUAGE_KEY, 'vi')
                logger.info(f"Set Vietnamese as default language for user: {user.username}")

                # Mark this user as processed in the session to avoid repeated checks
                request.session[session_key] = True

        except Exception as e:
            logger.error(f"Error setting Vietnamese default for user {user.username}: {e}")

        return None
