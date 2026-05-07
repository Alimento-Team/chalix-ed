from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0014_student_snapshot_source_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='learnerbehavior',
            name='materials_opened',
            field=models.IntegerField(default=0, help_text='Slides/HTML material opens'),
        ),
    ]
