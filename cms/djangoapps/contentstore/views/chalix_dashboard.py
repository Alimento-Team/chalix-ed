"""
Dashboard views for Vietnamese CMS interface with role-based access control
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
import json

# Local models
from cms.djangoapps.contentstore.models import LocalCourse, LocalProgram, ProgramTopic
from cms.djangoapps.contentstore.chalix_roles import (
    can_access_cms,
    require_cms_access,
    get_available_tabs,
    get_user_organization_display_name,
    get_user_primary_role,
    require_role
)

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import user_has_role
from common.djangoapps.student.roles import GlobalStaff, CourseStaffRole, CourseInstructorRole
from cms.djangoapps.contentstore.views.course import get_courses_accessible_to_user
from openedx.core.djangoapps.user_authn.cookies import _get_user_info_cookie_data


@login_required
@ensure_csrf_cookie
def cms_dashboard(request):
    """
    Displays the CMS dashboard with Vietnamese interface based on Figma design.
    This is the main landing page after login with role-based tab access:
    - Thống kê (Statistics) - All roles
    - Tạo tài khoản cán bộ (Create Staff Account) - Cơ quan only
    - Quản lý (Management) - Bộ, Cơ quan
    - Quản lý học tập (Learning Management) - Giảng viên, Cơ quan
    - Phê duyệt yêu cầu (Approve Requests) - Cơ quan only
    """
    user = request.user
    
    # Check if user can access CMS
    if not can_access_cms(user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Bạn không có quyền truy cập CMS. Vui lòng liên hệ quản trị viên.")
    
    # Get user permissions and role info
    is_staff = user.is_staff
    is_global_staff = user_has_role(user, GlobalStaff)
    user_role = get_user_primary_role(user)
    available_tabs = get_available_tabs(user)
    organization_name = get_user_organization_display_name(user)
    
    # Get accessible courses for context
    courses, in_process_course_actions = get_courses_accessible_to_user(request)
    courses_list = list(courses)  # Convert to list to allow len() and iteration
    
    # Get user info for template
    user_info = _get_user_info_cookie_data(request, user)
    
    # Get account URL from user info or settings
    account_url = user_info.get('header_urls', {}).get('account_settings', '/account/settings')
    
    # Prepare context for template
    context = {
        'user': user,
        'user_info': user_info,
        'account_url': account_url,
        'is_staff': is_staff,
        'is_global_staff': is_global_staff,
        'user_role': user_role,
        'organization_name': organization_name,
        'available_tabs': available_tabs,
        'courses_count': len(courses_list),
        'in_process_count': len(in_process_course_actions),
        'page_title': 'CMS Dashboard',
        'active_tab': request.GET.get('tab', 'statistics'),  # Default to statistics tab
    }
    
    return render_to_response('dashboard.html', context)


@login_required
def dashboard_api(request):
    """
    API endpoint to get dashboard data via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    tab = request.GET.get('tab')
    
    # Return tab-specific data
    if tab == 'statistics':
        data = _get_statistics_data(request)
    elif tab == 'create-account':
        data = _get_create_account_data(request)
    elif tab == 'management':
        data = _get_management_data(request)
    elif tab == 'learning-management':
        data = _get_learning_management_data(request)
    elif tab == 'approve-requests':
        data = _get_approve_requests_data(request)
    else:
        data = {'error': 'Invalid tab'}
        
    return JsonResponse(data)


def _get_statistics_data(request):
    """Get statistics data for the dashboard"""
    courses, _ = get_courses_accessible_to_user(request)
    courses_list = list(courses)
    
    return {
        'total_courses': len(courses_list),
        'active_courses': len([c for c in courses_list if not c.get('archived', False)]),
        'total_users': 0,  # Will be implemented later
        'active_users': 0,  # Will be implemented later
    }


def _get_create_account_data(request):
    """Get data for creating staff accounts"""
    return {
        'pending_requests': 0,  # Will be implemented later
        'total_accounts': 0,    # Will be implemented later
    }


def _get_management_data(request):
    """Get management data"""
    return {
        'system_status': 'operational',
        'pending_tasks': 0,  # Will be implemented later
    }


def _get_learning_management_data(request):
    """Get learning management data"""
    courses, _ = get_courses_accessible_to_user(request)
    courses_list = list(courses)
    
    return {
        'total_courses': len(courses_list),
        'draft_courses': len([c for c in courses_list if not c.get('published', True)]),
        'published_courses': len([c for c in courses_list if c.get('published', True)]),
    }


def _get_approve_requests_data(request):
    """Get approval requests data"""
    return {
        'pending_requests': [
            # Sample data - will be replaced with real data later
            {
                'id': 1,
                'title': 'Xin thi lại buổi thi kết thúc tháng 1',
                'requester': 'Lê Văn B',
                'date': '20:40 ngày 11/11/2025',
                'content': 'Vào ngày 10/11/2025 có buổi thi kết thúc tháng 1, vì một số lí do cá nhân nên tôi không thể tham gia vì thế viết đơn này xin phép admin cho phép thi lại bổ sung. Tôi xin cảm ơn!',
                'status': 'pending'
            }
        ],
        'total_requests': 1,
        'approved_today': 0,
        'rejected_today': 0,
    }



@login_required
@require_POST
def create_course_api(request):
    """Create a LocalCourse from dashboard POST data.
    
    Only users with giang_vien or co_quan roles can create courses.

    Expects JSON: {"title": "...", "short_description": "..."}
    Returns JSON with created course id and fields on success.
    """
    # Check role-based permission
    try:
        require_role(request.user, ['giang_vien', 'co_quan'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền tạo khóa học'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = payload.get('title', '').strip()
    short_description = payload.get('short_description', '').strip()
    # New fields: template_program_id (optional) and course_type (optional)
    template_program_id = payload.get('template_program_id')
    course_type = payload.get('course_type')

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    # Resolve template program if provided
    template_program = None
    if template_program_id:
        try:
            template_program = LocalProgram.objects.get(pk=template_program_id)
        except LocalProgram.DoesNotExist:
            template_program = None

    course = LocalCourse.objects.create(
        title=title,
        short_description=short_description,
        template_program=template_program,
        course_type=course_type or '',
        created_by=request.user if request.user.is_authenticated else None,
    )

    result = {
        'id': course.pk,
        'title': course.title,
        'created_at': course.created_at.isoformat(),
        'course_type': course.course_type,
        'template_program': None,
    }
    if template_program:
        result['template_program'] = {
            'id': template_program.pk,
            'title': template_program.title,
            'icon': template_program.icon,
        }

    return JsonResponse(result)


@login_required
def list_local_courses_api(request):
    """Return a list of LocalCourse objects visible to the user as JSON."""
    # For now, return recent courses (limit 100). In the future, add pagination and filtering.
    qs = LocalCourse.objects.all().order_by('-created_at')[:100]
    courses = [
        {
            'id': c.pk,
            'title': c.title,
            'short_description': c.short_description,
            'created_at': c.created_at.isoformat(),
            'created_by': getattr(c.created_by, 'username', None),
            'course_type': getattr(c, 'course_type', ''),
            'template_program': None,
        }
        for c in qs
    ]
    # Attach template_program details where available
    for idx, c in enumerate(qs):
        tp = getattr(c, 'template_program', None)
        if tp:
            courses[idx]['template_program'] = {
                'id': tp.pk,
                'title': tp.title,
                'icon': tp.icon,
            }

    return JsonResponse({'courses': courses})


@login_required
@require_POST
def create_program_api(request):
    """Create a LocalProgram from dashboard POST data.
    
    Only users with giang_vien or co_quan roles can create programs.

    Expects JSON: {
        "title": "...", 
        "icon": "seed-of-life",
        "update_topics": true/false,
        "topics": ["Topic 1", "Topic 2", ...]
    }
    Returns JSON with created program id and fields on success.
    """
    # Check role-based permission
    try:
        require_role(request.user, ['giang_vien', 'co_quan'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền tạo chương trình học'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = payload.get('title', '').strip()
    icon = payload.get('icon', 'seed-of-life')
    update_topics = payload.get('update_topics', False)
    topics = payload.get('topics', [])

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    # Create the program
    program = LocalProgram.objects.create(
        title=title,
        icon=icon,
        update_topics=update_topics,
        created_by=request.user if request.user.is_authenticated else None,
    )

    # Add topics if provided
    for index, topic_title in enumerate(topics):
        if topic_title.strip():
            ProgramTopic.objects.create(
                program=program,
                title=topic_title.strip(),
                order=index
            )

    # Return program data with topics
    topics_data = [
        {'id': topic.pk, 'title': topic.title, 'order': topic.order}
        for topic in program.topics.all().order_by('order')
    ]

    return JsonResponse({
        'id': program.pk, 
        'title': program.title, 
        'icon': program.icon,
        'update_topics': program.update_topics,
        'topics': topics_data,
        'created_at': program.created_at.isoformat()
    })


@login_required
def list_local_programs_api(request):
    """Return a list of LocalProgram objects visible to the user as JSON."""
    qs = LocalProgram.objects.prefetch_related('topics').all().order_by('-created_at')[:100]
    programs = []
    for p in qs:
        topics_data = [
            {'id': topic.pk, 'title': topic.title, 'order': topic.order}
            for topic in p.topics.all().order_by('order')
        ]
        programs.append({
            'id': p.pk,
            'title': p.title,
            'icon': p.icon,
            'update_topics': p.update_topics,
            'topics': topics_data,
            'created_at': p.created_at.isoformat(),
            'created_by': getattr(p.created_by, 'username', None),
        })
    return JsonResponse({'programs': programs})
