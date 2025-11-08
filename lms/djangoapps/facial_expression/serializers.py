"""
Serializers for facial expression recording API.
"""
from rest_framework import serializers
from lms.djangoapps.learning_analytics.models import FacialExpressionLog


class FacialExpressionUploadSerializer(serializers.Serializer):
    """Serializer for uploading facial expression videos."""
    
    video = serializers.FileField(required=True, help_text="Video file to upload")
    course_id = serializers.CharField(required=True, max_length=255)
    unit_id = serializers.CharField(required=True, max_length=255)
    topic_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    timestamp = serializers.DateTimeField(required=True)
    is_final = serializers.BooleanField(default=False, help_text="Whether this is the final chunk")
    duration_seconds = serializers.IntegerField(required=False, default=0, help_text="Recording duration in seconds")
    
    def validate_video(self, value):
        """Validate video file."""
        # Check file size (max 100MB per chunk)
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(f"Video file size exceeds maximum allowed size of {max_size / (1024*1024)}MB")
        
        # Check file extension
        allowed_extensions = ['.webm', '.mp4', '.avi']
        file_ext = value.name.split('.')[-1].lower()
        if f'.{file_ext}' not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}")
        
        return value


class FacialExpressionLogSerializer(serializers.ModelSerializer):
    """Serializer for facial expression log model."""
    
    recording_duration = serializers.ReadOnlyField()
    video_size_mb = serializers.ReadOnlyField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True, allow_null=True)
    
    class Meta:
        model = FacialExpressionLog
        fields = [
            'id',
            'user',
            'user_username',
            'course_id',
            'unit_id',
            'topic_id',
            'program_id',
            'org_id',
            'teacher_id',
            'teacher_username',
            'video_path',
            'video_size',
            'video_size_mb',
            'duration_seconds',
            'recording_duration',
            'start_timestamp',
            'end_timestamp',
            'is_complete',
            'processing_status',
            'analysis_results',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'video_size',
            'processing_status',
        ]


class FacialExpressionLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    video_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = FacialExpressionLog
        fields = [
            'id',
            'user_username',
            'course_id',
            'unit_id',
            'video_size_mb',
            'start_timestamp',
            'is_complete',
            'processing_status',
        ]
