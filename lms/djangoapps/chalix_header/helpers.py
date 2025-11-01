"""
Helper functions for the Chalix Header Module
"""

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_header_context(request):
    """
    Get the complete context needed for rendering the Chalix header.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Context dictionary with all header data
    """
    user = request.user
    
    # User information
    user_context = {
        'is_authenticated': user.is_authenticated,
        'username': user.username if user.is_authenticated else None,
        'full_name': user.get_full_name() if user.is_authenticated else None,
        'email': user.email if user.is_authenticated else None,
    }
    
    if user.is_authenticated and hasattr(user, 'profile'):
        profile = user.profile
        user_context.update({
            'profile_image_url': profile.profile_image_url,
            'has_profile_image': profile.profile_image_uploaded_at is not None,
        })
    else:
        user_context.update({
            'profile_image_url': None,
            'has_profile_image': False,
        })
    
    # Organization information
    org_context = {
        'name': configuration_helpers.get_value(
            'ORG_NAME', 
            'PHẦN MỀM HỌC TẬP THÔNG MINH DÀNH CHO CÔNG CHỨC, VIÊN CHỨC'
        ),
        'department': configuration_helpers.get_value('ORG_DEPARTMENT', ''),
        'label': configuration_helpers.get_value('ORG_LABEL', 'Cơ Quan 1'),
    }
    
    # Platform information
    platform_context = {
        'name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'site_name': configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
    }
    
    # URLs
    urls_context = {
        'lms_base': settings.LMS_ROOT_URL,
        'dashboard': reverse('dashboard'),
        'courses': reverse('courses'),
        'logout': reverse('logout'),
        'login': reverse('signin_user'),
        'register': reverse('register_user') if 'register_user' in [url.name for url in settings.ROOT_URLCONF] else None,
        'help': reverse('help') if 'help' in [url.name for url in settings.ROOT_URLCONF] else f"{settings.LMS_ROOT_URL}/help",
        'notifications': f"{settings.LMS_ROOT_URL}/notifications",
    }
    
    # Account MFE URL if available
    if hasattr(settings, 'ACCOUNT_MICROFRONTEND_URL') and settings.ACCOUNT_MICROFRONTEND_URL:
        urls_context['account_profile'] = settings.ACCOUNT_MICROFRONTEND_URL
    else:
        urls_context['account_profile'] = settings.LMS_ROOT_URL
    
    # Navigation items
    navigation_items = get_navigation_items(request)
    
    # User menu items
    user_menu_items = get_user_menu_items(request) if user.is_authenticated else []
    
    return {
        'user': user_context,
        'organization': org_context,
        'platform': platform_context,
        'urls': urls_context,
        'navigation_items': navigation_items,
        'user_menu_items': user_menu_items,
    }


def get_navigation_items(request):
    """
    Get navigation items for the header.
    
    Args:
        request: The HTTP request object
        
    Returns:
        list: List of navigation item dictionaries
    """
    user = request.user
    
    items = [
        {
            'id': 'home',
            'label': _('Trang chủ'),
            'url': reverse('dashboard'),
            'icon': 'home',
            'active': request.path == reverse('dashboard'),
            'visible': True,
        },
        {
            'id': 'courses',
            'label': _('Danh mục'),
            'url': reverse('courses'),
            'icon': 'list',
            'active': request.path.startswith('/courses'),
            'visible': True,
        },
        {
            'id': 'learning',
            'label': _('Học tập'),
            'url': reverse('dashboard'),
            'icon': 'study',
            'active': False,
            'visible': True,
        },
    ]
    
    # Add personalization item only for authenticated users
    if user.is_authenticated:
        items.append({
            'id': 'personalization',
            'label': _('Cá nhân hóa'),
            'url': reverse('personalization:dashboard'),
            'icon': 'person',
            'active': request.path == reverse('personalization:dashboard'),
            'visible': True,
        })
    
    return items


def get_user_menu_items(request):
    """
    Get user dropdown menu items.
    
    Args:
        request: The HTTP request object
        
    Returns:
        list: List of menu item dictionaries
    """
    user = request.user
    
    if not user.is_authenticated:
        return []
    
    # Get URLs
    dashboard_url = reverse('dashboard')
    courses_url = reverse('courses')
    logout_url = reverse('logout')
    help_url = reverse('help') if 'help' in [url.name for url in settings.ROOT_URLCONF] else f"{settings.LMS_ROOT_URL}/help"
    
    account_url = settings.ACCOUNT_MICROFRONTEND_URL if hasattr(settings, 'ACCOUNT_MICROFRONTEND_URL') else settings.LMS_ROOT_URL
    profile_url = f"{account_url}/u/{user.username}"
    
    menu_items = [
        {
            'id': 'courses',
            'label': _('Khóa học'),
            'url': courses_url,
            'icon': 'courses',
        },
        {
            'id': 'update-info',
            'label': _('Cập nhật thông tin'),
            'url': profile_url,
            'icon': 'edit',
        },
        {
            'id': 'personalization',
            'label': _('Cá nhân hóa'),
            'url': reverse('personalization:dashboard'),
            'icon': 'person',
        },
        {
            'id': 'request-list',
            'label': _('Danh sách yêu cầu'),
            'url': f"{dashboard_url}?tab=requests",
            'icon': 'list',
        },
        {
            'id': 'learning-results',
            'label': _('Kết quả học tập'),
            'url': f"{dashboard_url}?tab=progress",
            'icon': 'results',
        },
        {
            'id': 'personal-plan',
            'label': _('Lập kế hoạch cá nhân'),
            'url': f"{dashboard_url}?tab=learning-plan",
            'icon': 'plan',
        },
        {
            'id': 'teaching-registration',
            'label': _('Đăng ký giảng dạy'),
            'url': f"{dashboard_url}?tab=teaching",
            'icon': 'teach',
        },
        {
            'id': 'help',
            'label': _('Trợ giúp'),
            'url': help_url,
            'icon': 'help',
        },
        {
            'id': 'logout',
            'label': _('Đăng xuất'),
            'url': logout_url,
            'icon': 'logout',
        },
    ]
    
    return menu_items


def get_notification_api_urls():
    """
    Get API URLs for notifications.
    
    Returns:
        dict: Dictionary of notification API URLs
    """
    base_url = settings.LMS_ROOT_URL
    
    return {
        'notifications': f"{base_url}/api/chalix/user-menu/notifications/",
        'unread_count': f"{base_url}/api/chalix/user-menu/notifications/unread-count/",
        'mark_read': f"{base_url}/api/chalix/user-menu/notifications/{{id}}/read/",
        'mark_all_read': f"{base_url}/api/chalix/user-menu/notifications/mark-all-read/",
    }


def should_show_header(request):
    """
    Determine if the Chalix header should be shown for this request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        bool: True if header should be shown
    """
    # Get configuration
    show_header = configuration_helpers.get_value('SHOW_CHALIX_HEADER', True)
    
    # Don't show on certain paths
    excluded_paths = [
        '/admin/',
        '/login',
        '/register',
        '/logout',
    ]
    
    for path in excluded_paths:
        if request.path.startswith(path):
            return False
    
    return show_header
