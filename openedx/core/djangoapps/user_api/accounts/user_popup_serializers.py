"""
Serializers for user popup API endpoints.
"""

from rest_framework import serializers
from common.djangoapps.student.models import User, UserProfile


class UserPopupSerializer(serializers.Serializer):
    """
    Serializer for user popup data used in header and navigation.
    Provides lightweight user information for the popup menu.
    """
    
    user_id = serializers.IntegerField(source='id', read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    
    def get_full_name(self, obj):
        """Get user's full name from first and last name."""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    
    def get_profile_image_url(self, obj):
        """Get user's profile image URL (with absolute URL if request is available)."""
        try:
            if hasattr(obj, 'profile') and obj.profile:
                from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user
                # Get request from context for absolute URLs
                request = self.context.get('request')
                image_urls = get_profile_image_urls_for_user(obj, request=request)
                if image_urls:
                    return image_urls.get('full', image_urls.get('medium'))
        except Exception:
            pass
        return None
    
    def get_bio(self, obj):
        """Get user's bio from profile."""
        try:
            if hasattr(obj, 'profile') and obj.profile:
                return obj.profile.bio or None
        except Exception:
            pass
        return None
