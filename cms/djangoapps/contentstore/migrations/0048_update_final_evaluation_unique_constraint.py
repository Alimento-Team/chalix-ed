# Generated migration for final evaluation multiple types support

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0047_add_final_evaluation_models'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='finalevaluation',
            unique_together={('course_key', 'program', 'evaluation_type')},
        ),
    ]