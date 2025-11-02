"""
URL configuration for learning analytics API.
"""
from django.urls import path
from .views import (
    LearnerStatsAPIView,
    CourseProgressAPIView,
    RecommendationsAPIView,
    LearningHoursAPIView,
    LearningHoursApprovalAPIView,
    CourseCreditHoursAPIView,
    StudentProgressUpdateAPIView,
    LearningAnalyticsDashboardAPIView,
    LearningHoursCoursesAPIView,
)

app_name = 'learning_analytics'

urlpatterns = [
    # Learner statistics and progress
    path('stats/', LearnerStatsAPIView.as_view(), name='learner_stats'),
    path('course-progress/', CourseProgressAPIView.as_view(), name='course_progress'),
    path('recommendations/', RecommendationsAPIView.as_view(), name='recommendations'),

    # Learning hours management
    path('learning-hours/', LearningHoursAPIView.as_view(), name='learning_hours'),
    path('learning-hours-approval/', LearningHoursApprovalAPIView.as_view(), name='learning_hours_approval'),

    # Course credit hours management (for teachers/admins)
    path('course-credit-hours/', CourseCreditHoursAPIView.as_view(), name='course_credit_hours'),

    # Student progress updates (internal use)
    path('student-progress/', StudentProgressUpdateAPIView.as_view(), name='student_progress_update'),

    # Comprehensive dashboard
    path('dashboard/', LearningAnalyticsDashboardAPIView.as_view(), name='learning_analytics_dashboard'),
    
    # Learning hours courses list
    path('courses/', LearningHoursCoursesAPIView.as_view(), name='learning_hours_courses'),
]
