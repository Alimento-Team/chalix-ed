"""
REST API views for the personalization app.
"""
import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

from lms.djangoapps.courseware.courses import get_course_by_id
from openedx.core.lib.api.view_utils import view_auth_classes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    UserCoursePersonalization,
    LessonTimeTracking,
    PersonalizationYearlyStats
)

log = logging.getLogger(__name__)
User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """
    Get personalization statistics for the authenticated user.
    
    Returns:
        JSON response with:
        - yearly_stats: list of yearly statistics
        - current_courses: list of in-progress courses
        - completed_courses: list of completed courses
        - total_study_time: total time spent across all courses
    """
    user = request.user
    year = request.GET.get('year', datetime.now().year)
    
    try:
        year = int(year)
    except (ValueError, TypeError):
        year = datetime.now().year
    
    # Get yearly stats
    yearly_stats = PersonalizationYearlyStats.objects.filter(
        user=user,
        year=year
    ).first()
    
    yearly_stats_data = None
    if yearly_stats:
        yearly_stats_data = {
            'year': yearly_stats.year,
            'total_courses_assigned': yearly_stats.total_courses_assigned,
            'total_courses_completed': yearly_stats.total_courses_completed,
            'total_certificates_earned': yearly_stats.total_certificates_earned,
            'total_study_time_hours': yearly_stats.total_study_time_hours,
            'total_lessons_completed': yearly_stats.total_lessons_completed,
            'overall_completion_rate': yearly_stats.overall_completion_rate,
            'average_time_per_course': yearly_stats.average_time_per_course,
        }
    
    # Get current courses (in progress or not started)
    current_courses = UserCoursePersonalization.objects.filter(
        user=user,
        status__in=['in_progress', 'not_started']
    ).order_by('-last_accessed')
    
    current_courses_data = []
    for course_data in current_courses:
        current_courses_data.append({
            'course_id': str(course_data.course_id),
            'status': course_data.status,
            'completion_percentage': course_data.completion_percentage,
            'completed_lessons': course_data.completed_lessons,
            'total_lessons': course_data.total_lessons,
            'total_study_time': course_data.total_study_time,
            'last_accessed': course_data.last_accessed.isoformat() if course_data.last_accessed else None,
            'completed_certificates': course_data.completed_certificates,
            'total_certificates': course_data.total_certificates,
        })
    
    # Get completed courses
    completed_courses = UserCoursePersonalization.objects.filter(
        user=user,
        status='completed'
    ).order_by('-last_accessed')
    
    completed_courses_data = []
    for course_data in completed_courses:
        completed_courses_data.append({
            'course_id': str(course_data.course_id),
            'completion_percentage': course_data.completion_percentage,
            'completed_lessons': course_data.completed_lessons,
            'total_lessons': course_data.total_lessons,
            'total_study_time': course_data.total_study_time,
            'last_accessed': course_data.last_accessed.isoformat() if course_data.last_accessed else None,
            'completed_certificates': course_data.completed_certificates,
            'total_certificates': course_data.total_certificates,
        })
    
    # Calculate total study time
    total_study_time = UserCoursePersonalization.objects.filter(
        user=user
    ).aggregate(total=Sum('total_study_time'))['total'] or 0
    
    return Response({
        'yearly_stats': yearly_stats_data,
        'current_courses': current_courses_data,
        'completed_courses': completed_courses_data,
        'total_study_time': total_study_time,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_details(request, course_id):
    """
    Get detailed personalization data for a specific course.
    
    Args:
        course_id: Course ID string
        
    Returns:
        JSON response with course personalization details and lesson tracking
    """
    user = request.user
    
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return Response(
            {'error': 'Invalid course ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get course personalization data
    try:
        course_data = UserCoursePersonalization.objects.get(
            user=user,
            course_id=course_key
        )
    except UserCoursePersonalization.DoesNotExist:
        return Response(
            {'error': 'Course data not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get lesson tracking for this course
    lessons = LessonTimeTracking.objects.filter(
        user=user,
        course_id=course_key
    ).order_by('-modified')
    
    lessons_data = []
    for lesson in lessons:
        lessons_data.append({
            'lesson_id': lesson.lesson_id,
            'lesson_name': lesson.lesson_name,
            'time_spent_minutes': lesson.time_spent_minutes,
            'is_completed': lesson.is_completed,
            'completed_at': lesson.completed_at.isoformat() if lesson.completed_at else None,
            'last_modified': lesson.modified.isoformat(),
        })
    
    return Response({
        'course_id': str(course_data.course_id),
        'status': course_data.status,
        'completion_percentage': course_data.completion_percentage,
        'completed_lessons': course_data.completed_lessons,
        'total_lessons': course_data.total_lessons,
        'total_study_time': course_data.total_study_time,
        'last_accessed': course_data.last_accessed.isoformat() if course_data.last_accessed else None,
        'completed_certificates': course_data.completed_certificates,
        'total_certificates': course_data.total_certificates,
        'average_completion_time_per_lesson': course_data.average_completion_time_per_lesson,
        'lessons': lessons_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_lesson_progress(request):
    """
    Update progress for a specific lesson.
    
    Expected POST data:
        - course_id: Course ID string
        - lesson_id: Lesson ID string
        - lesson_name: Lesson name (optional)
        - time_spent_minutes: Time spent in minutes
        - is_completed: Boolean indicating completion status
        
    Returns:
        JSON response with updated lesson data
    """
    user = request.user
    course_id = request.data.get('course_id')
    lesson_id = request.data.get('lesson_id')
    lesson_name = request.data.get('lesson_name', '')
    time_spent_minutes = request.data.get('time_spent_minutes', 0)
    is_completed = request.data.get('is_completed', False)
    
    if not course_id or not lesson_id:
        return Response(
            {'error': 'course_id and lesson_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return Response(
            {'error': 'Invalid course ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create lesson tracking
    lesson_tracking, created = LessonTimeTracking.objects.get_or_create(
        user=user,
        course_id=course_key,
        lesson_id=lesson_id,
        defaults={
            'lesson_name': lesson_name,
            'time_spent_minutes': time_spent_minutes,
            'is_completed': is_completed,
        }
    )
    
    if not created:
        # Update existing record
        lesson_tracking.time_spent_minutes += float(time_spent_minutes)
        if is_completed and not lesson_tracking.is_completed:
            lesson_tracking.is_completed = True
            lesson_tracking.completed_at = datetime.now()
        if lesson_name and not lesson_tracking.lesson_name:
            lesson_tracking.lesson_name = lesson_name
        lesson_tracking.save()
    
    # Update course personalization stats
    course_personalization, _ = UserCoursePersonalization.objects.get_or_create(
        user=user,
        course_id=course_key,
        defaults={
            'status': 'in_progress',
            'total_lessons': 1,
        }
    )
    
    # Recalculate course stats
    total_lessons = LessonTimeTracking.objects.filter(
        user=user,
        course_id=course_key
    ).count()
    
    completed_lessons = LessonTimeTracking.objects.filter(
        user=user,
        course_id=course_key,
        is_completed=True
    ).count()
    
    total_time = LessonTimeTracking.objects.filter(
        user=user,
        course_id=course_key
    ).aggregate(total=Sum('time_spent_minutes'))['total'] or 0
    
    course_personalization.total_lessons = total_lessons
    course_personalization.completed_lessons = completed_lessons
    course_personalization.completion_percentage = (
        (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    )
    course_personalization.total_study_time = total_time / 60.0  # Convert to hours
    course_personalization.last_accessed = datetime.now()
    
    if completed_lessons == total_lessons and total_lessons > 0:
        course_personalization.status = 'completed'
    elif completed_lessons > 0:
        course_personalization.status = 'in_progress'
    
    course_personalization.save()
    
    return Response({
        'lesson_id': lesson_tracking.lesson_id,
        'lesson_name': lesson_tracking.lesson_name,
        'time_spent_minutes': lesson_tracking.time_spent_minutes,
        'is_completed': lesson_tracking.is_completed,
        'completed_at': lesson_tracking.completed_at.isoformat() if lesson_tracking.completed_at else None,
        'course_stats': {
            'completion_percentage': course_personalization.completion_percentage,
            'completed_lessons': course_personalization.completed_lessons,
            'total_lessons': course_personalization.total_lessons,
            'status': course_personalization.status,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_yearly_stats_list(request):
    """
    Get list of yearly statistics for the authenticated user.
    
    Returns:
        JSON response with list of yearly stats
    """
    user = request.user
    
    yearly_stats = PersonalizationYearlyStats.objects.filter(
        user=user
    ).order_by('-year')
    
    stats_data = []
    for stats in yearly_stats:
        stats_data.append({
            'year': stats.year,
            'total_courses_assigned': stats.total_courses_assigned,
            'total_courses_completed': stats.total_courses_completed,
            'total_certificates_earned': stats.total_certificates_earned,
            'total_study_time_hours': stats.total_study_time_hours,
            'total_lessons_completed': stats.total_lessons_completed,
            'overall_completion_rate': stats.overall_completion_rate,
            'average_time_per_course': stats.average_time_per_course,
        })
    
    return Response({'yearly_stats': stats_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_yearly_stats(request):
    """
    Refresh/recalculate yearly statistics for the authenticated user.
    
    Expected POST data:
        - year: Year to refresh (defaults to current year)
        
    Returns:
        JSON response with updated yearly stats
    """
    user = request.user
    year = request.data.get('year', datetime.now().year)
    
    try:
        year = int(year)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid year'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create yearly stats
    yearly_stats, created = PersonalizationYearlyStats.objects.get_or_create(
        user=user,
        year=year
    )
    
    # Calculate stats for the year
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)
    
    # Count courses
    courses_in_year = UserCoursePersonalization.objects.filter(
        user=user,
        last_accessed__range=(year_start, year_end)
    )
    
    total_assigned = courses_in_year.count()
    total_completed = courses_in_year.filter(status='completed').count()
    total_study_time = courses_in_year.aggregate(
        total=Sum('total_study_time')
    )['total'] or 0
    
    # Count lessons
    lessons_in_year = LessonTimeTracking.objects.filter(
        user=user,
        modified__range=(year_start, year_end)
    )
    
    total_lessons_completed = lessons_in_year.filter(is_completed=True).count()
    
    # Calculate averages
    overall_completion_rate = (
        (total_completed / total_assigned * 100) if total_assigned > 0 else 0
    )
    average_time_per_course = (
        total_study_time / total_assigned if total_assigned > 0 else 0
    )
    
    # Update yearly stats
    yearly_stats.total_courses_assigned = total_assigned
    yearly_stats.total_courses_completed = total_completed
    yearly_stats.total_study_time_hours = total_study_time
    yearly_stats.total_lessons_completed = total_lessons_completed
    yearly_stats.overall_completion_rate = overall_completion_rate
    yearly_stats.average_time_per_course = average_time_per_course
    yearly_stats.save()
    
    return Response({
        'year': yearly_stats.year,
        'total_courses_assigned': yearly_stats.total_courses_assigned,
        'total_courses_completed': yearly_stats.total_courses_completed,
        'total_certificates_earned': yearly_stats.total_certificates_earned,
        'total_study_time_hours': yearly_stats.total_study_time_hours,
        'total_lessons_completed': yearly_stats.total_lessons_completed,
        'overall_completion_rate': yearly_stats.overall_completion_rate,
        'average_time_per_course': yearly_stats.average_time_per_course,
    }, status=status.HTTP_200_OK)
