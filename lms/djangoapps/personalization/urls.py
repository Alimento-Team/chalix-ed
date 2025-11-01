"""
URL patterns for personalization app.
"""

from django.urls import path

from .views import personalization_dashboard, personalization_year_stats
from . import api

app_name = 'personalization'

urlpatterns = [
    # Main personalization dashboard page
    path('', personalization_dashboard, name='dashboard'),
    path('year/<int:year>/', personalization_year_stats, name='year_stats'),
    
    # API endpoints
    path('api/stats/', api.get_user_stats, name='api-user-stats'),
    path('api/course/<str:course_id>/', api.get_course_details, name='api-course-details'),
    path('api/lesson/update/', api.update_lesson_progress, name='api-update-lesson'),
    path('api/yearly-stats/', api.get_yearly_stats_list, name='api-yearly-stats-list'),
    path('api/yearly-stats/refresh/', api.refresh_yearly_stats, name='api-refresh-yearly-stats'),
]
