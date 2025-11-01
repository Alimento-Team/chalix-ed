"""
Views for personalization pages.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse

from .models import UserCoursePersonalization, PersonalizationYearlyStats


@login_required
def personalization_dashboard(request):
    """
    Main personalization dashboard view.
    Displays the user's learning statistics and course progress.
    """
    user = request.user
    current_year = timezone.now().year
    
    # Get or create yearly stats
    yearly_stats, created = PersonalizationYearlyStats.objects.get_or_create(
        user=user,
        year=current_year
    )
    
    # Get course personalizations
    active_courses = UserCoursePersonalization.objects.filter(
        user=user,
        status__in=['in_progress', 'not_started']
    ).order_by('-last_accessed')
    
    completed_courses = UserCoursePersonalization.objects.filter(
        user=user,
        status='completed'
    ).order_by('-modified')
    
    context = {
        'year': current_year,
        'yearly_stats': yearly_stats,
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'user': user,
    }
    
    return render(request, 'personalization/dashboard.html', context)


@login_required
def personalization_year_stats(request, year):
    """
    Get personalization stats for a specific year.
    Returns JSON response.
    """
    user = request.user
    
    try:
        stats = PersonalizationYearlyStats.objects.get(
            user=user,
            year=year
        )
        
        data = {
            'year': stats.year,
            'total_courses_assigned': stats.total_courses_assigned,
            'total_courses_completed': stats.total_courses_completed,
            'total_study_time_hours': stats.total_study_time_hours,
            'average_time_per_course': stats.average_time_per_course,
            'total_lessons_completed': stats.total_lessons_completed,
            'total_certificates_earned': stats.total_certificates_earned,
            'overall_completion_rate': stats.overall_completion_rate,
        }
        
        return JsonResponse(data)
    
    except PersonalizationYearlyStats.DoesNotExist:
        return JsonResponse(
            {'error': 'Stats not found for this year'},
            status=404
        )
