"""Initial migration for learning_analytics models.

This migration creates the tables for the various models defined in
`lms/djangoapps/learning_analytics/models.py` so that the code can run
`manage.py migrate` and have the expected tables present (including
`learning_analytics_studentcourseprogress`).
"""
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def current_year_default():
    # Use a fixed default so the migration is deterministic.
    # Makemigrations would normally capture the current year as a literal.
    return 2025


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LearnerBehavior',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(max_length=255)),
                ('total_time_spent_minutes', models.IntegerField(default=0, help_text='Total time spent in minutes')),
                ('last_activity', models.DateTimeField(blank=True, null=True)),
                ('completion_percentage', models.FloatField(default=0, help_text='Course completion percentage')),
                ('videos_watched', models.IntegerField(default=0)),
                ('problems_attempted', models.IntegerField(default=0)),
                ('discussions_participated', models.IntegerField(default=0)),
                ('preferred_learning_time', models.CharField(blank=True, choices=[('morning', 'Sáng'), ('afternoon', 'Chiều'), ('evening', 'Tối'), ('night', 'Đêm')], max_length=20, null=True)),
                ('average_session_duration', models.IntegerField(default=0, help_text='Average session duration in minutes')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learner_behavior', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_activity'],
            },
        ),

        migrations.CreateModel(
            name='CourseCreditHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(max_length=255, unique=True)),
                ('credit_hours', models.FloatField(help_text='Credit hours required to complete this course')),
                ('course_name', models.CharField(max_length=255, help_text='Display name of the course')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='Teacher who set the credit hours', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Course Credit Hours',
                'verbose_name_plural': 'Course Credit Hours',
            },
        ),

        migrations.CreateModel(
            name='StudentCourseProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('not_started', 'Chưa bắt đầu'), ('in_progress', 'Đang học'), ('completed', 'Hoàn thành'), ('failed', 'Không đạt')], default='not_started', max_length=20)),
                ('enrollment_date', models.DateTimeField(auto_now_add=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('credit_hours_earned', models.FloatField(default=0, help_text='Credit hours earned from this course (0 if not completed)')),
                ('progress_percentage', models.FloatField(default=0, help_text='Course completion percentage')),
                ('last_activity_date', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_progress', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-enrollment_date'],
                'unique_together': {('user', 'course_id')},
            },
        ),

        migrations.CreateModel(
            name='LearningHoursRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('required_hours', models.FloatField(help_text='Required learning hours (credit hours)')),
                ('current_year', models.IntegerField(default=current_year_default)),
                ('status', models.CharField(choices=[('pending', 'Đang chờ phê duyệt'), ('approved', 'Đã phê duyệt'), ('rejected', 'Từ chối'), ('in_progress', 'Đang thực hiện')], default='in_progress', max_length=20)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_learning_requirements', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_requirements', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'current_year')},
            },
        ),

        migrations.CreateModel(
            name='LearningHoursApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_hours', models.FloatField(help_text='Hours requested for approval')),
                ('evidence_description', models.TextField(help_text='Description of learning evidence')),
                ('evidence_files', models.JSONField(default=list, help_text='List of evidence file URLs')),
                ('status', models.CharField(choices=[('pending', 'Đang chờ phê duyệt'), ('approved', 'Đã phê duyệt'), ('rejected', 'Từ chối')], default='pending', max_length=20)),
                ('review_date', models.DateTimeField(blank=True, null=True)),
                ('review_comments', models.TextField(blank=True)),
                ('approved_hours', models.FloatField(blank=True, null=True, help_text='Actually approved hours')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_hour_approvals', to=settings.AUTH_USER_MODEL)),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='learning_analytics.learninghoursrequirement')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        migrations.CreateModel(
            name='LearnerRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(max_length=255)),
                ('recommendation_type', models.CharField(choices=[('suggested', 'Suggested'), ('trending', 'Trending'), ('similar', 'Similar to completed courses')], default='suggested', max_length=20)),
                ('confidence_score', models.FloatField(default=0.5, help_text='Confidence in recommendation (0-1)')),
                ('reason', models.TextField(blank=True, help_text='Why this course is recommended')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-confidence_score', '-created_at'],
            },
        ),

        migrations.CreateModel(
            name='LearningGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goal_type', models.CharField(choices=[('weekly_hours', 'Weekly Study Hours'), ('course_completion', 'Course Completion'), ('skill_development', 'Skill Development')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('target_value', models.IntegerField(help_text='Target value for the goal')),
                ('current_value', models.IntegerField(default=0)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_goals', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
