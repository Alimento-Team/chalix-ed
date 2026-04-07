"""
Services for learning analytics and credit hours management.
"""
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Count, Sum

from .models import (
    CourseCreditHours,
    StudentCourseProgress,
    LearningHoursRequirement,
    LearningHoursApproval,
    LearnerRecommendation,
    StudentLearningProcessSnapshot,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment


class LearningHoursService:
    """
    Service class for managing learning hours and credit-based tracking.
    """

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

    @staticmethod
    def get_for_user(user):
        return StudentLearningProcessSnapshot.objects.filter(user=user).first()

    @staticmethod
    def list_for_staff(filters):
        queryset = StudentLearningProcessSnapshot.objects.select_related('user').all()

        if filters.get('student_id'):
            queryset = queryset.filter(student_id__icontains=filters['student_id'])
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

        return queryset.order_by('student_id')

    @staticmethod
    def aggregate_for_staff():
        queryset = StudentLearningProcessSnapshot.objects.all()

        totals = queryset.aggregate(
            total_records=Count('id'),
            avg_final_score=Avg('final_score'),
            avg_week_1=Avg('week_1'),
            avg_week_2=Avg('week_2'),
            avg_week_3=Avg('week_3'),
            avg_vle_1=Avg('vle_1'),
            avg_vle_2=Avg('vle_2'),
            avg_vle_3=Avg('vle_3'),
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
            'avg_week_1': float(totals['avg_week_1'] or 0),
            'avg_week_2': float(totals['avg_week_2'] or 0),
            'avg_week_3': float(totals['avg_week_3'] or 0),
            'avg_vle_1': float(totals['avg_vle_1'] or 0),
            'avg_vle_2': float(totals['avg_vle_2'] or 0),
            'avg_vle_3': float(totals['avg_vle_3'] or 0),
            'position_distribution': as_distribution(queryset, 'position_code', 'position_text'),
            'gender_distribution': as_distribution(queryset, 'gender_code', 'gender_text'),
            'job_title_distribution': as_distribution(queryset, 'job_title_code', 'job_title_text'),
        }
