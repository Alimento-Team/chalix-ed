"""
Django Admin configuration for Personalization app
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    UserCoursePersonalization,
    PersonalizationYearlyStats,
    LessonTimeTracking
)


@admin.register(UserCoursePersonalization)
class UserCoursePersonalizationAdmin(admin.ModelAdmin):
    """
    Admin interface for UserCoursePersonalization model
    """
    list_display = [
        'user',
        'course_id',
        'get_course_name',
        'completed_lessons',
        'total_lessons',
        'completion_percentage',
        'status',
        'created',
    ]
    
    # Use actual model fields present on UserCoursePersonalization
    list_filter = [
        'status',
        'completed_certificates',
        'created',
        'modified',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'course_id',
    ]
    
    readonly_fields = [
        'created',
        'modified',
        'get_completion_percentage',
        'get_course_name',
    ]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'user',
                'course_id',
                'get_course_name',
            )
        }),
        (_('Progress Tracking'), {
            'fields': (
                'completed_lessons',
                'total_lessons',
                'get_completion_percentage',
                'status',
            )
        }),
        (_('Time Statistics'), {
            'fields': (
                'time_spent_minutes',
                'time_spent_hours',
                'last_accessed',
            )
        }),
        (_('Certificate'), {
            'fields': (
                'has_certificate',
                'certificate_earned_date',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created',
                'modified',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def get_course_name(self, obj):
        """Get display name for course"""
        # Models may not have a resolved course object in all environments; fall back to course_id
        try:
            return str(obj.course_id)
        except Exception:
            return ''
    get_course_name.short_description = _('Course Name')
    
    def get_completion_percentage(self, obj):
        """Get formatted completion percentage"""
        return f"{obj.completion_percentage}%"
    get_completion_percentage.short_description = _('Completion %')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_paused']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected courses as completed"""
        updated = queryset.update(status='completed')
        self.message_user(
            request,
            _(f'{updated} course(s) marked as completed.')
        )
    mark_as_completed.short_description = _('Mark as completed')
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected courses as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(
            request,
            _(f'{updated} course(s) marked as in progress.')
        )
    mark_as_in_progress.short_description = _('Mark as in progress')
    
    def mark_as_paused(self, request, queryset):
        """Mark selected courses as paused"""
        updated = queryset.update(status='paused')
        self.message_user(
            request,
            _(f'{updated} course(s) marked as paused.')
        )
    mark_as_paused.short_description = _('Mark as paused')


@admin.register(PersonalizationYearlyStats)
class PersonalizationYearlyStatsAdmin(admin.ModelAdmin):
    """
    Admin interface for PersonalizationYearlyStats model
    """
    # Align list display with actual model field names
    list_display = [
        'user',
        'year',
        'total_courses_assigned',
        'total_courses_completed',
        'total_certificates_earned',
        'total_study_time_hours',
    ]
    
    list_filter = [
        'year',
        'created',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
    ]
    
    readonly_fields = [
        'created',
        'modified',
    ]
    
    fieldsets = (
        (_('User and Year'), {
            'fields': (
                'user',
                'year',
            )
        }),
        (_('Course Statistics'), {
            'fields': (
                'total_courses',
                'active_courses',
                'completed_courses',
                'paused_courses',
            )
        }),
        (_('Learning Metrics'), {
            'fields': (
                'certificates_earned',
                'total_lessons_completed',
                'total_time_minutes',
                'total_time_hours',
                'average_completion_rate',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created',
                'modified',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(LessonTimeTracking)
class LessonTimeTrackingAdmin(admin.ModelAdmin):
    """
    Admin interface for LessonTimeTracking model
    """
    list_display = [
        'user',
        'get_course_id',
        'lesson_id',
        'time_spent_minutes',
        'is_completed',
        'completed_at',
    ]
    
    list_filter = [
        'is_completed',
        'completed_at',
        'created',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'course_id',
        'lesson_id',
    ]
    
    readonly_fields = [
        'created',
        'modified',
        'get_course_id',
    ]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'user',
                'course_personalization',
                'get_course_id',
                'lesson_id',
            )
        }),
        (_('Time Tracking'), {
            'fields': (
                'time_spent_minutes',
                'access_count',
                'last_accessed',
            )
        }),
        (_('Status'), {
            'fields': (
                'completed',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created',
                'modified',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def get_course_id(self, obj):
        """Get course ID from model field (fallback to '-')"""
        try:
            return str(obj.course_id) if obj.course_id else '-'
        except Exception:
            return '-'
    get_course_id.short_description = _('Course ID')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user',
            'course_personalization'
        )
    
    actions = ['mark_as_completed', 'mark_as_not_completed']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected lessons as completed"""
        updated = queryset.update(completed=True)
        self.message_user(
            request,
            _(f'{updated} lesson(s) marked as completed.')
        )
    mark_as_completed.short_description = _('Mark as completed')
    
    def mark_as_not_completed(self, request, queryset):
        """Mark selected lessons as not completed"""
        updated = queryset.update(completed=False)
        self.message_user(
            request,
            _(f'{updated} lesson(s) marked as not completed.')
        )
    mark_as_not_completed.short_description = _('Mark as not completed')
