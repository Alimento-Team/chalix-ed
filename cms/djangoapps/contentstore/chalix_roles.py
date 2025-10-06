"""
Chalix role management utilities and permission checking functions.
Integrates with OpenEdX's existing role system while adding custom organization-based roles.
"""

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from typing import Optional, List, Callable, Any
from functools import wraps

from cms.djangoapps.contentstore.models import ChalixUserRole, ChalixOrganization
from common.djangoapps.student.roles import (
    GlobalStaff,
    CourseStaffRole,
    CourseInstructorRole,
    OrgStaffRole,
    OrgInstructorRole
)


def get_user_chalix_roles(user: User) -> List[ChalixUserRole]:
    """Get all active Chalix roles for a user"""
    if not user.is_authenticated:
        return []
    
    return ChalixUserRole.objects.filter(
        user=user,
        is_active=True
    ).select_related('organization')


def get_user_primary_role(user: User) -> Optional[ChalixUserRole]:
    """Get the user's primary/highest priority role"""
    roles = get_user_chalix_roles(user)
    if not roles:
        return None
    
    # Role hierarchy (higher index = higher priority)
    role_priority = {
        'cong_chuc': 0,
        'giang_vien': 1, 
        'bo': 2,
        'co_quan': 3,
    }
    
    return max(roles, key=lambda r: role_priority.get(r.role, 0))


def get_user_organization(user: User) -> Optional[ChalixOrganization]:
    """Get the user's organization based on their primary role"""
    primary_role = get_user_primary_role(user)
    return primary_role.organization if primary_role else None


def can_access_cms(user: User) -> bool:
    """Check if user can access the CMS dashboard"""
    if not user.is_authenticated:
        return False
    
    # Global staff always has access
    if GlobalStaff().has_user(user):
        return True
        
    # Check Chalix roles
    primary_role = get_user_primary_role(user)
    if primary_role:
        return primary_role.can_access_cms
    
    # Fallback to OpenEdX roles - allow staff/instructor access
    # Check if user has any course staff/instructor role
    from common.djangoapps.student.models import CourseAccessRole
    has_course_role = CourseAccessRole.objects.filter(
        user=user,
        role__in=['staff', 'instructor']
    ).exists()
    
    return has_course_role


def get_available_tabs(user: User) -> List[str]:
    """Get list of tabs available to the user based on their role"""
    if not user.is_authenticated:
        return []
    
    # Global staff sees all tabs
    if GlobalStaff().has_user(user):
        return ['statistics', 'create-account', 'management', 'learning-management', 'approve-requests']
    
    primary_role = get_user_primary_role(user)
    if primary_role:
        return primary_role.available_tabs
    
    # Default fallback for users without Chalix roles but with OpenEdX roles
    if can_access_cms(user):
        return ['statistics', 'learning-management']
    
    return []


def require_cms_access(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """View decorator to require CMS access.

    When applied to a Django view, it verifies that request.user can access the
    CMS by calling :pyfunc:`can_access_cms`. If the check fails, a
    :class:`PermissionDenied` is raised. This function intentionally accepts and
    returns a view callable so it can be used as ``@require_cms_access``.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if not user or not can_access_cms(user):
            raise PermissionDenied("User does not have permission to access CMS")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def require_role(user: User, required_roles: List[str]):
    """Require user to have one of the specified Chalix roles"""
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required")
    
    if GlobalStaff().has_user(user):
        return  # Global staff bypasses role checks
    
    user_roles = get_user_chalix_roles(user)
    user_role_names = [r.role for r in user_roles]
    
    if not any(role in required_roles for role in user_role_names):
        raise PermissionDenied(f"User must have one of these roles: {', '.join(required_roles)}")


def can_create_accounts(user: User) -> bool:
    """Check if user can create other accounts (co_quan role)"""
    if not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role and primary_role.role in ['co_quan', 'bo']


def can_manage_courses(user: User) -> bool:
    """Check if user can manage courses (giang_vien, co_quan roles)"""
    if not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role and primary_role.role in ['giang_vien', 'co_quan']


def get_user_organization_display_name(user: User) -> str:
    """Get the display name for user's organization for header display"""
    organization = get_user_organization(user)
    if organization:
        return organization.display_name
    
    # Fallback to default
    return "CỤC HÀNG HẢI VÀ ĐƯỜNG THỦY NỘI ĐỊA VIỆT NAM"


def assign_role_to_user(user: User, role: str, organization: ChalixOrganization = None, created_by: User = None) -> ChalixUserRole:
    """Assign a Chalix role to a user"""
    chalix_role, created = ChalixUserRole.objects.get_or_create(
        user=user,
        role=role,
        organization=organization,
        defaults={
            'is_active': True,
            'created_by': created_by
        }
    )
    
    if not created and not chalix_role.is_active:
        chalix_role.is_active = True
        chalix_role.save()
    
    return chalix_role


def remove_role_from_user(user: User, role: str, organization: ChalixOrganization = None):
    """Remove a Chalix role from a user"""
    try:
        chalix_role = ChalixUserRole.objects.get(
            user=user,
            role=role,
            organization=organization
        )
        chalix_role.is_active = False
        chalix_role.save()
    except ChalixUserRole.DoesNotExist:
        pass  # Role didn't exist anyway
