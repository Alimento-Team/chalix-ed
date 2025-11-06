"""
Django admin configuration for facial expression recording.
"""
from django.contrib import admin
from lms.djangoapps.learning_analytics.models import FacialExpressionLog


@admin.register(FacialExpressionLog)
class FacialExpressionLogAdmin(admin.ModelAdmin):
    """Admin interface for facial expression logs."""
    
    list_display = [
        'id',
        'user',
        'course_id',
        'unit_id',
        'start_timestamp',
        'video_size_mb',
        'is_complete',
        'processing_status',
    ]
    
    list_filter = [
        'is_complete',
        'processing_status',
        'start_timestamp',
        'created_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'course_id',
        'unit_id',
        'video_path',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'video_size_mb',
        'recording_duration',
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'teacher_id')
        }),
        ('Course Information', {
            'fields': ('course_id', 'unit_id', 'topic_id', 'program_id', 'org_id')
        }),
        ('Video Information', {
            'fields': ('video_path', 'video_size', 'video_size_mb', 'duration_seconds', 'recording_duration')
        }),
        ('Recording Details', {
            'fields': ('start_timestamp', 'end_timestamp', 'is_complete')
        }),
        ('Processing', {
            'fields': ('processing_status', 'analysis_results')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'start_timestamp'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'teacher_id')
