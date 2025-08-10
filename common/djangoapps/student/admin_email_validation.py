"""
Admin-specific validation to prevent empty email users.
This prevents the IntegrityError when creating users through Django admin.
"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
import logging

log = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def validate_user_email_not_empty(sender, instance, **kwargs):
    """
    Prevent saving users with empty email addresses.
    This prevents MySQL duplicate key errors on the unique email constraint.
    """
    # Only validate for new users or when email is being changed
    if not instance.pk or (hasattr(instance, '_state') and instance._state.adding):
        if not instance.email or not instance.email.strip():
            log.error(f"Attempted to create user {instance.username} with empty email")
            raise ValidationError({
                'email': 'Email field is required and cannot be empty.'
            })

    # For existing users, ensure email isn't being set to empty
    elif instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
            if original.email and (not instance.email or not instance.email.strip()):
                log.error(f"Attempted to clear email for user {instance.username}")
                raise ValidationError({
                    'email': 'Email field cannot be cleared or set to empty.'
                })
        except User.DoesNotExist:
            # User doesn't exist yet, treat as new user
            if not instance.email or not instance.email.strip():
                log.error(f"Attempted to create user {instance.username} with empty email")
                raise ValidationError({
                    'email': 'Email field is required and cannot be empty.'
                })
