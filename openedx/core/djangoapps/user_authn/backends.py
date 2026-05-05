"""
Custom authentication backend for Chalix that supports login with email or phone number.
"""

import logging
import re
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from common.djangoapps.student.models import UserProfile

logger = logging.getLogger(__name__)


class EmailOrPhoneBackend(ModelBackend):
    """
    Authentication backend that accepts both email and phone number as login identifier.
    
    Features:
    - Accepts email (standard) or phone number (new)
    - Normalizes phone numbers (+84, 0 prefix variations)
    - Falls back to parent class for password validation
    - Only authenticates active users
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email or phone number + password.
        
        Args:
            request: HTTP request object
            username: Can be email, phone number, or actual username
            password: User's password
            
        Returns:
            User object if authenticated, None otherwise
        """
        if not username or not password:
            return None
        
        user = None
        
        # Try different lookups to find the user
        user = self._lookup_user(username)
        
        if user is not None and self.user_can_authenticate(user):
            if user.check_password(password):
                return user
        
        return None
    
    def _lookup_user(self, identifier):
        """
        Look up user by email, phone, or username.
        
        Args:
            identifier: Can be email, phone, or username
            
        Returns:
            User object or None
        """
        # Try direct username lookup first
        try:
            return User.objects.get(username=identifier, is_active=True)
        except User.DoesNotExist:
            pass
        
        # Try email lookup
        try:
            return User.objects.get(email=identifier, is_active=True)
        except User.DoesNotExist:
            pass
        
        # Try phone number lookup with normalization
        normalized_phone = self._normalize_phone(identifier)
        if normalized_phone:
            try:
                profile = UserProfile.objects.get(phone_number=normalized_phone)
                if profile.user.is_active:
                    return profile.user
            except UserProfile.DoesNotExist:
                pass
        
        return None
    
    def _normalize_phone(self, phone_input):
        """
        Normalize phone number to standard format.
        
        Supports:
        - Standard: 0123456789
        - With +84: +84123456789
        - With space/dash: 01 2345 6789
        
        Args:
            phone_input: Raw phone input from user
            
        Returns:
            Normalized phone number or None if invalid
        """
        if not phone_input:
            return None
        
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-]', '', phone_input)
        
        # Vietnamese phone numbers start with:
        # 0 followed by digits (local)
        # +84 followed by digits (international)
        # 84 followed by digits (international without +)
        
        if cleaned.startswith('+84'):
            # +84xxxxxxxxx -> 0xxxxxxxxx
            normalized = '0' + cleaned[3:]
        elif cleaned.startswith('84'):
            # 84xxxxxxxxx -> 0xxxxxxxxx
            normalized = '0' + cleaned[2:]
        elif cleaned.startswith('0'):
            # Already normalized
            normalized = cleaned
        else:
            # Invalid format
            return None
        
        # Validate: 10 digits starting with 0
        if re.match(r'^0\d{9}$', normalized):
            return normalized
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID (required by Django auth backend).
        
        Args:
            user_id: User's primary key
            
        Returns:
            User object or None
        """
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None
