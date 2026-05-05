# Generated manually to reconcile migration state with DB-safe operations in 0002.

from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        ('personalization', '0002_alter_lessontimetracking_options_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveIndex(
                    model_name='lessontimetracking',
                    name='personaliza_user_lesson_idx',
                ),
                migrations.RemoveIndex(
                    model_name='lessontimetracking',
                    name='personaliza_lesson_last_accessed_idx',
                ),
                migrations.RemoveIndex(
                    model_name='usercoursepersonalization',
                    name='personaliza_user_id_course_idx',
                ),
                migrations.RemoveIndex(
                    model_name='usercoursepersonalization',
                    name='personaliza_status_idx',
                ),
                migrations.RemoveIndex(
                    model_name='usercoursepersonalization',
                    name='personaliza_last_accessed_idx',
                ),
                migrations.RenameIndex(
                    model_name='personalizationyearlystats',
                    new_name='personaliza_user_id_249a40_idx',
                    old_name='personaliza_user_id_year_idx',
                ),
                migrations.AlterUniqueTogether(
                    name='lessontimetracking',
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='active_courses',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='average_completion_rate',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='certificates_earned',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='completed_courses',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='paused_courses',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='total_courses',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='total_time_hours',
                ),
                migrations.RemoveField(
                    model_name='personalizationyearlystats',
                    name='total_time_minutes',
                ),
                migrations.RemoveField(
                    model_name='usercoursepersonalization',
                    name='certificate_earned_date',
                ),
                migrations.RemoveField(
                    model_name='usercoursepersonalization',
                    name='has_certificate',
                ),
                migrations.RemoveField(
                    model_name='usercoursepersonalization',
                    name='time_spent_hours',
                ),
                migrations.RemoveField(
                    model_name='usercoursepersonalization',
                    name='time_spent_minutes',
                ),
                migrations.AddField(
                    model_name='lessontimetracking',
                    name='completed_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='lessontimetracking',
                    name='course_id',
                    field=opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255),
                ),
                migrations.AddField(
                    model_name='lessontimetracking',
                    name='is_completed',
                    field=models.BooleanField(db_index=True, default=False),
                ),
                migrations.AddField(
                    model_name='lessontimetracking',
                    name='lesson_name',
                    field=models.CharField(blank=True, max_length=255),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='average_time_per_course',
                    field=models.FloatField(default=0.0),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='overall_completion_rate',
                    field=models.FloatField(default=0.0),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='total_certificates_earned',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='total_courses_assigned',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='total_courses_completed',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='personalizationyearlystats',
                    name='total_study_time_hours',
                    field=models.FloatField(default=0.0),
                ),
                migrations.AddField(
                    model_name='usercoursepersonalization',
                    name='average_completion_time_per_lesson',
                    field=models.FloatField(default=0.0),
                ),
                migrations.AddField(
                    model_name='usercoursepersonalization',
                    name='completed_certificates',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='usercoursepersonalization',
                    name='total_certificates',
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name='usercoursepersonalization',
                    name='total_study_time',
                    field=models.FloatField(default=0.0),
                ),
                migrations.AlterUniqueTogether(
                    name='lessontimetracking',
                    unique_together={('user', 'course_id', 'lesson_id')},
                ),
                migrations.AddIndex(
                    model_name='lessontimetracking',
                    index=models.Index(fields=['user', 'course_id', 'is_completed'], name='personaliza_user_id_8184f4_idx'),
                ),
                migrations.AddIndex(
                    model_name='usercoursepersonalization',
                    index=models.Index(fields=['user', 'status'], name='personaliza_user_id_d26a1a_idx'),
                ),
                migrations.AddIndex(
                    model_name='usercoursepersonalization',
                    index=models.Index(fields=['user', 'completion_percentage'], name='personaliza_user_id_8b5491_idx'),
                ),
                migrations.RemoveField(
                    model_name='lessontimetracking',
                    name='access_count',
                ),
                migrations.RemoveField(
                    model_name='lessontimetracking',
                    name='completed',
                ),
                migrations.RemoveField(
                    model_name='lessontimetracking',
                    name='course_personalization',
                ),
                migrations.RemoveField(
                    model_name='lessontimetracking',
                    name='last_accessed',
                ),
            ],
        ),
    ]
