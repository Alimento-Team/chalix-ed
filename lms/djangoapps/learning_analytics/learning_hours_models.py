"""
Additional models for learning hours tracking and requirements.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LearningHoursRequirement(models.Model):
    """Model to track learning hours requirements for users."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_requirements')
    required_hours = models.IntegerField(help_text="Required learning hours")
    current_year = models.IntegerField(default=timezone.now().year)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Đang chờ phê duyệt'),
            ('approved', 'Đã phê duyệt'),
            ('rejected', 'Từ chối'),
            ('in_progress', 'Đang thực hiện'),
        ],
        default='in_progress'
    )
    
    # Approval tracking
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_learning_requirements'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'learning_analytics'
        unique_together = ('user', 'current_year')

    @property
    def completed_hours(self):
        """Calculate total completed hours for this requirement."""
        from .models import LearnerBehavior
        total_minutes = LearnerBehavior.objects.filter(
            user=self.user,
            created_at__year=self.current_year
        ).aggregate(
            total=models.Sum('total_time_spent')
        )['total'] or 0
        
        return round(total_minutes / 60, 1)
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if self.required_hours == 0:
            return 0
        return min(100, (self.completed_hours / self.required_hours) * 100)
    
    @property
    def is_completed(self):
        """Check if requirement is completed."""
        return self.completed_hours >= self.required_hours


class LearningHoursApproval(models.Model):
    """Model to track approval requests for learning hours."""
    
    requirement = models.ForeignKey(
        LearningHoursRequirement, 
        on_delete=models.CASCADE,
        related_name='approval_requests'
    )
    
    requested_hours = models.FloatField(help_text="Hours requested for approval")
    evidence_description = models.TextField(help_text="Description of learning evidence")
    evidence_files = models.JSONField(default=list, help_text="List of evidence file URLs")
    
    # Request status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Đang chờ phê duyệt'),
            ('approved', 'Đã phê duyệt'),
            ('rejected', 'Từ chối'),
        ],
        default='pending'
    )
    
    # Approval details
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_hour_approvals'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    approved_hours = models.FloatField(null=True, blank=True, help_text="Actually approved hours")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'learning_analytics'
        ordering = ['-created_at']


class OrganizationLearningPolicy(models.Model):
    """Model to define organization-wide learning policies."""
    
    organization_name = models.CharField(max_length=255)
    
    # Default requirements
    default_annual_hours = models.IntegerField(default=40, help_text="Default annual learning hours requirement")
    
    # Policy settings
    allow_self_reporting = models.BooleanField(default=True)
    require_approval = models.BooleanField(default=True)
    
    # Automatic approval settings
    auto_approve_platform_courses = models.BooleanField(default=True)
    auto_approve_threshold = models.FloatField(default=0.8, help_text="Auto-approve if completion >= this threshold")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'learning_analytics'
