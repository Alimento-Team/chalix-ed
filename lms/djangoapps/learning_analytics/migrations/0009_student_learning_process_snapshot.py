# Generated manually for student learning process snapshots

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_analytics', '0008_rename_learning_an_user_id_course_idx_learning_an_user_id_bb03fa_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentLearningProcessSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=32, unique=True)),
                ('position_code', models.PositiveSmallIntegerField()),
                ('position_text', models.CharField(max_length=64)),
                ('gender_code', models.PositiveSmallIntegerField()),
                ('gender_text', models.CharField(max_length=32)),
                ('location_code', models.PositiveSmallIntegerField()),
                ('location_text', models.CharField(max_length=128)),
                ('age_code', models.PositiveSmallIntegerField()),
                ('age_text', models.CharField(max_length=64)),
                ('job_title_code', models.PositiveSmallIntegerField()),
                ('job_title_text', models.CharField(max_length=64)),
                ('experience_code', models.PositiveSmallIntegerField()),
                ('experience_text', models.CharField(max_length=64)),
                ('week_1', models.DecimalField(decimal_places=2, max_digits=4)),
                ('week_2', models.DecimalField(decimal_places=2, max_digits=4)),
                ('week_3', models.DecimalField(decimal_places=2, max_digits=4)),
                ('vle_1', models.PositiveIntegerField()),
                ('vle_2', models.PositiveIntegerField()),
                ('vle_3', models.PositiveIntegerField()),
                ('final_score', models.DecimalField(decimal_places=2, max_digits=4)),
                ('source_file', models.CharField(blank=True, max_length=255)),
                ('source_row_number', models.PositiveIntegerField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='learning_process_snapshots',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['student_id'],
            },
        ),
        migrations.AddIndex(
            model_name='studentlearningprocesssnapshot',
            index=models.Index(fields=['user'], name='learning_an_user_id_8fdb00_idx'),
        ),
        migrations.AddIndex(
            model_name='studentlearningprocesssnapshot',
            index=models.Index(fields=['location_code'], name='learning_an_locatio_bec31a_idx'),
        ),
        migrations.AddIndex(
            model_name='studentlearningprocesssnapshot',
            index=models.Index(fields=['final_score'], name='learning_an_final_s_3a9f4f_idx'),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=models.Q(('week_1__gte', 0), ('week_1__lte', 10)),
                name='la_snapshot_week_1_0_10',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=models.Q(('week_2__gte', 0), ('week_2__lte', 10)),
                name='la_snapshot_week_2_0_10',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=models.Q(('week_3__gte', 0), ('week_3__lte', 10)),
                name='la_snapshot_week_3_0_10',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentlearningprocesssnapshot',
            constraint=models.CheckConstraint(
                check=models.Q(('final_score__gte', 0), ('final_score__lte', 10)),
                name='la_snapshot_final_0_10',
            ),
        ),
    ]
