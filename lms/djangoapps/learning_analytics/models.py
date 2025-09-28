"""
Models for learning analytics and personalized learning data.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
class LearnerBehavior(models.Model):
    """Model to track detailed learner behavior and engagement metrics."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learner_behavior')
    course_id = models.CharField(max_length=255)

    # Time tracking
    total_time_spent_minutes = models.IntegerField(default=0, help_text="Total time spent in minutes")
    last_activity = models.DateTimeField(null=True, blank=True)

    # Engagement metrics
    completion_percentage = models.FloatField(default=0, help_text="Course completion percentage")
    videos_watched = models.IntegerField(default=0)
    problems_attempted = models.IntegerField(default=0)
    discussions_participated = models.IntegerField(default=0)

    # Learning patterns
    preferred_learning_time = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Sáng'),
            ('afternoon', 'Chiều'),
            ('evening', 'Tối'),
            ('night', 'Đêm'),
        ],
        null=True,
        blank=True
    )
    average_session_duration = models.IntegerField(default=0, help_text="Average session duration in minutes")

    # Metadata
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'learning_analytics'
        unique_together = ('user', 'course_id')
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.course_id} ({self.completion_percentage}%)"

    @property
    def total_time_spent_hours(self):
        """Convert minutes to hours for display."""
        return self.total_time_spent_minutes / 60

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity', 'modified'])

    def add_session_time(self, minutes):
        """Add time spent in a learning session."""
        self.total_time_spent_minutes += minutes
        self.update_activity()

        # Update average session duration
        if self.videos_watched > 0 or self.problems_attempted > 0:
            # Simple average calculation - could be made more sophisticated
            total_activities = self.videos_watched + self.problems_attempted + self.discussions_participated
            if total_activities > 0:
                self.average_session_duration = self.total_time_spent_minutes // total_activities
            self.save(update_fields=['total_time_spent_minutes', 'average_session_duration', 'last_activity', 'modified'])


class CourseCreditHours(models.Model):
    """Model to store credit hours for each course set by teachers."""

    course_id = models.CharField(max_length=255, unique=True)
    credit_hours = models.FloatField(help_text="Credit hours required to complete this course")
    course_name = models.CharField(max_length=255, help_text="Display name of the course")

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Teacher who set the credit hours"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'learning_analytics'
        verbose_name = "Course Credit Hours"
        verbose_name_plural = "Course Credit Hours"

    def __str__(self):
        return f"{self.course_name} ({self.credit_hours} hours)"


class StudentCourseProgress(models.Model):
    """Model to track student progress and credit hours earned from courses."""

    STATUS_CHOICES = [
        ('not_started', 'Chưa bắt đầu'),
        ('in_progress', 'Đang học'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Không đạt'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    course_id = models.CharField(max_length=255)

    # Progress tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    # Credit hours tracking
    credit_hours_earned = models.FloatField(
        default=0,
        help_text="Credit hours earned from this course (0 if not completed)"
    )

    # Progress metrics
    progress_percentage = models.FloatField(default=0, help_text="Course completion percentage")
    last_activity_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'learning_analytics'
        unique_together = ('user', 'course_id')
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.user.username} - {self.course_id} ({self.status})"

    def save(self, *args, **kwargs):
        """Update credit hours earned based on completion status."""
        if self.status == 'completed':
            # Get credit hours from CourseCreditHours model
            try:
                course_credits = CourseCreditHours.objects.get(course_id=self.course_id)
                self.credit_hours_earned = course_credits.credit_hours
            except CourseCreditHours.DoesNotExist:
                # If no credit hours set for course, default to 0
                self.credit_hours_earned = 0
        else:
            # No credit hours earned if course is not completed
            self.credit_hours_earned = 0

        super().save(*args, **kwargs)


class LearningHoursRequirement(models.Model):
    """Model to track learning hours requirements for users."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_requirements')
    required_hours = models.FloatField(help_text="Required learning hours (credit hours)")
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

    def __str__(self):
        return f"{self.user.username} - {self.current_year} ({self.completed_hours}/{self.required_hours}h)"

    @property
    def completed_hours(self):
        """Calculate total completed credit hours for this requirement."""
        total_hours = StudentCourseProgress.objects.filter(
            user=self.user,
            status='completed',
            completion_date__year=self.current_year
        ).aggregate(
            total=models.Sum('credit_hours_earned')
        )['total'] or 0

        return round(total_hours, 1)

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

    @property
    def in_progress_hours(self):
        """Calculate hours from courses currently in progress."""
        in_progress_hours = StudentCourseProgress.objects.filter(
            user=self.user,
            status='in_progress'
        ).aggregate(
            total=models.Sum('credit_hours_earned')
        )['total'] or 0

        return round(in_progress_hours, 1)


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

    def __str__(self):
        return f"{self.requirement.user.username} - {self.requested_hours}h ({self.status})"


class LearnerRecommendation(models.Model):
    """Model to store personalized course recommendations."""

    RECOMMENDATION_TYPES = [
        ('suggested', 'Suggested'),
        ('trending', 'Trending'),
        ('similar', 'Similar to completed courses'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    course_id = models.CharField(max_length=255)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES, default='suggested')
    confidence_score = models.FloatField(default=0.5, help_text="Confidence in recommendation (0-1)")
    reason = models.TextField(blank=True, help_text="Why this course is recommended")

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'learning_analytics'
        ordering = ['-confidence_score', '-created_at']


class LearningGoal(models.Model):
    """Model to track learner goals and achievements."""

    GOAL_TYPES = [
        ('weekly_hours', 'Weekly Study Hours'),
        ('course_completion', 'Course Completion'),
        ('skill_development', 'Skill Development'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_value = models.IntegerField(help_text="Target value for the goal")
    current_value = models.IntegerField(default=0)
    deadline = models.DateField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'learning_analytics'

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)
