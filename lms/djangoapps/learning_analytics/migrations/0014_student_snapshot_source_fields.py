from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0013_student_snapshot_emotion_scores'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='completed_percentage',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='external_user_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='status',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='total_studied_time',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(completed_percentage__isnull=True) |
                    (models.Q(completed_percentage__gte=0) & models.Q(completed_percentage__lte=100))
                ),
                name='la_snapshot_completed_pct_0_100',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(total_studied_time__isnull=True) |
                    models.Q(total_studied_time__gte=0)
                ),
                name='la_snapshot_total_studied_time_non_negative',
            ),
        ),
    ]