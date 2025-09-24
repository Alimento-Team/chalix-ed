"""
Storage handlers for unit media files (videos and slides)
"""

import logging
import os
import uuid
from datetime import datetime
from urllib.parse import quote

import boto3
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import CourseKey

from .models import UnitMediaFile

LOGGER = logging.getLogger(__name__)

# File size limits (bytes)
MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024  # 500MB
MAX_SLIDE_SIZE_BYTES = 100 * 1024 * 1024   # 100MB

# Supported file formats
VIDEO_SUPPORTED_FILE_FORMATS = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.wmv': 'video/x-ms-wmv',
    '.mkv': 'video/x-matroska',
}

SLIDE_SUPPORTED_FILE_FORMATS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

def get_supported_formats(media_type):
    """Get supported file formats for a media type"""
    if media_type == 'video':
        return VIDEO_SUPPORTED_FILE_FORMATS
    elif media_type == 'slide':
        return SLIDE_SUPPORTED_FILE_FORMATS
    else:
        return {}

def get_max_file_size(media_type):
    """Get maximum file size for a media type"""
    if media_type == 'video':
        return MAX_VIDEO_SIZE_BYTES
    elif media_type == 'slide':
        return MAX_SLIDE_SIZE_BYTES
    else:
        return 0

def generate_unit_media_storage_path(unit_id, media_type, filename):
    """
    Generate storage path for unit media files.
    
    Pattern: upload/unit-media/{media_type}/{uuid}_{filename}
    (Uses same root path as video upload pipeline for compatibility)
    
    Args:
        unit_id (str): The unit identifier
        media_type (str): 'video' or 'slide'
        filename (str): Original filename
        
    Returns:
        str: Storage path
    """
    # Generate unique identifier to prevent filename conflicts
    file_uuid = str(uuid.uuid4())
    
    # Clean filename - remove spaces and special characters
    clean_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).rstrip()
    
    # Use the same root path as video upload pipeline for MinIO compatibility
    video_pipeline = getattr(settings, 'VIDEO_UPLOAD_PIPELINE', {})
    root_path = video_pipeline.get('ROOT_PATH', '')
    if root_path and not root_path.endswith('/'):
        root_path = root_path + '/'
    
    # Create storage path: upload/unit-media/video/uuid_filename.mp4
    storage_path = f"{root_path}unit-media/{media_type}/{file_uuid}_{clean_filename}"
    
    LOGGER.info(f"UNIT_MEDIA: Generated storage path: {storage_path} for unit: {unit_id}")
    
    return storage_path

def get_unit_media_storage_url(file_path):
    """
    Generate public URL for accessing uploaded unit media file.
    
    Args:
        file_path (str): Storage path of the file
        
    Returns:
        str: Public URL for the file
    """
    try:
        # Try to get URL from default storage first
        storage_url = default_storage.url(file_path)
        
        # If storage_url is a relative path, make it absolute
        if storage_url.startswith('/'):
            # Get the base URL from settings
            if hasattr(settings, 'LMS_BASE') and settings.LMS_BASE:
                base_url = settings.LMS_BASE.rstrip('/')
            else:
                # Fallback to localhost for development
                base_url = 'http://localhost:8000'
            
            storage_url = f"{base_url}{storage_url}"
        
        LOGGER.debug(f"Generated storage URL: {storage_url} for file_path: {file_path}")
        return storage_url
        
    except Exception as e:
        LOGGER.warning(f"Failed to generate storage URL for {file_path}: {str(e)}")
        
        # Fallback URL generation
        if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL:
            base_url = settings.MEDIA_URL.rstrip('/')
            fallback_url = f"{base_url}/{file_path}"
        else:
            # Last resort fallback
            fallback_url = f"http://localhost:8000/media/{file_path}"
        
        LOGGER.debug(f"Using fallback URL: {fallback_url}")
        return fallback_url

def generate_unit_media_presigned_upload_url(file_name, content_type, media_type):
    """
    Generate presigned upload URL for unit media files (similar to video upload system).
    
    Args:
        file_name (str): Name of the file
        content_type (str): MIME type of the file
        media_type (str): 'video' or 'slide'
        
    Returns:
        tuple: (upload_url, public_url, storage_key)
    """
    # Add very obvious logging to confirm this function is being called
    LOGGER.error(f"=== UNIT_MEDIA_PRESIGNED_URL_FUNCTION_CALLED === file_name: {file_name}, media_type: {media_type}")
    
    try:
        # Use the same S3 configuration as video upload pipeline
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        if not bucket_name:
            LOGGER.error("AWS_STORAGE_BUCKET_NAME not configured")
            return None, None, None
            
        # Create S3 client with same config as video system
        s3_client = boto3.client(
            's3',
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
        )
        
        # Use the same root path as video upload pipeline
        video_pipeline = getattr(settings, 'VIDEO_UPLOAD_PIPELINE', {})
        root_path = video_pipeline.get('ROOT_PATH', '')
        if root_path and not root_path.endswith('/'):
            root_path = root_path + '/'
        
        # Generate storage key using similar pattern to video system
        # Use format: {root_path}unit-media/{media_type}/{uuid}_{filename}
        # Clean filename to prevent URL encoding issues
        clean_filename = "".join(c for c in file_name if c.isalnum() or c in ('-', '_', '.')).rstrip()
        unique_filename = f"{uuid.uuid4().hex}_{clean_filename}"
        storage_key = f"{root_path}unit-media/{media_type}/{unique_filename}"
        
        LOGGER.info(f"UNIT_MEDIA: Using root_path: '{root_path}'")
        LOGGER.info(f"UNIT_MEDIA: Generated storage_key: '{storage_key}'")
        LOGGER.info(f"UNIT_MEDIA: Generating presigned URL with storage key: {storage_key}")
        LOGGER.info(f"UNIT_MEDIA: S3 client config - bucket: {bucket_name}, endpoint: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'None')}")
        
        # Generate presigned upload URL with same params as video system
        # Use the same expiration time as videos (24 hours)
        KEY_EXPIRATION_IN_SECONDS = 86400
        
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': storage_key,
                'ContentType': content_type,
            },
            ExpiresIn=KEY_EXPIRATION_IN_SECONDS,  # Same as videos (24 hours)
            HttpMethod='PUT'
        )
        
        LOGGER.info(f"UNIT_MEDIA: Generated upload_url (before public URL generation): {upload_url}")
        
        # Generate public URL using same logic as video system
        https_setting = getattr(settings, 'HTTPS', False)
        if isinstance(https_setting, str):
            protocol = 'https' if https_setting.lower() not in ('off', 'false', '0') else 'http'
        else:
            protocol = 'https' if https_setting else 'http'
            
        endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', '').replace('https://', '').replace('http://', '')
        # URL encode the storage key to handle filenames with spaces and special characters
        encoded_storage_key = quote(storage_key, safe='/')
        public_url = f"{protocol}://{endpoint_url}/{bucket_name}/{encoded_storage_key}"
        
        LOGGER.info(f"Generated presigned upload URL for {file_name}: {upload_url}")
        LOGGER.info(f"Public URL will be: {public_url}")
        
        return upload_url, public_url, storage_key
        
    except Exception as e:
        LOGGER.exception(f"Failed to generate presigned upload URL for {file_name}: {str(e)}")
        return None, None, None

def validate_unit_media_file(uploaded_file, media_type):
    """
    Validate uploaded unit media file.
    
    Args:
        uploaded_file: Django UploadedFile instance
        media_type (str): 'video' or 'slide'
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not uploaded_file:
        return False, _("No file provided")
    
    # Check file size
    max_size = get_max_file_size(media_type)
    if uploaded_file.size > max_size:
        max_size_mb = max_size // (1024 * 1024)
        return False, _(f"File size exceeds maximum allowed size of {max_size_mb}MB")
    
    # Check file extension
    filename = uploaded_file.name.lower()
    if '.' not in filename:
        return False, _("File must have a valid extension")
    
    extension = '.' + filename.split('.')[-1]
    supported_formats = get_supported_formats(media_type)
    
    if extension not in supported_formats:
        allowed_extensions = ', '.join(supported_formats.keys())
        return False, _(f"File type not supported. Allowed types: {allowed_extensions}")
    
    return True, None

def save_unit_media_file(uploaded_file, unit_id, course_id, media_type, user=None, display_name=None):
    """
    Save uploaded unit media file to storage and database.
    
    Args:
        uploaded_file: Django UploadedFile instance
        unit_id (str): Unit identifier
        course_id (str): Course identifier  
        media_type (str): 'video' or 'slide'
        user: User who uploaded the file
        display_name (str): Optional display name
        
    Returns:
        tuple: (UnitMediaFile instance, error_message)
    """
    try:
        # Validate file
        is_valid, error_msg = validate_unit_media_file(uploaded_file, media_type)
        if not is_valid:
            return None, error_msg
        
        # Generate storage path
        file_path = generate_unit_media_storage_path(unit_id, media_type, uploaded_file.name)
        
        # Save file to storage
        saved_path = default_storage.save(file_path, uploaded_file)
        
        # Generate public URL
        upload_url = get_unit_media_storage_url(saved_path)
        LOGGER.debug(f"Generated upload_url: {upload_url} for saved_path: {saved_path}")
        LOGGER.info(f"Upload URL length: {len(upload_url)} characters - URL: {upload_url}")
        
        # Validate the upload_url before saving
        if not upload_url or len(upload_url.strip()) == 0:
            LOGGER.error(f"Empty upload_url generated for saved_path: {saved_path}")
            return None, _("Failed to generate file URL. Please try again.")
        
        # Check URL length
        if len(upload_url) > 500:
            LOGGER.error(f"Generated URL too long ({len(upload_url)} chars): {upload_url}")
            return None, _("Generated file URL is too long. Please try a shorter filename.")
        
        # Get file content type
        extension = '.' + uploaded_file.name.lower().split('.')[-1]
        supported_formats = get_supported_formats(media_type)
        file_type = supported_formats.get(extension, uploaded_file.content_type)
        
        # Check if file already exists and handle accordingly
        try:
            existing_file = UnitMediaFile.objects.get(
                unit_id=unit_id,
                file_name=uploaded_file.name,
                media_type=media_type
            )
            # Update existing file
            existing_file.display_name = display_name or uploaded_file.name
            existing_file.file_size = uploaded_file.size
            if file_type:
                existing_file.file_type = file_type
            existing_file.file_path = saved_path
            existing_file.upload_url = upload_url
            existing_file.uploaded_by = user
            existing_file.updated_at = timezone.now()
            existing_file.save(update_fields=[
                'display_name', 'file_size', 'file_type', 'file_path', 
                'upload_url', 'uploaded_by', 'updated_at'
            ])
            media_file = existing_file
        except UnitMediaFile.DoesNotExist:
            # Create new database record
            media_file = UnitMediaFile(
                unit_id=unit_id,
                course_id=CourseKey.from_string(course_id) if isinstance(course_id, str) else course_id,
                media_type=media_type,
                file_name=uploaded_file.name,
                display_name=display_name or uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=file_type or uploaded_file.content_type,
                file_path=saved_path,
                upload_url=upload_url,
                uploaded_by=user
            )
            media_file.save()
        
        return media_file, None
        
    except Exception as e:
        LOGGER.exception(f"Error saving unit media file: {str(e)}")
        return None, _("Failed to save file. Please try again.")

def delete_unit_media_file(media_file):
    """
    Delete unit media file from storage and database.
    
    Args:
        media_file (UnitMediaFile): Media file instance to delete
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Delete file from storage
        if media_file.file_path and default_storage.exists(media_file.file_path):
            default_storage.delete(media_file.file_path)
        
        # Delete database record
        media_file.delete()
        
        return True, None
        
    except Exception as e:
        LOGGER.exception(f"Error deleting unit media file: {str(e)}")
        return False, _("Failed to delete file. Please try again.")

def get_unit_media_context(unit_id, media_type=None):
    """
    Get context data for unit media management.
    
    Args:
        unit_id (str): Unit identifier
        media_type (str): Optional media type filter
        
    Returns:
        dict: Context data for unit media
    """
    # Get existing media files
    media_files = UnitMediaFile.get_unit_media(unit_id, media_type)
    
    # Calculate statistics
    total_files = media_files.count()
    total_videos = media_files.filter(media_type='video').count()
    total_slides = media_files.filter(media_type='slide').count()
    total_size = sum(f.file_size for f in media_files)
    
    context = {
        'unit_id': unit_id,
        'media_files': media_files,
        'total_files': total_files,
        'total_videos': total_videos,
        'total_slides': total_slides,
        'total_size_bytes': total_size,
        'formatted_total_size': format_file_size(total_size),
        'supported_formats': {
            'video': VIDEO_SUPPORTED_FILE_FORMATS,
            'slide': SLIDE_SUPPORTED_FILE_FORMATS,
        },
        'max_file_sizes': {
            'video': MAX_VIDEO_SIZE_BYTES,
            'slide': MAX_SLIDE_SIZE_BYTES,
        },
        'max_file_sizes_mb': {
            'video': MAX_VIDEO_SIZE_BYTES // (1024 * 1024),
            'slide': MAX_SLIDE_SIZE_BYTES // (1024 * 1024),
        }
    }
    
    return context

def format_file_size(size_bytes):
    """
    Format file size in human readable format.
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Formatted file size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"