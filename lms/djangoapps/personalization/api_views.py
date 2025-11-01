"""
API views for personalization endpoints.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import UserCoursePersonalization, PersonalizationYearlyStats, LessonTimeTracking
from .serializers import (
    UserCoursePersonalizationSerializer,
    PersonalizationYearlyStatsSerializer,
    LessonTimeTrackingSerializer,
    PersonalizationDashboardSerializer,
)


class UserCoursePersonalizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user course personalization data.
    Provides CRUD operations for course progress tracking.
    """
    
    serializer_class = UserCoursePersonalizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's personalization data."""
        return UserCoursePersonalization.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """
        Update progress for a specific course.
        Expects: {
            'completed_lessons': int,
            'completed_certificates': int,
            'time_spent': float (minutes)
        }
        """
        personalization = self.get_object()
        
        completed_lessons = request.data.get('completed_lessons')
        completed_certificates = request.data.get('completed_certificates')
        time_spent = request.data.get('time_spent')
        
        if completed_lessons is not None:
            personalization.completed_lessons = completed_lessons
        
        if completed_certificates is not None:
            personalization.completed_certificates = completed_certificates
        
        if time_spent is not None:
            personalization.total_study_time += time_spent
        
        personalization.last_accessed = timezone.now()
        personalization.update_completion_percentage()
        
        # Update status based on completion
        if personalization.completion_percentage >= 100:
            personalization.status = 'completed'
        elif personalization.completion_percentage > 0:
            personalization.status = 'in_progress'
        
        personalization.save()
        
        serializer = self.get_serializer(personalization)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_courses(self, request):
        """Get all active (in-progress) courses for the user."""
        queryset = self.get_queryset().filter(
            status__in=['in_progress', 'not_started']
        ).order_by('-last_accessed')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed_courses(self, request):
        """Get all completed courses for the user."""
        queryset = self.get_queryset().filter(
            status='completed'
        ).order_by('-modified')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PersonalizationYearlyStatsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for yearly personalization statistics.
    """
    
    serializer_class = PersonalizationYearlyStatsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's yearly stats."""
        return PersonalizationYearlyStats.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current_year(self, request):
        """Get stats for the current year."""
        current_year = timezone.now().year
        stats, created = PersonalizationYearlyStats.objects.get_or_create(
            user=request.user,
            year=current_year
        )
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)


class PersonalizationDashboardView(APIView):
    """
    Main API view for the personalization dashboard.
    Returns comprehensive data for the dashboard page.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, year=None):
        """
        Get dashboard data for a specific year (or current year if not specified).
        """
        if year is None:
            year = timezone.now().year
        
        user = request.user
        
        # Get or create yearly stats
        yearly_stats, created = PersonalizationYearlyStats.objects.get_or_create(
            user=user,
            year=year
        )
        
        # Get active courses
        active_courses = UserCoursePersonalization.objects.filter(
            user=user,
            status__in=['in_progress', 'not_started']
        ).order_by('-last_accessed')
        
        # Get completed courses
        completed_courses = UserCoursePersonalization.objects.filter(
            user=user,
            status='completed'
        ).order_by('-modified')
        
        # Serialize data
        data = {
            'year': year,
            'yearly_stats': PersonalizationYearlyStatsSerializer(yearly_stats).data,
            'active_courses': UserCoursePersonalizationSerializer(active_courses, many=True).data,
            'completed_courses': UserCoursePersonalizationSerializer(completed_courses, many=True).data,
        }
        
        return Response(data)


class LessonTimeTrackingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for lesson time tracking.
    """
    
    serializer_class = LessonTimeTrackingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's lesson time tracking."""
        return LessonTimeTracking.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def track_time(self, request):
        """
        Track time spent on a lesson.
        Expects: {
            'course_id': str,
            'lesson_id': str,
            'lesson_name': str,
            'time_spent_minutes': float,
            'is_completed': bool
        }
        """
        course_id = request.data.get('course_id')
        lesson_id = request.data.get('lesson_id')
        lesson_name = request.data.get('lesson_name', '')
        time_spent = request.data.get('time_spent_minutes', 0)
        is_completed = request.data.get('is_completed', False)
        
        if not course_id or not lesson_id:
            return Response(
                {'error': 'course_id and lesson_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create lesson tracking
        tracking, created = LessonTimeTracking.objects.get_or_create(
            user=request.user,
            course_id=course_id,
            lesson_id=lesson_id,
            defaults={'lesson_name': lesson_name}
        )
        
        # Update time and completion
        tracking.time_spent_minutes += time_spent
        if is_completed and not tracking.is_completed:
            tracking.is_completed = True
            tracking.completed_at = timezone.now()
        tracking.save()
        
        serializer = self.get_serializer(tracking)
        return Response(serializer.data)
