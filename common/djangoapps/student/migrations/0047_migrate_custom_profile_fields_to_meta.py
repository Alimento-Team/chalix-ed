"""Migrate custom Chalix profile fields into the UserProfile.meta JSON field.

This data migration will copy values from custom columns (if they exist)
into the `meta` JSON stored on the UserProfile model. The migration is
careful: if a column does not exist on the model/schema it will be skipped.
After copying, the migration will null out the original column values to
avoid duplication while keeping the DB schema intact (no column drops).

Reversible: the reverse operation will attempt to copy values back from
`meta` into the original columns if they exist.
"""

from django.db import migrations
import json


CUSTOM_FIELDS = [
    'ten_co_quan',
    'ten_phong_ban',
    'work_position',
]


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('student', 'UserProfile')
    for profile in UserProfile.objects.all():
        try:
            meta = profile.get_meta() if hasattr(profile, 'get_meta') else (json.loads(profile.meta) if profile.meta else {})
        except Exception:
            meta = {}

        changed = False
        for field in CUSTOM_FIELDS:
            # Only process if the profile instance has the attribute
            if hasattr(profile, field):
                val = getattr(profile, field)
                # Only copy into meta if the value exists and meta doesn't already have it
                if val and not meta.get(field):
                    meta[field] = val
                    try:
                        setattr(profile, field, None)
                    except Exception:
                        # If we cannot set the field to None, ignore and continue
                        pass
                    changed = True

        if changed:
            # Save meta JSON back into profile.meta
            try:
                if hasattr(profile, 'set_meta'):
                    profile.set_meta(meta)
                else:
                    profile.meta = json.dumps(meta)
                profile.save()
            except Exception:
                # If saving fails for some profile, skip and continue
                continue


def backwards(apps, schema_editor):
    UserProfile = apps.get_model('student', 'UserProfile')
    for profile in UserProfile.objects.all():
        try:
            meta = profile.get_meta() if hasattr(profile, 'get_meta') else (json.loads(profile.meta) if profile.meta else {})
        except Exception:
            meta = {}

        changed = False
        for field in CUSTOM_FIELDS:
            if field in meta and hasattr(profile, field):
                try:
                    setattr(profile, field, meta.get(field))
                    changed = True
                    # remove from meta
                    meta.pop(field, None)
                except Exception:
                    pass

        if changed:
            try:
                if hasattr(profile, 'set_meta'):
                    profile.set_meta(meta)
                else:
                    profile.meta = json.dumps(meta)
                profile.save()
            except Exception:
                continue


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0046_alter_userprofile_phone_number'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
