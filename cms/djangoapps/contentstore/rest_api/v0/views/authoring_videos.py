"""
Public rest API endpoints for the Authoring API video assets.
"""
import logging
import requests
from django.http import HttpResponse, StreamingHttpResponse, Http404
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from rest_framework.parsers import (MultiPartParser, FormParser)
from django.views.decorators.csrf import csrf_exempt

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.lib.api.parsers import TypedFileUploadParser
from common.djangoapps.util.json_request import expect_json_in_class_view
from opaque_keys.edx.keys import CourseKey

from ....api import course_author_access_required

from cms.djangoapps.contentstore.video_storage_handlers import (
    handle_videos,
    get_video_encodings_download,
    handle_video_images,
    enabled_video_features
)
from cms.djangoapps.contentstore.rest_api.v1.serializers import (
    VideoUploadSerializer,
    VideoImageSerializer,
)
from .utils import validate_request_with_serializer


log = logging.getLogger(__name__)


@view_auth_classes()
class VideosUploadsView(DeveloperErrorViewMixin, RetrieveAPIView, DestroyAPIView):
    """
    public rest API endpoints for the CMS API video assets.
    course_key: required argument, needed to authorize course authors and identify the video.
    video_id: required argument, needed to identify the video.
    """
    serializer_class = VideoUploadSerializer

    @course_author_access_required
    def retrieve(self, request, course_key, edx_video_id=None):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id(), edx_video_id)

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, edx_video_id):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id(), edx_video_id)


@view_auth_classes()
class VideosCreateUploadView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoints for the CMS API video assets.
    course_key: required argument, needed to authorize course authors and identify the video.
    """
    serializer_class = VideoUploadSerializer

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    @validate_request_with_serializer
    def create(self, request, course_key):  # pylint: disable=arguments-differ
        return handle_videos(request, course_key.html_id())


@view_auth_classes()
class VideoImagesView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoint for uploading a video image.
    course_key: required argument, needed to authorize course authors and identify the video.
    video_id: required argument, needed to identify the video.
    """
    serializer_class = VideoImageSerializer
    parser_classes = (MultiPartParser, FormParser, TypedFileUploadParser)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    @validate_request_with_serializer
    def create(self, request, course_key, edx_video_id=None):  # pylint: disable=arguments-differ
        return handle_video_images(request, course_key.html_id(), edx_video_id)


@view_auth_classes()
class VideoEncodingsDownloadView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    public rest API endpoint providing a CSV report containing the encoded video URLs for video uploads.
    course_key: required argument, needed to authorize course authors and identify relevant videos.
    """

    # TODO: ARCH-91
    # This view is excluded from Swagger doc generation because it
    # does not specify a serializer class.
    swagger_schema = None

    @csrf_exempt
    @course_author_access_required
    def retrieve(self, request, course_key):  # pylint: disable=arguments-differ
        return get_video_encodings_download(request, course_key.html_id())


@view_auth_classes()
class VideoFeaturesView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    public rest API endpoint providing a list of enabled video features.
    """

    # TODO: ARCH-91
    # This view is excluded from Swagger doc generation because it
    # does not specify a serializer class.
    swagger_schema = None

    @csrf_exempt
    def retrieve(self, request):  # pylint: disable=arguments-differ
        return enabled_video_features(request)


@view_auth_classes()
class VideoStreamView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    Video streaming endpoint that proxies video files from S3 storage.
    This allows the frontend to stream videos without dealing with CORS issues.
    """

    # TODO: ARCH-91
    # This view is excluded from Swagger doc generation because it
    # does not specify a serializer class.
    swagger_schema = None

    def get_object(self):
        """
        Get the video URL for streaming - construct S3 URL using the video filename
        """
        video_id = self.kwargs.get('video_id')
        
        try:
            from django.conf import settings
            
            # Get S3 configuration
            bucket_name = getattr(settings, 'VIDEO_UPLOAD_PIPELINE', {}).get('BUCKET', 'openedxvideos')
            s3_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://files.local.openedx.io:9000')
            
            # The video_id could be either the filename (like "2010.mov") or the edxVideoId
            # Based on the console output, the path is: /openedxvideos/upload/2010.mov
            # So let's construct the URL using the upload path
            video_url = f"{s3_endpoint}/{bucket_name}/upload/{video_id}"
            
            logging.info(f"Constructed streaming URL: {video_url} for video_id: {video_id}")
            return video_url
            
        except Exception as e:
            logging.error(f"Error getting video URL for {video_id}: {str(e)}")
            raise Http404("Video not found or error retrieving video")

    @csrf_exempt
    def retrieve(self, request, video_id):  # pylint: disable=arguments-differ
        """
        Stream the video file by proxying the S3 URL
        """
        try:
            video_url = self.get_object()
            logging.info(f"Attempting to stream video from URL: {video_url}")
            
            # Stream the video content with better headers and error handling
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get content type from response or default to mp4
            content_type = response.headers.get('content-type', 'video/mp4')
            
            # Create a streaming HTTP response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        yield chunk
            
            streaming_response = StreamingHttpResponse(
                generate(),
                content_type=content_type
            )
            
            # Add appropriate headers for video streaming
            if 'content-length' in response.headers:
                streaming_response['Content-Length'] = response.headers['content-length']
            
            streaming_response['Accept-Ranges'] = 'bytes'
            streaming_response['Cache-Control'] = 'public, max-age=3600'
            streaming_response['Access-Control-Allow-Origin'] = '*'
            streaming_response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            streaming_response['Access-Control-Allow-Headers'] = 'Range'
            
            return streaming_response
            
        except requests.RequestException as e:
            logging.error(f"Error streaming video {video_id}: {str(e)}")
            return HttpResponse(f"Error streaming video: {str(e)}", status=500)
        except Exception as e:
            logging.error(f"Unexpected error streaming video {video_id}: {str(e)}")
            return HttpResponse(f"Error streaming video: {str(e)}", status=500)
