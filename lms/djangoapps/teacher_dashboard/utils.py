"""
Utility functions for Teacher Dashboard.
"""

from django.contrib.auth.models import User
from typing import List

from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    UserBasedRole,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_instructor_courses(user: User) -> List[CourseOverview]:
    """
    Get all courses where the user has instructor or staff role.
    
    Args:
        user: The user to get courses for
        
    Returns:
        List of CourseOverview objects where user has teaching permissions
    """
    # Get courses where user is instructor
    instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
    
    # Get courses where user is staff
    staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
    
    # Combine and deduplicate
    all_course_accesses = instructor_courses | staff_courses
    
    # Extract course keys
    course_keys = []
    user_global_orgs = set()
    
    for course_access in all_course_accesses:
        if course_access.course_id is not None:
            course_keys.append(course_access.course_id)
        elif course_access.org:
            user_global_orgs.add(course_access.org)
    
    # Get courses from global orgs if any
    if user_global_orgs:
        org_overviews = CourseOverview.get_all_courses(orgs=list(user_global_orgs))
        course_keys.extend([overview.id for overview in org_overviews])
    
    # Remove duplicates
    course_keys = list(set(course_keys))
    
    if course_keys:
        # Get CourseOverview objects
        courses = CourseOverview.get_all_courses(filter_={'id__in': course_keys})
        # Filter out courses that are None or have issues
        courses = [course for course in courses if course is not None]
        return courses
    
    return []


def format_course_schedule(course_data: dict) -> str:
    """
    Format the course schedule information for display.
    
    Args:
        course_data: Dictionary with course information
        
    Returns:
        Formatted schedule string
    """
    if course_data.get('start') and course_data.get('end'):
        start_date = course_data['start'].strftime('%d/%m/%Y') if course_data['start'] else ''
        end_date = course_data['end'].strftime('%d/%m/%Y') if course_data['end'] else ''
        return f"Thời gian: {start_date} - {end_date}"
    elif course_data.get('start'):
        start_date = course_data['start'].strftime('%d/%m/%Y')
        return f"Bắt đầu: {start_date}"
    elif course_data.get('enrollment_start'):
        enroll_start = course_data['enrollment_start'].strftime('%d/%m/%Y')
        return f"Đăng ký từ: {enroll_start}"
    else:
        return "Thời gian: Chưa xác định"
