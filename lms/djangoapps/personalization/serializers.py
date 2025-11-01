"""
Serializers for personalization API endpoints.
"""

from rest_framework import serializers
from .models import UserCoursePersonalization, PersonalizationYearlyStats, LessonTimeTracking


class UserCoursePersonalizationSerializer(serializers.ModelSerializer):
    """Serializer for user course personalization data."""
    
    course_name = serializers.SerializerMethodField()
    lesson_progress = serializers.SerializerMethodField()
    certificate_progress = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserCoursePersonalization
        fields = [
            'id',
            'course_id',
            'course_name',
            'total_lessons',
            'completed_lessons',
            'lesson_progress',
            'total_certificates',
            'completed_certificates',
            'certificate_progress',
            'status',
            'status_display',
            'average_completion_time_per_lesson',
            'total_study_time',
            'completion_percentage',
            'last_accessed',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'created', 'modified']
    
    def get_course_name(self, obj):
        """Get the course display name."""
        try:
            from xmodule.modulestore.django import modulestore
            course = modulestore().get_course(obj.course_id)
            if course:
                return course.display_name
        except Exception:
            pass
        return str(obj.course_id)
    
    def get_lesson_progress(self, obj):
        """Return lesson progress as ratio string."""
        return obj.get_lesson_progress_ratio()
    
    def get_certificate_progress(self, obj):
        """Return certificate progress as ratio string."""
        return obj.get_certificate_progress_ratio()


class PersonalizationYearlyStatsSerializer(serializers.ModelSerializer):
    """Serializer for yearly personalization statistics."""
    
    class Meta:
        model = PersonalizationYearlyStats
        fields = [
            'id',
            'year',
            'total_courses_assigned',
            'total_courses_completed',
            'total_study_time_hours',
            'average_time_per_course',
            'total_lessons_completed',
            'total_certificates_earned',
            'overall_completion_rate',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'created', 'modified']


class LessonTimeTrackingSerializer(serializers.ModelSerializer):
    """Serializer for lesson time tracking data."""
    
    class Meta:
        model = LessonTimeTracking
        fields = [
            'id',
            'course_id',
            'lesson_id',
            'lesson_name',
            'time_spent_minutes',
            'is_completed',
            'completed_at',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'created', 'modified']


class PersonalizationDashboardSerializer(serializers.Serializer):
    """
    Comprehensive serializer for the personalization dashboard.
    Combines data from multiple sources.
    """
    
    year = serializers.IntegerField()
    yearly_stats = PersonalizationYearlyStatsSerializer()
    active_courses = UserCoursePersonalizationSerializer(many=True)
    completed_courses = UserCoursePersonalizationSerializer(many=True)
    suggested_courses = UserCoursePersonalizationSerializer(many=True, required=False)
