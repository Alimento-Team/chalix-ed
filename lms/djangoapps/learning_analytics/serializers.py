"""
Serializers for learning analytics API.
"""
from rest_framework import serializers
from .models import (
    CourseCreditHours,
    StudentCourseProgress,
    LearningHoursRequirement,
    LearningHoursApproval,
    LearnerRecommendation
)


class LearnerStatsSerializer(serializers.Serializer):
    """Serializer for learner statistics."""
    total_courses_joined = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    certificates_earned = serializers.IntegerField()
    total_tests_completed = serializers.IntegerField()
    total_credit_hours = serializers.FloatField()
    monthly_credit_hours = serializers.FloatField()
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
    credit_hours_earned = serializers.FloatField()
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


class CourseCreditHoursSerializer(serializers.ModelSerializer):
    """Serializer for course credit hours."""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = CourseCreditHours
        fields = [
            'id', 'course_id', 'course_name', 'credit_hours',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StudentCourseProgressSerializer(serializers.ModelSerializer):
    """Serializer for student course progress."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StudentCourseProgress
        fields = [
            'id', 'user', 'username', 'course_id', 'status',
            'progress_percentage', 'credit_hours_earned', 'enrollment_date',
            'completion_date', 'last_activity_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LearningHoursRequirementSerializer(serializers.ModelSerializer):
    """Serializer for learning hours requirements."""
    completed_hours = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LearningHoursRequirement
        fields = [
            'id', 'user', 'username', 'required_hours', 'year', 'status',
            'completed_hours', 'completion_percentage', 'is_completed',
            'approval_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'approval_date']


class LearningHoursApprovalSerializer(serializers.ModelSerializer):
    """Serializer for learning hours approval requests."""
    username = serializers.CharField(source='requirement.user.username', read_only=True)
    year = serializers.IntegerField(source='requirement.year', read_only=True)

    class Meta:
        model = LearningHoursApproval
        fields = [
            'id', 'requirement', 'username', 'year', 'requested_hours',
            'evidence_description', 'evidence_files', 'status',
            'approved_hours', 'review_comments', 'review_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'review_date']


class LearningHoursSummarySerializer(serializers.Serializer):
    """Serializer for learning hours summary data."""
    completed_hours = serializers.FloatField()
    required_hours = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    status = serializers.CharField()
    remaining_hours = serializers.FloatField()
    pending_approval_hours = serializers.FloatField()
    year = serializers.IntegerField()


class LearnerRecommendationModelSerializer(serializers.ModelSerializer):
    """Serializer for learner recommendations."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LearnerRecommendation
        fields = [
            'id', 'user', 'username', 'course_id', 'recommendation_type',
            'confidence_score', 'reason', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
