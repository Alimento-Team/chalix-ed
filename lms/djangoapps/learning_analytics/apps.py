# lint-amnesty, pylint: disable=missing-module-docstring
from django.apps import AppConfig


class LearningAnalyticsConfig(AppConfig):
    """
    Application Configuration for learning analytics.
    """
    name = 'lms.djangoapps.learning_analytics'
    verbose_name = "Learning Analytics"

    def ready(self):
        # Import signal handlers so they're registered when Django starts.
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid breaking startup if signals import fails; errors will be
            # captured by the Django error logging during startup.
            pass
