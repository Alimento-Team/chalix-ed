"""
URL patterns for Chalix User Menu API endpoints
"""
from django.urls import path

from .views import (
    get_user_courses,
    user_personalization,
    user_requests,
    learning_results,
    learning_plans,
    teaching_registration,
    help_resources,
    user_logout,
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    get_unread_count,
    create_notification,
    notification_preferences,
    course_detail_api,
    professional_fields_proxy,
)

app_name = 'chalix_user_menu'

urlpatterns = [
    # Course management
    path('courses/', get_user_courses, name='user_courses'),

    # Course detail (new endpoint for learning MFE)
    # Use the 'path' converter so slashes in the course key are captured correctly
    path('course-detail/<path:course_key_string>/', course_detail_api, name='chalix_course_detail'),

    # User profile and personalization
    path('personalization/', user_personalization, name='user_personalization'),

    # User requests
    path('requests/', user_requests, name='user_requests'),

    # Learning progress and results
    path('learning-results/', learning_results, name='learning_results'),

    # Personal learning plans
    path('learning-plans/', learning_plans, name='learning_plans'),

    # Teaching registration
    path('teaching/', teaching_registration, name='teaching_registration'),

    # Help resources
    path('help/', help_resources, name='help_resources'),

    # Notifications
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/unread-count/', get_unread_count, name='get_unread_count'),
    path('notifications/create/', create_notification, name='create_notification'),
    path('notifications/preferences/', notification_preferences, name='notification_preferences'),

    # Professional fields proxy (to avoid CORS issues)
    path('professional-fields/', professional_fields_proxy, name='professional_fields_proxy'),

    # Logout
    path('logout/', user_logout, name='user_logout'),
]
