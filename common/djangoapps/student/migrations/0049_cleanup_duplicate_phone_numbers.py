# Data migration to handle duplicate phone numbers before adding unique constraint

from django.db import migrations


def cleanup_duplicate_phone_numbers(apps, schema_editor):
    """
    Remove duplicate phone numbers by keeping the first occurrence and clearing others.
    This prepares the data for adding a unique constraint.
    """
    UserProfile = apps.get_model('student', 'UserProfile')
    
    # Find all phone numbers that appear more than once
    from django.db.models import Count
    from django.db.models.functions import Coalesce
    
    duplicate_phones = UserProfile.objects.values('phone_number').filter(
        phone_number__isnull=False
    ).annotate(
        phone_count=Count('id')
    ).filter(
        phone_count__gt=1
    )
    
    # For each duplicate, keep the first and clear the rest
    for dup in duplicate_phones:
        phone = dup['phone_number']
        profiles = UserProfile.objects.filter(phone_number=phone).order_by('id')
        # Keep the first one, clear phone_number for the rest
        for profile in profiles[1:]:
            profile.phone_number = None
            profile.save(update_fields=['phone_number'])


def reverse_cleanup(apps, schema_editor):
    """Reversible - nothing to do on reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0048_add_vietnamese_profile_fields'),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_phone_numbers, reverse_cleanup),
    ]
