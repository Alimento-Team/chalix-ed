# Generated migration for Chalix profile enhancements

from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0049_cleanup_duplicate_phone_numbers'),
    ]

    operations = [
        # Add unique constraint to phone_number to support phone login
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                validators=[RegexValidator(
                    regex=r'^\+?1?\d*$',
                    message="Phone number must start with '+' (optional) followed by digits (0-9) only.",
                )],
                db_index=False
            ),
        ),

        # Add birth_date field for full date of birth (not just year)
        migrations.AddField(
            model_name='userprofile',
            name='birth_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),

        # Add job_position field with choices
        migrations.AddField(
            model_name='userprofile',
            name='job_position',
            field=models.CharField(
                blank=True,
                choices=[
                    ('leader', 'Lãnh đạo'),
                    ('senior_expert', 'Chuyên viên chính'),
                    ('expert', 'Chuyên viên'),
                    ('staff', 'Nhân viên'),
                ],
                db_index=True,
                max_length=20,
                null=True,
            ),
        ),

        # Add province field for province/region
        migrations.AddField(
            model_name='userprofile',
            name='province',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),

        # Add civil_servant_type field with choices
        migrations.AddField(
            model_name='userprofile',
            name='civil_servant_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('civil_servant', 'Công chức'),
                    ('official', 'Viên chức'),
                ],
                db_index=True,
                max_length=20,
                null=True,
            ),
        ),
    ]
