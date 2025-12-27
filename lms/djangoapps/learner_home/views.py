"""
Views for Learner Home
"""

import logging
from collections import OrderedDict

from completion.exceptions import UnavailableCompletionData
from completion.utilities import get_key_to_last_completed_block
from django.conf import settings
from django.db import models
from django.urls import reverse
from edx_django_utils import monitoring as monitoring_utils
from edx_django_utils.monitoring import function_trace
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.edxmako.shortcuts import marketing_link
from common.djangoapps.student.helpers import (
    cert_info,
    user_has_passing_grade_in_course,
)
from common.djangoapps.student.views.dashboard import (
    complete_course_mode_info,
    credit_statuses,
    get_course_enrollments,
    get_filtered_course_entitlements,
    get_org_black_and_whitelist_for_site,
)
from common.djangoapps.util.course import (
    get_encoded_course_sharing_utm_params,
    get_link_for_about_page,
)
from common.djangoapps.util.milestones_helpers import (
    get_pre_requisite_courses_not_completed,
)
from lms.djangoapps.bulk_email.models import Optout
from lms.djangoapps.bulk_email.models_api import is_bulk_email_feature_enabled
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.courseware.access import administrative_accesses_to_course_for_user
from lms.djangoapps.courseware.access_utils import check_course_open_for_learner
from lms.djangoapps.learner_home.serializers import (
    LearnerDashboardSerializer,
)
from lms.djangoapps.learner_home.utils import (
    get_masquerade_user,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.features.course_duration_limits.access import (
    get_user_course_expiration_date,
)
from openedx.features.enterprise_support.api import (
    enterprise_customer_from_session_or_learner_data,
    get_enterprise_learner_data_from_db,
)
from openedx.features.course_experience import course_home_url
from lms.djangoapps.learner_home.utils import course_progress_url

logger = logging.getLogger(__name__)


@function_trace("get_platform_settings")
def get_platform_settings():
    """Get settings used for platform level connections: emails, url routes, etc."""

    return {
        "supportEmail": settings.DEFAULT_FEEDBACK_EMAIL,
        "billingEmail": settings.PAYMENT_SUPPORT_EMAIL,
        "courseSearchUrl": marketing_link("COURSES"),
    }


@function_trace("get_user_account_confirmation_info")
def get_user_account_confirmation_info(user):
    """Determine if a user needs to verify their account and related URL info"""
    send_activation_email_url = (
        configuration_helpers.get_value(
            "SEND_ACTIVATION_EMAIL_URL", settings.SEND_ACTIVATION_EMAIL_URL
        )
        or settings.SUPPORT_SITE_LINK
    )

    email_confirmation = {
        "isNeeded": not user.is_active,
        "sendEmailUrl": send_activation_email_url,
    }

    return email_confirmation


@function_trace("_add_visible_courses_as_pseudo_enrollments")
def _add_visible_courses_as_pseudo_enrollments(existing_enrollments, user):
    """
    Add pseudo-enrollments for courses the user can see but isn't enrolled in.
    This allows the dashboard to show all available courses, not just enrolled ones.
    
    Args:
        existing_enrollments: List of actual CourseEnrollment objects
        user: The user to check visibility for
        
    Returns:
        Combined list of actual enrollments + pseudo-enrollments for visible courses
    """
    try:
        from lms.djangoapps.course_home_api.models import ChalixCourseMetadataLMS
        from common.djangoapps.student.models import CourseEnrollment
        from django.db import connection
        from django.utils import timezone
        
        logger.info(f"[VISIBLE COURSES] Getting visible courses for user {user.username}")
        
        # Get user's organization ID
        user_org_id = None
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT organization_id FROM contentstore_chalixuserrole WHERE user_id = %s AND is_active = TRUE LIMIT 1",
                    [user.id]
                )
                row = cursor.fetchone()
                if row:
                    user_org_id = row[0]
            logger.info(f"[VISIBLE COURSES] User organization_id: {user_org_id}")
        except Exception as e:
            logger.warning(f"[VISIBLE COURSES] Error getting user org: {e}")
        
        # Get IDs of courses user is already enrolled in
        enrolled_course_ids = {str(enrollment.course_id) for enrollment in existing_enrollments}
        logger.info(f"[VISIBLE COURSES] User already enrolled in {len(enrolled_course_ids)} courses")
        
        # Get all courses that user can see but isn't enrolled in
        if user_org_id:
            # Find visible courses: public courses OR courses from same organization
            visible_metadata = ChalixCourseMetadataLMS.objects.filter(
                models.Q(is_public=True) | models.Q(creator_organization_id=user_org_id)
            ).exclude(course_id__in=enrolled_course_ids)
        else:
            # User has no org, only show public courses
            visible_metadata = ChalixCourseMetadataLMS.objects.filter(
                is_public=True
            ).exclude(course_id__in=enrolled_course_ids)
        
        logger.info(f"[VISIBLE COURSES] Found {visible_metadata.count()} visible unenrolled courses")
        
        # Create pseudo-enrollments for visible courses
        pseudo_enrollments = []
        for metadata in visible_metadata:
            try:
                course_key = CourseKey.from_string(metadata.course_id)
                # Check if course exists in CourseOverview
                course_overview = CourseOverview.objects.filter(id=course_key).first()
                if course_overview:
                    # Create a pseudo-enrollment object (not saved to DB)
                    pseudo_enrollment = CourseEnrollment(
                        user=user,
                        course_id=course_key,
                        created=timezone.now(),
                        is_active=False,  # Mark as inactive to distinguish from real enrollments
                        mode='audit'  # Default mode for unenrolled courses
                    )
                    # Add a marker attribute so we can identify pseudo-enrollments
                    pseudo_enrollment.is_pseudo_enrollment = True
                    pseudo_enrollments.append(pseudo_enrollment)
                    logger.debug(f"[VISIBLE COURSES] Added pseudo-enrollment for {metadata.course_id}")
            except Exception as e:
                logger.warning(f"[VISIBLE COURSES] Error creating pseudo-enrollment for {metadata.course_id}: {e}")
        
        logger.info(f"[VISIBLE COURSES] Created {len(pseudo_enrollments)} pseudo-enrollments")
        
        # Combine actual enrollments with pseudo-enrollments
        all_enrollments = list(existing_enrollments) + pseudo_enrollments
        logger.info(f"[VISIBLE COURSES] Total courses to show: {len(all_enrollments)}")
        return all_enrollments
        
    except Exception as e:
        logger.error(f"[VISIBLE COURSES] Error adding visible courses: {e}", exc_info=True)
        return existing_enrollments


@function_trace("filter_enrollments_by_chalix_metadata")
def filter_enrollments_by_chalix_metadata(enrollments, user, filter_type=None):
    """
    Filter enrollments based on Chalix course metadata.
    
    Args:
        enrollments: List of CourseEnrollment objects
        user: The learner user
        filter_type: Type of filter to apply:
            - 'all_visible': Return all visible courses (Bo public + same org courses) - for AI suggested
            - 'mandatory': Return courses with course_category='mandatory' or is_mandatory_course=True
            - 'elective': Return courses with course_category='elective'
            - 'organization': Return organization-specific courses (is_public=False, same org)
            - 'ministry': Return public ministry courses (is_public=True)
            - 'teaching': Return courses where user is instructor/staff
            - None or 'all': Return all enrollments (no filter)
    
    Returns:
        Filtered list of enrollments
    """
    if not filter_type or filter_type == 'all':
        return enrollments
    
    try:
        from lms.djangoapps.course_home_api.models import ChalixCourseMetadataLMS
        from django.db import connection
        logger.info(f"[CHALIX FILTER] Filtering {len(enrollments)} enrollments for user {user.username} with filter_type={filter_type}")
        
        # Get user's organization ID for filtering (query directly from DB)
        user_org_id = None
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT organization_id FROM contentstore_chalixuserrole WHERE user_id = %s AND is_active = TRUE LIMIT 1",
                    [user.id]
                )
                row = cursor.fetchone()
                if row:
                    user_org_id = row[0]
            logger.info(f"[CHALIX FILTER] User {user.username} organization_id: {user_org_id}")
        except Exception as e:
            logger.warning(f"[CHALIX FILTER] Error getting user org: {e}")
        
        filtered_enrollments = []
        
        for enrollment in enrollments:
            try:
                course_id_str = str(enrollment.course_id)
                metadata = ChalixCourseMetadataLMS.objects.filter(course_id=course_id_str).first()
                
                if not metadata:
                    # Course has no metadata - include it by default for backward compatibility
                    if filter_type in ['all', 'all_visible', 'ministry', None]:
                        filtered_enrollments.append(enrollment)
                    continue
                
                if filter_type == 'all_visible':
                    # AI suggested: Show all visible courses
                    # Rule 1: Public courses (Bo role) are visible to everyone
                    if metadata.is_public:
                        logger.info(f"[CHALIX FILTER] Including public course {course_id_str}")
                        filtered_enrollments.append(enrollment)
                        continue
                    # Rule 2: Private courses are visible to same organization members
                    if not metadata.is_public and user_org_id and metadata.creator_organization_id:
                        if metadata.creator_organization_id == user_org_id:
                            logger.info(f"[CHALIX FILTER] Including org course {course_id_str} (org_id={user_org_id})")
                            filtered_enrollments.append(enrollment)
                            continue
                    logger.debug(f"[CHALIX FILTER] Excluding course {course_id_str} (is_public={metadata.is_public}, user_org={user_org_id}, course_org={metadata.creator_organization_id})")
                
                elif filter_type == 'mandatory':
                    # Filter: mandatory courses (course_category='mandatory' or is_mandatory_course=True)
                    if metadata.course_category == 'mandatory' or metadata.is_mandatory_course:
                        filtered_enrollments.append(enrollment)
                
                elif filter_type == 'elective':
                    # Filter: elective courses (course_category='elective')
                    if metadata.course_category == 'elective' or metadata.publish_type == 'elective':
                        filtered_enrollments.append(enrollment)
                
                elif filter_type == 'organization':
                    # Filter: organization-specific courses (not public, same organization)
                    # This shows courses created by users from the same organization that are NOT public
                    if not metadata.is_public and user_org_id and metadata.creator_organization_id:
                        if metadata.creator_organization_id == user_org_id:
                            filtered_enrollments.append(enrollment)
                            logger.debug(f"Including org course {enrollment.course_id} for user {user.username}")
                
                elif filter_type == 'ministry':
                    # Filter: public ministry courses (is_public=True)
                    # These are courses created by users from the same organization that are NOT public
                    if metadata.is_public:
                        filtered_enrollments.append(enrollment)
                        logger.debug(f"Including ministry course {enrollment.course_id} for user {user.username}")
                
                elif filter_type == 'teaching':
                    # Filter: courses where user is instructor or staff
                    _, staff_access, instructor_access = administrative_accesses_to_course_for_user(
                        user, enrollment.course_id
                    )
                    if staff_access or instructor_access:
                        filtered_enrollments.append(enrollment)
                
            except Exception as e:
                logger.warning(f"[CHALIX FILTER] Error filtering enrollment {enrollment.course_id}: {str(e)}")
                # Include enrollment if there's an error to avoid hiding courses
                filtered_enrollments.append(enrollment)
        
        logger.info(f"[CHALIX FILTER] Filtered to {len(filtered_enrollments)} enrollments")
        return filtered_enrollments
        
    except ImportError as e:
        logger.warning(f"[CHALIX FILTER] ChalixCourseMetadataLMS not available: {e}, returning all enrollments")
        return enrollments
    except Exception as e:
        logger.error(f"[CHALIX FILTER] Error in filter_enrollments_by_chalix_metadata: {str(e)}", exc_info=True)
        return enrollments


@function_trace("get_enrollments")
def get_enrollments(user, org_allow_list, org_block_list, course_limit=None, filter_type=None):
    """Get enrollments and enrollment course modes for user
    
    Note: When filter_type='all_visible', this will also include pseudo-enrollments
    for courses the user can see but isn't enrolled in yet.
    """

    course_enrollments = list(
        get_course_enrollments(user, org_allow_list, org_block_list, course_limit)
    )
    
    # If filter_type is 'all_visible', add pseudo-enrollments for courses user can see
    if filter_type == 'all_visible':
        course_enrollments = _add_visible_courses_as_pseudo_enrollments(
            course_enrollments, user
        )
    
    # Apply Chalix metadata filtering if requested
    if filter_type:
        course_enrollments = filter_enrollments_by_chalix_metadata(
            course_enrollments, user, filter_type
        )

    # Sort the enrollments by enrollment date
    course_enrollments.sort(key=lambda x: x.created, reverse=True)

    # Record how many courses there are so that we can get a better
    # understanding of usage patterns on prod.
    monitoring_utils.accumulate("num_courses", len(course_enrollments))

    # Retrieve the course modes for each course
    enrolled_course_ids = [enrollment.course_id for enrollment in course_enrollments]
    __, unexpired_course_modes = CourseMode.all_and_unexpired_modes_for_courses(
        enrolled_course_ids
    )
    course_modes_by_course = {
        course_id: {mode.slug: mode for mode in modes}
        for course_id, modes in unexpired_course_modes.items()
    }

    # Construct a dictionary of course mode information
    # used to render the course list.  We re-use the course modes dict
    # we loaded earlier to avoid hitting the database.
    course_mode_info = {
        enrollment.course_id: complete_course_mode_info(
            enrollment.course_id,
            enrollment,
            modes=course_modes_by_course[enrollment.course_id],
        )
        for enrollment in course_enrollments
    }

    return course_enrollments, course_mode_info


@function_trace("get_entitlements")
def get_entitlements(user, org_allow_list, org_block_list):
    """Get entitlements for the user"""
    (
        filtered_entitlements,
        course_entitlement_available_sessions,
        unfulfilled_entitlement_pseudo_sessions,
    ) = get_filtered_course_entitlements(user, org_allow_list, org_block_list)
    fulfilled_entitlements_by_course_key = {}
    unfulfilled_entitlements = []

    for course_entitlement in filtered_entitlements:
        if course_entitlement.enrollment_course_run:
            course_id = str(course_entitlement.enrollment_course_run.course.id)
            fulfilled_entitlements_by_course_key[course_id] = course_entitlement
        else:
            unfulfilled_entitlements.append(course_entitlement)

    return (
        fulfilled_entitlements_by_course_key,
        unfulfilled_entitlements,
        course_entitlement_available_sessions,
        unfulfilled_entitlement_pseudo_sessions,
    )


@function_trace("get_course_overviews_for_pseudo_sessions")
def get_course_overviews_for_pseudo_sessions(unfulfilled_entitlement_pseudo_sessions):
    """
    Get course overviews for entitlement pseudo sessions. This is required for
    serializing course providers for entitlements.

    Returns: dict of course overviews, keyed by CourseKey
    """
    course_ids = []

    # Get course IDs from unfulfilled entitlement pseudo sessions
    for pseudo_session in unfulfilled_entitlement_pseudo_sessions.values():
        if not pseudo_session:
            continue
        course_id = pseudo_session.get("key")
        if course_id:
            course_ids.append(CourseKey.from_string(course_id))

    return CourseOverview.get_from_ids(course_ids)


@function_trace("get_email_settings_info")
def get_email_settings_info(user, course_enrollments):
    """
    Given a user and enrollments, determine which courses allow bulk email (show_email_settings_for)
    and which the learner has opted out from (optouts)
    """
    course_optouts = Optout.objects.filter(user=user).values_list(
        "course_id", flat=True
    )

    # only show email settings for course where bulk email is turned on
    show_email_settings_for = frozenset(
        enrollment.course_id
        for enrollment in course_enrollments
        if (is_bulk_email_feature_enabled(enrollment.course_id))
    )

    return show_email_settings_for, course_optouts


@function_trace("get_enterprise_customer")
def get_enterprise_customer(user, request, is_masquerading):
    """
    If we are not masquerading, try to load the enterprise learner from session data, falling back to the db.
    If we are masquerading, don't read or write to/from session data, go directly to db.
    """
    if is_masquerading:
        learner_data = get_enterprise_learner_data_from_db(user)
        return learner_data[0]["enterprise_customer"] if learner_data else None
    else:
        return enterprise_customer_from_session_or_learner_data(request)


@function_trace("get_ecommerce_payment_page")
def get_ecommerce_payment_page(user):
    """Determine the ecommerce payment page URL if enabled for this user"""
    ecommerce_service = EcommerceService()
    return (
        ecommerce_service.payment_page_url()
        if ecommerce_service.is_enabled(user)
        else None
    )


@function_trace("get_cert_statuses")
def get_cert_statuses(user, course_enrollments):
    """Get cert status by course for user enrollments"""

    cert_statuses = {}

    for enrollment in course_enrollments:
        # APER-2171 - trying to get a cert for a deleted course can throw an exception
        # Wrap in exception handling to avoid this issue.
        try:
            certificate_for_course = cert_info(user, enrollment)

            if certificate_for_course:
                cert_statuses[enrollment.course_id] = certificate_for_course

        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(
                f"Error getting certificate status for (user, course) ({user}, {enrollment.course_id}): {ex}"
            )

    return cert_statuses


@function_trace("get_org_block_and_allow_lists")
def get_org_block_and_allow_lists():
    """Proxy for get_org_black_and_whitelist_for_site to allow for modification / profiling"""
    return get_org_black_and_whitelist_for_site()


@function_trace("get_resume_urls_for_course_enrollments")
def get_resume_urls_for_course_enrollments(user, course_enrollments):
    """
    Modeled off of get_resume_urls_for_enrollments but removes check for actual presence of block
    in course structure for better performance.
    """
    resume_course_urls = OrderedDict()
    for enrollment in course_enrollments:
        url_to_block = None
        try:
            block_key = get_key_to_last_completed_block(user, enrollment.course_id)
            if block_key:
                url_to_block = reverse(
                    "jump_to",
                    kwargs={"course_id": enrollment.course_id, "location": block_key},
                )
        except UnavailableCompletionData:
            # This is acceptable, the user hasn't started the course so jump URL will be None
            pass
        resume_course_urls[enrollment.course_id] = url_to_block
    return resume_course_urls


def _get_courses_with_unmet_prerequisites(user, course_enrollments):
    """
    Determine which courses have unmet prerequisites.
    NOTE: that courses w/out prerequisites, or with met prerequisites are not returned
    in the output dict. That way we can do a simple "course_id in dict" check.

    Returns: {
        <course_id>: { "courses": [listing of unmet prerequisites] }
    }
    """

    courses_having_prerequisites = frozenset(
        enrollment.course_id
        for enrollment in course_enrollments
        if enrollment.course_overview.pre_requisite_courses
    )

    return get_pre_requisite_courses_not_completed(user, courses_having_prerequisites)


@function_trace("check_course_access")
def check_course_access(user, course_enrollments):
    """
    Wrapper for checks surrounding user ability to view courseware

    Returns: {
        <course_enrollment.id>: {
            "has_unmet_prerequisites": True/False,
            "is_too_early_to_view": True/False,
            "user_has_staff_access": True/False
        }
    }
    """

    course_access_dict = {}

    courses_with_unmet_prerequisites = _get_courses_with_unmet_prerequisites(
        user, course_enrollments
    )

    for course_enrollment in course_enrollments:
        course_access_dict[course_enrollment.course_id] = {
            "has_unmet_prerequisites": course_enrollment.course_id
            in courses_with_unmet_prerequisites,
            "is_too_early_to_view": not check_course_open_for_learner(
                user, course_enrollment.course
            ),
            "user_has_staff_access": any(
                administrative_accesses_to_course_for_user(
                    user, course_enrollment.course_id
                )
            ),
        }

    return course_access_dict


@function_trace("get_course_programs")
def get_course_programs(user, course_enrollments, site):
    """
    Get programs related to the courses the user is enrolled in.

    Returns: {
        str(<course_id>): {
            "programs": [list of programs]
        }
    }
    """
    meter = ProgramProgressMeter(
        site, user, enrollments=course_enrollments, include_course_entitlements=True
    )
    return meter.invert_programs()


@function_trace("get_suggested_courses")
def get_suggested_courses():
    """
    Currently just returns general recommendations from settings
    """
    empty_course_suggestions = {"courses": [], "is_personalized_recommendation": False}
    return (
        configuration_helpers.get_value(
            "GENERAL_RECOMMENDATION", settings.GENERAL_RECOMMENDATION
        )
        or empty_course_suggestions
    )


@function_trace("get_social_share_settings")
def get_social_share_settings():
    """Config around social media sharing campaigns"""

    share_settings = configuration_helpers.get_value(
        "SOCIAL_SHARING_SETTINGS", getattr(settings, "SOCIAL_SHARING_SETTINGS", {})
    )

    utm_sources = get_encoded_course_sharing_utm_params()

    default_brand = "edX.org"

    return {
        "facebook": {
            "is_enabled": share_settings.get("DASHBOARD_FACEBOOK", False),
            "brand": share_settings.get("FACEBOOK_BRAND", default_brand),
            "utm_params": utm_sources.get("facebook"),
        },
        "twitter": {
            "is_enabled": share_settings.get("DASHBOARD_TWITTER", False),
            "brand": share_settings.get("TWITTER_BRAND", default_brand),
            "utm_params": utm_sources.get("twitter"),
        },
    }


@function_trace("get_course_share_urls")
def get_course_share_urls(course_enrollments):
    """Get course URLs for sharing on social media"""
    return {
        course_enrollment.course_id: get_link_for_about_page(course_enrollment.course)
        for course_enrollment in course_enrollments
    }


@function_trace("get_audit_access_deadlines")
def get_audit_access_deadlines(user, course_enrollments):
    """
    Get audit access deadlines for each course enrollment

    Returns:
    - Dict {course_id: <datetime or None>}
    """
    return {
        course_enrollment.course_id: get_user_course_expiration_date(
            user, course_enrollment.course
        )
        for course_enrollment in course_enrollments
    }


@function_trace("get_user_grade_passing_statuses")
def get_user_grade_passing_statuses(course_enrollments):
    """
    Get "passing" status for user in each course

    Returns:
    - Dict {course_id: <boolean (True = Passing grade, False = Failing grade)>}
    """
    return {
        course_enrollment.course_id: user_has_passing_grade_in_course(course_enrollment)
        for course_enrollment in course_enrollments
    }


@function_trace("get_credit_statuses")
def get_credit_statuses(user, course_enrollments):
    """
    Wrapper for getting credit statuses. Credit statuses are already in a
    format we can use so this is largely for profiling / testing.

    Returns (only for courses with credit options)
    - Dict {course_id: <credit_status>}
    """
    return credit_statuses(user, course_enrollments)


@function_trace("serialize_learner_home_data")
def serialize_learner_home_data(data, context):
    """Wrapper for serialization so we can profile"""
    return LearnerDashboardSerializer(data, context=context).data


class InitializeView(APIView):  # pylint: disable=unused-argument
    """List of courses a user is enrolled in or entitled to"""

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Get masquerade user and proxy to init request"""
        masquerade_user = get_masquerade_user(request)

        if masquerade_user:
            return self._initialize(masquerade_user, is_masquerade=True)
        else:
            return self._initialize(request.user)

    def _initialize(self, user, is_masquerade=False):
        """
        Load information required for displaying the learner home
        """
        # Get filter type from query parameters (if provided)
        filter_type = self.request.GET.get('filter_type', None)
        
        # Determine if user needs to confirm email account
        email_confirmation = get_user_account_confirmation_info(user)

        # Gather info for enterprise dashboard
        enterprise_customer = get_enterprise_customer(user, self.request, is_masquerade)

        # Get site-wide social sharing config
        social_share_settings = get_social_share_settings()

        # Get platform-level settings
        platform_settings = get_platform_settings()

        # Get the org whitelist or the org blacklist for the current site
        site_org_whitelist, site_org_blacklist = get_org_block_and_allow_lists()

        # Get entitlements and course overviews for serializing
        (
            fulfilled_entitlements_by_course_key,
            unfulfilled_entitlements,
            course_entitlement_available_sessions,
            unfulfilled_entitlement_pseudo_sessions,
        ) = get_entitlements(user, site_org_whitelist, site_org_blacklist)
        pseudo_session_course_overviews = get_course_overviews_for_pseudo_sessions(
            unfulfilled_entitlement_pseudo_sessions
        )

        # Get enrollments with optional filter
        course_enrollments, course_mode_info = get_enrollments(
            user, site_org_whitelist, site_org_blacklist, filter_type=filter_type
        )

        # Get audit access deadlines
        audit_access_deadlines = get_audit_access_deadlines(user, course_enrollments)

        # Get email opt-outs for student
        show_email_settings_for, course_optouts = get_email_settings_info(
            user, course_enrollments
        )

        # Get grade passing status by course
        grade_statuses = get_user_grade_passing_statuses(course_enrollments)

        # Get cert status by course
        cert_statuses = get_cert_statuses(user, course_enrollments)

        # Determine view access for course, (for showing courseware link) involves:
        course_access_checks = check_course_access(user, course_enrollments)

        # Get programs related to the courses the user is enrolled in
        programs = get_course_programs(user, course_enrollments, self.request.site)

        # e-commerce info
        ecommerce_payment_page = get_ecommerce_payment_page(user)

        # Gather urls for course card resume buttons.
        resume_button_urls = get_resume_urls_for_course_enrollments(
            user, course_enrollments
        )

        # Get suggested courses
        suggested_courses = get_suggested_courses().get("courses", [])

        # Get social media sharing config
        course_share_urls = get_course_share_urls(course_enrollments)

        # Get credit availability
        user_credit_statuses = get_credit_statuses(user, course_enrollments)

        learner_dash_data = {
            "emailConfirmation": email_confirmation,
            "enterpriseDashboard": enterprise_customer,
            "platformSettings": platform_settings,
            "enrollments": course_enrollments,
            "unfulfilledEntitlements": unfulfilled_entitlements,
            "socialShareSettings": social_share_settings,
            "suggestedCourses": suggested_courses,
        }

        context = {
            "audit_access_deadlines": audit_access_deadlines,
            "ecommerce_payment_page": ecommerce_payment_page,
            "cert_statuses": cert_statuses,
            "course_mode_info": course_mode_info,
            "course_optouts": course_optouts,
            "course_access_checks": course_access_checks,
            "credit_statuses": user_credit_statuses,
            "grade_statuses": grade_statuses,
            "resume_course_urls": resume_button_urls,
            "course_share_urls": course_share_urls,
            "show_email_settings_for": show_email_settings_for,
            "fulfilled_entitlements": fulfilled_entitlements_by_course_key,
            "course_entitlement_available_sessions": course_entitlement_available_sessions,
            "unfulfilled_entitlement_pseudo_sessions": unfulfilled_entitlement_pseudo_sessions,
            "pseudo_session_course_overviews": pseudo_session_course_overviews,
            "programs": programs,
        }

        response_data = serialize_learner_home_data(learner_dash_data, context)

        return Response(response_data)


# Note: AvailableCoursesView removed - AI suggested section now uses 'all_visible' filter
# which shows all visible courses regardless of enrollment status
