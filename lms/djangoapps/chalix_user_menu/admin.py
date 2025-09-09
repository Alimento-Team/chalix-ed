"""
Django admin configuration for Chalix User Menu models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserLearningPlan, TeachingRequest, UserRequest, UserPersonalization, Notification, NotificationType, NotificationPreference


@admin.register(UserLearningPlan)
class UserLearningPlanAdmin(admin.ModelAdmin):
    """
    Admin interface for UserLearningPlan model
    """
    list_display = ('user', 'title', 'target_hours', 'completed_hours', 'progress_percentage', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'title')
    readonly_fields = ('progress_percentage', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Thông tin cơ bản'), {
            'fields': ('user', 'title', 'description', 'status')
        }),
        (_('Thời gian và tiến độ'), {
            'fields': ('start_date', 'end_date', 'target_hours', 'completed_hours', 'progress_percentage')
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeachingRequest)
class TeachingRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for TeachingRequest model
    """
    list_display = ('user', 'course_title', 'status', 'proposed_duration', 'submitted_at', 'reviewer')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'course_title')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)

    fieldsets = (
        (_('Thông tin đăng ký'), {
            'fields': ('user', 'course_title', 'course_description', 'proposed_duration')
        }),
        (_('Kinh nghiệm và trình độ'), {
            'fields': ('teaching_experience', 'qualifications')
        }),
        (_('Trạng thái phê duyệt'), {
            'fields': ('status', 'reviewer', 'reviewed_at', 'review_notes')
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Set reviewer and reviewed_at when status changes
        """
        if change and 'status' in form.changed_data and obj.status != 'pending':
            obj.reviewer = request.user
            from django.utils import timezone
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(UserRequest)
class UserRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for UserRequest model
    """
    list_display = ('user', 'request_type', 'title', 'status', 'priority', 'created_at', 'assignee')
    list_filter = ('request_type', 'status', 'priority', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Thông tin yêu cầu'), {
            'fields': ('user', 'request_type', 'title', 'description', 'priority')
        }),
        (_('Trạng thái xử lý'), {
            'fields': ('status', 'assignee', 'resolution_notes', 'resolved_at')
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Set resolved_at when status changes to resolved
        """
        if change and 'status' in form.changed_data and obj.status == 'resolved':
            from django.utils import timezone
            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(UserPersonalization)
class UserPersonalizationAdmin(admin.ModelAdmin):
    """
    Admin interface for UserPersonalization model
    """
    list_display = ('user', 'learning_style', 'preferred_language', 'theme_preference', 'updated_at')
    list_filter = ('learning_style', 'preferred_language', 'theme_preference', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('Tùy chọn cá nhân'), {
            'fields': ('user', 'learning_style', 'preferred_language', 'theme_preference')
        }),
        (_('Tùy chọn nâng cao'), {
            'fields': ('notification_preferences', 'accessibility_preferences'),
            'classes': ('collapse',)
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationType model
    """
    list_display = ('display_name', 'name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    readonly_fields = ('created_at',)
    ordering = ('display_name',)

    fieldsets = (
        (_('Thông tin cơ bản'), {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model
    """
    list_display = ('user', 'title', 'notification_type', 'priority', 'is_read', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'is_archived', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'title', 'message')
    readonly_fields = ('created_at', 'read_at', 'time_since_created')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Thông tin cơ bản'), {
            'fields': ('user', 'notification_type', 'title', 'message', 'priority')
        }),
        (_('Trạng thái'), {
            'fields': ('is_read', 'read_at', 'is_archived', 'expires_at')
        }),
        (_('Hành động'), {
            'fields': ('action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        (_('Dữ liệu bổ sung'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at', 'time_since_created'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread', 'archive_notifications']

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f"{updated} thông báo đã được đánh dấu là đã đọc.")
    mark_as_read.short_description = _("Đánh dấu là đã đọc")

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f"{updated} thông báo đã được đánh dấu là chưa đọc.")
    mark_as_unread.short_description = _("Đánh dấu là chưa đọc")

    def archive_notifications(self, request, queryset):
        """Archive selected notifications"""
        updated = queryset.filter(is_archived=False).update(is_archived=True)
        self.message_user(request, f"{updated} thông báo đã được lưu trữ.")
    archive_notifications.short_description = _("Lưu trữ thông báo")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationPreference model
    """
    list_display = ('user', 'notification_type', 'delivery_method', 'is_enabled', 'updated_at')
    list_filter = ('delivery_method', 'is_enabled', 'notification_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('Tùy chọn thông báo'), {
            'fields': ('user', 'notification_type', 'delivery_method', 'is_enabled')
        }),
        (_('Thông tin hệ thống'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
