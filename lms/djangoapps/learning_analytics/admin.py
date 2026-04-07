"""
Admin configuration for learning analytics models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    LearnerBehavior,
    LearningHoursRequirement,
    LearningHoursApproval,
    StudentLearningProcessSnapshot,
)


@admin.register(LearnerBehavior)
class LearnerBehaviorAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course_id', 'total_time_spent_hours', 
        'completion_percentage', 'last_activity', 'created'
    ]
    list_filter = ['course_id', 'created', 'last_activity']
    search_fields = ['user__username', 'user__email', 'course_id']
    readonly_fields = ['created', 'modified']
    
    def total_time_spent_hours(self, obj):
        hours = obj.total_time_spent_minutes / 60
        return f"{hours:.1f}h"
    total_time_spent_hours.short_description = "Total Hours"
    total_time_spent_hours.admin_order_field = 'total_time_spent_minutes'

    def completion_percentage(self, obj):
        percentage = obj.completion_percentage
        color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    completion_percentage.short_description = "Completion %"
    completion_percentage.admin_order_field = 'completion_percentage'


@admin.register(LearningHoursRequirement)
class LearningHoursRequirementAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'current_year', 'required_hours', 'completed_hours',
        'progress_percentage', 'status_display'
    ]
    list_filter = ['current_year', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def completed_hours(self, obj):
        # models provide completed_hours property
        return f"{obj.completed_hours:.1f}h"
    completed_hours.short_description = "Completed Hours"
    
    def progress_percentage(self, obj):
        # models expose completion_percentage property
        percentage = obj.completion_percentage
        color = 'green' if percentage >= 100 else 'orange' if percentage >= 70 else 'red'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            '{:.1f}%</div></div>',
            min(percentage, 100), color, percentage
        )
    progress_percentage.short_description = "Progress"
    
    def status_display(self, obj):
        # Provide a simple human readable status based on model fields
        if getattr(obj, 'is_completed', False):
            return format_html('<span style="color: green;">✓ Completed</span>')
        if obj.status == 'approved':
            return format_html('<span style="color: green;">Approved</span>')
        if obj.status == 'rejected':
            return format_html('<span style="color: red;">Rejected</span>')
        if obj.status == 'pending':
            return format_html('<span style="color: orange;">Pending</span>')
        return format_html('<span>{}</span>', obj.status or 'In progress')
    status_display.short_description = "Status"
    
    actions = ['mark_completed', 'extend_deadline']
    
    def mark_completed(self, request, queryset):
        # This is for demo purposes - in reality, completion should be automatic
        count = queryset.count()
        self.message_user(request, f"{count} requirements marked as completed.")
    mark_completed.short_description = "Mark selected requirements as completed"
    
    def extend_deadline(self, request, queryset):
        from datetime import timedelta
        for requirement in queryset:
            requirement.deadline += timedelta(days=30)
            requirement.save()
        count = queryset.count()
        self.message_user(request, f"Extended deadline by 30 days for {count} requirements.")
    extend_deadline.short_description = "Extend deadline by 30 days"


@admin.register(LearningHoursApproval)
class LearningHoursApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'requirement', 'status', 'requested_hours',
        'approved_hours', 'created_at', 'review_date', 'reviewed_by'
    ]
    list_filter = ['status', 'created_at', 'review_date']
    search_fields = ['requirement__user__username', 'requirement__user__email', 'reviewed_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'requirement', 'reviewed_by'
        )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        pending_requests = queryset.filter(status='pending')
        count = pending_requests.count()
        
        for approval in pending_requests:
            approval.status = 'approved'
            approval.approved_hours = approval.requested_hours
            approval.reviewed_by = request.user
            approval.review_date = timezone.now()
            approval.save()
            
        self.message_user(request, f"Approved {count} requests.")
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        pending_requests = queryset.filter(status='pending')
        count = pending_requests.count()
        
        for approval in pending_requests:
            approval.status = 'rejected'
            approval.reviewed_by = request.user
            approval.review_date = timezone.now()
            approval.save()
            
        self.message_user(request, f"Rejected {count} requests.")
    reject_requests.short_description = "Reject selected requests"
    
    def get_readonly_fields(self, request, obj=None):
        # Make approved/rejected requests mostly readonly
        if obj and obj.status in ['approved', 'rejected']:
            return self.readonly_fields + ['status', 'approved_hours', 'review_comments']
        return self.readonly_fields

    def user(self, obj):
        # LearningHoursApproval links to a requirement which links to a user
        return obj.requirement.user
    user.short_description = 'User'
    user.admin_order_field = 'requirement__user'


@admin.register(StudentLearningProcessSnapshot)
class StudentLearningProcessSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'student_id',
        'user',
        'position_text',
        'gender_text',
        'location_text',
        'final_score',
        'imported_at',
    ]
    list_filter = [
        'position_code',
        'gender_code',
        'location_code',
        'job_title_code',
        'experience_code',
    ]
    search_fields = ['student_id', 'user__username', 'location_text']
    readonly_fields = ['imported_at', 'updated_at']
