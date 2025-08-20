"""
Course search views for Chalix platform
"""
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.urls import reverse

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.courseware.courses import get_course_overview_with_access
from common.djangoapps.student.models import CourseEnrollment

log = logging.getLogger(__name__)


class CourseSearchView(View):
    """
    View for searching courses by title and content
    """

    def get(self, request):
        """
        Handle course search requests
        """
        query = request.GET.get('q', '').strip()
        page = request.GET.get('page', 1)

        context = {
            'query': query,
            'courses': [],
            'page_obj': None,
            'is_paginated': False,
            'paginator': None,
        }

        if query:
            # Search in course titles and descriptions
            courses = self._search_courses(query, request.user)

            # Paginate results
            paginator = Paginator(courses, 20)  # Show 20 courses per page

            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            context.update({
                'courses': page_obj.object_list,
                'page_obj': page_obj,
                'is_paginated': page_obj.has_other_pages(),
                'paginator': paginator,
            })

        return render(request, 'course_search/search_results.html', context)

    def _search_courses(self, query, user):
        """
        Search for courses matching the query in title, description, and content
        """
        # Basic search in course overviews
        course_overviews = CourseOverview.objects.filter(
            Q(display_name__icontains=query) |
            Q(short_description__icontains=query) |
            Q(overview__icontains=query)
        ).filter(
            catalog_visibility='both'  # Only show publicly visible courses
        ).order_by('-modified')

        # Convert to list and add enrollment status
        courses = []
        for overview in course_overviews:
            try:
                # Check if user has access to the course
                course = get_course_overview_with_access(user, 'load', overview.id)
                if course:
                    course_data = {
                        'overview': overview,
                        'is_enrolled': False,
                        'enrollment_url': reverse('course_modes_choose', args=[overview.id]),
                        'course_url': reverse('course_root', args=[overview.id]),
                    }

                    # Check enrollment status for authenticated users
                    if user.is_authenticated:
                        enrollment = CourseEnrollment.objects.filter(
                            user=user,
                            course_id=overview.id,
                            is_active=True
                        ).first()
                        course_data['is_enrolled'] = enrollment is not None

                    courses.append(course_data)
            except Exception as e:
                log.warning(f"Error accessing course {overview.id}: {e}")
                continue

        return courses


class CourseSearchAPIView(View):
    """
    API endpoint for course search (for AJAX requests)
    """

    def get(self, request):
        """
        Return JSON response with search results
        """
        query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 results

        if not query:
            return JsonResponse({
                'results': [],
                'query': query,
                'count': 0
            })

        search_view = CourseSearchView()
        courses = search_view._search_courses(query, request.user)[:limit]

        results = []
        for course_data in courses:
            overview = course_data['overview']
            results.append({
                'id': str(overview.id),
                'display_name': overview.display_name,
                'short_description': overview.short_description or '',
                'course_image_url': overview.course_image_url,
                'course_url': course_data['course_url'],
                'enrollment_url': course_data['enrollment_url'],
                'is_enrolled': course_data['is_enrolled'],
                'org': overview.org,
                'course_number': overview.number,
            })

        return JsonResponse({
            'results': results,
            'query': query,
            'count': len(results)
        })
