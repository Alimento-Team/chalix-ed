"""
Django app configuration for Chalix User Menu
"""
from django.apps import AppConfig


class ChalixUserMenuConfig(AppConfig):
    """
    Configuration for the Chalix User Menu Django app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms.djangoapps.chalix_user_menu'
    verbose_name = 'Chalix User Menu'
