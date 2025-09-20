"""
API Serializers for slides
"""
from rest_framework import serializers

from cms.djangoapps.contentstore.rest_api.serializers.common import StrictSerializer


class SlideFileSpecSerializer(StrictSerializer):
    """ Strict Serializer for slide file specs """
    file_name = serializers.CharField()
    content_type = serializers.ChoiceField(choices=[
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-powerpoint'
    ])


class SlideModelSerializer(serializers.Serializer):
    """Serializer for a slide"""
    slide_id = serializers.CharField()
    display_name = serializers.CharField()
    file_name = serializers.CharField()
    file_size = serializers.IntegerField()
    file_type = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.CharField()
    download_link = serializers.CharField()
    public_url = serializers.CharField()
    url = serializers.CharField()
    contentType = serializers.CharField()


class CourseSlidesSerializer(serializers.Serializer):
    """Serializer for course slides"""
    slide_handler_url = serializers.CharField()
    previous_uploads = SlideModelSerializer(many=True, required=False)
    slides = SlideModelSerializer(many=True, required=False)
    supported_file_formats = serializers.DictField(
        child=serializers.CharField()
    )
    max_file_size_mb = serializers.IntegerField()
    course_key_string = serializers.CharField()
    slide_supported_file_formats = serializers.DictField(
        child=serializers.CharField()
    )
    slide_upload_max_file_size = serializers.IntegerField()


class SlideUploadSerializer(StrictSerializer):
    """
    Strict Serializer for slide upload urls.
    Note that these are not actual slide uploads but endpoints to generate an upload url for S3
    and generating a slide placeholder without performing an actual upload.
    """
    files = serializers.ListField(
        child=SlideFileSpecSerializer()
    )


class SlideUsageSerializer(serializers.Serializer):
    """Serializer for slide usage"""
    usage_locations = serializers.ListField(
        child=serializers.DictField()
    )


class SlideDownloadSerializer(serializers.Serializer):
    """Serializer for slide downloads"""
    files = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )