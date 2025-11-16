"""
API views for user popup data endpoints.
"""

import logging

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthentication

from .user_popup_serializers import UserPopupSerializer

log = logging.getLogger(__name__)
User = get_user_model()


class UserPopupView(APIView):
    """
    API endpoint for retrieving user popup data.
    
    This view provides user information needed for displaying user popups
    in headers and navigation menus across CMS and LMS.
    
    Authenticated users can retrieve their own profile data.
    """
    
    authentication_classes = [
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
        BearerAuthentication,
    ]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current user's popup data.
        
        Returns:
            Response with user popup data or 404 if user not found.
        """
        try:
            user = request.user
            if not user.is_authenticated:
                return Response(
                    {'detail': 'Not authenticated'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            serializer = UserPopupSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            log.error(f"Error in UserPopupView.get: {str(e)}")
            return Response(
                {'detail': 'Error retrieving user data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserPopupByUsernameView(APIView):
    """
    API endpoint for retrieving user popup data by username.
    
    This view allows retrieving public user information for display purposes.
    Note: Returns only public profile information.
    """
    
    authentication_classes = [
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
        BearerAuthentication,
    ]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, username):
        """
        Get user popup data by username.
        
        Args:
            username: The username to retrieve
            
        Returns:
            Response with user popup data or 404 if user not found.
        """
        try:
            user = get_object_or_404(User, username=username)
            serializer = UserPopupSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            log.error(f"Error in UserPopupByUsernameView.get: {str(e)}")
            return Response(
                {'detail': 'Error retrieving user data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
