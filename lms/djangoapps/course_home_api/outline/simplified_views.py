"""
Simplified Outline Tab Views for the new course structure.

This implements a simplified course structure:
- Course → Modules → Units → Content (video/slide/questions only)

Removes the section/chapter layer and restricts content to 3 types only.
"""
from datetime import datetime, timezone
from functools import cached_property

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_home_api.utils import get_course_or_403
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.masquerade import is_masquerading, setup_masquerade
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_404
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum

from .simplified_serializers import SimplifiedOutlineTabSerializer


class SimplifiedOutlineTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Simplified Outline Tab

    **Example Requests**

        GET api/course_home/v1/simplified_outline/{course_key}

    **Response Values**

        Body consists of the following structure:

        course_info:
            title: (str) The course title
            instructor_name: (str) The instructor name
            total_modules: (int) Total number of modules in the course
            completed_modules: (int) Number of completed modules
            progress_percentage: (float) Completion percentage
        modules: List of module objects with:
            id: (str) The module ID
            title: (str) The module title
            units_count: (int) Number of units in this module
            complete: (bool) Whether the module is completed
            units: List of unit objects with:
                id: (str) The unit ID
                title: (str) The unit title
                content_type: (str) One of: 'video', 'slide', 'questions'
                content_metadata: (dict) Additional metadata based on content type
                complete: (bool) Whether the unit is completed

    **Returns**

        * 200 on success.
        * 403 if the user does not currently have access to the course.
        * 404 if the course is not available.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    serializer_class = SimplifiedOutlineTabSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)

        course = get_course_or_403(request.user, 'load', course_key, check_if_enrolled=False)

        masquerade_object, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )

        course_overview = get_course_overview_or_404(course_key)
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)

        is_enrolled = enrollment and enrollment.is_active
        is_staff = bool(has_access(request.user, 'staff', course_key))
        show_enrolled = is_enrolled or is_staff

        if not show_enrolled:
            return Response({'error': 'Access denied'}, status=403)

        # Get simplified course structure
        course_data = self._get_simplified_course_structure(course, request.user)

        context = self.get_serializer_context()
        context['course_overview'] = course_overview
        context['enrollment'] = enrollment
        serializer = self.get_serializer_class()(course_data, context=context)

        return Response(serializer.data)

    def _get_simplified_course_structure(self, course, user):
        """
        Get the simplified course structure: course -> units only.
        """
        modulestore_instance = modulestore()

        # Get all units directly from the course (verticals)
        units = []
        total_units = 0
        completed_units = 0

        # Get course children from modulestore
        course_children = modulestore_instance.get_children(course.location, depth=None)

        # Check if this course uses simplified structure (units directly under course)
        direct_units = [child for child in course_children if child.category == 'vertical']

        if direct_units:
            # Simplified structure: units are direct children of course
            for unit_block in direct_units:
                total_units += 1
                unit_data = self._process_unit(unit_block, user, modulestore_instance)

                if unit_data['complete']:
                    completed_units += 1

                units.append(unit_data)
        else:
            # Traditional structure: find units in chapters/sections
            for module_block in course_children:
                if module_block.category != 'chapter':
                    continue

                # Get module children (units, formerly sequentials)
                module_children = modulestore_instance.get_children(module_block.location, depth=None)

                for section_block in module_children:
                    if section_block.category != 'sequential':
                        continue

                    # Get section children (actual units/verticals)
                    section_children = modulestore_instance.get_children(section_block.location, depth=None)

                    for unit_block in section_children:
                        if unit_block.category != 'vertical':
                            continue

                        total_units += 1
                        unit_data = self._process_unit(unit_block, user, modulestore_instance)

                        if unit_data['complete']:
                            completed_units += 1

                        units.append(unit_data)

        # Calculate progress
        progress_percentage = (completed_units / total_units * 100) if total_units > 0 else 0

        # Get instructor name from course metadata
        instructor_name = self._get_instructor_name(course)

        return {
            'course_info': {
                'title': course.display_name,
                'instructor_name': instructor_name,
                'total_units': total_units,
                'completed_units': completed_units,
                'progress_percentage': progress_percentage,
            },
            'units': units,
        }

    def _process_unit(self, unit_block, user, modulestore_instance):
        """
        Process a single unit and determine its content type and metadata.
        """
        # Get unit children (content blocks)
        unit_children = modulestore_instance.get_children(unit_block.location, depth=None)

        # Determine primary content type and collect metadata
        content_type, content_metadata = self._analyze_unit_content(unit_children)

        # Check completion status
        unit_complete = self._check_unit_completion(unit_block, user)

        return {
            'id': str(unit_block.location),
            'title': unit_block.display_name,
            'content_type': content_type,
            'content_metadata': content_metadata,
            'complete': unit_complete,
        }

    def _analyze_unit_content(self, unit_children):
        """
        Analyze unit content and determine the primary content type.
        Returns content type and relevant metadata.
        """
        video_count = 0
        slide_count = 0
        question_count = 0

        for child in unit_children:
            if child.category == 'video':
                video_count += 1
            elif child.category in ['html', 'library_content'] and self._is_slide_content(child):
                slide_count += 1
            elif child.category in ['problem', 'openassessment']:
                question_count += 1

        # Determine primary content type based on what's most prominent
        if video_count > 0:
            return 'video', {
                'video_count': video_count,
                'duration_estimate': self._estimate_video_duration(unit_children),
                'subtitle': f'{video_count} video{"s" if video_count > 1 else ""}',
            }
        elif question_count > 0:
            return 'questions', {
                'question_count': question_count,
                'subtitle': f'{question_count} question{"s" if question_count > 1 else ""}',
            }
        elif slide_count > 0:
            return 'slide', {
                'slide_count': slide_count,
                'subtitle': f'{slide_count} slide{"s" if slide_count > 1 else ""}',
            }
        else:
            # Default to video type if unclear
            return 'video', {
                'subtitle': 'Learning content',
            }

    def _is_slide_content(self, block):
        """
        Determine if an HTML or library content block contains slide material.
        This is a heuristic based on content analysis.
        """
        if hasattr(block, 'data') and block.data:
            content = str(block.data).lower()
            # Look for indicators that this might be slide content
            slide_indicators = ['slide', 'presentation', '.ppt', '.pdf', 'powerpoint']
            return any(indicator in content for indicator in slide_indicators)
        return False

    def _estimate_video_duration(self, unit_children):
        """
        Estimate total video duration in minutes.
        """
        total_duration = 0
        for child in unit_children:
            if child.category == 'video' and hasattr(child, 'youtube_id_1_0'):
                # This is a simplified estimation - in practice you'd want to
                # fetch actual video duration from the video API
                total_duration += 10  # Default 10 minutes per video
        return f"{total_duration} min" if total_duration > 0 else "Video content"

    def _check_unit_completion(self, unit_block, user):
        """
        Check if a unit is completed by the user.
        """
        try:
            from completion.models import BlockCompletion
            completion = BlockCompletion.objects.get(
                user=user,
                block_key=unit_block.location
            )
            return completion.completion == 1.0
        except BlockCompletion.DoesNotExist:
            return False

    def _get_instructor_name(self, course):
        """
        Extract instructor name from course metadata.
        """
        # Try to get instructor info from course metadata
        if hasattr(course, 'instructor_info') and course.instructor_info:
            # Parse instructor info - this might be HTML or structured data
            instructor_info = course.instructor_info
            if isinstance(instructor_info, dict) and 'instructors' in instructor_info:
                instructors = instructor_info['instructors']
                if instructors and len(instructors) > 0:
                    return instructors[0].get('name', 'Course Instructor')

        # Fallback to a default
        return 'Course Instructor'
