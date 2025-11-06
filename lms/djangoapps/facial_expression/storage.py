"""
Storage utilities for facial expression videos using MinIO.
"""
import os
import logging
from datetime import datetime
from django.conf import settings
from openedx.core.storage import get_storage

logger = logging.getLogger(__name__)


class FacialExpressionStorage:
    """Handle storage operations for facial expression videos."""

    def __init__(self):
        """Initialize storage backend."""
        self.storage = get_storage(
            storage_class=getattr(
                settings,
                'FACIAL_EXPRESSION_STORAGE_CLASS',
                'storages.backends.s3boto3.S3Boto3Storage'
            ),
            **self._get_storage_kwargs()
        )

    def _get_storage_kwargs(self):
        """Get storage configuration kwargs."""
        return {
            'bucket_name': getattr(settings, 'FACIAL_EXPRESSION_STORAGE_BUCKET', 'facial-expressions'),
            'location': getattr(settings, 'FACIAL_EXPRESSION_STORAGE_ROOT', 'facial_expressions/'),
            'access_key': getattr(settings, 'FACIAL_EXPRESSION_STORAGE_ACCESS_KEY', None),
            'secret_key': getattr(settings, 'FACIAL_EXPRESSION_STORAGE_SECRET_KEY', None),
            'endpoint_url': getattr(settings, 'FACIAL_EXPRESSION_STORAGE_ENDPOINT', None),
            'custom_domain': False,
            'file_overwrite': False,
        }

    def generate_video_path(self, user_id, course_id, unit_id, timestamp=None):
        """
        Generate a unique path for storing facial expression video.
        
        Format: facial_expressions/{course_id}/{user_id}/{unit_id}/{timestamp}.webm
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        date_path = timestamp.strftime('%Y/%m/%d')
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{timestamp.microsecond}.webm"
        
        path = os.path.join(
            'facial_expressions',
            self._sanitize_path_component(course_id),
            str(user_id),
            self._sanitize_path_component(unit_id),
            date_path,
            filename
        )
        
        return path

    def _sanitize_path_component(self, component):
        """Sanitize path component to be filesystem-safe."""
        return component.replace('/', '_').replace('\\', '_').replace(':', '_')

    def save_video(self, video_file, path):
        """
        Save video file to storage.
        
        Args:
            video_file: File object or file-like object
            path: Destination path in storage
            
        Returns:
            str: The path where the file was saved
        """
        try:
            saved_path = self.storage.save(path, video_file)
            logger.info(f"Saved facial expression video to: {saved_path}")
            return saved_path
        except Exception as e:
            logger.error(f"Error saving facial expression video: {e}")
            raise

    def get_video_url(self, path, expiry=3600):
        """
        Get a presigned URL for accessing the video.
        
        Args:
            path: Path to the video in storage
            expiry: URL expiry time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            if hasattr(self.storage, 'url'):
                return self.storage.url(path)
            return None
        except Exception as e:
            logger.error(f"Error generating video URL: {e}")
            return None

    def delete_video(self, path):
        """
        Delete a video from storage.
        
        Args:
            path: Path to the video in storage
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.storage.delete(path)
            logger.info(f"Deleted facial expression video: {path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting facial expression video: {e}")
            return False

    def video_exists(self, path):
        """
        Check if a video exists in storage.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if exists
        """
        try:
            return self.storage.exists(path)
        except Exception as e:
            logger.error(f"Error checking video existence: {e}")
            return False


# Singleton instance
_storage_instance = None


def get_facial_expression_storage():
    """Get or create storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FacialExpressionStorage()
    return _storage_instance
