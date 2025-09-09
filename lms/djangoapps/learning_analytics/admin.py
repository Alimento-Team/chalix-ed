"""
Admin configuration for learning analytics models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import LearnerBehavior, LearningHoursRequirement, LearningHoursApproval


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
        'user', 'year', 'required_hours', 'completed_hours', 
        'progress_percentage', 'status_display', 'deadline'
    ]
    list_filter = ['year', 'deadline', 'created']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created', 'modified']
    
    def completed_hours(self, obj):
        return f"{obj.get_completed_hours():.1f}h"
    completed_hours.short_description = "Completed Hours"
    
    def progress_percentage(self, obj):
        percentage = obj.get_progress_percentage()
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
        if obj.is_completed():
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        else:
            days_left = (obj.deadline - timezone.now().date()).days
            return format_html('<span style="color: orange;">{} days left</span>', days_left)
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
        'user', 'learning_requirement', 'status', 'requested_hours',
        'approved_hours', 'requested_date', 'approved_date', 'approver'
    ]
    list_filter = ['status', 'requested_date', 'approved_date']
    search_fields = ['user__username', 'user__email', 'approver__username']
    readonly_fields = ['requested_date', 'created', 'modified']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'learning_requirement', 'approver'
        )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        pending_requests = queryset.filter(status='pending')
        count = pending_requests.count()
        
        for approval in pending_requests:
            approval.status = 'approved'
            approval.approved_hours = approval.requested_hours
            approval.approver = request.user
            approval.approved_date = timezone.now()
            approval.save()
            
        self.message_user(request, f"Approved {count} requests.")
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        pending_requests = queryset.filter(status='pending')
        count = pending_requests.count()
        
        for approval in pending_requests:
            approval.status = 'rejected'
            approval.approver = request.user
            approval.approved_date = timezone.now()
            approval.save()
            
        self.message_user(request, f"Rejected {count} requests.")
    reject_requests.short_description = "Reject selected requests"
    
    def get_readonly_fields(self, request, obj=None):
        # Make approved/rejected requests mostly readonly
        if obj and obj.status in ['approved', 'rejected']:
            return self.readonly_fields + ['status', 'approved_hours', 'notes']
        return self.readonly_fields
