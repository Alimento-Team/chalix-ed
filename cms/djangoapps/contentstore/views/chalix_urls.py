"""
URL patterns for Chalix unit types and dashboard.
"""

from django.urls import path, re_path
from . import chalix_unit_types, chalix_dashboard, chalix_quiz

app_name = 'chalix'

urlpatterns = [
    # Chalix CMS Dashboard
    path(
        'dashboard/',
        chalix_dashboard.cms_dashboard,
        name='chalix_dashboard'
    ),
    
    # Dashboard API endpoints
    path(
        'dashboard/api/',
        chalix_dashboard.dashboard_api,
        name='chalix_dashboard_api'
    ),
    
    # Create single account endpoint
    path(
        'dashboard/create-single-account/',
        chalix_dashboard.create_single_account_api,
        name='chalix_create_single_account'
    ),

    # Create a local course via dashboard
    path(
        'dashboard/create-course/',
        chalix_dashboard.create_course_api,
        name='chalix_create_course'
    ),
    path(
        'dashboard/list-courses/',
        chalix_dashboard.list_local_courses_api,
        name='chalix_list_local_courses'
    ),

    # Create and list programs via dashboard
    path(
        'dashboard/create-program/',
        chalix_dashboard.create_program_api,
        name='chalix_create_program'
    ),
    path(
        'dashboard/update-program/',
        chalix_dashboard.update_program_api,
        name='chalix_update_program'
    ),
    path(
        'dashboard/list-programs/',
        chalix_dashboard.list_local_programs_api,
        name='chalix_list_local_programs'
    ),

    # Course and program detail endpoints
    re_path(
        r'^dashboard/course-detail/(?P<course_key_string>.+)/$',
        chalix_dashboard.course_detail_api,
        name='chalix_course_detail'
    ),
    path(
        'dashboard/program-detail/<int:cid>/',
        chalix_dashboard.program_detail_api,
        name='chalix_program_detail'
    ),

    # Update course endpoint
    path(
        'dashboard/update-course/',
        chalix_dashboard.update_course_api,
        name='chalix_update_course'
    ),
    # Delete course endpoint
    path(
        'dashboard/delete-course/',
        chalix_dashboard.delete_course_api,
        name='chalix_delete_course'
    ),
    # Delete program endpoint
    path(
        'dashboard/delete-program/',
        chalix_dashboard.delete_program_api,
        name='chalix_delete_program'
    ),

    # Get available content types
    path(
        'content-types/<str:course_id>',
        chalix_unit_types.get_chalix_content_types,
        name='chalix_content_types'
    ),

    # Create unit type (simplified endpoint)
    path(
        'unit_types/',
        chalix_unit_types.create_unit_type,
        name='chalix_unit_types'
    ),

    # Create new unit with content type
    path(
        'units/create/<str:course_id>',
        chalix_unit_types.create_chalix_unit,
        name='chalix_create_unit'
    ),

    # Update unit content
    re_path(
        r'^units/update/(?P<course_id>[^/]+)/(?P<unit_locator>.+)$',
        chalix_unit_types.update_chalix_unit_content,
        name='chalix_update_unit'
    ),

    # Update online class configuration
    re_path(
        r'^online-class/update/(?P<course_id>.+)$',
        chalix_unit_types.update_online_class_config,
        name='chalix_update_online_class'
    ),

    # Quiz management endpoints
    path(
        'quiz/create/',
        chalix_quiz.create_quiz_api,
        name='chalix_create_quiz'
    ),
    path(
        'quiz/<int:quiz_id>/',
        chalix_quiz.get_quiz_api,
        name='chalix_get_quiz'
    ),
    path(
        'quiz/list/<str:course_key_string>/',
        chalix_quiz.list_quizzes_api,
        name='chalix_list_quizzes'
    ),
    path(
        'quiz/update/<int:quiz_id>/',
        chalix_quiz.update_quiz_api,
        name='chalix_update_quiz'
    ),
    path(
        'quiz/delete/<int:quiz_id>/',
        chalix_quiz.delete_quiz_api,
        name='chalix_delete_quiz'
    ),
]
