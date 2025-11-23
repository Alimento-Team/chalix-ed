"""
Custom permission classes for Chalix API endpoints.
"""
from rest_framework import permissions
from cms.djangoapps.contentstore.chalix_roles import is_bo_user


class IsBoUser(permissions.BasePermission):
    """
    Permission check for Bộ (Ministry) role.
    Allows access to users with GlobalStaff permissions or Chalix 'bo' role.
    """
    
    def has_permission(self, request, view):
        """
        Check if user has Bộ (Ministry) permissions.
        """
        return is_bo_user(request.user)
