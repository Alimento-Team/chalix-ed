from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0050_add_chalix_profile_enhancement_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='job_title',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
