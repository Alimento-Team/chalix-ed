"""
Serializers for learning analytics API.
"""
from rest_framework import serializers
from .models import LearnerBehavior, LearnerRecommendation, LearningGoal


class LearnerStatsSerializer(serializers.Serializer):
    """Serializer for learner statistics."""
    total_courses_joined = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    certificates_earned = serializers.IntegerField()
    total_tests_completed = serializers.IntegerField()
    total_study_time_hours = serializers.FloatField()
    monthly_study_time_hours = serializers.FloatField()
    recent_enrollments = serializers.IntegerField()
    completion_rate = serializers.FloatField()


class CourseProgressSerializer(serializers.Serializer):
    """Serializer for course progress data."""
    course_id = serializers.CharField()
    course_name = serializers.CharField()
    course_number = serializers.CharField()
    enrollment_date = serializers.DateTimeField()
    progress_percentage = serializers.FloatField()
    status = serializers.CharField()
    study_time_hours = serializers.FloatField()
    assignments_completed = serializers.IntegerField()
    certificate_earned = serializers.BooleanField()
    course_image_url = serializers.CharField()
    instructor_name = serializers.CharField()


class LearnerRecommendationSerializer(serializers.Serializer):
    """Serializer for course recommendations."""
    course_id = serializers.CharField()
    course_name = serializers.CharField()
    course_number = serializers.CharField()
    recommendation_type = serializers.CharField()
    confidence_score = serializers.FloatField()
    reason = serializers.CharField()
    course_image_url = serializers.CharField()
    instructor_name = serializers.CharField()


class LearningGoalSerializer(serializers.ModelSerializer):
    """Serializer for learning goals."""
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = LearningGoal
        fields = [
            'id', 'goal_type', 'title', 'description',
            'target_value', 'current_value', 'deadline',
            'is_completed', 'progress_percentage', 'created_at'
        ]
        read_only_fields = ['created_at']


class LearnerBehaviorSerializer(serializers.ModelSerializer):
    """Serializer for learner behavior data."""

    class Meta:
        model = LearnerBehavior
        fields = [
            'course_id', 'total_time_spent', 'last_activity',
            'videos_watched', 'assignments_completed', 'discussions_participated',
            'login_frequency', 'study_streak', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
