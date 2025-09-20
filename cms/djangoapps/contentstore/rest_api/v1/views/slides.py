"""
Public rest API endpoints for contentstore API slide assets
"""
import edx_api_doc_tools as apidocs
import logging
from opaque_keys.edx.keys import CourseKey
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes, verify_course_exists
from common.djangoapps.student.auth import has_studio_read_access

from ....slide_storage_handlers import get_course_slides_context

from cms.djangoapps.contentstore.rest_api.v1.serializers import (
    CourseSlidesSerializer,
)

log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class CourseSlidesView(DeveloperErrorViewMixin, APIView):
    """
    View for course slides.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseSlidesSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested course does not exist",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing course slides.
        
        **Example Request**
            GET /api/contentstore/v1/slides/{course_id}
        
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response contains a single dict that contains keys that
        are the course's slides.
        
        **Example Response**
        ```json
        {
            "slide_handler_url": "/slides/course_id",
            "previous_uploads": [
                {
                    "slide_id": "slide-001",
                    "display_name": "Introduction Slides",
                    "file_name": "intro.pdf",
                    "file_size": 2048576,
                    "file_type": "application/pdf",
                    "status": "Ready",
                    "created_at": "2025-09-20T00:00:00",
                    "download_link": "/slides/course_id/slide-001/download",
                    "public_url": "https://minio.example.com/openedxuploads/slides/course_id/slide-001/intro.pdf",
                    "url": "https://minio.example.com/openedxuploads/slides/course_id/slide-001/intro.pdf",
                    "contentType": "application/pdf"
                }
            ],
            "slide_supported_file_formats": {
                ".pdf": "application/pdf",
                ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                ".ppt": "application/vnd.ms-powerpoint"
            },
            "slide_upload_max_file_size": 100
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        # Get the course object using the same method as other views
        from cms.djangoapps.contentstore.views.course import get_course_and_check_access
        course = get_course_and_check_access(course_key, request.user)

        course_slides_context = get_course_slides_context(course)
        
        # Create a serializable context by excluding the non-serializable course object
        serializable_context = {k: v for k, v in course_slides_context.items() if k != 'course'}
        serializer = CourseSlidesSerializer(serializable_context)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class SlideUsageView(DeveloperErrorViewMixin, APIView):
    """Return (stub) usage locations for a slide. Currently returns empty list."""
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
            apidocs.string_parameter("slide_id", apidocs.ParameterLocation.PATH, description="Slide ID"),
        ],
        responses={
            200: "{""usage_locations"": []}",
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested course does not exist",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str, slide_id: str):  # pylint: disable=unused-argument
        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)
        return Response({"usage_locations": []})