"""
Contains all the URLs for the Course Home
"""


from django.conf import settings
from django.urls import re_path

from django.urls import include

from lms.djangoapps.course_home_api.course_metadata.views import CourseHomeMetadataView
from lms.djangoapps.course_home_api.dates.views import DatesTabView
from lms.djangoapps.course_home_api.outline.views import (
    CourseNavigationBlocksView,
    OutlineTabView,
    dismiss_welcome_message,
    save_course_goal,
    unsubscribe_from_course_goal_by_token,
)
from lms.djangoapps.course_home_api.outline.simplified_views import SimplifiedOutlineTabView
from lms.djangoapps.course_home_api.progress.views import ProgressTabView
from lms.djangoapps.course_home_api.reviews.views import CourseReviewView, CourseReviewSummaryView
from lms.djangoapps.course_home_api.studio_proxy.views import StudioProxyView

# This API is a BFF ("backend for frontend") designed for the learning MFE. It's not versioned because there is no
# guarantee of stability over time. It may change from one Open edX release to another. Don't write any scripts
# that depend on it.

urlpatterns = []

# URL for Course metadata content
urlpatterns += [
    re_path(
        fr'course_metadata/{settings.COURSE_KEY_PATTERN}',
        CourseHomeMetadataView.as_view(),
        name='course-metadata'
    ),
]

# Dates Tab URLs
urlpatterns += [
    re_path(
        fr'dates/{settings.COURSE_KEY_PATTERN}',
        DatesTabView.as_view(),
        name='dates-tab'
    ),
]

# Outline Tab URLs
urlpatterns += [
    re_path(
        fr'outline/{settings.COURSE_KEY_PATTERN}',
        OutlineTabView.as_view(),
        name='outline-tab'
    ),
    re_path(
        fr'simplified_outline/{settings.COURSE_KEY_PATTERN}',
        SimplifiedOutlineTabView.as_view(),
        name='simplified-outline-tab'
    ),
    re_path(
        fr'navigation/{settings.COURSE_KEY_PATTERN}',
        CourseNavigationBlocksView.as_view(),
        name='course-navigation'
    ),
    re_path(
        r'dismiss_welcome_message',
        dismiss_welcome_message,
        name='dismiss-welcome-message'
    ),
    re_path(
        r'save_course_goal',
        save_course_goal,
        name='save-course-goal'
    ),
    re_path(
        r'unsubscribe_from_course_goal/(?P<token>[^/]*)$',
        unsubscribe_from_course_goal_by_token,
        name='unsubscribe-from-course-goal'
    ),
]

# Progress Tab URLs
urlpatterns += [
    re_path(
        fr'progress/{settings.COURSE_KEY_PATTERN}/(?P<student_id>[^/]+)',
        ProgressTabView.as_view(),
        name='progress-tab-other-student'
    ),
    re_path(
        fr'progress/{settings.COURSE_KEY_PATTERN}',
        ProgressTabView.as_view(),
        name='progress-tab'
    ),
]

# Reviews URLs (emoji-based quick review)
urlpatterns += [
    re_path(
        fr'reviews/{settings.COURSE_KEY_PATTERN}$',
        CourseReviewView.as_view(),
        name='course-review'
    ),
    re_path(
        fr'reviews/{settings.COURSE_KEY_PATTERN}/summary$',
        CourseReviewSummaryView.as_view(),
        name='course-review-summary'
    ),
    # Legacy proxy endpoints - deprecated in favor of content API
    # Kept for backward compatibility but redirected to content API
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>videos|slides)/$',
        StudioProxyView.as_view(),
        name='course-home-unit-media-proxy',
    ),
    re_path(
        fr'container_handler/(?P<unit_id>[^/]+)$',
        StudioProxyView.as_view(),
        name='course-home-unit-container-proxy',
    ),
]

# Content API URLs (mirrors of CMS contentstore for read-only access)
urlpatterns += [
    re_path(
        r'^content/',
        include('lms.djangoapps.course_home_api.content.urls')
    ),
]

# Final Evaluation API URLs
urlpatterns += [
    re_path(
        r'^final_evaluation/',
        include('lms.djangoapps.course_home_api.final_evaluation.urls')
    ),
]
