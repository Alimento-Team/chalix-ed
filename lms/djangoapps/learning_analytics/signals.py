"""
Signals to automatically track learning hours and activities.
"""
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in

from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.user_api.models import CourseProgress
from .services import LearningHoursService


@receiver(post_save, sender=StudentModule)
def track_student_activity(sender, instance, created, **kwargs):
    """Track student activity when modules are accessed or completed."""
    if created or instance.grade:
        # Track time spent (estimate based on module type)
        estimated_minutes = 15  # Default estimate for module completion
        
        # Different estimates based on module type
        module_type = getattr(instance, 'module_type', 'unknown')
        time_estimates = {
            'video': 20,
            'problem': 25,
            'discussion': 10,
            'html': 5,
            'sequential': 30,
        }
        
        estimated_minutes = time_estimates.get(module_type, estimated_minutes)
        
        # Track the time
        LearningHoursService.track_time_spent(
            user=instance.student,
            course_id=instance.course_id,
            minutes_spent=estimated_minutes
        )
        
        # Update activity metrics
        if instance.grade and instance.grade > 0:
            LearningHoursService.update_activity_metrics(
                user=instance.student,
                course_id=instance.course_id,
                activity_type='assignment_completed'
            )


@receiver(post_save, sender=GeneratedCertificate)
def track_course_completion(sender, instance, created, **kwargs):
    """Track learning hours when a course is completed (certificate earned)."""
    if instance.status == 'downloadable' and created:
        # Auto-track course completion hours
        LearningHoursService.auto_track_course_completion(
            user=instance.user,
            course_id=instance.course_id
        )


@receiver(user_logged_in)
def update_login_frequency(sender, request, user, **kwargs):
    """Update login frequency for learning analytics."""
    # This would typically be handled by a more sophisticated tracking system
    # For now, we'll skip detailed login tracking
    pass


# Custom signal for video tracking
class VideoWatchedSignal:
    """Custom signal for when a video is watched."""
    
    @staticmethod
    def send(user, course_id, video_duration_minutes=None):
        """Send signal when a video is watched."""
        # Track video watching time
        time_spent = video_duration_minutes or 10  # Default 10 minutes
        LearningHoursService.track_time_spent(
            user=user,
            course_id=course_id,
            minutes_spent=time_spent
        )
        
        # Update video watched count
        LearningHoursService.update_activity_metrics(
            user=user,
            course_id=course_id,
            activity_type='video_watched'
        )


# Custom signal for discussion participation
class DiscussionParticipatedSignal:
    """Custom signal for when a user participates in discussions."""
    
    @staticmethod
    def send(user, course_id):
        """Send signal when user participates in discussion."""
        # Track discussion participation time (estimate 5 minutes)
        LearningHoursService.track_time_spent(
            user=user,
            course_id=course_id,
            minutes_spent=5
        )
        
        # Update discussion participation count
        LearningHoursService.update_activity_metrics(
            user=user,
            course_id=course_id,
            activity_type='discussion_participated'
        )


# Utility class to manually track learning time
class LearningTimeTracker:
    """Utility class for manually tracking learning time in views."""
    
    def __init__(self, user, course_id):
        self.user = user
        self.course_id = course_id
        self.start_time = None
    
    def start_session(self):
        """Start tracking a learning session."""
        from django.utils import timezone
        self.start_time = timezone.now()
    
    def end_session(self):
        """End tracking and save the session time."""
        if not self.start_time:
            return 0
        
        from django.utils import timezone
        end_time = timezone.now()
        session_duration = end_time - self.start_time
        minutes_spent = int(session_duration.total_seconds() / 60)
        
        if minutes_spent > 0:
            LearningHoursService.track_time_spent(
                user=self.user,
                course_id=self.course_id,
                minutes_spent=minutes_spent
            )
        
        return minutes_spent
    
    def track_activity(self, activity_type, duration_minutes=None):
        """Track a specific learning activity."""
        if duration_minutes:
            LearningHoursService.track_time_spent(
                user=self.user,
                course_id=self.course_id,
                minutes_spent=duration_minutes
            )
        
        LearningHoursService.update_activity_metrics(
            user=self.user,
            course_id=self.course_id,
            activity_type=activity_type
        )
