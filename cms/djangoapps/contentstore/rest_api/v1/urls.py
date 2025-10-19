""" Contenstore API v1 URLs. """

from django.conf import settings
from django.urls import re_path, path

from openedx.core.constants import COURSE_ID_PATTERN

from .views import (
    ContainerHandlerView,
    CourseCertificatesView,
    CourseDetailsView,
    CourseTeamView,
    CourseTextbooksView,
    CourseIndexView,
    CourseGradingView,
    CourseGroupConfigurationsView,
    CourseRerunView,
    CourseSettingsView,
    CourseSlidesView,
    CourseVideosView,
    CourseWaffleFlagsView,
    HomePageView,
    HomePageCoursesView,
    HomePageLibrariesView,
    ProctoredExamSettingsView,
    ProctoringErrorsView,
    HelpUrlsView,
    VideoUsageView,
    SlideUsageView,
    VideoDownloadView,
    VerticalContainerView,
    UnitMediaListView,
    UnitMediaDetailView,
    UnitMediaStatsView,
    UnitMediaFinalizeUploadView,
)

# Import user management views
from ...views.user_management import (
    create_user_account,
    bulk_create_users,
    get_user_organizations,
    get_available_roles,
    list_users,
)

# Import user template views
from ...views.user_template import (
    download_user_template,
    get_upload_instructions,
)


app_name = 'v1'

VIDEO_ID_PATTERN = r'(?P<edx_video_id>[-\w]+)'

urlpatterns = [
    path(
        'home',
        HomePageView.as_view(),
        name="home"
    ),
    path(
        'home/courses',
        HomePageCoursesView.as_view(),
        name="courses"),
    path(
        'home/libraries',
        HomePageLibrariesView.as_view(),
        name="libraries"),
    re_path(
        fr'^videos/{COURSE_ID_PATTERN}$',
        CourseVideosView.as_view(),
        name="course_videos"
    ),
    re_path(
        fr'^slides/{COURSE_ID_PATTERN}$',
        CourseSlidesView.as_view(),
        name="course_slides"
    ),
    re_path(
        fr'^slides/{COURSE_ID_PATTERN}/(?P<slide_id>[-\w]+)/usage$',
        SlideUsageView.as_view(),
        name="slide_usage"
    ),

    # Unit Media URLs
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>video|slide)s/$',
        UnitMediaListView.as_view(),
        name="unit_media_list"
    ),
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>video|slide)s/(?P<media_id>[-\w]+)/$',
        UnitMediaDetailView.as_view(),
        name="unit_media_detail"
    ),
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>video|slide)s/(?P<media_id>[-\w]+)/finalize/$',
        UnitMediaFinalizeUploadView.as_view(),
        name="unit_media_finalize"
    ),
    re_path(
        r'^units/(?P<unit_id>[^/]+)/media/stats/$',
        UnitMediaStatsView.as_view(),
        name="unit_media_stats"
    ),

    re_path(
        fr'^videos/{COURSE_ID_PATTERN}/{VIDEO_ID_PATTERN}/usage$',
        VideoUsageView.as_view(),
        name="video_usage"
    ),
    re_path(
        fr'^videos/{COURSE_ID_PATTERN}/download$',
        VideoDownloadView.as_view(),
        name="video_usage"
    ),
    re_path(
        fr'^proctored_exam_settings/{COURSE_ID_PATTERN}$',
        ProctoredExamSettingsView.as_view(),
        name="proctored_exam_settings"
    ),
    re_path(
        fr'^proctoring_errors/{COURSE_ID_PATTERN}$',
        ProctoringErrorsView.as_view(),
        name="proctoring_errors"
    ),
    re_path(
        fr'^course_settings/{COURSE_ID_PATTERN}$',
        CourseSettingsView.as_view(),
        name="course_settings"
    ),
    re_path(
        fr'^course_index/{COURSE_ID_PATTERN}$',
        CourseIndexView.as_view(),
        name="course_index"
    ),
    re_path(
        fr'^course_details/{COURSE_ID_PATTERN}$',
        CourseDetailsView.as_view(),
        name="course_details"
    ),
    re_path(
        fr'^course_team/{COURSE_ID_PATTERN}$',
        CourseTeamView.as_view(),
        name="course_team"
    ),
    re_path(
        fr'^course_grading/{COURSE_ID_PATTERN}$',
        CourseGradingView.as_view(),
        name="course_grading"
    ),
    path(
        'help_urls',
        HelpUrlsView.as_view(),
        name="help_urls"
    ),
    re_path(
        fr'^course_rerun/{COURSE_ID_PATTERN}$',
        CourseRerunView.as_view(),
        name="course_rerun"
    ),
    re_path(
        fr'^textbooks/{COURSE_ID_PATTERN}$',
        CourseTextbooksView.as_view(),
        name="textbooks"
    ),
    re_path(
        fr'^certificates/{COURSE_ID_PATTERN}$',
        CourseCertificatesView.as_view(),
        name="certificates"
    ),
    re_path(
        fr'^group_configurations/{COURSE_ID_PATTERN}$',
        CourseGroupConfigurationsView.as_view(),
        name="group_configurations"
    ),
    re_path(
        fr'^container_handler/{settings.USAGE_KEY_PATTERN}$',
        ContainerHandlerView.as_view(),
        name="container_handler"
    ),
    re_path(
        fr'^container/vertical/{settings.USAGE_KEY_PATTERN}/children$',
        VerticalContainerView.as_view(),
        name="container_vertical"
    ),
    re_path(
        fr'^course_waffle_flags(?:/{COURSE_ID_PATTERN})?$',
        CourseWaffleFlagsView.as_view(),
        name="course_waffle_flags"
    ),

    # User management endpoints
    path('users/create', create_user_account, name='create_user_account'),
    path('users/bulk-create', bulk_create_users, name='bulk_create_users'), 
    path('users/organizations', get_user_organizations, name='get_user_organizations'),
    path('users/roles', get_available_roles, name='get_available_roles'),
    path('users/list', list_users, name='list_users'),
    
    # Template and instructions
    path('users/template/download', download_user_template, name='download_user_template'),
    path('users/template/instructions', get_upload_instructions, name='get_upload_instructions'),

    # Authoring API
    # Do not use under v1 yet (Nov. 23). The Authoring API is still experimental and the v0 versions should be used
]
