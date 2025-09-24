"""
API Serializers for unit media files
"""
from rest_framework import serializers
from cms.djangoapps.contentstore.rest_api.serializers.common import StrictSerializer
from cms.djangoapps.contentstore.models import UnitMediaFile


class UnitMediaFileSerializer(serializers.ModelSerializer):
    """Serializer for UnitMediaFile model"""
    
    # Read-only computed fields
    file_extension = serializers.CharField(read_only=True)
    formatted_file_size = serializers.CharField(read_only=True)
    is_video = serializers.BooleanField(read_only=True)
    is_slide = serializers.BooleanField(read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = UnitMediaFile
        fields = [
            'id',
            'unit_id',
            'course_id',
            'media_type',
            'file_name',
            'display_name',
            'file_size',
            'formatted_file_size',
            'file_type',
            'file_path',
            'upload_url',
            'file_extension',
            'is_video',
            'is_slide',
            'uploaded_by',
            'uploaded_by_username',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'file_path',
            'upload_url',
            'uploaded_by',
            'created_at',
            'updated_at'
        ]


class UnitMediaFileListSerializer(serializers.Serializer):
    """Serializer for listing unit media files"""
    count = serializers.IntegerField()
    results = UnitMediaFileSerializer(many=True)
    unit_id = serializers.CharField()
    media_type = serializers.CharField()


class UnitMediaFileUploadSerializer(StrictSerializer):
    """Serializer for media file uploads"""
    
    file = serializers.FileField(
        help_text="The media file to upload"
    )
    
    display_name = serializers.CharField(
        required=False,
        max_length=255,
        help_text="Optional display name for the file"
    )
    
    def validate_file(self, value):
        """Validate uploaded file based on media type and size limits"""
        # Get media type from context (set by the view)
        media_type = self.context.get('media_type')
        
        if not media_type:
            raise serializers.ValidationError("Media type must be specified")
        
        # Define file size limits (in bytes)
        MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
        MAX_SLIDE_SIZE = 100 * 1024 * 1024  # 100MB
        
        # Define allowed extensions
        VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'wmv', 'mkv']
        SLIDE_EXTENSIONS = ['pdf', 'pptx', 'ppt']
        
        # Get file extension
        file_name = value.name.lower()
        if '.' not in file_name:
            raise serializers.ValidationError("File must have a valid extension")
        
        extension = file_name.split('.')[-1]
        
        # Validate based on media type
        if media_type == 'video':
            if extension not in VIDEO_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Video files must have one of these extensions: {', '.join(VIDEO_EXTENSIONS)}"
                )
            if value.size > MAX_VIDEO_SIZE:
                raise serializers.ValidationError(
                    f"Video files must be smaller than {MAX_VIDEO_SIZE // (1024*1024)}MB"
                )
        elif media_type == 'slide':
            if extension not in SLIDE_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Slide files must have one of these extensions: {', '.join(SLIDE_EXTENSIONS)}"
                )
            if value.size > MAX_SLIDE_SIZE:
                raise serializers.ValidationError(
                    f"Slide files must be smaller than {MAX_SLIDE_SIZE // (1024*1024)}MB"
                )
        else:
            raise serializers.ValidationError("Invalid media type")
        
        return value
    
    def validate(self, attrs):
        """Additional validation"""
        # Set display_name to filename if not provided
        if not attrs.get('display_name'):
            attrs['display_name'] = attrs['file'].name
        
        return attrs


class UnitMediaErrorSerializer(serializers.Serializer):
    """Serializer for API errors"""
    error = serializers.CharField()
    details = serializers.DictField(required=False)


class UnitMediaFileStatsSerializer(serializers.Serializer):
    """Serializer for media file statistics"""
    unit_id = serializers.CharField()
    total_files = serializers.IntegerField()
    total_videos = serializers.IntegerField()
    total_slides = serializers.IntegerField()
    total_size_bytes = serializers.IntegerField()
    formatted_total_size = serializers.CharField()


class UnitMediaPresignedUrlSerializer(serializers.Serializer):
    """
    Serializer for presigned URL requests.
    """
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    
    def validate_file_name(self, value):
        """
        Validate the file name and extension.
        """
        if not value:
            raise serializers.ValidationError("File name is required")
        
        # Get media type from context
        media_type = self.context.get('media_type', '')
        
        # Define allowed extensions based on media type
        if media_type == 'video':
            allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        elif media_type == 'slide':
            allowed_extensions = ['.pdf', '.docx']
        else:
            raise serializers.ValidationError("Invalid media type")
        
        # Check file extension
        file_name = value.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"File type not supported for {media_type}. "
                f"Allowed extensions: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate_content_type(self, value):
        """
        Validate the content type.
        """
        if not value:
            raise serializers.ValidationError("Content type is required")
        
        # Get media type from context
        media_type = self.context.get('media_type', '')
        
        # Define allowed content types based on media type
        if media_type == 'video':
            allowed_types = [
                'video/mp4', 'video/avi', 'video/quicktime', 'video/x-ms-wmv',
                'video/x-flv', 'video/webm', 'video/x-matroska'
            ]
        elif media_type == 'slide':
            allowed_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
        else:
            raise serializers.ValidationError("Invalid media type")
        
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Content type '{value}' not supported for {media_type}"
            )
        
        return value


class UnitMediaPresignedUrlListSerializer(serializers.Serializer):
    """
    Serializer for multiple presigned URL requests.
    """
    files = UnitMediaPresignedUrlSerializer(many=True)