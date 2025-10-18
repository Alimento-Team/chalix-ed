"""
API Views for unit media files (videos and slides)
"""

import logging
import uuid
from django.http import Http404
from django.shortcuts import get_object_or_404
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import edx_api_doc_tools as apidocs
from cms.djangoapps.contentstore.models import UnitMediaFile
from cms.djangoapps.contentstore.unit_media_storage_handlers import (
    save_unit_media_file,
    delete_unit_media_file,
    get_unit_media_context,
    get_supported_formats,
    get_max_file_size,
)
from ..serializers import (
    UnitMediaFileSerializer,
    UnitMediaFileListSerializer,
    UnitMediaFileUploadSerializer,
    UnitMediaErrorSerializer,
    UnitMediaFileStatsSerializer,
    UnitMediaPresignedUrlListSerializer
)
from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes, verify_course_exists

LOGGER = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class UnitMediaListView(DeveloperErrorViewMixin, APIView):
    """
    View for listing and uploading unit media files.
    
    GET: List all media files for a unit
    POST: Upload a new media file to a unit
    """
    
    parser_classes = [MultiPartParser, JSONParser]
    
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("unit_id", apidocs.ParameterLocation.PATH, description="Unit ID"),
            apidocs.string_parameter("media_type", apidocs.ParameterLocation.PATH, 
                                   description="Media type (video or slide)"),
        ],
        responses={
            200: UnitMediaFileListSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested unit does not exist",
        },
    )
    def get(self, request: Request, unit_id: str, media_type: str):
        """
        Get list of media files for a unit.
        
        **Example Request**
            GET /api/contentstore/v1/units/{unit_id}/{media_type}s/
            
        **Response Values**
        Returns a paginated list of media files with metadata.
        """
        # Validate media type
        if media_type not in ['video', 'slide']:
            return Response(
                {'error': 'Invalid media type. Must be "video" or "slide".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get unit media files
            media_files = UnitMediaFile.get_unit_media(unit_id, media_type)
            
            # Check if user has read access (we'll verify course access via first media file)
            if media_files.exists():
                first_media = media_files.first()
                if not has_studio_read_access(request.user, first_media.course_id):
                    return Response(
                        {'error': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Serialize response
            response_data = {
                'count': media_files.count(),
                'results': UnitMediaFileSerializer(media_files, many=True).data,
                'unit_id': unit_id,
                'media_type': media_type,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            LOGGER.exception(f"Error listing unit media files: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve media files'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("unit_id", apidocs.ParameterLocation.PATH, description="Unit ID"),
            apidocs.string_parameter("media_type", apidocs.ParameterLocation.PATH, 
                                   description="Media type (video or slide)"),
        ],
        responses={
            201: UnitMediaFileSerializer,
            400: UnitMediaErrorSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            413: "File too large",
            500: "Internal server error",
        },
    )
    def post(self, request: Request, unit_id: str, media_type: str):
        """
        Upload a new media file to a unit.
        
        **Example Request**
            POST /api/contentstore/v1/units/{unit_id}/{media_type}s/
            Content-Type: multipart/form-data
            
            file: <media_file>
            display_name: "My Video" (optional)
        """
        # Validate media type
        if media_type not in ['video', 'slide']:
            return Response(
                {'error': 'Invalid media type. Must be "video" or "slide".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Debug: Log request data
        LOGGER.info(f"📤 POST request received for {media_type}")
        LOGGER.info(f"📤 Request Content-Type: {request.content_type}")
        LOGGER.info(f"📤 Request keys in request.data: {list(request.data.keys())}")
        LOGGER.info(f"📤 Full request.data: {request.data}")
        
        try:
            # Derive course_id from unit_id
            try:
                usage_key = UsageKey.from_string(unit_id)
                course_key = usage_key.context_key
                course_id = str(course_key)
            except InvalidKeyError:
                return Response(
                    {'error': 'Invalid unit_id format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify course access
            if not has_studio_write_access(request.user, course_key):
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate upload data - support both file uploads and URL submissions
            if 'file' in request.data:
                # Direct file upload requires validation
                serializer = UnitMediaFileUploadSerializer(
                    data=request.data,
                    context={'media_type': media_type}
                )
                
                if not serializer.is_valid():
                    return Response(
                        {'error': 'Invalid upload data', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif 'video_url' in request.data:
                # NEW: Handle video URL submission (YouTube, Google Drive, etc.)
                LOGGER.info("✅ Detected video_url in request data")
                video_url = request.data.get('video_url', '').strip()
                video_source_type = request.data.get('video_source_type', '')
                display_name = request.data.get('display_name', 'External Video')
                
                LOGGER.info(f"📝 video_url={video_url}, source_type={video_source_type}, display_name={display_name}")
                
                if not video_url:
                    return Response(
                        {'error': 'video_url is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Basic URL validation
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(video_url)
                    if not parsed.scheme or not parsed.netloc:
                        raise ValueError("Invalid URL")
                except:
                    return Response(
                        {'error': 'Invalid video URL format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate supported video sources
                is_youtube = 'youtube.com' in video_url or 'youtu.be' in video_url
                is_google_drive = 'drive.google.com' in video_url
                
                if not (is_youtube or is_google_drive):
                    return Response(
                        {'error': 'Only YouTube and Google Drive URLs are currently supported'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create a media file record for the URL
                try:
                    # Try to fetch a nicer title for the video (YouTube oEmbed / Drive)
                    try:
                        from cms.djangoapps.contentstore.unit_media_storage_handlers import fetch_remote_video_title
                        fetched_title = fetch_remote_video_title(video_url, video_source_type)
                    except Exception:
                        fetched_title = None

                    final_title = fetched_title or display_name

                    # Determine an embeddable public URL for known providers
                    embeddable_public_url = video_url
                    try:
                        from urllib.parse import parse_qs, urlparse
                        parsed = urlparse(video_url)
                        # YouTube: convert watch or youtu.be to embed URL
                        if 'youtube.com' in video_url or 'youtu.be' in video_url:
                            # Extract video id
                            video_id = None
                            if 'youtu.be' in parsed.netloc:
                                # path like /<id>
                                video_id = parsed.path.lstrip('/')
                            else:
                                qs = parse_qs(parsed.query)
                                video_id = qs.get('v', [None])[0]
                            if video_id:
                                embeddable_public_url = f'https://www.youtube.com/embed/{video_id}'

                        # Google Drive: use preview endpoint
                        if 'drive.google.com' in video_url:
                            # Replace /view with /preview when present
                            if video_url.endswith('/view'):
                                embeddable_public_url = video_url.replace('/view', '/preview')
                            else:
                                embeddable_public_url = video_url
                    except Exception:
                        embeddable_public_url = video_url

                    media_file = UnitMediaFile.objects.create(
                        unit_id=unit_id,
                        course_id=course_id,
                        media_type=media_type,
                        file_name=f"{final_title}.url",
                        display_name=final_title,
                        file_size=0,  # URLs don't have file size
                        file_type='video/external',  # Special type for external videos
                        file_path=None,  # No file path for URLs
                        upload_url=None,  # No upload URL for external videos
                        public_url=embeddable_public_url,
                        url=video_url,
                        upload_status='ready',
                        created_by=request.user,
                        external_url=video_url,  # Store the URL
                        video_source_type=video_source_type,  # Store the source type
                        client_video_id=str(uuid.uuid4()),  # Generate unique ID
                    )
                    
                    LOGGER.info(f"✅ Successfully created external video: {media_file.id}")
                    
                    # Return created file
                    response_data = UnitMediaFileSerializer(media_file).data
                    return Response(response_data, status=status.HTTP_201_CREATED)
                    
                except Exception as e:
                    LOGGER.error(f"Failed to create URL media file: {str(e)}")
                    return Response(
                        {'error': 'Failed to create video from URL'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Presigned URL request - use serializer for validation
                serializer = UnitMediaPresignedUrlListSerializer(
                    data=request.data,
                    context={'media_type': media_type}
                )
                
                if not serializer.is_valid():
                    return Response(
                        {'error': 'Invalid request data', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check if this is a file upload request or presigned URL request
            if 'file' in request.data:
                # Direct file upload (legacy support)
                uploaded_file = serializer.validated_data['file']
                display_name = serializer.validated_data.get('display_name')
                
                media_file, error_msg = save_unit_media_file(
                    uploaded_file=uploaded_file,
                    unit_id=unit_id,
                    course_id=course_id,
                    media_type=media_type,
                    user=request.user,
                    display_name=display_name
                )
                
                if not media_file:
                    return Response(
                        {'error': error_msg or 'Failed to save file'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Return created file
                response_data = UnitMediaFileSerializer(media_file).data
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                # Generate presigned upload URL (like video system)
                from cms.djangoapps.contentstore.unit_media_storage_handlers import generate_unit_media_presigned_upload_url
                
                # Get validated file details from serializer
                files_data = serializer.validated_data.get('files', [])
                if not files_data:
                    return Response(
                        {'error': 'No files specified for upload'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                response_files = []
                for file_data in files_data:
                    file_name = file_data.get('file_name')
                    content_type = file_data.get('content_type', 'application/octet-stream')
                    
                    if not file_name:
                        continue
                        
                    # Generate presigned upload URL
                    upload_url, public_url, storage_key = generate_unit_media_presigned_upload_url(
                        file_name, content_type, media_type
                    )
                    
                    if upload_url:
                        # Create the media file record immediately
                        try:
                            # Ensure the public URL is properly encoded for database storage
                            from urllib.parse import quote, urlparse, urlunparse
                            
                            # Parse and re-encode the public URL to handle spaces and special characters
                            try:
                                parsed = urlparse(public_url)
                                # URL encode the path component
                                encoded_path = quote(parsed.path, safe='/')
                                encoded_public_url = urlunparse((
                                    parsed.scheme, parsed.netloc, encoded_path, 
                                    parsed.params, parsed.query, parsed.fragment
                                ))
                            except Exception as url_error:
                                LOGGER.warning(f"Failed to encode public URL {public_url}: {url_error}")
                                # Fallback: try simple replacement of spaces
                                encoded_public_url = public_url.replace(' ', '%20')
                                
                            media_file = UnitMediaFile.objects.create(
                                unit_id=unit_id,
                                course_id=course_id,
                                media_type=media_type,
                                file_name=file_name,
                                display_name=file_name,  # Use file_name as display_name
                                file_type=content_type,
                                file_path=storage_key,
                                upload_url=encoded_public_url,  # Use properly encoded URL
                                uploaded_by=request.user,
                                file_size=0,  # We don't know the size yet
                            )
                            
                            response_files.append({
                                'file_name': file_name,
                                'upload_url': upload_url,
                                'id': str(media_file.id),
                                'public_url': public_url,
                                'storage_key': storage_key
                            })
                        except Exception as create_error:
                            LOGGER.exception(f"Failed to create UnitMediaFile record: {str(create_error)}")
                            # Still return the upload URL even if database creation fails
                            media_file_id = str(uuid.uuid4())
                            response_files.append({
                                'file_name': file_name,
                                'upload_url': upload_url,
                                'id': media_file_id,
                                'public_url': public_url,
                                'storage_key': storage_key
                            })
                
                return Response({
                    'files': response_files,
                    'unit_id': unit_id,
                    'media_type': media_type
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            LOGGER.exception(f"Error uploading unit media file: {str(e)}")
            return Response(
                {'error': 'Failed to upload file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@view_auth_classes(is_authenticated=True)
class UnitMediaDetailView(DeveloperErrorViewMixin, APIView):
    """
    View for individual unit media file operations.
    
    GET: Get details of a specific media file
    DELETE: Delete a media file
    """
    
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("unit_id", apidocs.ParameterLocation.PATH, description="Unit ID"),
            apidocs.string_parameter("media_type", apidocs.ParameterLocation.PATH, 
                                   description="Media type (video or slide)"),
            apidocs.string_parameter("media_id", apidocs.ParameterLocation.PATH, description="Media file ID"),
        ],
        responses={
            200: UnitMediaFileSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested media file does not exist",
        },
    )
    def get(self, request: Request, unit_id: str, media_type: str, media_id: str):
        """
        Get details of a specific media file.
        
        **Example Request**
            GET /api/contentstore/v1/units/{unit_id}/{media_type}s/{media_id}/
        """
        try:
            # Get media file
            media_file = get_object_or_404(
                UnitMediaFile,
                id=media_id,
                unit_id=unit_id,
                media_type=media_type
            )
            
            # Check access permissions
            if not has_studio_read_access(request.user, media_file.course_id):
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Serialize and return
            response_data = UnitMediaFileSerializer(media_file).data
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Http404:
            return Response(
                {'error': 'Media file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            LOGGER.exception(f"Error retrieving unit media file: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve media file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("unit_id", apidocs.ParameterLocation.PATH, description="Unit ID"),
            apidocs.string_parameter("media_type", apidocs.ParameterLocation.PATH, 
                                   description="Media type (video or slide)"),
            apidocs.string_parameter("media_id", apidocs.ParameterLocation.PATH, description="Media file ID"),
        ],
        responses={
            204: "Media file deleted successfully",
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
            404: "The requested media file does not exist",
        },
    )
    def delete(self, request: Request, unit_id: str, media_type: str, media_id: str):
        """
        Delete a media file.
        
        **Example Request**
            DELETE /api/contentstore/v1/units/{unit_id}/{media_type}s/{media_id}/
        """
        try:
            # Add debugging
            LOGGER.info(f"DELETE request - unit_id: {unit_id}, media_type: {media_type}, media_id: {media_id}")
            
            # Check if any records exist with this media_id
            all_matching = UnitMediaFile.objects.filter(id=media_id)
            LOGGER.info(f"Records with media_id {media_id}: {all_matching.count()}")
            for record in all_matching:
                LOGGER.info(f"  - ID: {record.id}, unit_id: {record.unit_id}, media_type: {record.media_type}")
            
            # Get media file
            media_file = get_object_or_404(
                UnitMediaFile,
                id=media_id,
                unit_id=unit_id,
                media_type=media_type
            )
            
            # Check access permissions
            if not has_studio_write_access(request.user, media_file.course_id):
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete file
            success, error_msg = delete_unit_media_file(media_file)
            
            if not success:
                return Response(
                    {'error': error_msg or 'Failed to delete file'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Http404:
            return Response(
                {'error': 'Media file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            LOGGER.exception(f"Error deleting unit media file: {str(e)}")
            return Response(
                {'error': 'Failed to delete media file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@view_auth_classes(is_authenticated=True)
class UnitMediaStatsView(DeveloperErrorViewMixin, APIView):
    """
    View for unit media statistics.
    """
    
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("unit_id", apidocs.ParameterLocation.PATH, description="Unit ID"),
        ],
        responses={
            200: UnitMediaFileStatsSerializer,
            401: "The requester is not authenticated",
            403: "The requester cannot access the specified course",
        },
    )
    def get(self, request: Request, unit_id: str):
        """
        Get statistics for all media files in a unit.
        
        **Example Request**
            GET /api/contentstore/v1/units/{unit_id}/media/stats/
        """
        try:
            # Get unit media context
            context = get_unit_media_context(unit_id)
            
            # Check access permissions (if any files exist)
            if context['total_files'] > 0:
                first_media = UnitMediaFile.get_unit_media(unit_id).first()
                if first_media and not has_studio_read_access(request.user, first_media.course_id):
                    return Response(
                        {'error': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Serialize statistics
            stats_data = {
                'unit_id': unit_id,
                'total_files': context['total_files'],
                'total_videos': context['total_videos'],
                'total_slides': context['total_slides'],
                'total_size_bytes': context['total_size_bytes'],
                'formatted_total_size': context['formatted_total_size'],
            }
            
            return Response(stats_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            LOGGER.exception(f"Error retrieving unit media stats: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve media statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@view_auth_classes(is_authenticated=True)
class UnitMediaFinalizeUploadView(DeveloperErrorViewMixin, APIView):
    """Finalize unit media upload by updating file_size via S3 HEAD."""

    def post(self, request: Request, unit_id: str, media_type: str, media_id: str):
        try:
            media_file = get_object_or_404(
                UnitMediaFile,
                id=media_id,
                unit_id=unit_id,
                media_type=media_type
            )

            if not has_studio_write_access(request.user, media_file.course_id):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # If file_size already set, return early
            if media_file.file_size and media_file.file_size > 0:
                return Response({'id': str(media_file.id), 'file_size': media_file.file_size}, status=status.HTTP_200_OK)

            # Query object size from S3/MinIO
            import boto3
            from django.conf import settings

            bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            if not bucket_name or not media_file.file_path:
                return Response({'error': 'Storage not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            s3_client = boto3.client(
                's3',
                endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            )

            head = s3_client.head_object(Bucket=bucket_name, Key=media_file.file_path)
            size = head.get('ContentLength', 0)

            media_file.file_size = size or 0
            media_file.save(update_fields=['file_size', 'updated_at'])

            return Response({'id': str(media_file.id), 'file_size': media_file.file_size}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'error': 'Media file not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            LOGGER.exception(f"Error finalizing unit media upload: {str(e)}")
            return Response({'error': 'Failed to finalize upload'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)