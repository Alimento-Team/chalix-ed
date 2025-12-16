"""
Learner Home URL routing configuration
"""

from django.urls import path
from django.urls import include, re_path

from lms.djangoapps.learner_home import views
from .rest_api import urls as rest_api_urls


app_name = "learner_home"

# Learner Dashboard Routing
urlpatterns = [
    re_path(r"^init/?", views.InitializeView.as_view(), name="initialize"),
    # Note: available_courses endpoint removed - all filtering now done via init endpoint with filter_type parameter
    path("mock/", include("lms.djangoapps.learner_home.mock.urls")),
    path("", include(rest_api_urls)),
]
