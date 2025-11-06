# Generated migration for facial expression log model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_analytics', '0001_initial'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='FacialExpressionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(help_text='Course ID', max_length=255)),
                ('unit_id', models.CharField(help_text='Unit/Block ID (slide or video)', max_length=255)),
                ('topic_id', models.CharField(blank=True, help_text='Topic/Section ID', max_length=255, null=True)),
                ('program_id', models.CharField(blank=True, help_text='Program ID', max_length=255, null=True)),
                ('org_id', models.CharField(blank=True, help_text='Organization ID', max_length=255, null=True)),
                ('video_path', models.CharField(help_text='MinIO storage path for the video file', max_length=512)),
                ('video_size', models.BigIntegerField(default=0, help_text='Video file size in bytes')),
                ('duration_seconds', models.IntegerField(default=0, help_text='Recording duration in seconds')),
                ('start_timestamp', models.DateTimeField(help_text='When the recording started')),
                ('end_timestamp', models.DateTimeField(blank=True, help_text='When the recording ended', null=True)),
                ('is_complete', models.BooleanField(default=False, help_text='Whether this is a complete recording or partial chunk')),
                ('processing_status', models.CharField(choices=[('pending', 'Pending Processing'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', help_text='Status of video processing/analysis', max_length=20)),
                ('analysis_results', models.JSONField(blank=True, help_text='JSON data containing facial expression analysis results', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facial_expression_logs', to=settings.AUTH_USER_MODEL)),
                ('teacher_id', models.ForeignKey(blank=True, help_text='Teacher/Instructor for this course', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='student_facial_expressions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-start_timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='facialexpressionlog',
            index=models.Index(fields=['user', 'course_id'], name='learning_an_user_id_course_idx'),
        ),
        migrations.AddIndex(
            model_name='facialexpressionlog',
            index=models.Index(fields=['course_id', 'unit_id'], name='learning_an_course_unit_idx'),
        ),
        migrations.AddIndex(
            model_name='facialexpressionlog',
            index=models.Index(fields=['start_timestamp'], name='learning_an_start_t_idx'),
        ),
        migrations.AddIndex(
            model_name='facialexpressionlog',
            index=models.Index(fields=['processing_status'], name='learning_an_process_idx'),
        ),
    ]
