from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0010_ensure_learnerbehavior_activity_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentlearningprocesssnapshot',
            name='final_score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='predicted_final_score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='prediction_source',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='prediction_week',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='prediction_input_hash',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='prediction_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentlearningprocesssnapshot',
            name='prediction_error',
            field=models.TextField(blank=True),
        ),
        migrations.AddIndex(
            model_name='studentlearningprocesssnapshot',
            index=models.Index(fields=['predicted_final_score'], name='learning_an_predict_6e2f18_idx'),
        ),
        migrations.RemoveConstraint(
            model_name='studentlearningprocesssnapshot',
            name='la_snapshot_final_0_10',
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(final_score__isnull=True)
                    | (models.Q(final_score__gte=0) & models.Q(final_score__lte=10))
                ),
                name='la_snapshot_final_0_10',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(predicted_final_score__isnull=True)
                    | (models.Q(predicted_final_score__gte=0) & models.Q(predicted_final_score__lte=10))
                ),
                name='la_snapshot_predicted_final_0_10',
            ),
        ),
    ]
