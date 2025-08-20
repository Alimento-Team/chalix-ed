"""
Views for Teacher Dashboard.
"""

import logging
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
)
from lms.djangoapps.courseware.access import has_access
from openedx.core.lib.courses import get_courses
from xmodule.modulestore.django import modulestore

from .utils import get_instructor_courses

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@login_required
def teacher_dashboard_view(request):
    """
    Display the teacher dashboard showing all courses the user is teaching.
    """
    user = request.user

    # Check if user has any instructor or staff roles
    if not (CourseInstructorRole.user_has_role(user) or CourseStaffRole.user_has_role(user)):
        raise Http404("You don't have permission to access the teacher dashboard.")

    # Get all courses where the user is an instructor or staff member
    instructor_courses = get_instructor_courses(user)

    # Prepare course data for template
    courses_data = []
    for course_overview in instructor_courses:
        try:
            course = modulestore().get_course(course_overview.id)
            if course:
                # Check user's role in this specific course
                is_instructor = has_access(user, 'instructor', course)
                is_staff = has_access(user, 'staff', course)

                if is_instructor or is_staff:
                    course_data = {
                        'id': str(course_overview.id),
                        'display_name': course_overview.display_name,
                        'short_description': getattr(course_overview, 'short_description', ''),
                        'start': course_overview.start,
                        'end': course_overview.end,
                        'enrollment_start': course_overview.enrollment_start,
                        'enrollment_end': course_overview.enrollment_end,
                        'course_image_url': course_overview.course_image_url,
                        'org': course_overview.org,
                        'course_number': course_overview.number,
                        'role': 'instructor' if is_instructor else 'staff',
                        'has_started': course_overview.has_started(),
                        'has_ended': course_overview.has_ended(),
                    }
                    courses_data.append(course_data)
        except Exception as e:
            log.warning(f"Could not load course {course_overview.id}: {e}")
            continue

    # Sort courses by start date (most recent first)
    courses_data.sort(key=lambda x: x['start'] or x['enrollment_start'], reverse=True)

    context = {
        'user': user,
        'courses': courses_data,
        'courses_count': len(courses_data),
    }

    return render_to_response('teacher_dashboard/teacher_dashboard.html', context)
