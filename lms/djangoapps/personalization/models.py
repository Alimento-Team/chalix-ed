"""
Models for student personalization and learning statistics tracking.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField
from model_utils.models import TimeStampedModel

User = get_user_model()


class UserCoursePersonalization(TimeStampedModel):
    """
    Tracks personalization data for a user's course enrollment.
    Stores completion status, progress tracking, and time statistics.
    """
    
    COURSE_STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('paused', _('Paused')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_personalizations',
        db_index=True,
    )
    
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        help_text=_("Course ID for this personalization data")
    )
    
    # Progress tracking
    total_lessons = models.IntegerField(
        default=0,
        help_text=_("Total number of lessons in the course")
    )
    
    completed_lessons = models.IntegerField(
        default=0,
        help_text=_("Number of completed lessons")
    )
    
    total_certificates = models.IntegerField(
        default=0,
        help_text=_("Total number of certificates/assessments")
    )
    
    completed_certificates = models.IntegerField(
        default=0,
        help_text=_("Number of completed certificates/assessments")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=COURSE_STATUS_CHOICES,
        default='not_started',
        db_index=True,
    )
    
    # Time tracking (in minutes)
    average_completion_time_per_lesson = models.FloatField(
        default=0.0,
        help_text=_("Average time to complete a lesson in minutes")
    )
    
    total_study_time = models.FloatField(
        default=0.0,
        help_text=_("Total study time in minutes")
    )
    
    # Completion tracking
    completion_percentage = models.FloatField(
        default=0.0,
        help_text=_("Overall course completion percentage (0-100)")
    )
    
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last time the user accessed this course")
    )
    
    class Meta:
        unique_together = ('user', 'course_id')
        ordering = ['-last_accessed']
        verbose_name = _("User Course Personalization")
        verbose_name_plural = _("User Course Personalizations")
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'completion_percentage']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.course_id} ({self.status})"
    
    def update_completion_percentage(self):
        """Calculate and update completion percentage based on completed items."""
        total_items = self.total_lessons + self.total_certificates
        if total_items > 0:
            completed_items = self.completed_lessons + self.completed_certificates
            self.completion_percentage = (completed_items / total_items) * 100
        else:
            self.completion_percentage = 0.0
        self.save(update_fields=['completion_percentage'])
        return self.completion_percentage
    
    def get_lesson_progress_ratio(self):
        """Returns the lesson progress as a ratio string (e.g., '4/4')."""
        return f"{self.completed_lessons}/{self.total_lessons}"
    
    def get_certificate_progress_ratio(self):
        """Returns the certificate progress as a ratio string (e.g., '3/8')."""
        return f"{self.completed_certificates}/{self.total_certificates}"


class PersonalizationYearlyStats(TimeStampedModel):
    """
    Tracks yearly personalization statistics for a user.
    Aggregates data for annual overview and reporting.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='yearly_stats',
        db_index=True,
    )
    
    year = models.IntegerField(
        db_index=True,
        help_text=_("Year for these statistics")
    )
    
    # Course statistics
    total_courses_assigned = models.IntegerField(
        default=0,
        help_text=_("Total number of courses assigned in this year")
    )
    
    total_courses_completed = models.IntegerField(
        default=0,
        help_text=_("Total number of courses completed in this year")
    )
    
    # Time tracking
    total_study_time_hours = models.FloatField(
        default=0.0,
        help_text=_("Total study time in hours for the year")
    )
    
    average_time_per_course = models.FloatField(
        default=0.0,
        help_text=_("Average time per course in hours")
    )
    
    # Progress tracking
    total_lessons_completed = models.IntegerField(
        default=0,
        help_text=_("Total lessons completed in the year")
    )
    
    total_certificates_earned = models.IntegerField(
        default=0,
        help_text=_("Total certificates earned in the year")
    )
    
    # Completion rate
    overall_completion_rate = models.FloatField(
        default=0.0,
        help_text=_("Overall completion rate percentage for the year")
    )
    
    class Meta:
        unique_together = ('user', 'year')
        ordering = ['-year']
        verbose_name = _("Personalization Yearly Stats")
        verbose_name_plural = _("Personalization Yearly Stats")
        indexes = [
            models.Index(fields=['user', 'year']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.year} ({self.overall_completion_rate}%)"
    
    def update_completion_rate(self):
        """Calculate and update overall completion rate."""
        if self.total_courses_assigned > 0:
            self.overall_completion_rate = (
                self.total_courses_completed / self.total_courses_assigned
            ) * 100
        else:
            self.overall_completion_rate = 0.0
        self.save(update_fields=['overall_completion_rate'])
        return self.overall_completion_rate


class LessonTimeTracking(TimeStampedModel):
    """
    Tracks time spent on individual lessons for detailed analytics.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_time_tracking',
        db_index=True,
    )
    
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
    )
    
    lesson_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Unique identifier for the lesson/unit")
    )
    
    lesson_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Name of the lesson")
    )
    
    time_spent_minutes = models.FloatField(
        default=0.0,
        help_text=_("Time spent on this lesson in minutes")
    )
    
    is_completed = models.BooleanField(
        default=False,
        db_index=True,
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    class Meta:
        unique_together = ('user', 'course_id', 'lesson_id')
        ordering = ['-modified']
        verbose_name = _("Lesson Time Tracking")
        verbose_name_plural = _("Lesson Time Tracking")
        indexes = [
            models.Index(fields=['user', 'course_id', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson_name} ({self.time_spent_minutes}m)"
