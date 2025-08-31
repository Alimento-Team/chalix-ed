"""
Simplified Outline Tab Serializers for the new course structure.
"""

from rest_framework import serializers


class UnitContentMetadataSerializer(serializers.Serializer):
    """
    Serializer for unit content metadata
    """
    video_count = serializers.IntegerField(required=False)
    slide_count = serializers.IntegerField(required=False)
    question_count = serializers.IntegerField(required=False)
    duration_estimate = serializers.CharField(required=False)
    subtitle = serializers.CharField(required=False)


class SimplifiedUnitSerializer(serializers.Serializer):
    """
    Serializer for simplified unit objects
    """
    id = serializers.CharField()
    title = serializers.CharField()
    content_type = serializers.ChoiceField(choices=['video', 'slide', 'questions'])
    content_metadata = UnitContentMetadataSerializer()
    complete = serializers.BooleanField()


class CourseInfoSerializer(serializers.Serializer):
    """
    Serializer for course information
    """
    title = serializers.CharField()
    instructor_name = serializers.CharField()
    total_units = serializers.IntegerField()
    completed_units = serializers.IntegerField()
    progress_percentage = serializers.FloatField()


class SimplifiedOutlineTabSerializer(serializers.Serializer):
    """
    Serializer for the Simplified Outline Tab
    """
    course_info = CourseInfoSerializer()
    units = SimplifiedUnitSerializer(many=True)
