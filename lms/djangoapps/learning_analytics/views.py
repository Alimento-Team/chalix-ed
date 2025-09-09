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

from .models import LearnerBehavior, LearnerRecommendation, LearningGoal
from .serializers import (
    LearnerStatsSerializer,
    CourseProgressSerializer,
    LearnerRecommendationSerializer,
    LearningGoalSerializer,
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
        total_time_spent = 0

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

            # Get completed assignments/tests
            completed_modules = StudentModule.objects.filter(
                student=user,
                course_id=course_key,
                grade__isnull=False,
                grade__gt=0
            ).count()

            total_tests_completed += completed_modules

            # Get learner behavior data
            behavior = LearnerBehavior.objects.filter(user=user, course_id=str(course_key)).first()
            if behavior:
                total_time_spent += behavior.total_time_spent

        # Get recent activity
        recent_enrollments = enrollments.filter(
            created__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Calculate current month statistics
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_behaviors = LearnerBehavior.objects.filter(
            user=user,
            updated_at__gte=current_month_start
        )

        monthly_study_time = monthly_behaviors.aggregate(
            total=Sum('total_time_spent')
        )['total'] or 0

        stats_data = {
            'total_courses_joined': total_enrolled,
            'courses_completed': completed_courses,
            'certificates_earned': certificates_earned,
            'total_tests_completed': total_tests_completed,
            'total_study_time_hours': round(total_time_spent / 60, 1),
            'monthly_study_time_hours': round(monthly_study_time / 60, 1),
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

            # Get learner behavior data
            behavior = LearnerBehavior.objects.filter(user=user, course_id=str(course_key)).first()
            study_time_hours = round(behavior.total_time_spent / 60, 1) if behavior else 0

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
                'study_time_hours': study_time_hours,
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
        user_completed_courses = CourseEnrollment.objects.filter(
            user=user,
            is_active=True
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


class LearningGoalsAPIView(APIView):
    """
    API view to manage learning goals.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        goals = LearningGoal.objects.filter(user=user).order_by('-created_at')

        serializer = LearningGoalSerializer(goals, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        data = request.data.copy()
        data['user'] = user.id

        serializer = LearningGoalSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
