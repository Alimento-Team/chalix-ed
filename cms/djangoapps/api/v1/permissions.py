"""
Custom permission classes for Chalix API endpoints.
"""
from rest_framework import permissions
from cms.djangoapps.contentstore.chalix_roles import get_user_primary_role
from common.djangoapps.student.roles import GlobalStaff


class IsBoUser(permissions.BasePermission):
    """
    Permission check for Bộ (Ministry) role.
    Allows access to users with GlobalStaff permissions or Chalix 'bo' role.
    """
    
    def has_permission(self, request, view):
        """
        Check if user has Bộ (Ministry) permissions.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is GlobalStaff (Django superuser/staff)
        if GlobalStaff().has_user(request.user):
            return True
        
        # Check if user has Chalix 'bo' role
        primary_role = get_user_primary_role(request.user)
        return primary_role and primary_role.role == 'bo'
