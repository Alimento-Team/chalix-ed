"""
Handlers for slide upload functionality
"""

import json
import logging
from datetime import datetime, timedelta
from uuid import uuid4

import boto3
from urllib.parse import quote
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status as rest_status

from common.djangoapps.edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore

from .views.course import get_course_and_check_access

LOGGER = logging.getLogger(__name__)

SLIDE_SUPPORTED_FILE_FORMATS = {
    '.pdf': 'application/pdf',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt': 'application/vnd.ms-powerpoint',
}

SLIDE_UPLOAD_MAX_FILE_SIZE_MB = 100


def handle_slides(request, course_key_string, slide_id=None):
    """
    Restful handler for slide uploads.

    GET
        html: return an HTML page to display previous slide uploads and allow
            new ones
        json: return json representing the slides that have been uploaded and
            their statuses
    POST
        json: generate new slide upload urls, for example upload urls for S3 buckets. To upload the slide, you should
            make a PUT request to the returned upload_url values. This can happen on the frontend, MFE,
            or client side - it is not implemented in the backend.
            Example payload:
                {
                    "files": [{
                        "file_name": "slides.pdf",
                        "content_type": "application/pdf"
                    }]
                }
            Returns (JSON):
                {
                    "files": [{
                        "file_name": "slides.pdf",
                        "content_type": "application/pdf",
                        "upload_url": "https://s3.amazonaws.com/...",
                        "slide_id": "slide-123"
                    }]
                }
    DELETE
        soft deletes a slide for particular course
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return JsonResponse(
            {'error': _('Invalid course key')},
            status=rest_status.HTTP_400_BAD_REQUEST
        )

    course = get_course_and_check_access(course_key, request.user)

    if request.method == 'GET':
        return handle_slides_get(request, course)
    elif request.method == 'POST':
        return handle_slides_post(request, course)
    elif request.method == 'DELETE':
        return handle_slides_delete(request, course, slide_id)
    else:
        return JsonResponse(
            {'error': _('Method not allowed')},
            status=rest_status.HTTP_405_METHOD_NOT_ALLOWED
        )


def handle_slides_get(request, course):
    """
    Handle GET requests for slides
    """
    if request.META.get('HTTP_ACCEPT') == 'application/json':
        return slides_index_json(course)
    else:
        return slides_index_html(course)


def handle_slides_post(request, course):
    """
    Handle POST requests for slides
    """
    return slides_post(course, request)


def handle_slides_delete(request, course, slide_id):
    """
    Handle DELETE requests for slides
    """
    if not slide_id:
        return JsonResponse(
            {'error': _('Slide ID is required for deletion')},
            status=rest_status.HTTP_400_BAD_REQUEST
        )

    # Delete all files for this slide from S3
    try:
        s3_client = get_s3_client()
        bucket_name = 'openedxuploads'
        prefix = f"slides/{course.id}/{slide_id}/"
        # List all objects under the slide folder
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        deleted_files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                s3_client.delete_object(Bucket=bucket_name, Key=key)
                deleted_files.append(key)
        # Delete slide record(s) from database
        LOGGER.info(f"Deleted slide {slide_id} for course {course.id} from S3. Files: {deleted_files}")
        return JsonResponse({'success': True, 'deleted_files': deleted_files})
    except Exception as e:
        LOGGER.error(f"Failed to delete slide {slide_id} for course {course.id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR)


def slides_index_html(course):
    """
    Return HTML page for slides management
    """
    context = get_course_slides_context(course)
    return render_to_response('slides_index.html', context)


def slides_index_json(course):
    """
    Return JSON data for slides
    """
    context = get_course_slides_context(course)
    return JsonResponse(context)


def slides_post(course, request):
    """
    Handle slide upload POST request
    """
    try:
        data = json.loads(request.body)

        # Handle different data formats
        if isinstance(data, list):
            # This is a status update request
            return handle_slide_status_update(course, data)
        elif isinstance(data, dict):
            # This is a file upload request
            files = data.get('files', [])

            if not files:
                return JsonResponse(
                    {'error': _('No files provided')},
                    status=rest_status.HTTP_400_BAD_REQUEST
                )

            response_data = {'files': []}
            has_errors = False

            for file_info in files:
                file_name = file_info.get('file_name', '')
                content_type = file_info.get('content_type', '')

                if not file_name or not content_type:
                    continue

                # Generate a unique slide ID
                slide_id = f"slide-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(file_name) % 10000}"

                # Generate S3 presigned URL similar to video upload
                try:
                    upload_url = generate_slide_upload_url(course, file_name, content_type, slide_id)
                    
                    response_data['files'].append({
                        'file_name': file_name,
                        'content_type': content_type,
                        'upload_url': upload_url,
                        'slide_id': slide_id
                    })
                except Exception as e:
                    LOGGER.error(f"Failed to generate upload URL for {file_name}: {str(e)}")
                    has_errors = True
                    response_data['files'].append({
                        'file_name': file_name,
                        'content_type': content_type,
                        'upload_url': None,
                        'slide_id': slide_id,
                        'error': 'Failed to generate upload URL'
                    })

            # If any upload URL generation failed, return 500
            if has_errors:
                return JsonResponse(
                    response_data,
                    status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return JsonResponse(response_data)
        else:
            return JsonResponse(
                {'error': _('Invalid data format')},
                status=rest_status.HTTP_400_BAD_REQUEST
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': _('Invalid JSON data')},
            status=rest_status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        LOGGER.error(f"Error in slides_post: {str(e)}")
        return JsonResponse(
            {'error': _('Internal server error')},
            status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_slide_status_update(course, status_data):
    """
    Handle slide status update requests
    """
    # For now, just return success
    # In production, this would update the slide status in the database
    return JsonResponse({'success': True})


def generate_slide_upload_url(course, file_name, content_type, slide_id):
    """
    Generate a presigned S3 URL for slide upload, using openedxuploads bucket as default
    """
    try:
        # Use openedxuploads bucket as default for slides
        bucket_name = 'openedxuploads'
        
        # Create slides path with course and slide organization
        slides_path = f"slides/{course.id}/{slide_id}/{file_name}"

        # Configure S3 client using the same method as video uploads
        s3_client = get_s3_client()

        # Generate presigned URL with minimal metadata to avoid encoding issues
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': slides_path,
                'ContentType': content_type,
            },
            ExpiresIn=86400,  # 24 hours
            HttpMethod='PUT'
        )

        LOGGER.info(f'Generated slide upload URL for {file_name} in bucket {bucket_name} at path {slides_path}')
        LOGGER.info(f'Presigned URL: {upload_url}')
        return upload_url

    except Exception as e:
        LOGGER.error(f"Error generating slide upload URL: {str(e)}")
        raise


def get_s3_client():
    """
    Get configured S3 client for slide uploads using the same configuration as video uploads
    """
    https_setting = getattr(settings, 'HTTPS', False)
    # Handle both boolean and string values for HTTPS setting
    if isinstance(https_setting, str):
        protocol = 'https' if https_setting.lower() not in ('off', 'false', '0') else 'http'
    else:
        protocol = 'https' if https_setting else 'http'
    
    params = {
        'endpoint_url': protocol + '://' + settings.AWS_S3_ENDPOINT_URL.replace('https://', '').replace('http://', ''),
        'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        'verify': False
    }
    s3_client = boto3.client('s3', **params)
    return s3_client


def generate_slide_public_url(course_id, slide_id, file_name):
    """
    Generate a public URL for accessing a slide file
    """
    # Use the same S3 endpoint configuration as for uploads
    https_setting = getattr(settings, 'HTTPS', False)
    if isinstance(https_setting, str):
        protocol = 'https' if https_setting.lower() not in ('off', 'false', '0') else 'http'
    else:
        protocol = 'https' if https_setting else 'http'
    
    base_url = protocol + '://' + settings.AWS_S3_ENDPOINT_URL.replace('https://', '').replace('http://', '')
    bucket_name = 'openedxuploads'
    # Encode only the file name segment to preserve directory separators
    encoded_file_name = quote(file_name)
    slides_path = f"slides/{course_id}/{slide_id}/{encoded_file_name}"
    
    return f"{base_url}/{bucket_name}/{slides_path}"


def generate_slide_signed_url(course_id, slide_id, file_name, expiration=3600):
    """
    Generate a temporary signed S3 URL for accessing a slide file
    This is needed for react-doc-viewer to access PPTX files
    
    Args:
        course_id: Course identifier
        slide_id: Slide identifier  
        file_name: Name of the slide file
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        str: Signed S3 URL for temporary access
    """
    try:
        s3_client = get_s3_client()
        bucket_name = 'openedxuploads'
        slides_path = f"slides/{course_id}/{slide_id}/{file_name}"
        
        # Generate presigned URL for GET operation with CORS-friendly parameters
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': slides_path,
                'ResponseContentDisposition': f'inline; filename="{file_name}"',
                'ResponseContentType': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            },
            ExpiresIn=expiration,
            HttpMethod='GET'
        )
        
        LOGGER.info(f'Generated signed URL for slide {slide_id} file {file_name} (expires in {expiration}s)')
        return signed_url
        
    except Exception as e:
        LOGGER.error(f"Error generating signed URL for slide: {str(e)}")
        # Fallback to public URL if signed URL generation fails
        return generate_slide_public_url(course_id, slide_id, file_name)


def get_course_slides_from_s3(course):
    """
    Get actual slides from S3 bucket for the course
    """
    try:
        s3_client = get_s3_client()
        bucket_name = 'openedxuploads'
        prefix = f"slides/{course.id}/"
        
        # List all objects in the slides folder for this course
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        slides = []
        
        if 'Contents' in response:
            # Group files by slide_id (folder structure: slides/course_id/slide_id/filename)
            slide_groups = {}
            
            for obj in response['Contents']:
                key = obj['Key']
                # Skip folder markers
                if key.endswith('/'):
                    continue
                    
                # Parse the key structure: slides/course_id/slide_id/filename
                key_parts = key.split('/')
                if len(key_parts) >= 4:
                    slide_id = key_parts[2]
                    file_name = key_parts[3]
                    
                    if slide_id not in slide_groups:
                        slide_groups[slide_id] = []
                    
                    slide_groups[slide_id].append({
                        'key': key,
                        'file_name': file_name,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat() if obj.get('LastModified') else None
                    })
            
            # Convert grouped files to slide objects
            for slide_id, files in slide_groups.items():
                # Determine primary file and URLs based on file type
                primary_file = None
                pptx_file = None
                pdf_file = None
                
                # Categorize files
                for f in files:
                    if f['file_name'].lower().endswith('.pdf'):
                        pdf_file = f
                    elif f['file_name'].lower().endswith(('.ppt', '.pptx')):
                        pptx_file = f
                
                # For PPTX files, use the original PPTX and provide signed URL
                # For PDF files, use the PDF and provide public URL
                if pptx_file:
                    primary_file = pptx_file
                    file_name = primary_file['file_name']
                    file_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    # Generate signed URL for PPTX files (needed for react-doc-viewer)
                    public_url = generate_slide_signed_url(course.id, slide_id, file_name)
                    # Also provide a viewer-specific URL for the frontend
                    viewer_url = public_url
                elif pdf_file:
                    primary_file = pdf_file
                    file_name = primary_file['file_name']
                    file_type = 'application/pdf'
                    # Use public URL for PDF files
                    public_url = generate_slide_public_url(course.id, slide_id, file_name)
                    viewer_url = public_url
                else:
                    # Fallback to first file if no PDF or PPTX found
                    primary_file = files[0]
                    file_name = primary_file['file_name']
                    file_type = 'application/pdf'  # Default assumption
                    public_url = generate_slide_public_url(course.id, slide_id, file_name)
                    viewer_url = public_url
                
                # Build base slide dict
                slide_dict = {
                    'slide_id': slide_id,
                    'display_name': file_name,  # Use filename as display name for now
                    'file_name': file_name,
                    'file_size': primary_file['size'],
                    'file_type': file_type,
                    'status': 'Ready',
                    'created_at': primary_file['last_modified'],
                    'download_link': public_url,  # Same as public URL for now
                    'public_url': public_url,
                    'url': public_url,
                    'viewer_url': viewer_url,  # Signed URL for PPTX, public URL for PDF
                    'contentType': file_type,
                    'is_pptx': file_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                }

                # Video-specific alias fields removed; frontend should use slide-specific fields now

                slides.append(slide_dict)
            LOGGER.info("Slides S3 fetch: found %d slides for course %s: %s", len(slides), course.id, [s['slide_id'] for s in slides])
        
        return slides
        
    except Exception as e:
        LOGGER.error(f"Error fetching slides from S3: {str(e)}")
        # Fall back to mock data if S3 fetch fails
        return []


def get_course_slides_context(course):
    """
    Get context data for slides page
    """
    # Try to get real slides from S3 first, fall back to mock data
    slides = get_course_slides_from_s3(course)
    
    if not slides:
        # Mock data fallback
        slide_id = 'slide-001'
        file_name = 'intro.pdf'
        public_url = generate_slide_public_url(course.id, slide_id, file_name)
        
        created_ts = datetime.now().isoformat()
        slides = [{
            'slide_id': slide_id,
            'display_name': 'Introduction Slides',
            'file_name': file_name,
            'file_size': 2048576,  # 2MB
            'file_type': 'application/pdf',
            'status': 'Ready',
            'created_at': created_ts,
            'download_link': public_url,
            'public_url': public_url,
            'url': public_url,
            'viewer_url': public_url,
            'contentType': 'application/pdf',
            'is_pptx': False,
        }]

    return {
        'course': course,
        'previous_uploads': slides,  # Template expects 'previous_uploads'
        'slides': slides,  # Keep this for backward compatibility
        'supported_file_formats': SLIDE_SUPPORTED_FILE_FORMATS,
        'max_file_size_mb': SLIDE_UPLOAD_MAX_FILE_SIZE_MB,
        'course_key_string': str(course.id),
        'slide_handler_url': f'/slides/{course.id}',
        'slide_supported_file_formats': SLIDE_SUPPORTED_FILE_FORMATS,
        'slide_upload_max_file_size': SLIDE_UPLOAD_MAX_FILE_SIZE_MB
    }