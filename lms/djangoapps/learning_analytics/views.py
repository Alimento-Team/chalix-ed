"""
API views for learning analytics and personalized learning data.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.grades.api import CourseGradeFactory

from .models import (
    CourseCreditHours,
    StudentCourseProgress,
    LearningHoursRequirement,
    LearningHoursApproval,
    LearnerRecommendation
)
from .services import LearningHoursService
from .serializers import (
    LearnerStatsSerializer,
    CourseProgressSerializer,
    LearnerRecommendationSerializer,
    LearningHoursRequirementSerializer,
    LearningHoursApprovalSerializer,
    LearningHoursSummarySerializer,
)


class LearnerStatsAPIView(APIView):
    """
    API view to get comprehensive learner statistics for the personalized dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get enrollment statistics
        enrollments = CourseEnrollment.objects.filter(user=user, is_active=True)
        total_enrolled = enrollments.count()

        # Get completion statistics
        completed_courses = 0
        certificates_earned = 0
        total_tests_completed = 0
        total_credit_hours = 0

        for enrollment in enrollments:
            course_key = enrollment.course_id

            # Check if course is completed (has certificate)
            certificate = GeneratedCertificate.objects.filter(
                user=user,
                course_id=course_key,
                status='downloadable'
            ).first()

            if certificate:
                completed_courses += 1
                certificates_earned += 1

                # Get credit hours earned for completed course
                progress = StudentCourseProgress.objects.filter(
                    user=user,
                    course_id=str(course_key),
                    status='completed'
                ).first()
                if progress:
                    total_credit_hours += progress.credit_hours_earned

            # Get completed assignments/tests
            completed_modules = StudentModule.objects.filter(
                student=user,
                course_id=course_key,
                grade__isnull=False,
                grade__gt=0
            ).count()

            total_tests_completed += completed_modules

        # Get recent activity
        recent_enrollments = enrollments.filter(
            created__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Calculate current month statistics
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_progress = StudentCourseProgress.objects.filter(
            user=user,
            updated_at__gte=current_month_start
        )

        monthly_credit_hours = monthly_progress.aggregate(
            total=Sum('credit_hours_earned')
        )['total'] or 0

        stats_data = {
            'total_courses_joined': total_enrolled,
            'courses_completed': completed_courses,
            'certificates_earned': certificates_earned,
            'total_tests_completed': total_tests_completed,
            'total_credit_hours': round(total_credit_hours, 1),
            'monthly_credit_hours': round(monthly_credit_hours, 1),
            'recent_enrollments': recent_enrollments,
            'completion_rate': round((completed_courses / total_enrolled * 100) if total_enrolled > 0 else 0, 1)
        }

        serializer = LearnerStatsSerializer(stats_data)
        return Response(serializer.data)


class CourseProgressAPIView(APIView):
    """
    API view to get detailed course progress information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        year_filter = request.query_params.get('year')
        status_filter = request.query_params.get('status')  # 'completed', 'in_progress', 'not_started'

        enrollments = CourseEnrollment.objects.filter(user=user, is_active=True)

        # Apply year filter
        if year_filter:
            try:
                year = int(year_filter)
                enrollments = enrollments.filter(created__year=year)
            except ValueError:
                pass

        course_progress_data = []

        for enrollment in enrollments:
            course_key = enrollment.course_id

            try:
                course_overview = CourseOverview.objects.get(id=course_key)
            except CourseOverview.DoesNotExist:
                continue

            # Get course grade
            course_grade = CourseGradeFactory().read(user, course_key=course_key)
            progress_percentage = round(course_grade.percent * 100, 1) if course_grade else 0

            # Get certificate status
            certificate = GeneratedCertificate.objects.filter(
                user=user,
                course_id=course_key,
                status='downloadable'
            ).first()

            # Determine status
            if certificate:
                course_status = 'completed'
            elif progress_percentage > 0:
                course_status = 'in_progress'
            else:
                course_status = 'not_started'

            # Apply status filter
            if status_filter and course_status != status_filter:
                continue

            # Get student progress data
            progress = StudentCourseProgress.objects.filter(
                user=user,
                course_id=str(course_key)
            ).first()

            credit_hours_earned = progress.credit_hours_earned if progress else 0

            # Get assignments completed
            completed_assignments = StudentModule.objects.filter(
                student=user,
                course_id=course_key,
                grade__isnull=False,
                grade__gt=0
            ).count()

            course_data = {
                'course_id': str(course_key),
                'course_name': course_overview.display_name or 'Unnamed Course',
                'course_number': course_overview.number or '',
                'enrollment_date': enrollment.created,
                'progress_percentage': progress_percentage,
                'status': course_status,
                'credit_hours_earned': credit_hours_earned,
                'assignments_completed': completed_assignments,
                'certificate_earned': bool(certificate),
                'course_image_url': course_overview.course_image_url,
                'instructor_name': getattr(course_overview, 'instructor', 'Unknown'),
            }

            course_progress_data.append(course_data)

        # Sort by enrollment date (most recent first)
        course_progress_data.sort(key=lambda x: x['enrollment_date'], reverse=True)

        serializer = CourseProgressSerializer(course_progress_data, many=True)
        return Response(serializer.data)


class RecommendationsAPIView(APIView):
    """
    API view to get personalized course recommendations.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 5))

        # Get existing recommendations
        recommendations = LearnerRecommendation.objects.filter(
            user=user,
            is_active=True
        )[:limit]

        recommendation_data = []

        for rec in recommendations:
            try:
                course_overview = CourseOverview.objects.get(id=rec.course_id)

                # Check if already enrolled
                is_enrolled = CourseEnrollment.objects.filter(
                    user=user,
                    course_id=rec.course_id,
                    is_active=True
                ).exists()

                if not is_enrolled:  # Only show courses not already enrolled
                    rec_data = {
                        'course_id': rec.course_id,
                        'course_name': course_overview.display_name,
                        'course_number': course_overview.number,
                        'recommendation_type': rec.recommendation_type,
                        'confidence_score': rec.confidence_score,
                        'reason': rec.reason,
                        'course_image_url': course_overview.course_image_url,
                        'instructor_name': getattr(course_overview, 'instructor', 'Unknown'),
                    }
                    recommendation_data.append(rec_data)

            except CourseOverview.DoesNotExist:
                continue

        # If we don't have enough recommendations, generate some based on completed courses
        if len(recommendation_data) < limit:
            self._generate_recommendations(user, limit - len(recommendation_data))

        serializer = LearnerRecommendationSerializer(recommendation_data, many=True)
        return Response(serializer.data)

    def _generate_recommendations(self, user, count_needed):
        """
        Generate recommendations based on user's completed courses and popular courses.
        """
        # Get user's completed courses
        user_completed_courses = StudentCourseProgress.objects.filter(
            user=user,
            status='completed'
        ).values_list('course_id', flat=True)

        # Get popular courses that user hasn't enrolled in
        popular_courses = CourseOverview.objects.exclude(
            id__in=user_completed_courses
        ).filter(
            enrollment_start__lte=timezone.now(),
            enrollment_end__gte=timezone.now()
        )[:count_needed]

        for course in popular_courses:
            LearnerRecommendation.objects.get_or_create(
                user=user,
                course_id=str(course.id),
                defaults={
                    'recommendation_type': 'trending',
                    'confidence_score': 0.7,
                    'reason': 'Popular course in your area of interest',
                    'is_active': True
                }
            )


class LearningHoursAPIView(APIView):
    """
    API view to get and manage learning hours requirements.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get learning hours summary for the current user."""
        user = request.user
        year = int(request.query_params.get('year', timezone.now().year))

        # Get learning hours summary
        summary = LearningHoursService.get_user_learning_hours_summary(user, year)

        serializer = LearningHoursSummarySerializer(summary)
        return Response(serializer.data)

    def post(self, request):
        """Create or update learning hours requirement."""
        user = request.user
        year = int(request.data.get('year', timezone.now().year))
        required_hours = float(request.data.get('required_hours', 40))

        requirement = LearningHoursService.create_learning_requirement(
            user, required_hours, year
        )

        serializer = LearningHoursRequirementSerializer(requirement)
        return Response(serializer.data)


class LearningHoursApprovalAPIView(APIView):
    """
    API view to manage learning hours approval requests.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all approval requests for the current user."""
        user = request.user
        approvals = LearningHoursApproval.objects.filter(
            requirement__user=user
        ).order_by('-created_at')

        serializer = LearningHoursApprovalSerializer(approvals, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new approval request."""
        user = request.user
        requested_hours = float(request.data.get('requested_hours', 0))
        evidence_description = request.data.get('evidence_description', '')
        evidence_files = request.data.get('evidence_files', [])

        if requested_hours <= 0:
            return Response(
                {'error': 'Requested hours must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approval = LearningHoursService.request_hours_approval(
            user, requested_hours, evidence_description, evidence_files
        )

        serializer = LearningHoursApprovalSerializer(approval)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseCreditHoursAPIView(APIView):
    """
    API view to manage course credit hours (for teachers/admins).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get credit hours for courses."""
        course_id = request.query_params.get('course_id')

        if course_id:
            # Get specific course credit hours
            try:
                course_credits = CourseCreditHours.objects.get(course_id=course_id)
                return Response({
                    'course_id': course_credits.course_id,
                    'course_name': course_credits.course_name,
                    'credit_hours': course_credits.credit_hours,
                    'created_by': course_credits.created_by.username if course_credits.created_by else None,
                    'created_at': course_credits.created_at,
                    'updated_at': course_credits.updated_at
                })
            except CourseCreditHours.DoesNotExist:
                return Response(
                    {'error': 'Credit hours not set for this course'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get all course credit hours
            course_credits = CourseCreditHours.objects.all().order_by('course_name')
            data = []
            for credits in course_credits:
                data.append({
                    'course_id': credits.course_id,
                    'course_name': credits.course_name,
                    'credit_hours': credits.credit_hours,
                    'created_by': credits.created_by.username if credits.created_by else None,
                    'created_at': credits.created_at,
                    'updated_at': credits.updated_at
                })
            return Response(data)

    def post(self, request):
        """Set credit hours for a course (teacher/admin action)."""
        course_id = request.data.get('course_id')
        credit_hours = float(request.data.get('credit_hours', 0))

        if not course_id:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if credit_hours <= 0:
            return Response(
                {'error': 'Credit hours must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        course_credits = LearningHoursService.set_course_credit_hours(
            course_id, credit_hours, request.user
        )

        return Response({
            'course_id': course_credits.course_id,
            'course_name': course_credits.course_name,
            'credit_hours': course_credits.credit_hours,
            'created_by': course_credits.created_by.username if course_credits.created_by else None,
            'created_at': course_credits.created_at,
            'updated_at': course_credits.updated_at
        }, status=status.HTTP_201_CREATED)


class StudentProgressUpdateAPIView(APIView):
    """
    API view to update student course progress (internal use).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update student progress for a course."""
        user = request.user
        course_id = request.data.get('course_id')
        status_value = request.data.get('status', 'in_progress')
        progress_percentage = request.data.get('progress_percentage')

        if not course_id:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if status_value not in ['not_started', 'in_progress', 'completed', 'failed']:
            return Response(
                {'error': 'Invalid status value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        progress = LearningHoursService.update_student_course_progress(
            user, course_id, status_value, progress_percentage
        )

        return Response({
            'course_id': progress.course_id,
            'status': progress.status,
            'progress_percentage': progress.progress_percentage,
            'credit_hours_earned': progress.credit_hours_earned,
            'completion_date': progress.completion_date
        })


class LearningAnalyticsDashboardAPIView(APIView):
    """
    API view to get comprehensive learning analytics dashboard data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        year = int(request.query_params.get('year', timezone.now().year))

        # Get learning hours summary
        hours_summary = LearningHoursService.get_user_learning_hours_summary(user, year)

        # Get course progress summary
        course_progress = StudentCourseProgress.objects.filter(user=user)
        total_enrolled = course_progress.count()
        completed_count = course_progress.filter(status='completed').count()
        in_progress_count = course_progress.filter(status='in_progress').count()

        # Get credit hours breakdown by course
        completed_courses = course_progress.filter(status='completed')
        credit_hours_breakdown = []
        for progress in completed_courses:
            try:
                course_overview = CourseOverview.objects.get(id=progress.course_id)
                course_name = course_overview.display_name
            except CourseOverview.DoesNotExist:
                course_name = f"Course {progress.course_id}"

            credit_hours_breakdown.append({
                'course_id': progress.course_id,
                'course_name': course_name,
                'credit_hours': progress.credit_hours_earned,
                'completion_date': progress.completion_date
            })

        dashboard_data = {
            'learning_hours': hours_summary,
            'course_summary': {
                'total_enrolled': total_enrolled,
                'completed': completed_count,
                'in_progress': in_progress_count,
                'completion_rate': round((completed_count / total_enrolled * 100), 1) if total_enrolled > 0 else 0
            },
            'credit_hours_breakdown': credit_hours_breakdown,
            'year': year
        }

        return Response(dashboard_data)
