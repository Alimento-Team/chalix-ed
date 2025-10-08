# Generated manually for Chalix role system updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0053_rename_contentstore_chalixquiz_course_key_is_active_idx_contentstor_course__eee874_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chalixuserrole',
            name='role',
            field=models.CharField(
                choices=[
                    ('department', 'Department'),
                    ('division', 'Division'),
                    ('instructor', 'Instructor'),
                    ('learner', 'Learner')
                ],
                max_length=20
            ),
        ),
    ]