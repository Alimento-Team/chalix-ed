"""
App configuration for facial expression recording.
"""
from django.apps import AppConfig


class FacialExpressionConfig(AppConfig):
    """Configuration for the facial expression app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms.djangoapps.facial_expression'
    verbose_name = "Facial Expression Recording"

    def ready(self):
        """Import signal handlers when the app is ready."""
        pass
