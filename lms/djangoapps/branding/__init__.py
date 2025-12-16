"""
EdX Branding package.

Provides a way to retrieve "branded" parts of the site.

This module provides functions to retrieve basic branded parts
such as the site visible courses, university name and logo.
"""


from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_visible_courses(org=None, filter_=None, active_only=False, course_keys=None, user=None):
    """
    Yield the CourseOverviews that should be visible in this branded
    instance.

    Arguments:
        org (string): Optional parameter that allows case-insensitive
            filtering by organization.
        filter_ (dict): Optional parameter that allows custom filtering by
            fields on the course.
        active_only (bool): Optional parameter that enables fetching active courses only.
        course_keys (list[str]): Optional parameter that allows for selecting which
            courses to fetch the `CourseOverviews` for
        user: Optional Django User object for org-based filtering
    """
    # Import is placed here to avoid model import at project startup.
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

    current_site_orgs = configuration_helpers.get_current_site_orgs()

    courses = CourseOverview.objects.none()

    if org:
        # Check the current site's orgs to make sure the org's courses should be displayed
        if not current_site_orgs or org in current_site_orgs:
            courses = CourseOverview.get_all_courses(
                orgs=[org], filter_=filter_, active_only=active_only, course_keys=course_keys
            )
    elif current_site_orgs:
        # Only display courses that should be displayed on this site
        courses = CourseOverview.get_all_courses(
            orgs=current_site_orgs, filter_=filter_, active_only=active_only, course_keys=course_keys
        )
    else:
        courses = CourseOverview.get_all_courses(filter_=filter_, active_only=active_only, course_keys=course_keys)

    courses = courses.order_by('id')

    # Apply Chalix-specific visibility filtering based on ChalixCourseMetadata
    if user and user.is_authenticated:
        try:
            # Use Django's app registry to get models - works in both CMS and LMS contexts
            from django.apps import apps
            
            # Check if contentstore app is loaded (it should be in both CMS and LMS)
            if not apps.is_installed('cms.djangoapps.contentstore'):
                # Skip Chalix filtering if contentstore app not available
                pass
            else:
                ChalixCourseMetadata = apps.get_model('contentstore', 'ChalixCourseMetadata')
                ChalixUserRole = apps.get_model('contentstore', 'ChalixUserRole')
                
                # Get user's primary role
                user_role = ChalixUserRole.objects.filter(
                    user=user,
                    is_active=True
                ).select_related('organization').first()
                
                if user_role:
                    # Get user's highest priority role (simplified version)
                    role_priority = {'cong_chuc': 0, 'giang_vien': 1, 'co_quan': 2, 'bo': 3}
                    user_roles = ChalixUserRole.objects.filter(
                        user=user,
                        is_active=True
                    ).select_related('organization')
                    user_role = max(user_roles, key=lambda r: role_priority.get(r.role, 0), default=None)
                
                user_org = user_role.organization if user_role else None
                
                # Get all course metadata
                course_metadata = {
                    meta.course_id: meta 
                    for meta in ChalixCourseMetadata.objects.select_related('creator_organization').all()
                }
                
                # Filter courses based on Chalix visibility rules
                visible_course_ids = []
                for course in courses:
                    course_id = course.id
                    metadata = course_metadata.get(course_id)
                    
                    if not metadata:
                        # No metadata: show course to all users (backwards compatibility)
                        # This ensures courses created before metadata system still appear
                        visible_course_ids.append(course_id)
                        logger.debug(f"Course {course_id} has no metadata, showing to all users")
                        continue
                    
                    # Rule 1: Public courses (is_public=True, typically bo role courses) are visible to everyone
                    if metadata.is_public:
                        visible_course_ids.append(course_id)
                        logger.debug(f"Course {course_id} is public, showing to all users")
                        continue
                    
                    # Rule 2: Private courses (is_public=False) are only visible to users from the same organization
                    if user_org and metadata.creator_organization:
                        if user_org.pk == metadata.creator_organization.pk:
                            visible_course_ids.append(course_id)
                            logger.debug(f"Course {course_id} is private, showing to org {user_org.name} members")
                            continue
                    
                    # If no rules matched, course is not visible to this user
                    logger.debug(f"Course {course_id} not visible to user {user.username}")
                
                # Filter the courses queryset to only include visible courses
                courses = courses.filter(id__in=visible_course_ids)
            
        except Exception as e:
            # If there's an error with Chalix filtering, log it and show all courses
            # (fail open rather than fail closed)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error applying Chalix course visibility filtering: {e}")
    
    # Filtering can stop here for org-filtered courses
    if current_site_orgs:
        return courses

    # See if we have filtered course listings in this domain
    filtered_visible_ids = None

    # this is legacy format, which also handle dev case, which should not filter
    subdomain = configuration_helpers.get_value('subdomain', 'default')
    if hasattr(settings, 'COURSE_LISTINGS') and subdomain in settings.COURSE_LISTINGS and not settings.DEBUG:
        filtered_visible_ids = frozenset(
            [CourseKey.from_string(c) for c in settings.COURSE_LISTINGS[subdomain]]
        )

    if filtered_visible_ids:
        return courses.filter(id__in=filtered_visible_ids)
    else:
        # Filter out any courses based on current org, to avoid leaking these.
        orgs = configuration_helpers.get_all_orgs()
        return courses.exclude(org__in=orgs)


def get_university_for_request():
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    return configuration_helpers.get_value('university')
