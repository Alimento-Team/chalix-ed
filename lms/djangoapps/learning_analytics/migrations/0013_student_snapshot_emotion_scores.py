from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0012_student_snapshot_course_scope'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='eye_score',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='nose_score',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='mouth_score',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='emotion_score',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True),
        ),
    ]
