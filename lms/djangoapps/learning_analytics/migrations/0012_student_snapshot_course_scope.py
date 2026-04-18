from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0011_student_snapshot_prediction_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='course_id',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='studentlearningprocesssnapshot',
            name='student_id',
            field=models.CharField(max_length=32),
        ),
        migrations.AddIndex(
            model_name='studentlearningprocesssnapshot',
            index=models.Index(fields=['course_id'], name='learning_an_course__6ad0d9_idx'),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.UniqueConstraint(
                fields=('student_id', 'course_id'),
                name='la_snapshot_student_course_unique',
            ),
        ),
    ]
