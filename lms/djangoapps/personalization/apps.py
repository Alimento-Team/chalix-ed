"""
Django app configuration for personalization module.
"""

from django.apps import AppConfig


class PersonalizationConfig(AppConfig):
    name = 'lms.djangoapps.personalization'
    verbose_name = 'Student Personalization and Learning Statistics'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        # Import signals to register them
        # from . import signals  # Uncomment when signals are created
        pass
