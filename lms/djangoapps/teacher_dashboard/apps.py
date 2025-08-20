"""
Django app configuration for Teacher Dashboard.
"""

from django.apps import AppConfig


class TeacherDashboardConfig(AppConfig):
    """
    Configuration for the Teacher Dashboard Django app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms.djangoapps.teacher_dashboard'
    verbose_name = 'Teacher Dashboard'
