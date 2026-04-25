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


class FacialExpressionLog(models.Model):
    """Model to store facial expression video recordings metadata."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facial_expression_logs')
    
    # Course hierarchy
    course_id = models.CharField(max_length=255, help_text="Course ID")
    unit_id = models.CharField(max_length=255, help_text="Unit/Block ID (slide or video)")
    
    # Additional context (nullable for flexibility)
    topic_id = models.CharField(max_length=255, blank=True, null=True, help_text="Topic/Section ID")
    program_id = models.CharField(max_length=255, blank=True, null=True, help_text="Program ID")
    org_id = models.CharField(max_length=255, blank=True, null=True, help_text="Organization ID")
    teacher_id = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_facial_expressions',
        help_text="Teacher/Instructor for this course"
    )
    
    # Video storage
    video_path = models.CharField(max_length=512, help_text="MinIO storage path for the video file")
    video_size = models.BigIntegerField(default=0, help_text="Video file size in bytes")
    duration_seconds = models.IntegerField(default=0, help_text="Recording duration in seconds")
    
    # Recording metadata
    start_timestamp = models.DateTimeField(help_text="When the recording started")
    end_timestamp = models.DateTimeField(null=True, blank=True, help_text="When the recording ended")
    is_complete = models.BooleanField(default=False, help_text="Whether this is a complete recording or partial chunk")
    
    # Processing status
    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of video processing/analysis"
    )
    
    # Analysis results (can be populated by ML models later)
    analysis_results = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON data containing facial expression analysis results"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'learning_analytics'
        ordering = ['-start_timestamp']
        indexes = [
            models.Index(fields=['user', 'course_id']),
            models.Index(fields=['course_id', 'unit_id']),
            models.Index(fields=['start_timestamp']),
            models.Index(fields=['processing_status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course_id} - {self.unit_id} ({self.start_timestamp})"

    @property
    def recording_duration(self):
        """Calculate recording duration in a readable format."""
        if self.end_timestamp and self.start_timestamp:
            delta = self.end_timestamp - self.start_timestamp
            return delta.total_seconds()
        return self.duration_seconds

    @property
    def video_size_mb(self):
        """Convert video size to MB for display."""
        return round(self.video_size / (1024 * 1024), 2)


class StudentLearningProcessSnapshot(models.Model):
    """Stores one learning-process snapshot record per student/course pair."""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='learning_process_snapshots'
    )
    student_id = models.CharField(max_length=32)
    course_id = models.CharField(max_length=255)
    external_user_id = models.CharField(max_length=64, blank=True)

    position_code = models.PositiveSmallIntegerField()
    position_text = models.CharField(max_length=64)
    gender_code = models.PositiveSmallIntegerField()
    gender_text = models.CharField(max_length=32)
    location_code = models.PositiveSmallIntegerField()
    location_text = models.CharField(max_length=128)
    age_code = models.PositiveSmallIntegerField()
    age_text = models.CharField(max_length=64)
    job_title_code = models.PositiveSmallIntegerField()
    job_title_text = models.CharField(max_length=64)
    experience_code = models.PositiveSmallIntegerField()
    experience_text = models.CharField(max_length=64)

    week_1 = models.DecimalField(max_digits=4, decimal_places=2)
    week_2 = models.DecimalField(max_digits=4, decimal_places=2)
    week_3 = models.DecimalField(max_digits=4, decimal_places=2)
    vle_1 = models.PositiveIntegerField()
    vle_2 = models.PositiveIntegerField()
    vle_3 = models.PositiveIntegerField()
    total_studied_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completed_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=32, blank=True)
    final_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    predicted_final_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    prediction_source = models.CharField(max_length=32, blank=True)
    prediction_week = models.PositiveSmallIntegerField(null=True, blank=True)
    prediction_input_hash = models.CharField(max_length=64, blank=True)
    prediction_updated_at = models.DateTimeField(null=True, blank=True)
    prediction_error = models.TextField(blank=True)
    eye_score = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    nose_score = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    mouth_score = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    emotion_score = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)

    source_file = models.CharField(max_length=255, blank=True)
    source_row_number = models.PositiveIntegerField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'learning_analytics'
        ordering = ['student_id', 'course_id']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['course_id']),
            models.Index(fields=['location_code']),
            models.Index(fields=['final_score']),
            models.Index(fields=['predicted_final_score']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student_id', 'course_id'],
                name='la_snapshot_student_course_unique',
            ),
            models.CheckConstraint(
                check=models.Q(week_1__gte=0) & models.Q(week_1__lte=10),
                name='la_snapshot_week_1_0_10',
            ),
            models.CheckConstraint(
                check=models.Q(week_2__gte=0) & models.Q(week_2__lte=10),
                name='la_snapshot_week_2_0_10',
            ),
            models.CheckConstraint(
                check=models.Q(week_3__gte=0) & models.Q(week_3__lte=10),
                name='la_snapshot_week_3_0_10',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(final_score__isnull=True) |
                    (models.Q(final_score__gte=0) & models.Q(final_score__lte=10))
                ),
                name='la_snapshot_final_0_10',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(completed_percentage__isnull=True) |
                    (models.Q(completed_percentage__gte=0) & models.Q(completed_percentage__lte=100))
                ),
                name='la_snapshot_completed_pct_0_100',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(total_studied_time__isnull=True) |
                    models.Q(total_studied_time__gte=0)
                ),
                name='la_snapshot_total_studied_time_non_negative',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(predicted_final_score__isnull=True) |
                    (models.Q(predicted_final_score__gte=0) & models.Q(predicted_final_score__lte=10))
                ),
                name='la_snapshot_predicted_final_0_10',
            ),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.course_id} ({self.final_score})"
