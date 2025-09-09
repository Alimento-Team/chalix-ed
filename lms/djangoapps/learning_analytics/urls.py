"""
URL configuration for learning analytics API.
"""
from django.urls import path
from .views import (
    LearnerStatsAPIView,
    CourseProgressAPIView,
    RecommendationsAPIView,
    LearningGoalsAPIView,
)

app_name = 'learning_analytics'

urlpatterns = [
    path('stats/', LearnerStatsAPIView.as_view(), name='learner_stats'),
    path('course-progress/', CourseProgressAPIView.as_view(), name='course_progress'),
    path('recommendations/', RecommendationsAPIView.as_view(), name='recommendations'),
    path('goals/', LearningGoalsAPIView.as_view(), name='learning_goals'),
]
