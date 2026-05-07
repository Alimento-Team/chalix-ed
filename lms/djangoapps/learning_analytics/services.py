"""
Services for learning analytics and credit hours management.
"""
import hashlib
import json
import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection, transaction
from django.db.models import F, Q
from django.db.models import Avg, Count, Sum

from .models import (
    LearnerBehavior,
    CourseCreditHours,
    StudentCourseProgress,
    LearningHoursRequirement,
    LearningHoursApproval,
    LearnerRecommendation,
    FacialExpressionLog,
    StudentLearningProcessSnapshot,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_home_api.models import ChalixCourseMetadataLMS


LOGGER = logging.getLogger(__name__)


class CourseSuggestionService:
    """Generate weighted course recommendations used by learner-home and dashboard surfaces."""

    WEIGHT_POPULAR_ORG = 0.35
    WEIGHT_POSITION_MATCH = 0.30
    WEIGHT_MANDATORY_INTERNAL = 0.20
    WEIGHT_MANDATORY_MINISTRY = 0.15
    WEIGHT_ELECTIVE = 0.10

    @staticmethod
    def _get_user_context(user):
        """Return user organization/professional field context from Chalix role table."""
        context = {
            'organization_id': None,
            'professional_field_id': None,
        }
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT organization_id
                    FROM contentstore_chalixuserrole
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    [user.id],
                )
                row = cursor.fetchone()
                if row:
                    context['organization_id'] = row[0]
        except Exception:  # pragma: no cover - defensive fallback
            LOGGER.exception('Unable to load Chalix user context for recommendations')
        return context

    @staticmethod
    def _deterministic_noise(user_id, course_id):
        """Stable pseudo-random value in [0, 1) used to diversify elective ties."""
        digest = hashlib.sha256(f"{user_id}:{course_id}".encode('utf-8')).hexdigest()
        return int(digest[:8], 16) / float(0xFFFFFFFF)

    @staticmethod
    def _get_learning_hours_state(user):
        """Get remaining required learning hours for current year."""
        try:
            summary = LearningHoursService.get_user_learning_hours_summary(
                user,
                timezone.now().year,
            )
            required = float(summary.get('required_hours') or 40)
            completed = float(summary.get('completed_hours') or 0)
            return max(required - completed, 0)
        except Exception:  # pragma: no cover - defensive fallback
            return 40

    @staticmethod
    def _get_visible_metadata_for_user(user_context):
        """Return visible course metadata records for a learner."""
        org_id = user_context.get('organization_id')
        visibility_query = Q(is_public=True)
        if org_id:
            visibility_query |= Q(is_public=False, creator_organization_id=org_id)

        return list(ChalixCourseMetadataLMS.objects.filter(visibility_query))

    @staticmethod
    def _get_popularity_map(course_ids):
        """Return active enrollment counts for course IDs."""
        if not course_ids:
            return {}

        rows = (
            CourseEnrollment.objects.filter(is_active=True, course_id__in=course_ids)
            .values('course_id')
            .annotate(total=Count('id'))
        )
        return {str(row['course_id']): int(row['total']) for row in rows}

    @classmethod
    def get_ranked_course_ids(cls, user, limit=50):
        """
        Return ranked visible course IDs for a learner using weighted criteria.

        Criteria currently implemented:
        - Popular courses in same organization
        - Professional field match (position proxy)
        - Mandatory/elective recommendations to satisfy 40-hour requirement
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return []

        user_context = cls._get_user_context(user)
        visible_metadata = cls._get_visible_metadata_for_user(user_context)
        if not visible_metadata:
            return []

        course_ids = [meta.course_id for meta in visible_metadata]
        popularity_map = cls._get_popularity_map(course_ids)
        remaining_hours = cls._get_learning_hours_state(user)
        user_org_id = user_context.get('organization_id')
        user_professional_field_id = user_context.get('professional_field_id')

        scored = []
        has_profile_signal = bool(user_professional_field_id)

        for meta in visible_metadata:
            course_id = str(meta.course_id)
            enrollment_count = popularity_map.get(course_id, 0)
            is_internal_scope = (
                (meta.is_public is False)
                and bool(user_org_id)
                and meta.creator_organization_id == user_org_id
            )
            is_ministry_scope = bool(meta.is_public)
            is_mandatory = bool(meta.is_mandatory_course) or meta.course_category == 'mandatory'
            is_elective = (
                meta.course_category == 'elective' or meta.publish_type == 'elective'
            )

            score = 0.0

            # Criterion 1: Most popular in same organization.
            if is_internal_scope and enrollment_count > 0:
                score += cls.WEIGHT_POPULAR_ORG * min(enrollment_count / 20.0, 1.0)

            # Criterion 2: Position/job match using professional_field_id proxy.
            if (
                user_professional_field_id
                and meta.professional_field_id
                and meta.professional_field_id == user_professional_field_id
            ):
                score += cls.WEIGHT_POSITION_MATCH

            # Criteria 3/4: Mandatory and elective coverage for remaining 40-hour requirement.
            if remaining_hours > 0:
                if is_mandatory and is_internal_scope:
                    score += cls.WEIGHT_MANDATORY_INTERNAL
                elif is_mandatory and is_ministry_scope:
                    score += cls.WEIGHT_MANDATORY_MINISTRY
                elif is_elective and (is_internal_scope or is_ministry_scope):
                    score += cls.WEIGHT_ELECTIVE

            # Cold-start fallback: lean on popularity when profile signals are missing.
            if not has_profile_signal:
                score += 0.15 * min(enrollment_count / 30.0, 1.0)

            # Keep low-confidence candidates in deterministic order.
            score += cls._deterministic_noise(user.id, course_id) * 0.01

            scored.append((course_id, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [course_id for course_id, _ in scored[:limit]]

    @classmethod
    def get_recommendation_rank_map(cls, user, limit=50):
        """Return a course_id -> rank map for fast ordering in view/serializer layers."""
        ranked_ids = cls.get_ranked_course_ids(user=user, limit=limit)
        return {course_id: index for index, course_id in enumerate(ranked_ids)}


class LearningHoursService:
    """
    Service class for managing learning hours and credit-based tracking.
    """

    @staticmethod
    def track_time_spent(user, course_id, minutes_spent):
        """Track learning time for a user/course pair."""
        if not user or not getattr(user, 'is_authenticated', False):
            return None

        if minutes_spent is None or minutes_spent <= 0:
            return None

        behavior, _ = LearnerBehavior.objects.get_or_create(
            user=user,
            course_id=str(course_id),
            defaults={
                'total_time_spent_minutes': 0,
                'last_activity': timezone.now(),
            },
        )
        behavior.total_time_spent_minutes += int(minutes_spent)
        behavior.last_activity = timezone.now()
        behavior.save(update_fields=['total_time_spent_minutes', 'last_activity', 'modified'])
        return behavior

    @staticmethod
    def update_activity_metrics(user, course_id, activity_type):
        """Update lightweight activity counters on learner behavior."""
        if not user or not getattr(user, 'is_authenticated', False):
            return None

        behavior, _ = LearnerBehavior.objects.get_or_create(
            user=user,
            course_id=str(course_id),
            defaults={'last_activity': timezone.now()},
        )

        update_fields = ['last_activity', 'modified']
        if activity_type in ('video_watched', 'video_opened'):
            behavior.videos_watched += 1
            update_fields.append('videos_watched')
        elif activity_type in ('assignment_completed', 'quiz_opened', 'problem_opened'):
            behavior.problems_attempted += 1
            update_fields.append('problems_attempted')
        elif activity_type in ('discussion_participated',):
            behavior.discussions_participated += 1
            update_fields.append('discussions_participated')
        elif activity_type in ('material_opened',):
            behavior.materials_opened += 1
            update_fields.append('materials_opened')

        behavior.last_activity = timezone.now()
        behavior.save(update_fields=update_fields)
        return behavior

    @staticmethod
    def auto_track_course_completion(user, course_id):
        """Mark a learner's course progress as completed when auto-detected."""
        return LearningHoursService.update_student_course_progress(
            user=user,
            course_id=str(course_id),
            status='completed',
            progress_percentage=100,
        )

    @staticmethod
    def increment_student_vle_for_week(user, course_id, week_number, increment_by=1):
        """Increment a student's weekly VLE interaction counter in snapshot table."""
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        if week_number not in (1, 2, 3) or increment_by <= 0:
            return False

        normalized_course_id = str(course_id or '').strip()
        if not normalized_course_id:
            return False

        vle_field = f'vle_{week_number}'
        updated = StudentLearningProcessSnapshot.objects.filter(
            user=user,
            course_id=normalized_course_id,
        ).update(
            **{vle_field: F(vle_field) + int(increment_by)}
        )
        return updated > 0

    @staticmethod
    def resolve_learning_week(user, course_id):
        """Resolve current learning week from enrollment age (1..3)."""
        if not user or not getattr(user, 'is_authenticated', False):
            return 1

        enrollment = CourseEnrollment.objects.filter(
            user=user,
            course_id=course_id,
            is_active=True,
        ).order_by('created').first()
        if not enrollment or not enrollment.created:
            return 1

        days_since_enrollment = max(0, (timezone.now() - enrollment.created).days)
        return min(3, (days_since_enrollment // 7) + 1)

    @staticmethod
    def record_material_open(user, course_id, module_type='html'):
        """Record one learning-material open event and increment the matching weekly VLE counter."""
        if not user or not getattr(user, 'is_authenticated', False):
            return {'tracked': False, 'reason': 'anonymous_user'}

        module_type = (module_type or 'html').lower().strip()
        activity_type = {
            'video': 'video_opened',
            'problem': 'problem_opened',
            'quiz': 'quiz_opened',
            'html': 'material_opened',
            'slides': 'material_opened',
        }.get(module_type, 'material_opened')

        week_number = LearningHoursService.resolve_learning_week(user, course_id)
        incremented = LearningHoursService.increment_student_vle_for_week(
            user=user,
            course_id=course_id,
            week_number=week_number,
            increment_by=1,
        )

        LearningHoursService.update_activity_metrics(
            user=user,
            course_id=course_id,
            activity_type=activity_type,
        )

        return {
            'tracked': True,
            'week_number': week_number,
            'snapshot_updated': incremented,
            'activity_type': activity_type,
        }

    @staticmethod
    def set_course_credit_hours(course_id, credit_hours, created_by):
        """
        Set credit hours for a course.

        Args:
            course_id: Course ID string
            credit_hours: Number of credit hours for the course
            created_by: User who is setting the credit hours

        Returns:
            CourseCreditHours object
        """
        # Get course name from CourseOverview
        try:
            course_overview = CourseOverview.objects.get(id=course_id)
            course_name = course_overview.display_name
        except CourseOverview.DoesNotExist:
            course_name = f"Course {course_id}"

        # Create or update course credit hours
        course_credits, created = CourseCreditHours.objects.get_or_create(
            course_id=course_id,
            defaults={
                'course_name': course_name,
                'credit_hours': credit_hours,
                'created_by': created_by
            }
        )

        if not created:
            course_credits.credit_hours = credit_hours
            course_credits.updated_at = timezone.now()
            course_credits.save()

        return course_credits

    @staticmethod
    def update_student_course_progress(user, course_id, status, progress_percentage=None):
        """
        Update student progress for a course and automatically allocate credit hours on completion.

        Args:
            user: User object
            course_id: Course ID string
            status: Course status ('not_started', 'in_progress', 'completed', 'failed')
            progress_percentage: Progress percentage (0-100)

        Returns:
            StudentCourseProgress object
        """
        # Get or create progress record
        progress, created = StudentCourseProgress.objects.get_or_create(
            user=user,
            course_id=course_id,
            defaults={
                'status': status,
                'progress_percentage': progress_percentage or 0,
                'enrollment_date': timezone.now()
            }
        )

        if not created:
            progress.status = status
            if progress_percentage is not None:
                progress.progress_percentage = progress_percentage

            # If course is completed, allocate credit hours
            if status == 'completed' and progress.status != 'completed':
                progress.completion_date = timezone.now()

                # Get course credit hours
                try:
                    course_credits = CourseCreditHours.objects.get(course_id=course_id)
                    progress.credit_hours_earned = course_credits.credit_hours
                except CourseCreditHours.DoesNotExist:
                    # If no credit hours set, default to 0
                    progress.credit_hours_earned = 0

            progress.last_activity_date = timezone.now()
            progress.save()

        return progress

    @staticmethod
    def get_student_completed_hours(user, year=None):
        """
        Get total completed credit hours for a student.

        Args:
            user: User object
            year: Year to filter by (optional)

        Returns:
            Total completed credit hours
        """
        query = StudentCourseProgress.objects.filter(
            user=user,
            status='completed'
        )

        if year:
            query = query.filter(completion_date__year=year)

        total_hours = query.aggregate(
            total=Sum('credit_hours_earned')
        )['total'] or 0

        return total_hours

    @staticmethod
    def get_user_learning_hours_summary(user, year):
        """
        Get comprehensive learning hours summary for a user.

        Args:
            user: User object
            year: Year for the summary

        Returns:
            Dictionary with learning hours summary
        """
        # Get completed hours
        completed_hours = LearningHoursService.get_student_completed_hours(user, year)

        # Get requirement for the year
        try:
            requirement = LearningHoursRequirement.objects.get(
                user=user,
                current_year=year
            )
            required_hours = requirement.required_hours
            status = requirement.status
        except LearningHoursRequirement.DoesNotExist:
            required_hours = 40  # Default
            status = 'in_progress'

        # Calculate completion percentage
        completion_percentage = min(100, (completed_hours / required_hours * 100)) if required_hours > 0 else 0

        # Get pending approvals
        pending_approvals = LearningHoursApproval.objects.filter(
            requirement__user=user,
            requirement__current_year=year,
            status='pending'
        )
        pending_hours = sum(approval.requested_hours for approval in pending_approvals)

        return {
            'completed_hours': completed_hours,
            'required_hours': required_hours,
            'completion_percentage': round(completion_percentage, 1),
            'status': status,
            'remaining_hours': max(0, required_hours - completed_hours),
            'pending_approval_hours': pending_hours,
            'year': year
        }

    @staticmethod
    def create_learning_requirement(user, required_hours, year):
        """
        Create or update learning hours requirement for a user.

        Args:
            user: User object
            required_hours: Required hours for the year
            year: Year for the requirement

        Returns:
            LearningHoursRequirement object
        """
        requirement, created = LearningHoursRequirement.objects.get_or_create(
            user=user,
            current_year=year,
            defaults={
                'required_hours': required_hours,
                'status': 'in_progress'
            }
        )

        if not created:
            requirement.required_hours = required_hours
            requirement.save()

        return requirement

    @staticmethod
    def request_hours_approval(user, requested_hours, evidence_description, evidence_files):
        """
        Create a request for additional hours approval.

        Args:
            user: User object
            requested_hours: Hours being requested
            evidence_description: Description of evidence
            evidence_files: List of evidence files

        Returns:
            LearningHoursApproval object
        """
        # Get current year requirement
        year = timezone.now().year
        try:
            requirement = LearningHoursRequirement.objects.get(
                user=user,
                current_year=year
            )
        except LearningHoursRequirement.DoesNotExist:
            requirement = LearningHoursService.create_learning_requirement(user, 40, year)

        approval = LearningHoursApproval.objects.create(
            requirement=requirement,
            requested_hours=requested_hours,
            evidence_description=evidence_description,
            evidence_files=evidence_files,
            status='pending'
        )

        return approval

    @staticmethod
    def get_course_credit_hours(course_id):
        """
        Get credit hours for a specific course.

        Args:
            course_id: Course ID string

        Returns:
            CourseCreditHours object or None
        """
        try:
            return CourseCreditHours.objects.get(course_id=course_id)
        except CourseCreditHours.DoesNotExist:
            return None

    @staticmethod
    def get_student_course_progress(user, course_id):
        """
        Get student progress for a specific course.

        Args:
            user: User object
            course_id: Course ID string

        Returns:
            StudentCourseProgress object or None
        """
        try:
            return StudentCourseProgress.objects.get(user=user, course_id=course_id)
        except StudentCourseProgress.DoesNotExist:
            return None


class StudentLearningProcessService:
    """Service methods for student learning-process snapshots."""

    SUPPORTED_PREDICTION_MODES = {'mla', 'emotion'}

    @staticmethod
    def _prediction_enabled():
        return bool(getattr(settings, 'LEARNING_ANALYTICS_PREDICTION_ENABLED', False))

    @staticmethod
    def _prediction_mode():
        mode = str(getattr(settings, 'LEARNING_ANALYTICS_PREDICTION_MODE', 'emotion')).strip().lower()
        if mode not in StudentLearningProcessService.SUPPORTED_PREDICTION_MODES:
            return 'emotion'
        return mode

    @staticmethod
    def _prediction_timeout_seconds():
        timeout = getattr(settings, 'LEARNING_ANALYTICS_PREDICTION_TIMEOUT_SECONDS', 3)
        try:
            return max(1.0, float(timeout))
        except (TypeError, ValueError):
            return 3.0

    @staticmethod
    def _prediction_headers():
        token = str(getattr(settings, 'LEARNING_ANALYTICS_PREDICTION_AUTH_TOKEN', '')).strip()
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    @staticmethod
    def _prediction_url(mode):
        if mode == 'emotion':
            return str(getattr(settings, 'LEARNING_ANALYTICS_EMOTION_PREDICTION_URL', '')).strip()
        return str(getattr(settings, 'LEARNING_ANALYTICS_MLA_PREDICTION_URL', '')).strip()

    @staticmethod
    def _prediction_week(snapshot):
        if snapshot.week_3 is not None and snapshot.vle_3 is not None:
            return 3
        if snapshot.week_2 is not None and snapshot.vle_2 is not None:
            return 2
        return 1

    @staticmethod
    def _as_float(value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError, InvalidOperation):
            return None

    @staticmethod
    def _latest_emotion_file_url(snapshot, course_id=None, week_number=None):
        if not snapshot or not snapshot.user:
            return None

        queryset = FacialExpressionLog.objects.filter(
            user=snapshot.user,
            is_complete=True,
        )
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if week_number:
            queryset = queryset.filter(video_path__contains=f'/week_{int(week_number)}/')

        latest_log = queryset.order_by('-start_timestamp', '-id').first()
        if not latest_log:
            return None
        return latest_log.video_path

    @staticmethod
    def _build_prediction_payload(snapshot, mode, course_id=None, week_number=None):
        resolved_week_number = week_number or StudentLearningProcessService._prediction_week(snapshot)
        payload = {
            'week_number': resolved_week_number,
            'position': snapshot.position_text,
            'gender': snapshot.gender_text,
            'location': snapshot.location_text,
            'age': snapshot.age_text,
            'job_title': snapshot.job_title_text,
            'experience': snapshot.experience_text,
            'score_1': StudentLearningProcessService._as_float(snapshot.week_1),
            'vle_1': StudentLearningProcessService._as_float(snapshot.vle_1),
        }

        if resolved_week_number >= 2:
            payload['score_2'] = StudentLearningProcessService._as_float(snapshot.week_2)
            payload['vle_2'] = StudentLearningProcessService._as_float(snapshot.vle_2)
        if resolved_week_number >= 3:
            payload['score_3'] = StudentLearningProcessService._as_float(snapshot.week_3)
            payload['vle_3'] = StudentLearningProcessService._as_float(snapshot.vle_3)

        if mode == 'emotion':
            file_url = StudentLearningProcessService._latest_emotion_file_url(
                snapshot,
                course_id=course_id,
                week_number=resolved_week_number,
            )
            if not file_url:
                raise ValueError('No completed emotion recording found for this learner')
            payload['file_url'] = file_url

        return payload

    @staticmethod
    def _prediction_input_hash(payload):
        normalized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _call_prediction_api(mode, payload):
        url = StudentLearningProcessService._prediction_url(mode)
        if not url:
            raise ValueError(f'Missing prediction URL for mode: {mode}')

        response = requests.post(
            url,
            json=payload,
            headers=StudentLearningProcessService._prediction_headers(),
            timeout=StudentLearningProcessService._prediction_timeout_seconds(),
        )
        response.raise_for_status()
        body = response.json()
        score = body.get('predicted_score')
        if score is None:
            raise ValueError('Prediction API did not return predicted_score')

        predicted_score = Decimal(str(score))
        if predicted_score < Decimal('0') or predicted_score > Decimal('10'):
            raise ValueError('Prediction API returned predicted_score outside 0..10 range')

        result = {
            'predicted_score': predicted_score,
            'week_number': int(body.get('week_number') or payload.get('week_number') or 1),
        }

        # Capture emotion features if present (emotion-prediction endpoint only)
        for field in ('eye_score', 'nose_score', 'mouth_score', 'emotion_score'):
            raw = body.get(field)
            if raw is not None:
                result[field] = Decimal(str(raw))

        return result

    @staticmethod
    def refresh_prediction(snapshot, force=False, course_id=None, week_number=None):
        """Refresh persisted prediction if inputs changed or force=True."""
        if not snapshot or not StudentLearningProcessService._prediction_enabled():
            return snapshot

        try:
            mode = StudentLearningProcessService._prediction_mode()
            payload = StudentLearningProcessService._build_prediction_payload(
                snapshot,
                mode,
                course_id=course_id,
                week_number=week_number,
            )
            input_hash = StudentLearningProcessService._prediction_input_hash(payload)

            has_prediction = snapshot.predicted_final_score is not None
            if not force and has_prediction and snapshot.prediction_input_hash == input_hash:
                return snapshot

            result = StudentLearningProcessService._call_prediction_api(mode, payload)
            snapshot.predicted_final_score = result['predicted_score']
            snapshot.prediction_week = result['week_number']
            snapshot.prediction_source = mode
            snapshot.prediction_input_hash = input_hash
            snapshot.prediction_updated_at = timezone.now()
            snapshot.prediction_error = ''

            # Persist emotion feature scores when returned by the API
            emotion_fields = ('eye_score', 'nose_score', 'mouth_score', 'emotion_score')
            for field in emotion_fields:
                if field in result:
                    setattr(snapshot, field, result[field])

            update_fields = [
                'predicted_final_score',
                'prediction_week',
                'prediction_source',
                'prediction_input_hash',
                'prediction_updated_at',
                'prediction_error',
                'updated_at',
            ] + [f for f in emotion_fields if f in result]

            snapshot.save(update_fields=update_fields)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning('Failed to refresh prediction for student_id=%s: %s', snapshot.student_id, exc)
            snapshot.prediction_error = str(exc)
            snapshot.save(update_fields=['prediction_error', 'updated_at'])

        return snapshot

    @staticmethod
    def get_for_user(user, refresh_prediction=False, course_id=None, week_number=None):
        normalized_course_id = str(course_id or '').strip()
        if not normalized_course_id:
            return None

        snapshot = StudentLearningProcessSnapshot.objects.filter(
            user=user,
            course_id=normalized_course_id,
        ).first()
        if refresh_prediction and snapshot:
            resolved_week = week_number
            if resolved_week is None:
                resolved_week = LearningHoursService.resolve_learning_week(user, normalized_course_id)
            return StudentLearningProcessService.refresh_prediction(
                snapshot,
                course_id=normalized_course_id,
                week_number=resolved_week,
            )
        return snapshot

    @staticmethod
    def get_or_create_live_snapshot(user, course_id):
        """Return existing snapshot for user/course, or create a minimal live one.

        For learners who enrolled directly (not imported from CSV), no snapshot
        row exists. This method creates a stub record with neutral defaults so
        that live predictions (emotion-score API) can still be run.
        """
        normalized_course_id = str(course_id or '').strip()
        if not user or not normalized_course_id:
            return None

        snapshot = StudentLearningProcessSnapshot.objects.filter(
            user=user,
            course_id=normalized_course_id,
        ).first()
        if snapshot:
            return snapshot

        # Try to derive gender from user profile
        gender_code = 0
        gender_text = 'Unknown'
        try:
            profile = user.profile
            if profile.gender == 'm':
                gender_code, gender_text = 1, 'Male'
            elif profile.gender == 'f':
                gender_code, gender_text = 2, 'Female'
            elif profile.gender == 'o':
                gender_code, gender_text = 3, 'Other'
        except Exception:  # pylint: disable=broad-except
            pass

        snapshot = StudentLearningProcessSnapshot.objects.create(
            user=user,
            student_id=str(user.id),
            course_id=normalized_course_id,
            position_code=0,
            position_text='Unknown',
            gender_code=gender_code,
            gender_text=gender_text,
            location_code=0,
            location_text='Unknown',
            age_code=0,
            age_text='Unknown',
            job_title_code=0,
            job_title_text='Unknown',
            experience_code=0,
            experience_text='Unknown',
            week_1=Decimal('0'),
            week_2=Decimal('0'),
            week_3=Decimal('0'),
            vle_1=0,
            vle_2=0,
            vle_3=0,
            prediction_source='live',
        )
        return snapshot

    @staticmethod
    def list_for_staff(filters):
        queryset = StudentLearningProcessSnapshot.objects.select_related('user').all()

        if filters.get('student_id'):
            queryset = queryset.filter(student_id__icontains=filters['student_id'])
        if filters.get('course_id'):
            queryset = queryset.filter(course_id__icontains=filters['course_id'])
        if filters.get('position_code') is not None:
            queryset = queryset.filter(position_code=filters['position_code'])
        if filters.get('gender_code') is not None:
            queryset = queryset.filter(gender_code=filters['gender_code'])
        if filters.get('location_code') is not None:
            queryset = queryset.filter(location_code=filters['location_code'])
        if filters.get('min_final_score') is not None:
            queryset = queryset.filter(final_score__gte=filters['min_final_score'])
        if filters.get('max_final_score') is not None:
            queryset = queryset.filter(final_score__lte=filters['max_final_score'])

        return queryset.order_by('student_id', 'course_id')

    @staticmethod
    def aggregate_for_staff(course_id=None):
        queryset = StudentLearningProcessSnapshot.objects.all()
        normalized_course_id = str(course_id or '').strip()
        if normalized_course_id:
            queryset = queryset.filter(course_id__icontains=normalized_course_id)

        totals = queryset.aggregate(
            total_records=Count('id'),
            avg_final_score=Avg('final_score'),
            avg_predicted_final_score=Avg('predicted_final_score'),
            avg_week_1=Avg('week_1'),
            avg_week_2=Avg('week_2'),
            avg_week_3=Avg('week_3'),
            avg_vle_1=Avg('vle_1'),
            avg_vle_2=Avg('vle_2'),
            avg_vle_3=Avg('vle_3'),
            total_with_actual_score=Count('id', filter=Q(final_score__isnull=False)),
            total_with_predicted_score=Count('id', filter=Q(predicted_final_score__isnull=False)),
        )

        def as_distribution(grouped_queryset, key_field, label_field):
            distribution = {}
            for row in grouped_queryset.values(key_field, label_field).annotate(count=Count('id')).order_by(key_field):
                label = f"{row[key_field]}:{row[label_field]}"
                distribution[label] = row['count']
            return distribution

        return {
            'total_records': totals['total_records'] or 0,
            'avg_final_score': float(totals['avg_final_score'] or 0),
            'avg_predicted_final_score': float(totals['avg_predicted_final_score'] or 0),
            'avg_week_1': float(totals['avg_week_1'] or 0),
            'avg_week_2': float(totals['avg_week_2'] or 0),
            'avg_week_3': float(totals['avg_week_3'] or 0),
            'avg_vle_1': float(totals['avg_vle_1'] or 0),
            'avg_vle_2': float(totals['avg_vle_2'] or 0),
            'avg_vle_3': float(totals['avg_vle_3'] or 0),
            'total_with_actual_score': int(totals['total_with_actual_score'] or 0),
            'total_with_predicted_score': int(totals['total_with_predicted_score'] or 0),
            'position_distribution': as_distribution(queryset, 'position_code', 'position_text'),
            'gender_distribution': as_distribution(queryset, 'gender_code', 'gender_text'),
            'job_title_distribution': as_distribution(queryset, 'job_title_code', 'job_title_text'),
        }
