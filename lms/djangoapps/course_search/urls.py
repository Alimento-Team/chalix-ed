"""
Course search URL configuration
"""
from django.urls import path
from .views import CourseSearchView, CourseSearchAPIView

urlpatterns = [
    path('search/', CourseSearchView.as_view(), name='course_search_results'),
    path('api/search/', CourseSearchAPIView.as_view(), name='course_search_api'),
]
