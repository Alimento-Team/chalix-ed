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
        'cong_chuc': 0,    # Learner/Student level (multiple accounts)
        'giang_vien': 1,   # Teacher/Instructor level (multiple accounts)
        'co_quan': 2,      # Organization level (multiple accounts)
        'bo': 3,           # Department level (single account)
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
    """Check if user can create other accounts (bo and co_quan roles)"""
    if not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role in ['bo', 'co_quan']


def is_bo_user(user: User) -> bool:
    """
    Check if user has Bộ (Ministry) role permissions.
    Returns True if user is GlobalStaff or has Chalix 'bo' role.
    
    This is the centralized function for checking 'bo' role across the CMS.
    Use this instead of inline checks to ensure consistency.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user has 'bo' role or is GlobalStaff
    """
    if not user or not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role == 'bo'


def is_co_quan_user(user: User) -> bool:
    """
    Check if user has Cơ quan (Organization) role permissions.
    Returns True if user is GlobalStaff or has Chalix 'co_quan' role.
    
    This is the centralized function for checking 'co_quan' role across the CMS.
    Use this instead of inline checks to ensure consistency.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user has 'co_quan' role or is GlobalStaff
    """
    if not user or not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role == 'co_quan'


def is_giang_vien_user(user: User) -> bool:
    """
    Check if user has Giảng viên (Teacher/Instructor) role permissions.
    Returns True if user is GlobalStaff or has Chalix 'giang_vien' role.
    
    This is the centralized function for checking 'giang_vien' role across the CMS.
    Use this instead of inline checks to ensure consistency.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user has 'giang_vien' role or is GlobalStaff
    """
    if not user or not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role == 'giang_vien'


def is_cong_chuc_user(user: User) -> bool:
    """
    Check if user has Công chức (Learner/Student) role permissions.
    Returns True if user has Chalix 'cong_chuc' role.
    Note: GlobalStaff does NOT automatically have cong_chuc role.
    
    This is the centralized function for checking 'cong_chuc' role across the CMS.
    Use this instead of inline checks to ensure consistency.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user has 'cong_chuc' role
    """
    if not user or not user.is_authenticated:
        return False
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role == 'cong_chuc'


def can_import_users(user: User) -> bool:
    """Check if user can import users via Excel (bo and co_quan roles)"""
    return is_bo_user(user) or is_co_quan_user(user)


def can_manage_courses(user: User) -> bool:
    """Check if user can create and manage courses (giang_vien, co_quan, bo roles)"""
    if not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    return primary_role is not None and primary_role.role in ['giang_vien', 'co_quan', 'bo']


def can_edit_course(user: User, course_id=None) -> bool:
    """
    Check if user can edit a specific course.
    Only users with 'co_quan' or 'giang_vien' roles can edit courses.
    
    Args:
        user: The user to check
        course_id: Optional course ID to check specific course permissions
        
    Returns:
        bool: True if user can edit courses (or the specific course if course_id provided)
    """
    if not user.is_authenticated:
        return False
        
    if GlobalStaff().has_user(user):
        return True
    
    primary_role = get_user_primary_role(user)
    if not primary_role:
        return False
    
    # Only co_quan and giang_vien can edit courses
    if primary_role.role not in ['co_quan', 'giang_vien']:
        return False
    
    # If no specific course_id provided, just check role
    if course_id is None:
        return True
    
    # Check if user has staff/instructor access to the specific course
    from common.djangoapps.student.models import CourseAccessRole
    has_course_access = CourseAccessRole.objects.filter(
        user=user,
        course_id=course_id,
        role__in=['staff', 'instructor']
    ).exists()
    
    return has_course_access


def require_course_edit_permission(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    View decorator to require course edit permission.
    Only allows users with 'co_quan' or 'giang_vien' roles to access the view.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        
        # Extract course_id from kwargs or request if available
        course_id = kwargs.get('course_key_string') or kwargs.get('course_id')
        
        if not can_edit_course(user, course_id):
            raise PermissionDenied(
                "Only instructors and organization administrators can edit courses. "
                "Learner accounts (cong_chuc) and ministry accounts (bo) cannot edit courses."
            )
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def enforce_single_bo_account(user: User, role: str, organization: ChalixOrganization = None, exclude_instance=None):
    """Enforce that only one 'bo' (department) account can exist
    
    Args:
        user: The user being assigned the role
        role: The role being assigned
        organization: Optional organization
        exclude_instance: Optional ChalixUserRole instance to exclude from the check (for edits)
    """
    if role == 'bo':
        queryset = ChalixUserRole.objects.filter(role='bo', is_active=True)
        
        # Exclude the current instance if editing
        if exclude_instance and exclude_instance.pk:
            queryset = queryset.exclude(pk=exclude_instance.pk)
        
        existing_bo = queryset.first()
        if existing_bo and existing_bo.user != user:
            raise PermissionDenied("Only one department account (bo) is allowed in the system")


def get_role_constraints():
    """Get constraints for each role type"""
    return {
        'bo': {
            'max_accounts': 1,
            'description': 'Department level - single account only',
            'can_create_accounts': True,
            'can_manage_courses': True,
            'cms_access': True
        },
        'co_quan': {
            'max_accounts': None,  # Unlimited
            'description': 'Organization level - multiple accounts allowed',
            'can_create_accounts': True,
            'can_manage_courses': True,
            'cms_access': True
        },
        'giang_vien': {
            'max_accounts': None,  # Unlimited
            'description': 'Teacher/Instructor level - multiple accounts allowed',
            'can_create_accounts': False,
            'can_manage_courses': True,
            'cms_access': True
        },
        'cong_chuc': {
            'max_accounts': None,  # Unlimited
            'description': 'Learner/Student level - multiple accounts allowed',
            'can_create_accounts': False,
            'can_manage_courses': False,
            'cms_access': False
        }
    }


def get_user_organization_display_name(user: User) -> str:
    """Get the display name for user's organization for header display"""
    organization = get_user_organization(user)
    if organization:
        return organization.display_name


def assign_role_to_user(user: User, role: str, organization: ChalixOrganization = None, created_by: User = None) -> ChalixUserRole:
    """Assign a Chalix role to a user with proper constraints"""
    # Enforce single bo account constraint
    enforce_single_bo_account(user, role, organization)
    
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
