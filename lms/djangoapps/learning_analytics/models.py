"""
Models for learning analytics and personalized learning data.
"""
from django.db import models
from django.contrib.auth.models import User
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment


class LearnerBehavior(models.Model):
    """Model to track learner behavior and engagement metrics."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learner_behaviors')
    course_id = models.CharField(max_length=255)

    # Time tracking
    total_time_spent = models.IntegerField(default=0, help_text="Total time spent in minutes")
    last_activity = models.DateTimeField(auto_now=True)

    # Progress metrics
    videos_watched = models.IntegerField(default=0)
    assignments_completed = models.IntegerField(default=0)
    discussions_participated = models.IntegerField(default=0)

    # Engagement metrics
    login_frequency = models.IntegerField(default=0, help_text="Number of logins this month")
    study_streak = models.IntegerField(default=0, help_text="Consecutive days of study")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'lms.djangoapps.learning_analytics'
        unique_together = ('user', 'course_id')


class LearnerRecommendation(models.Model):
    """Model to store personalized course recommendations."""

    RECOMMENDATION_TYPES = [
        ('suggested', 'Suggested'),
        ('trending', 'Trending'),
        ('similar', 'Similar to completed courses'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    course_id = models.CharField(max_length=255)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES, default='suggested')
    confidence_score = models.FloatField(default=0.5, help_text="Confidence in recommendation (0-1)")
    reason = models.TextField(blank=True, help_text="Why this course is recommended")

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'lms.djangoapps.learning_analytics'
        ordering = ['-confidence_score', '-created_at']


class LearningGoal(models.Model):
    """Model to track learner goals and achievements."""

    GOAL_TYPES = [
        ('weekly_hours', 'Weekly Study Hours'),
        ('course_completion', 'Course Completion'),
        ('skill_development', 'Skill Development'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_value = models.IntegerField(help_text="Target value for the goal")
    current_value = models.IntegerField(default=0)
    deadline = models.DateField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'lms.djangoapps.learning_analytics'

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)
