"""
Dashboard views for Vietnamese CMS interface with role-based access control
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
import json
import uuid

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
from common.djangoapps.student.auth import user_has_role, has_studio_read_access, has_studio_write_access
from common.djangoapps.student.roles import GlobalStaff, CourseStaffRole, CourseInstructorRole
from cms.djangoapps.contentstore.views.course import get_courses_accessible_to_user
from openedx.core.djangoapps.user_authn.cookies import _get_user_info_cookie_data

# Additional imports for course creation
from cms.djangoapps.contentstore.views.course import create_new_course
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError
from opaque_keys.edx.keys import CourseKey
from rest_framework.exceptions import ValidationError


def _create_course_structure_from_program(store, course_key, user_id, template_program, program_topics):
    """
    Create OpenEdX course structure from program topics.
    
    Structure created:
    Course 
    └── Section (Chapter): "{Program Title}"
        ├── Subsection (Sequential): "{Topic 1 Title}" 
        │   └── Unit (Vertical): "{Topic 1 Title} - Bài học" (empty unit)
        ├── Subsection (Sequential): "{Topic 2 Title}"
        │   └── Unit (Vertical): "{Topic 2 Title} - Bài học" (empty unit)
        └── ... (more topics)
    
    Returns number of units created.
    """
    units_created = 0
    
    # Create a main section to organize all program topics
    main_chapter = store.create_child(
        user_id,
        course_key,
        'chapter',
        fields={
            'display_name': template_program.title,
        }
    )
    
    # For each program topic, create a subsection with an empty unit
    for topic in program_topics:
        # Create subsection (sequential) for the topic
        # Topic name becomes the subsection name in the course outline
        sequential = store.create_child(
            user_id,
            main_chapter.location,
            'sequential',
            fields={
                'display_name': topic.title,  # Program topic name → Subsection name
            }
        )
        
        # Create an empty unit (vertical) under the subsection
        # This unit will be empty, allowing instructors to add content
        vertical = store.create_child(
            user_id,
            sequential.location,
            'vertical',
            fields={
                'display_name': f'{topic.title} - Bài học',  # Topic name → Unit name
            }
        )
        
        # Publish the created components so they appear in the course
        store.publish(sequential.location, user_id)
        store.publish(vertical.location, user_id)
        units_created += 1

    # Publish the main chapter
    store.publish(main_chapter.location, user_id)
    
    return units_created


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
    """Create a new OpenEDX course using the standard course creation logic.
    
    Only users with giang_vien or co_quan roles can create courses.
    If template_program_id is provided, creates course structure based on program topics.

    Expects JSON: {
        "title": "Course Title",
        "org": "chalix", 
        "number": "course_code",
        "run": "2024",
        "template_program_id": 123 (optional)
    }
    Returns JSON with created course key and details on success.
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

    # Required fields for OpenEDX course creation
    title = payload.get('title', '').strip()
    org = payload.get('org', 'chalix').strip()
    number = payload.get('number', '').strip()
    run = payload.get('run', '2024').strip()
    
    # Optional fields
    short_description = payload.get('short_description', '').strip()
    template_program_id = payload.get('template_program_id')
    course_type = payload.get('course_type', '')

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)
    
    # Auto-generate course number if not provided
    if not number:
        number = f'course_{uuid.uuid4().hex[:8]}'

    # Resolve template program if provided
    template_program = None
    program_topics = []
    if template_program_id:
        try:
            template_program = LocalProgram.objects.get(pk=template_program_id)
            program_topics = list(ProgramTopic.objects.filter(program=template_program).order_by('order'))
        except LocalProgram.DoesNotExist:
            template_program = None

    try:
        # Use OpenEDX standard course creation
        course_fields = {
            'display_name': title,
            'course_type': course_type,
        }
        
        # Add short description if provided
        if short_description:
            course_fields['short_description'] = short_description
        
        # Create the course using OpenEDX standard method
        new_course = create_new_course(
            user=request.user,
            org=org,
            number=number,
            run=run,
            fields=course_fields
        )
        
        course_key = new_course.id
        
        # Create course structure based on program topics if template provided
        units_created = 0
        if template_program and program_topics:
            store = modulestore()
            with store.bulk_operations(course_key):
                units_created = _create_course_structure_from_program(
                    store, 
                    course_key, 
                    request.user.id, 
                    template_program, 
                    program_topics
                )

        # Prepare response with OpenEDX course data
        result = {
            'course_key': str(course_key),
            'title': new_course.display_name,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'course_type': course_fields.get('course_type', ''),
            'short_description': course_fields.get('short_description', ''),
            'created_by': request.user.username,
            'units_created': units_created,
            'url': f'/courses/{course_key}/',
            'studio_url': f'/course/{course_key}',
            'template_program': None,
        }
        
        # Add template program info if used
        if template_program:
            result['template_program'] = {
                'id': template_program.pk,
                'title': template_program.title,
                'icon': template_program.icon,
                'topics_count': len(program_topics)
            }

        return JsonResponse(result)

    except DuplicateCourseError:
        return JsonResponse({
            'error': 'Khóa học với mã số này đã tồn tại. Vui lòng chọn mã số khác.',
            'error_code': 'DUPLICATE_COURSE'
        }, status=400)
    except ValidationError as ex:
        return JsonResponse({'error': str(ex)}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create course: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi tạo khóa học. Vui lòng thử lại.',
            'error_code': 'CREATION_FAILED'
        }, status=500)


@login_required
@require_POST 
def create_program_api(request):
    """Create a new OpenEDX course using the standard course creation logic.
    
    Only users with giang_vien or co_quan roles can create courses.
    If template_program_id is provided, creates course structure based on program topics.

    Expects JSON: {
        "title": "Course Title",
        "org": "chalix", 
        "number": "course_code",
        "run": "2024",
        "template_program_id": 123 (optional)
    }
    Returns JSON with created course key and details on success.
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

    # Required fields for OpenEDX course creation
    title = payload.get('title', '').strip()
    org = payload.get('org', 'chalix').strip()
    number = payload.get('number', '').strip()
    run = payload.get('run', '2024').strip()
    
    # Optional fields
    short_description = payload.get('short_description', '').strip()
    template_program_id = payload.get('template_program_id')
    course_type = payload.get('course_type', '')

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)
    
    # Auto-generate course number if not provided
    if not number:
        number = f'course_{uuid.uuid4().hex[:8]}'

    # Resolve template program if provided
    template_program = None
    program_topics = []
    if template_program_id:
        try:
            template_program = LocalProgram.objects.get(pk=template_program_id)
            program_topics = list(ProgramTopic.objects.filter(program=template_program).order_by('order'))
        except LocalProgram.DoesNotExist:
            template_program = None

    try:
        # Use OpenEDX standard course creation
        course_fields = {
            'display_name': title,
            'course_type': course_type,
        }
        
        # Add short description if provided
        if short_description:
            course_fields['short_description'] = short_description
        
        # Create the course using OpenEDX standard method
        new_course = create_new_course(
            user=request.user,
            org=org,
            number=number,
            run=run,
            fields=course_fields
        )
        
        course_key = new_course.id
        
        # Create course structure based on program topics if template provided
        units_created = 0
        if template_program and program_topics:
            store = modulestore()
            with store.bulk_operations(course_key):
                units_created = _create_course_structure_from_program(
                    store, 
                    course_key, 
                    request.user.id, 
                    template_program, 
                    program_topics
                )

        # Prepare response with OpenEDX course data
        result = {
            'course_key': str(course_key),
            'title': new_course.display_name,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'course_type': course_fields.get('course_type', ''),
            'short_description': course_fields.get('short_description', ''),
            'created_by': request.user.username,
            'units_created': units_created,
            'url': f'/courses/{course_key}/',
            'studio_url': f'/course/{course_key}',
            'template_program': None,
        }
        
        # Add template program info if used
        if template_program:
            result['template_program'] = {
                'id': template_program.pk,
                'title': template_program.title,
                'icon': template_program.icon,
                'topics_count': len(program_topics)
            }

        return JsonResponse(result)

    except DuplicateCourseError:
        return JsonResponse({
            'error': 'Khóa học với mã số này đã tồn tại. Vui lòng chọn mã số khác.',
            'error_code': 'DUPLICATE_COURSE'
        }, status=400)
    except ValidationError as ex:
        return JsonResponse({'error': str(ex)}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create course: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi tạo khóa học. Vui lòng thử lại.',
            'error_code': 'CREATION_FAILED'
        }, status=500)


@login_required
def list_local_courses_api(request):
    """Return a list of OpenEDX courses visible to the user as JSON."""
    # Get courses accessible to the user using standard OpenEDX logic
    courses, _ = get_courses_accessible_to_user(request)
    courses_list = list(courses)
    
    # Convert to our expected format
    formatted_courses = []
    for course_overview in courses_list:
        try:
            # CourseOverview object has direct attributes, not dictionary-style access
            course_key = course_overview.id  # CourseOverview uses 'id' for the course key
            
            # Create formatted course using CourseOverview and course_key directly
            formatted_course = {
                'course_key': str(course_key),
                'title': getattr(course_overview, 'display_name', '') or 'Untitled Course',
                # Get org, number, run from the course key
                'org': course_key.org,
                'number': course_key.course,  # 'number' field is called 'course' in the key
                'run': course_key.run,
                'short_description': getattr(course_overview, 'short_description', ''),
                'course_type': '',  # CourseOverview doesn't have course_type
                'created': course_overview.created.isoformat() if hasattr(course_overview, 'created') and course_overview.created else '',
                'url': f'/courses/{course_key}/',
                'studio_url': f'/course/{course_key}',
                'published': getattr(course_overview, 'published', True),
                'thumbnail': getattr(course_overview, 'course_image_url', ''),
                'start_date': course_overview.start.isoformat() if hasattr(course_overview, 'start') and course_overview.start else None,
                'end_date': course_overview.end.isoformat() if hasattr(course_overview, 'end') and course_overview.end else None,
            }
            formatted_courses.append(formatted_course)
        except Exception as e:
            # Skip courses that can't be loaded
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not load course {course_overview.id if hasattr(course_overview, 'id') else 'unknown'}: {str(e)}")
            continue

    return JsonResponse({'courses': formatted_courses})


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
    for index, topic_item in enumerate(topics):
        # Handle both string topics and object topics. Coerce to string before strip
        if isinstance(topic_item, dict):
            title_val = topic_item.get('title', '')
            topic_title = str(title_val).strip()
        else:
            topic_title = str(topic_item).strip()

        if topic_title:
            ProgramTopic.objects.create(
                program=program,
                title=topic_title,
                order=index
            )

    # Return program data with topics
    topics_data = [
        {'id': topic.pk, 'title': topic.title, 'order': topic.order}
        for topic in ProgramTopic.objects.filter(program=program).order_by('order')
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
@require_POST
def update_program_api(request):
    """Update an existing LocalProgram from dashboard POST data.
    
    Only users with giang_vien or co_quan roles can update programs.

    Expects JSON: {
        "id": 123,
        "title": "...", 
        "icon": "seed-of-life",
        "update_topics": true/false,
        "topics": ["Topic 1", "Topic 2", ...]
    }
    Returns JSON with updated program data on success.
    """
    # Check role-based permission
    try:
        require_role(request.user, ['giang_vien', 'co_quan'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền cập nhật chương trình học'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    program_id = payload.get('id')
    title = payload.get('title', '').strip()
    icon = payload.get('icon', 'seed-of-life')
    update_topics = payload.get('update_topics', False)
    topics = payload.get('topics', [])

    if not program_id:
        return JsonResponse({'error': 'Program ID is required'}, status=400)
    
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    # Get the program to update
    try:
        program = LocalProgram.objects.get(pk=program_id)
    except LocalProgram.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)

    # Update the program fields
    program.title = title
    program.icon = icon
    program.update_topics = update_topics
    program.save()

    # Update topics - delete existing and create new ones
    ProgramTopic.objects.filter(program=program).delete()  # Remove existing topics
    
    # Add new topics
    for index, topic_item in enumerate(topics):
        # Handle both string topics and object topics. Coerce to string before strip
        if isinstance(topic_item, dict):
            title_val = topic_item.get('title', '')
            topic_title = str(title_val).strip()
        else:
            topic_title = str(topic_item).strip()

        if topic_title:
            ProgramTopic.objects.create(
                program=program,
                title=topic_title,
                order=index
            )

    # Return updated program data with topics
    topics_data = [
        {'id': topic.pk, 'title': topic.title, 'order': topic.order}
        for topic in ProgramTopic.objects.filter(program=program).order_by('order')
    ]

    return JsonResponse({
        'id': program.pk, 
        'title': program.title, 
        'icon': program.icon,
        'update_topics': program.update_topics,
        'topics': topics_data,
        'updated_at': program.updated_at.isoformat(),
        'message': 'Đã cập nhật chương trình học thành công!'
    })


@login_required
def list_local_programs_api(request):
    """Return a list of LocalProgram objects visible to the user as JSON."""
    qs = LocalProgram.objects.prefetch_related('topics').all().order_by('-created_at')[:100]
    programs = []
    for p in qs:
        topics_data = [
            {'id': topic.pk, 'title': topic.title, 'order': topic.order}
            for topic in ProgramTopic.objects.filter(program=p).order_by('order')
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


@login_required
def course_detail_api(request, course_key_string):
    """Get detailed information about a specific OpenEDX course by course key.
    
    URL: /api/chalix/dashboard/course-detail/<course_key>/
    Returns JSON with course details.
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)
    
    # Check user access to the course
    if not has_studio_read_access(request.user, course_key):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        store = modulestore()
        course = store.get_course(course_key)
        
        if not course:
            return JsonResponse({'error': 'Course not found'}, status=404)
        
        # Get course overview for additional data
        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
            course_overview = CourseOverview.get_from_id(course_key)
            created_date = course_overview.created.isoformat() if course_overview.created else ''
        except Exception:
            created_date = ''
        
        course_data = {
            'course_key': str(course_key),
            'title': getattr(course, 'display_name', '') or 'Untitled Course',
            # Get org, number, run from the course key, not the course object
            'org': course_key.org,
            'number': course_key.course,  # 'number' field is called 'course' in the key
            'run': course_key.run,
            'short_description': getattr(course, 'short_description', ''),
            'course_type': getattr(course, 'course_type', ''),
            'created': created_date,
            'url': f'/courses/{course_key}/',
            'studio_url': f'/course/{course_key}',
            'language': getattr(course, 'language', 'en'),
            'start_date': getattr(course, 'start', None).isoformat() if getattr(course, 'start', None) else None,
            'end_date': getattr(course, 'end', None).isoformat() if getattr(course, 'end', None) else None,
        }
        
        return JsonResponse(course_data)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting course details for {course_key_string}: {str(e)}")
        return JsonResponse({'error': 'Course not found or inaccessible'}, status=404)


@login_required
def program_detail_api(request, cid):
    """Get detailed information about a specific program by ID.
    
    URL: /api/chalix/dashboard/program-detail/<cid>/
    Returns JSON with program details including all topics and associated courses.
    """
    try:
        program = LocalProgram.objects.get(pk=cid)
    except LocalProgram.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)
    
    # Get all topics for this program
    topics_data = [
        {'id': topic.pk, 'title': topic.title, 'order': topic.order}
        for topic in ProgramTopic.objects.filter(program=program).order_by('order')
    ]
    
    # Get all courses that use this program as template
    associated_courses = LocalCourse.objects.filter(template_program=program).order_by('-created_at')
    courses_data = [
        {
            'id': course.pk,
            'title': course.title,
            'short_description': course.short_description,
            'course_type': course.course_type,
            'created_at': course.created_at.isoformat(),
            'created_by': getattr(course.created_by, 'username', None),
        }
        for course in associated_courses
    ]
    
    program_data = {
        'id': program.pk,
        'title': program.title,
        'icon': program.icon,
        'update_topics': program.update_topics,
        'created_at': program.created_at.isoformat(),
        'updated_at': program.updated_at.isoformat(),
        'created_by': getattr(program.created_by, 'username', None),
        'topics': topics_data,
        'associated_courses': courses_data,
        'topics_count': len(topics_data),
        'courses_count': len(courses_data),
    }
    
    return JsonResponse(program_data)


@login_required
@require_POST
def update_course_api(request):
    """Update an existing OpenEDX course settings.
    
    Only users with studio write access can update courses.

    Expects JSON: {
        "course_key": "course-v1:org+number+run",
        "title": "New Course Title",
        "short_description": "New description",
        "start_date": "2024-01-01T00:00:00Z" (optional),
        "end_date": "2024-12-31T23:59:59Z" (optional)
    }
    Returns JSON with updated course data on success.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    course_key_string = payload.get('course_key', '').strip()
    title = payload.get('title', '').strip()
    short_description = payload.get('short_description', '').strip()
    start_date_str = payload.get('start_date')
    end_date_str = payload.get('end_date')

    if not course_key_string:
        return JsonResponse({'error': 'Course key is required'}, status=400)
    
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key format'}, status=400)

    # Check user permissions
    if not has_studio_write_access(request.user, course_key):
        return JsonResponse({'error': 'Bạn không có quyền chỉnh sửa khóa học này'}, status=403)

    try:
        store = modulestore()
        course = store.get_course(course_key)
        
        if not course:
            return JsonResponse({'error': 'Course not found'}, status=404)

        # Update course fields
        course.display_name = title
        if short_description:
            course.short_description = short_description
        
        # Parse and set dates if provided
        if start_date_str:
            from dateutil import parser as date_parser
            try:
                course.start = date_parser.parse(start_date_str)
            except Exception:
                return JsonResponse({'error': 'Invalid start date format'}, status=400)
                
        if end_date_str:
            from dateutil import parser as date_parser
            try:
                course.end = date_parser.parse(end_date_str)
            except Exception:
                return JsonResponse({'error': 'Invalid end date format'}, status=400)

        # Save the course
        store.update_item(course, request.user.id)

        # Return updated course data
        return JsonResponse({
            'course_key': str(course_key),
            'title': course.display_name,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'short_description': getattr(course, 'short_description', ''),
            'start_date': course.start.isoformat() if course.start else None,
            'end_date': course.end.isoformat() if course.end else None,
            'message': 'Đã cập nhật khóa học thành công!'
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating course {course_key_string}: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi cập nhật khóa học. Vui lòng thử lại.'
        }, status=500)
