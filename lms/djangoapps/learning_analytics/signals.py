"""Signals for learning_analytics.

Auto-enroll all existing users into a course when a CourseOverview is created.
This behavior is guarded by settings.LEARNING_ANALYTICS_AUTO_ENROLL_ALL (default False)
and will skip staff/superusers if LEARNING_ANALYTICS_AUTO_ENROLL_SKIP_STAFF is True.
"""
import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models.course_enrollment import CourseEnrollment, AlreadyEnrolledError

log = logging.getLogger(__name__)

# Treat these module types as "learning material opens" for VLE counting.
TRACKED_LEARNING_MATERIAL_TYPES = {'html', 'video', 'problem'}


@receiver(post_save, sender=CourseOverview)
def auto_enroll_all_users_on_course_create(sender, instance, created, **kwargs):
    """Enroll all existing users into a newly created course overview.

    This is intentionally opt-in via settings to avoid surprising behavior.
    """
    if not created:
        return

    if not getattr(settings, 'LEARNING_ANALYTICS_AUTO_ENROLL_ALL', False):
        log.debug('LEARNING_ANALYTICS_AUTO_ENROLL_ALL is disabled; skipping auto-enroll for %s', instance.id)
        return

    skip_staff = getattr(settings, 'LEARNING_ANALYTICS_AUTO_ENROLL_SKIP_STAFF', True)

    User = get_user_model()
    course_key = instance.id

    # Use a transaction per batch to avoid partial updates in case of errors.
    users_qs = User.objects.all()
    if skip_staff:
        users_qs = users_qs.filter(is_staff=False, is_superuser=False)

    total = users_qs.count()
    log.info('Auto-enrolling %d users into course %s', total, course_key)

    # Iterate in batches to avoid loading all users into memory
    batch_size = 500
    offset = 0
    while True:
        batch = list(users_qs[offset:offset + batch_size])
        if not batch:
            break

        with transaction.atomic():
            for user in batch:
                try:
                    # CourseEnrollment.enroll is idempotent in practice; it logs if already enrolled.
                    CourseEnrollment.enroll(user, course_key, check_access=False)
                except AlreadyEnrolledError:
                    # Silently ignore; user already enrolled
                    continue
                except Exception as exc:  # pylint: disable=broad-except
                    log.exception('Failed to auto-enroll user %s into %s: %s', user.username, course_key, exc)

        offset += batch_size

    log.info('Auto-enroll completed for course %s', course_key)
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
    if created and instance.module_type in TRACKED_LEARNING_MATERIAL_TYPES:
        LearningHoursService.record_material_open(
            user=instance.student,
            course_id=instance.course_id,
            module_type=instance.module_type,
        )

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
    """Perform lightweight login-time tasks.

    - Optionally auto-enroll a user into courses for which a CourseEnrollmentAllowed
      entry exists with auto_enroll=True (feature-gated).
    """
    try:
        if getattr(settings, 'LEARNING_ANALYTICS_AUTO_ENROLL_FROM_ALLOWEDS_ON_LOGIN', True):
            # Local import to avoid import cycles on startup
            from common.djangoapps.student.models import CourseEnrollmentAllowed  # pylint: disable=import-outside-toplevel

            alloweds_qs = CourseEnrollmentAllowed.objects.filter(
                email=user.email,
                auto_enroll=True,
            )

            count = alloweds_qs.count()
            if count:
                log.info('Auto-enrolling %s from %d alloweds on login', user.username, count)
            for cea in alloweds_qs:
                course_key = cea.course_id
                try:
                    # Enroll regardless of enrollment window; we intentionally pass check_access=False
                    CourseEnrollment.enroll(user, course_key, check_access=False)
                    # Link the CEA to the user if it isn't already linked, mirroring built-in behavior
                    if not getattr(cea, 'user_id', None):
                        cea.user = user
                        cea.save(update_fields=['user'])
                except AlreadyEnrolledError:
                    # Ensure linkage even if already enrolled
                    if not getattr(cea, 'user_id', None):
                        cea.user = user
                        cea.save(update_fields=['user'])
                    continue
                except Exception as exc:  # pylint: disable=broad-except
                    log.exception('Login auto-enroll failed for user %s into %s: %s', user.username, course_key, exc)
    except Exception:  # pylint: disable=broad-except
        # We never want login to fail due to non-critical enrollment logic
        log.exception('Unexpected error during login-time auto-enroll processing for %s', getattr(user, 'username', 'unknown'))


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
