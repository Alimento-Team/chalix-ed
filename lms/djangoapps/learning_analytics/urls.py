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
    MaterialOpenEventAPIView,
    LearningAnalyticsDashboardAPIView,
    LearningHoursCoursesAPIView,
    StudentLearningProcessSelfAPIView,
    StudentLearningProcessListAPIView,
    StudentLearningProcessAggregateAPIView,
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
    path('material-open/', MaterialOpenEventAPIView.as_view(), name='material_open_event'),

    # Comprehensive dashboard
    path('dashboard/', LearningAnalyticsDashboardAPIView.as_view(), name='learning_analytics_dashboard'),
    
    # Learning hours courses list
    path('courses/', LearningHoursCoursesAPIView.as_view(), name='learning_hours_courses'),

    # Student learning-process snapshots
    path('student-learning-process/me/', StudentLearningProcessSelfAPIView.as_view(), name='student_learning_process_me'),
    path('student-learning-process/', StudentLearningProcessListAPIView.as_view(), name='student_learning_process_list'),
    path('student-learning-process/aggregate/', StudentLearningProcessAggregateAPIView.as_view(), name='student_learning_process_aggregate'),
]
