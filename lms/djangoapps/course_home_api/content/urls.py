"""
LMS Content API URLs - Mirror of CMS contentstore API patterns for read-only access.
"""

from django.conf import settings
from django.urls import re_path

from .views import (
    UnitMediaListView,
    UnitMediaDetailView, 
    UnitMediaStatsView,
    ContainerHandlerView,
    VerticalContainerView,
    CourseAggregateView,
    QuizDetailView,
    QuizSubmitView,
)

app_name = 'content'

urlpatterns = [
    # Course aggregate content (config + details + topics media)
    re_path(
        fr'^course/{settings.COURSE_KEY_PATTERN}/aggregate$',
        CourseAggregateView.as_view(),
        name="course_aggregate"
    ),
    # Unit Media URLs (read-only mirrors of CMS)
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>videos|slides|quizzes)/$',
        UnitMediaListView.as_view(),
        name="unit_media_list"
    ),
    re_path(
        r'^units/(?P<unit_id>[^/]+)/(?P<media_type>video|slide|quiz)s/(?P<media_id>[-\w]+)/$',
        UnitMediaDetailView.as_view(),
        name="unit_media_detail"
    ),
    re_path(
        r'^units/(?P<unit_id>[^/]+)/media/stats/$',
        UnitMediaStatsView.as_view(),
        name="unit_media_stats"
    ),
    
    # Container/Vertical URLs (read-only mirrors of CMS)
    re_path(
        fr'^container_handler/(?P<unit_id>[^/]+)$',
        ContainerHandlerView.as_view(),
        name="container_handler"
    ),
    re_path(
        fr'^container/vertical/(?P<unit_id>[^/]+)/children$',
        VerticalContainerView.as_view(),
        name="container_vertical"
    ),
    re_path(
        r'^quizzes/(?P<quiz_id>\d+)/$',
        QuizDetailView.as_view(),
        name='quiz_detail'
    ),
    re_path(
        r'^quizzes/(?P<quiz_id>\d+)/submit/$',
        QuizSubmitView.as_view(),
        name='quiz_submit'
    ),
]