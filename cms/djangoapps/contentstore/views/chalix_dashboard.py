"""
Dashboard views for Vietnamese CMS interface with role-based access control
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
import json
import uuid
import logging

logger = logging.getLogger(__name__)

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
from openedx.core.djangoapps.models.course_details import CourseDetails


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
    
    # Get the course object from the course key
    course = store.get_course(course_key)
    
    # Create a main section to organize all program topics
    main_chapter = store.create_child(
        user_id,
        course.location,  # Use course location instead of course_key
        'chapter',
        fields={
            'display_name': template_program.title,
        }
    )
    
    # For each program topic, create a subsection with an empty unit
    for i, topic in enumerate(program_topics, 1):
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


@login_required
@require_POST
def create_single_account_api(request):
    """Create a single user account with extended profile information.
    
    Only users with co_quan role can create accounts.
    
    Expects JSON: {
        "username": "user123",
        "email": "user@example.com", 
        "password": "password123",
        "name": "Full Name",
        "ten_co_quan": "Organization Name",
        "ten_phong_ban": "Department Name",
        "phone_number": "+84123456789",
        "city": "Ho Chi Minh City",
        "level_of_education": "b",
        "gender": "m"
    }
    Returns JSON with created user info on success.
    """
    from cms.djangoapps.contentstore.chalix_roles import require_role
    from common.djangoapps.student.helpers import create_account_with_params
    from common.djangoapps.student.models import User, UserProfile
    from django.contrib.auth.hashers import make_password
    from openedx.core.djangoapps.user_authn.exceptions import AccountValidationError
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check role-based permission - only co_quan can create accounts
    try:
        require_role(request.user, ['co_quan'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền tạo tài khoản.'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Dữ liệu gửi lên không hợp lệ.'}, status=400)
    
    # Extract required fields
    username = payload.get('username', '').strip()
    email = payload.get('email', '').strip()
    password = payload.get('password', '').strip()
    name = payload.get('name', '').strip()
    
    # Extract extended profile fields
    ten_co_quan = payload.get('ten_co_quan', '').strip()
    ten_phong_ban = payload.get('ten_phong_ban', '').strip()
    phone_number = payload.get('phone_number', '').strip()
    city = payload.get('city', '').strip()
    level_of_education = payload.get('level_of_education', '').strip()
    gender = payload.get('gender', '').strip()
    
    # Validate required fields
    if not username:
        return JsonResponse({'error': 'Tên đăng nhập là bắt buộc.'}, status=400)
    if not email:
        return JsonResponse({'error': 'Email là bắt buộc.'}, status=400)
    if not password:
        return JsonResponse({'error': 'Mật khẩu là bắt buộc.'}, status=400)
    if not name:
        return JsonResponse({'error': 'Họ và tên là bắt buộc.'}, status=400)
    
    # Check if username or email already exists
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': f'Tên đăng nhập "{username}" đã được sử dụng.'}, status=400)
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': f'Email "{email}" đã được sử dụng.'}, status=400)
    
    # Validate email format
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Định dạng email không hợp lệ.'}, status=400)
    
    # Validate password strength (basic)
    if len(password) < 6:
        return JsonResponse({'error': 'Mật khẩu phải có ít nhất 6 ký tự.'}, status=400)
    
    try:
        # Create user account
        with transaction.atomic():
            # Create User object
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create or get UserProfile
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            # Update profile with provided information
            profile.name = name
            if phone_number:
                profile.phone_number = phone_number
            if city:
                profile.city = city
            if level_of_education and level_of_education in [choice[0] for choice in UserProfile.LEVEL_OF_EDUCATION_CHOICES]:
                profile.level_of_education = level_of_education
            if gender and gender in [choice[0] for choice in UserProfile.GENDER_CHOICES]:
                profile.gender = gender
            
            # Store custom organization and department info in meta field
            meta_data = profile.get_meta()
            if ten_co_quan:
                meta_data['ten_co_quan'] = ten_co_quan
            if ten_phong_ban:
                meta_data['ten_phong_ban'] = ten_phong_ban
            
            profile.set_meta(meta_data)
            profile.save()
            
            logger.info(f"[CHALIX] Created user account: {username} ({email}) by {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': f'Đã tạo tài khoản thành công cho {name}',
                'user': {
                    'id': user.id,
                    'username': username,
                    'email': email,
                    'name': name,
                    'ten_co_quan': ten_co_quan,
                    'ten_phong_ban': ten_phong_ban,
                    'phone_number': phone_number,
                    'city': city,
                    'level_of_education': profile.level_of_education_display if level_of_education else '',
                    'gender': profile.gender_display if gender else '',
                    'created_by': request.user.username
                }
            })
            
    except Exception as e:
        logger.error(f"[CHALIX] Error creating user account {username}: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi tạo tài khoản. Vui lòng thử lại.'
        }, status=500)


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
        return JsonResponse({'errMsg': 'Bạn không có quyền tạo khóa học.'}, status=403)
    
    def _get_payload_value(data, *keys, default=''):
        """Fetch the first non-empty value from payload using provided keys."""
        for key in keys:
            if key in data:
                value = data.get(key)
                if isinstance(value, str):
                    value = value.strip()
                if value not in (None, ''):
                    return value
        return default

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'errMsg': 'Dữ liệu gửi lên không hợp lệ.'}, status=400)

    # Required fields for OpenEDX course creation
    title = _get_payload_value(payload, 'title', 'display_name', 'displayName')
    org = _get_payload_value(payload, 'org', default='chalix')
    number = _get_payload_value(payload, 'number')
    run = _get_payload_value(payload, 'run', default='2024')
    
    # Optional fields
    short_description = _get_payload_value(payload, 'short_description', 'shortDescription')
    template_program_id = _get_payload_value(payload, 'template_program_id', 'templateProgramId', default=None)
    course_type = _get_payload_value(payload, 'course_type', 'courseType', default='')
    online_course_link = _get_payload_value(payload, 'online_course_link', 'onlineCourseLink', default='')
    instructor = _get_payload_value(payload, 'instructor', default='')
    estimated_hours_raw = _get_payload_value(payload, 'estimated_hours', 'estimatedHours', default=None)

    # Convert numeric fields
    estimated_hours = None
    if estimated_hours_raw not in (None, ''):
        try:
            estimated_hours = int(estimated_hours_raw)
        except (TypeError, ValueError):
            return JsonResponse({'errMsg': 'Thời lượng dự kiến phải là số nguyên.'}, status=400)

    if template_program_id in (None, ''):
        template_program_id = None
    else:
        try:
            template_program_id = int(template_program_id)
        except (TypeError, ValueError):
            return JsonResponse({'errMsg': 'Mã chương trình mẫu không hợp lệ.'}, status=400)

    if not title:
        return JsonResponse({'errMsg': 'Tên khóa học là bắt buộc.'}, status=400)
    
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
        
        # Create the course using OpenEDX standard method
        new_course = create_new_course(
            user=request.user,
            org=org,
            number=number,
            run=run,
            fields=course_fields
        )
        
        course_key = new_course.id
        logger.info(f"[CHALIX] Created OpenEDX course with key: {course_key}")
        
        # Create course structure based on program topics if template provided
        units_created = 0
        if template_program and program_topics:
            try:
                store = modulestore()
                with store.bulk_operations(course_key):
                    units_created = _create_course_structure_from_program(
                        store, 
                        course_key, 
                        request.user.id, 
                        template_program, 
                        program_topics
                    )
            except Exception as structure_error:
                # Log structure creation error but don't fail the whole course creation
                print(f"Course structure creation failed: {structure_error}")
                units_created = 0  # Course created but no structure
            logger.info(f"[CHALIX] Course structure creation complete. Units created: {units_created}")
        else:
            logger.info(f"[CHALIX] No template program provided, skipping structure creation")

        # Update course with new fields if provided
        updated_course_details = None
        if short_description or online_course_link or instructor or estimated_hours is not None:
            try:
                from openedx.core.djangoapps.models.course_details import CourseDetails
                course_update_data = {}
                if short_description:
                    course_update_data['short_description'] = short_description
                if online_course_link:
                    course_update_data['online_course_link'] = online_course_link
                if instructor:
                    course_update_data['instructor'] = instructor
                if estimated_hours is not None:
                    course_update_data['estimated_hours'] = estimated_hours
                
                # Need to provide required fields to avoid KeyError
                course_update_data['overview'] = ''
                course_update_data['intro_video'] = ''
                
                # Update the course with new fields
                updated_course_details = CourseDetails.update_from_json(course_key, course_update_data, request.user)
                logger.info(f"[CHALIX] Updated course with new fields: {course_update_data}")
            except Exception as update_error:
                    logger.warning(f"[CHALIX] Failed to update course with new fields: {update_error}")
                # Don't fail the whole creation if field update fails

        # Create LocalCourse record to track the course-program relationship
        # Persist a LocalCourse record and store the modulestore course key string
        local_course_short_description = short_description if short_description else ''
        if updated_course_details:
            local_course_short_description = getattr(updated_course_details, 'short_description', local_course_short_description)
        
        local_course = LocalCourse.objects.create(
            title=new_course.display_name,
            short_description=local_course_short_description,
            template_program=template_program,
            course_type=course_fields.get('course_type', ''),
            created_by=request.user if request.user.is_authenticated else None,
            course_key=str(course_key),
        )

        # Prepare response with OpenEDX course data
        result = {
            'course_key': str(course_key),
            'local_course_id': local_course.pk,
            'title': new_course.display_name,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'course_type': course_fields.get('course_type', ''),
            'short_description': course_fields.get('short_description', ''),
            'online_course_link': online_course_link or '',
            'instructor': instructor or '',
            'estimated_hours': estimated_hours if estimated_hours is not None else 0,
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

        # Align success payload with Studio expectations
        success_payload = {
            'url': result['studio_url'],
            'studio_url': result['studio_url'],
            'course_key': result['course_key'],
            'local_course_id': result['local_course_id'],
            'title': result['title'],
            'org': result['org'],
            'number': result['number'],
            'run': result['run'],
            'course_type': result['course_type'],
            'short_description': result['short_description'],
            'online_course_link': result['online_course_link'],
            'instructor': result['instructor'],
            'estimated_hours': result['estimated_hours'],
            'units_created': result['units_created'],
        }
        if template_program:
            success_payload['template_program'] = result['template_program']

        return JsonResponse(success_payload)

    except DuplicateCourseError:
        return JsonResponse({
            'errMsg': 'Khóa học với mã số này đã tồn tại. Vui lòng chọn mã số khác.',
            'error_code': 'DUPLICATE_COURSE'
        }, status=400)
    except ValidationError as ex:
        return JsonResponse({'errMsg': str(ex)}, status=400)
    except Exception as e:
        # Log the error and return a generic error response
        import traceback
        logger.exception("[CHALIX] Course creation error: %s", e)
        return JsonResponse({
            'errMsg': 'Có lỗi xảy ra khi tạo khóa học. Vui lòng thử lại.',
            'error_code': 'CREATION_FAILED',
            'debug': str(e),
            'trace': traceback.format_exc(),
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
                'id': str(course_key),
                'course_key': str(course_key),
                'title': getattr(course_overview, 'display_name', '') or 'Untitled Course',
                # Get org, number, run from the course key
                'org': course_key.org,
                'number': course_key.course,  # 'number' field is called 'course' in the key
                'run': course_key.run,
                'short_description': getattr(course_overview, 'short_description', ''),
                'course_type': '',  # Will be populated from course block
                'course_level': '',  # Will be populated from course block
                'created': course_overview.created.isoformat() if hasattr(course_overview, 'created') and course_overview.created else '',
                'url': f'/courses/{course_key}/',
                'studio_url': f'/course/{course_key}',
                'published': getattr(course_overview, 'published', True),
                'thumbnail': getattr(course_overview, 'course_image_url', ''),
                'start_date': course_overview.start.isoformat() if hasattr(course_overview, 'start') and course_overview.start else None,
                'end_date': course_overview.end.isoformat() if hasattr(course_overview, 'end') and course_overview.end else None,
            }
            # Try to enrich with additional fields stored on the modulestore course block
            try:
                # Use CourseDetails.fetch which consolidates course block attributes
                try:
                    details = CourseDetails.fetch(course_key)
                    formatted_course['online_course_link'] = getattr(details, 'online_course_link', '')
                    formatted_course['instructor'] = getattr(details, 'instructor', '')
                    formatted_course['estimated_hours'] = getattr(details, 'estimated_hours', 0)
                    # Also get course_type and course_level from the course details
                    store = modulestore()
                    # Force refresh to avoid caching issues
                    block = store.get_course(course_key, depth=0)
                    if block:
                        formatted_course['course_type'] = getattr(block, 'course_type', '')
                        formatted_course['course_level'] = getattr(block, 'course_level', '')
                except Exception:
                    # Fallback: try to read raw block attributes
                    store = modulestore()
                    # Force refresh to avoid caching issues
                    block = store.get_course(course_key, depth=0)
                    if block:
                        formatted_course['online_course_link'] = getattr(block, 'online_course_link', '')
                        formatted_course['instructor'] = getattr(block, 'instructor', '')
                        formatted_course['estimated_hours'] = getattr(block, 'estimated_hours', 0)
                        formatted_course['course_type'] = getattr(block, 'course_type', '')
                        formatted_course['course_level'] = getattr(block, 'course_level', '')
            except Exception:
                # If enrichment fails, continue without the extra fields
                pass

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
    short_description = payload.get('short_description', '').strip()
    icon = payload.get('icon', 'seed-of-life')
    update_topics = payload.get('update_topics', False)
    topics = payload.get('topics', [])

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    # Use database transaction to ensure atomicity
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Create the program
            program = LocalProgram.objects.create(
                title=title,
                short_description=short_description,
                icon=icon,
                update_topics=update_topics,
                created_by=request.user if request.user.is_authenticated else None,
            )

            # Add topics if provided
            topics_to_create = []
            for index, topic_item in enumerate(topics):
                # Handle both string topics and object topics. Coerce to string before strip
                if isinstance(topic_item, dict):
                    title_val = topic_item.get('title', '')
                    topic_title = str(title_val).strip()
                else:
                    topic_title = str(topic_item).strip()

                if topic_title:
                    topics_to_create.append(ProgramTopic(
                        program=program,
                        title=topic_title,
                        order=index
                    ))
            
            # Bulk create all topics at once
            if topics_to_create:
                ProgramTopic.objects.bulk_create(topics_to_create)

        # Return program data with topics
        topics_data = [
            {'id': topic.pk, 'title': topic.title, 'order': topic.order}
            for topic in ProgramTopic.objects.filter(program=program).order_by('order')
        ]

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Successfully created program {program.pk} with {len(topics_data)} topics")

        return JsonResponse({
            'id': program.pk, 
            'title': program.title,
            'short_description': program.short_description, 
            'icon': program.icon,
            'update_topics': program.update_topics,
            'topics': topics_data,
            'created_at': program.created_at.isoformat()
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating program: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi tạo chương trình học. Vui lòng thử lại.'
        }, status=500)


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
    short_description = payload.get('short_description', '').strip()
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

    # Use database transaction to ensure atomicity
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Update the program fields
            program.title = title
            program.short_description = short_description
            program.icon = icon
            program.update_topics = update_topics
            program.save()

            # Update topics - delete existing and create new ones
            # Use the related manager for better performance and consistency
            ProgramTopic.objects.filter(program=program).delete()  # Remove existing topics
            
            # Add new topics
            topics_to_create = []
            for index, topic_item in enumerate(topics):
                # Handle both string topics and object topics. Coerce to string before strip
                if isinstance(topic_item, dict):
                    title_val = topic_item.get('title', '')
                    topic_title = str(title_val).strip()
                else:
                    topic_title = str(topic_item).strip()

                if topic_title:
                    topics_to_create.append(ProgramTopic(
                        program=program,
                        title=topic_title,
                        order=index
                    ))
            
            # Bulk create all topics at once for better performance
            if topics_to_create:
                ProgramTopic.objects.bulk_create(topics_to_create)

        # Refresh from database to get the latest data
        program.refresh_from_db()
        
        # Return updated program data with topics
        topics_data = [
            {'id': topic.pk, 'title': topic.title, 'order': topic.order}
            for topic in ProgramTopic.objects.filter(program=program).order_by('order')
        ]

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Successfully updated program {program_id} with {len(topics_data)} topics: {[t['title'] for t in topics_data]}")
        
        # Additional debugging: Check database directly
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM contentstore_programtopic WHERE program_id = %s", [program.pk])
            db_count = cursor.fetchone()[0]
            logger.info(f"Direct database query shows {db_count} topics for program {program_id}")

        return JsonResponse({
            'id': program.pk, 
            'title': program.title,
            'short_description': program.short_description, 
            'icon': program.icon,
            'update_topics': program.update_topics,
            'topics': topics_data,
            'updated_at': program.updated_at.isoformat(),
            'message': 'Đã cập nhật chương trình học thành công!'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating program {program_id}: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi cập nhật chương trình học. Vui lòng thử lại.'
        }, status=500)


@login_required
def list_local_programs_api(request):
    """Return a list of LocalProgram objects visible to the user as JSON."""
    # Don't use prefetch_related since we need fresh data after updates
    qs = LocalProgram.objects.all().order_by('-created_at')[:100]
    programs = []
    
    import logging
    logger = logging.getLogger(__name__)
    
    for p in qs:
        # Always fetch fresh topics data to avoid caching issues
        topics_queryset = ProgramTopic.objects.filter(program=p).order_by('order')
        topics_data = [
            {'id': topic.pk, 'title': topic.title, 'order': topic.order}
            for topic in topics_queryset
        ]
        
        # Log the topics for debugging
        logger.info(f"Program {p.pk} ({p.title}) has {len(topics_data)} topics: {[t['title'] for t in topics_data]}")
        
        programs.append({
            'id': p.pk,
            'title': p.title,
            'short_description': p.short_description,
            'icon': p.icon,
            'update_topics': p.update_topics,
            'topics': topics_data,
            'topics_count': len(topics_data),
            'created_at': p.created_at.isoformat(),
            'created_by': getattr(p.created_by, 'username', None),
        })
    
    logger.info(f"Returning {len(programs)} programs in list_local_programs_api")
    
    # Add debugging info to track fresh responses
    import time
    response_data = {
        'programs': programs,
        'debug_info': {
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_programs': len(programs),
        }
    }
    
    # Create response with cache-busting headers to ensure fresh data
    response = JsonResponse(response_data)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Debug-Timestamp'] = str(time.time())
    return response


@login_required
def course_detail_api(request, course_key_string):
    """Get or update detailed information about a specific OpenEDX course by course key.
    
    URL: /api/chalix/dashboard/course-detail/<course_key>/
    Methods: GET, PATCH
    Returns JSON with course details.
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)
    
    # Check user access to the course
    if not has_studio_read_access(request.user, course_key):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Handle PATCH request to update course details
    if request.method == 'PATCH':
        try:
            import json
            data = json.loads(request.body)
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"PATCH request to update course {course_key_string} with data: {data}")
            
            # Use CourseDetails.update_from_json to handle the update properly
            # This method handles date parsing and all field updates correctly
            updated_details = CourseDetails.update_from_json(course_key, data, request.user)
            
            logger.info(f"Successfully updated course details for {course_key_string}")
            
            # Return the updated course data using the GET handler
            return course_detail_api_get(request, course_key)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating course details for {course_key_string}: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Failed to update course: {str(e)}'}, status=500)
    
    # Handle GET request
    return course_detail_api_get(request, course_key)


def course_detail_api_get(request, course_key):
    """Get detailed information about a specific OpenEDX course by course key.
    
    URL: /api/chalix/dashboard/course-detail/<course_key>/
    Returns JSON with course details.
    """
    try:
        # course_key is already parsed, no need to parse again
        pass
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
            'id': str(course_key),
            'course_key': str(course_key),
            'title': getattr(course, 'display_name', '') or 'Untitled Course',
            # Get org, number, run from the course key, not the course object
            'org': course_key.org,
            'number': course_key.course,  # 'number' field is called 'course' in the key
            'run': course_key.run,
            'short_description': getattr(course, 'short_description', ''),
            'course_type': getattr(course, 'course_type', ''),
            'course_level': getattr(course, 'course_level', ''),
            'created': created_date,
            'url': f'/courses/{course_key}/',
            'studio_url': f'/course/{course_key}',
            'language': getattr(course, 'language', 'en'),
            'start_date': getattr(course, 'start', None).isoformat() if getattr(course, 'start', None) else None,
            'end_date': getattr(course, 'end', None).isoformat() if getattr(course, 'end', None) else None,
            'units': []  # Initialize empty units array
        }
        # Include newly-added fields from modulestore block if present
        try:
            # Prefer CourseDetails.fetch which consolidates about attributes and block attributes
            try:
                details = CourseDetails.fetch(course_key)
                course_data['online_course_link'] = getattr(details, 'online_course_link', '')
                course_data['instructor'] = getattr(details, 'instructor', '')
                course_data['estimated_hours'] = getattr(details, 'estimated_hours', 0)
            except Exception:
                # Fallback: read directly from course block
                course_data['online_course_link'] = getattr(course, 'online_course_link', '')
                course_data['instructor'] = getattr(course, 'instructor', '')
                course_data['estimated_hours'] = getattr(course, 'estimated_hours', 0)
        except Exception:
            course_data['online_course_link'] = ''
            course_data['instructor'] = ''
            course_data['estimated_hours'] = 0
        
        # Add course structure (chapters/sections as units)
        try:
            chapters = course.get_children()
            units = []
            for chapter in chapters:
                if hasattr(chapter, 'display_name'):
                    unit_data = {
                        'title': getattr(chapter, 'display_name', 'Chương'),
                        'name': getattr(chapter, 'display_name', 'Chương'),
                        'description': getattr(chapter, 'short_description', '') or 'Chưa có mô tả'
                    }
                    units.append(unit_data)
            course_data['units'] = units
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Could not load course units for {course_key}: {str(e)}")
            course_data['units'] = []
        
        return JsonResponse(course_data)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting course details for {course_key}: {str(e)}")
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
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Get all topics for this program - ensure fresh data
    topics_queryset = ProgramTopic.objects.filter(program=program).order_by('order')
    topics_data = [
        {'id': topic.pk, 'title': topic.title, 'order': topic.order}
        for topic in topics_queryset
    ]
    
    # Log the topics for debugging
    logger.info(f"Program detail {cid}: Found {len(topics_data)} topics: {[t['title'] for t in topics_data]}")
    
    # Get all courses that use this program as template
    associated_courses = LocalCourse.objects.filter(template_program=program).order_by('-created_at')
    courses_data = [
        {
            'id': course.pk,
            'local_course_id': course.pk,
            'course_key': course.course_key,
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
        'short_description': program.short_description,
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
    
    # Create response with cache-busting headers to ensure fresh data
    response = JsonResponse(program_data)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@ensure_csrf_cookie
@require_http_methods(["POST"])
@login_required
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

    # Handle both 'course_key' and 'course_id' field names
    course_key_string = payload.get('course_key', '') or payload.get('course_id', '')
    course_key_string = course_key_string.strip() if course_key_string else ''
    title = payload.get('title', '').strip()
    short_description = payload.get('short_description', '').strip()
    start_date_str = payload.get('start_date')
    end_date_str = payload.get('end_date')
    online_course_link = payload.get('online_course_link', '').strip()
    instructor = payload.get('instructor', '').strip()
    estimated_hours = payload.get('estimated_hours')

    if not course_key_string:
        return JsonResponse({'error': 'Course key is required'}, status=400)
    
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key format'}, status=400)

    # Check if course exists
    store = modulestore()
    course = store.get_course(course_key)
    if not course:
        return JsonResponse({'error': 'Course not found'}, status=404)
    
    # Check user permissions
    if not has_studio_write_access(request.user, course_key):
        return JsonResponse({'error': 'Bạn không có quyền chỉnh sửa khóa học này'}, status=403)

    try:
        from openedx.core.djangoapps.models.course_details import CourseDetails
        
        # Prepare the course update payload similar to how CourseDetails.update_from_json expects it
        course_update_data = {
            'title': title,
            'short_description': short_description,
        }
        
        # Add new fields
        if online_course_link:
            course_update_data['online_course_link'] = online_course_link
        if instructor:
            course_update_data['instructor'] = instructor
        if estimated_hours is not None:
            course_update_data['estimated_hours'] = estimated_hours
        
        # Add course_type and course_level fields from payload
        # Always include these fields even if empty to ensure they get updated
        course_type = payload.get('course_type', '').strip()
        course_update_data['course_type'] = course_type
        
        # Handle both 'level' (backward compatibility) and 'course_level' fields
        level = payload.get('course_level', payload.get('level', '')).strip()
        # Ensure proper encoding for Vietnamese text  
        course_update_data['course_level'] = level
        
        # Add date fields if provided - CourseDetails.update_from_json expects these field names
        if start_date_str:
            course_update_data['start_date'] = start_date_str
        if end_date_str:
            course_update_data['end_date'] = end_date_str
        # Ensure 'overview' and 'intro_video' keys exist and are strings to avoid KeyError
        # and to normalize None values coming from the client.
        course_update_data['overview'] = str(payload.get('overview', '') or '')
        course_update_data['intro_video'] = str(payload.get('intro_video', '') or '')

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Update course API: course_key={course_key_string}, level='{level}', course_type='{course_type}'")

        # Call CourseDetails.update_from_json defensively: if a KeyError occurs because
        # some code path expects a key to exist, set a sensible default and retry once.
        
        try:
            updated_course_details = CourseDetails.update_from_json(course_key, course_update_data, request.user)
        except KeyError as ke:
            # ke.args[0] is the missing key (e.g. 'overview')
            missing_key = str(ke.args[0]) if ke.args else str(ke)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "KeyError %s in CourseDetails.update_from_json; setting default and retrying. payload keys: %s",
                missing_key,
                list(course_update_data.keys()),
            )
            # Set a default for the missing key and retry once
            course_update_data[missing_key] = ''
            updated_course_details = CourseDetails.update_from_json(course_key, course_update_data, request.user)

        # Return updated course data - get fresh course block to include course_type and course_level
        store = modulestore()
        # Force refresh from database to avoid caching issues
        updated_block = store.get_course(course_key, depth=0)
        
        # Log the successful update
        logger.info(f"Course updated successfully: course_type='{getattr(updated_block, 'course_type', '')}', course_level='{getattr(updated_block, 'course_level', '')}'")
        
        return JsonResponse({
            'course_key': str(course_key),
            'title': updated_course_details.title,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'short_description': updated_course_details.short_description,
            'course_type': getattr(updated_block, 'course_type', ''),
            'course_level': getattr(updated_block, 'course_level', ''),
            'online_course_link': getattr(updated_course_details, 'online_course_link', ''),
            'instructor': getattr(updated_course_details, 'instructor', ''),
            'estimated_hours': getattr(updated_course_details, 'estimated_hours', 0),
            'start_date': updated_course_details.start_date.isoformat() if updated_course_details.start_date else None,
            'end_date': updated_course_details.end_date.isoformat() if updated_course_details.end_date else None,
            'message': 'Đã cập nhật khóa học thành công!'
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating course {course_key_string}: {str(e)}")
        return JsonResponse({
            'error': 'Có lỗi xảy ra khi cập nhật khóa học. Vui lòng thử lại.'
        }, status=500)


@login_required
@require_POST
def delete_course_api(request):
    """Delete an OpenEDX course by course key or local id.

    Expects JSON: { "course_id": <local id> } OR { "course_key": "course-v1:org+num+run" }
    Only users with studio write access or staff may delete a course.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    course_id = payload.get('course_id')
    course_key_string = payload.get('course_key')

    # If local DB model used for LocalCourse, attempt to delete by PK
    if course_id:
        try:
            lc = LocalCourse.objects.get(pk=course_id)
        except LocalCourse.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)

        # Permission check: only creator or staff can delete LocalCourse
        if not (request.user.is_staff or getattr(lc.created_by, 'id', None) == request.user.id):
            return JsonResponse({'error': 'Bạn không có quyền xóa khóa học này'}, status=403)

        lc.delete()
        return JsonResponse({'success': True, 'message': 'Đã xóa khóa học thành công'})

    # Otherwise try to delete by course key using modulestore
    if not course_key_string:
        return JsonResponse({'error': 'Course identifier required'}, status=400)

    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key format'}, status=400)

    # Permission: require studio write access to delete course
    if not has_studio_write_access(request.user, course_key):
        return JsonResponse({'error': 'Bạn không có quyền xóa khóa học này'}, status=403)

    try:
        store = modulestore()
        course = store.get_course(course_key)
        if not course:
            return JsonResponse({'error': 'Course not found'}, status=404)

        # Use modulestore to delete course
        store.delete_course(course_key, request.user.id)

        return JsonResponse({'success': True, 'message': 'Đã xóa khóa học thành công'})

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Failed to delete course {course_key_string}: {str(e)}")
        return JsonResponse({'error': 'Không thể xóa khóa học, vui lòng thử lại'}, status=500)


@login_required
@require_POST
def delete_program_api(request):
    """Delete a LocalProgram by id.

    Expects JSON: { "program_id": <id> }
    Only staff or creator can delete.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    program_id = payload.get('program_id')
    if not program_id:
        return JsonResponse({'error': 'Program ID is required'}, status=400)

    try:
        prog = LocalProgram.objects.get(pk=program_id)
    except LocalProgram.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)

    # Permission check
    if not (request.user.is_staff or getattr(prog.created_by, 'id', None) == request.user.id):
        return JsonResponse({'error': 'Bạn không có quyền xóa chương trình này'}, status=403)

    try:
        prog.delete()
        return JsonResponse({'success': True, 'message': 'Đã xóa chương trình học thành công'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Failed to delete program {program_id}: {str(e)}")
        return JsonResponse({'error': 'Không thể xóa chương trình, vui lòng thử lại'}, status=500)


@login_required
@require_cms_access
@require_http_methods(['GET', 'POST'])
def dashboard_api(request):
    """
    API endpoint for dashboard tabs.
    Handles different tab requests including statistics.
    """
    tab = request.GET.get('tab', '')
    
    if tab == 'statistics':
        return _get_statistics_data(request)
    else:
        return JsonResponse({'error': 'Invalid tab specified'}, status=400)


def _get_statistics_data(request):
    """
    Get statistics data for the dashboard.
    
    This function provides learner statistics with filtering options:
    - Filter by learner phone
    - Filter by learner name  
    - Filter by year
    - Filter by completion status (calculated as total estimated hours / 40 hours)
    """
    from django.core.paginator import Paginator
    from django.db.models import Q, Count, Sum, Avg
    from common.djangoapps.student.models import UserProfile, CourseEnrollment, User
    from lms.djangoapps.grades.models import PersistentCourseGrade
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    import re
    
    # Check if this is an export request
    if request.GET.get('export') == 'csv':
        return _export_statistics_csv(request)
    
    # Get filter parameters
    phone_filter = request.GET.get('phone', '').strip()
    name_filter = request.GET.get('name', '').strip()
    year_filter = request.GET.get('year', '').strip()
    completion_filter = request.GET.get('completion', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = 20
    
    # Base queryset - get all users with profiles and enrollments
    users_query = User.objects.select_related('profile').filter(
        courseenrollment__is_active=True
    ).distinct()
    
    # Apply phone filter
    if phone_filter:
        users_query = users_query.filter(
            Q(profile__phone_number__icontains=phone_filter)
        )
    
    # Apply name filter
    if name_filter:
        users_query = users_query.filter(
            Q(profile__name__icontains=name_filter) |
            Q(first_name__icontains=name_filter) |
            Q(last_name__icontains=name_filter)
        )
    
    # Apply year filter (based on enrollment date)
    if year_filter:
        users_query = users_query.filter(
            courseenrollment__created__year=int(year_filter)
        )
    
    # Get learner statistics
    learners_data = []
    total_learners = users_query.count()
    completed_learners = 0
    total_completion_sum = 0
    total_hours_sum = 0
    
    for user in users_query:
        # Get user's enrollments
        enrollments = CourseEnrollment.objects.filter(
            user=user, 
            is_active=True
        ).select_related('course')
        
        if not enrollments.exists():
            continue
            
        # Calculate total estimated hours and completion
        total_estimated_hours = 0
        completion_percentage = 0
        
        for enrollment in enrollments:
            try:
                # Get course overview for estimated hours
                course_overview = CourseOverview.objects.get(id=enrollment.course_id)
                # Use effort field if available, otherwise estimate based on course length
                if hasattr(course_overview, 'effort') and course_overview.effort:
                    # Parse effort string like "2-3 hours/week" or "10 hours"
                    effort_str = str(course_overview.effort).lower()
                    hours_match = re.search(r'(\d+)', effort_str)
                    if hours_match:
                        weekly_hours = int(hours_match.group(1))
                        # Estimate total hours (assuming 10-week course)
                        total_estimated_hours += weekly_hours * 10
                else:
                    # Default estimate: 20 hours per course
                    total_estimated_hours += 20
                
                # Get grade/completion data
                try:
                    grade = PersistentCourseGrade.objects.get(
                        user_id=user.id,
                        course_id=enrollment.course_id
                    )
                    if grade.percent_grade is not None:
                        # Convert grade percentage to completion hours
                        completion_percentage += (grade.percent_grade * 100)
                except PersistentCourseGrade.DoesNotExist:
                    completion_percentage += 0
                    
            except CourseOverview.DoesNotExist:
                # If course overview doesn't exist, use default
                total_estimated_hours += 20
                completion_percentage += 0
        
        # Calculate average completion percentage across all courses
        if enrollments.count() > 0:
            completion_percentage = completion_percentage / enrollments.count()
        
        # Apply completion filter
        if completion_filter:
            if completion_filter == 'completed' and completion_percentage < 100:
                continue
            elif completion_filter == '80' and (completion_percentage < 80 or completion_percentage >= 100):
                continue
            elif completion_filter == '60' and (completion_percentage < 60 or completion_percentage >= 80):
                continue
            elif completion_filter == '50' and (completion_percentage < 50 or completion_percentage >= 60):
                continue
            elif completion_filter == 'under_50' and completion_percentage >= 50:
                continue
        
        # Get enrollment year (most recent)
        latest_enrollment = enrollments.order_by('-created').first()
        enrollment_year = latest_enrollment.created.year if latest_enrollment else datetime.now().year
        
        learner_data = {
            'id': user.id,
            'name': user.profile.name if hasattr(user, 'profile') and user.profile.name else f"{user.first_name} {user.last_name}".strip(),
            'phone': user.profile.phone_number if hasattr(user, 'profile') else None,
            'year': enrollment_year,
            'total_hours': round(total_estimated_hours * (completion_percentage / 100), 1),
            'completion_percentage': round(completion_percentage, 1),
            'enrollments_count': enrollments.count()
        }
        
        learners_data.append(learner_data)
        total_completion_sum += completion_percentage
        total_hours_sum += learner_data['total_hours']
        
        if completion_percentage >= 100:
            completed_learners += 1
    
    # Sort learners by completion percentage (descending)
    learners_data.sort(key=lambda x: x['completion_percentage'], reverse=True)
    
    # Paginate results
    paginator = Paginator(learners_data, per_page)
    page_obj = paginator.get_page(page)
    
    # Calculate summary statistics
    average_completion = (total_completion_sum / len(learners_data)) if learners_data else 0
    average_hours = (total_hours_sum / len(learners_data)) if learners_data else 0
    
    stats_data = {
        'summary': {
            'total_learners': total_learners,
            'completed_learners': completed_learners,
            'completion_rate': round(average_completion, 1),
            'average_hours': round(average_hours, 1)
        },
        'learners': list(page_obj.object_list),
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'per_page': per_page,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next()
        }
    }
    
    return JsonResponse(stats_data)


def _export_statistics_csv(request):
    """Export statistics data as CSV file."""
    from django.db.models import Q
    from common.djangoapps.student.models import UserProfile, CourseEnrollment, User
    from lms.djangoapps.grades.models import PersistentCourseGrade
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    import re
    
    # Get filter parameters (same as main function)
    phone_filter = request.GET.get('phone', '').strip()
    name_filter = request.GET.get('name', '').strip()
    year_filter = request.GET.get('year', '').strip()
    completion_filter = request.GET.get('completion', '').strip()
    
    # Base queryset
    users_query = User.objects.select_related('profile').filter(
        courseenrollment__is_active=True
    ).distinct()
    
    # Apply filters (same logic as main function)
    if phone_filter:
        users_query = users_query.filter(Q(profile__phone_number__icontains=phone_filter))
    if name_filter:
        users_query = users_query.filter(
            Q(profile__name__icontains=name_filter) |
            Q(first_name__icontains=name_filter) |
            Q(last_name__icontains=name_filter)
        )
    if year_filter:
        users_query = users_query.filter(courseenrollment__created__year=int(year_filter))
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="thong-ke-nguoi-hoc-{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # Add BOM for proper UTF-8 encoding in Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(['STT', 'Tên người học', 'Số điện thoại', 'Năm', 'Tổng giờ học', 'Tỷ lệ hoàn thành (%)', 'Trạng thái'])
    
    # Write data rows
    row_num = 1
    for user in users_query:
        enrollments = CourseEnrollment.objects.filter(user=user, is_active=True).select_related('course')
        if not enrollments.exists():
            continue
            
        # Calculate statistics (same logic as main function)
        total_estimated_hours = 0
        completion_percentage = 0
        
        for enrollment in enrollments:
            try:
                course_overview = CourseOverview.objects.get(id=enrollment.course_id)
                if hasattr(course_overview, 'effort') and course_overview.effort:
                    effort_str = str(course_overview.effort).lower()
                    hours_match = re.search(r'(\d+)', effort_str)
                    if hours_match:
                        weekly_hours = int(hours_match.group(1))
                        total_estimated_hours += weekly_hours * 10
                else:
                    total_estimated_hours += 20
                
                try:
                    grade = PersistentCourseGrade.objects.get(user_id=user.id, course_id=enrollment.course_id)
                    if grade.percent_grade is not None:
                        completion_percentage += (grade.percent_grade * 100)
                except PersistentCourseGrade.DoesNotExist:
                    completion_percentage += 0
            except CourseOverview.DoesNotExist:
                total_estimated_hours += 20
                completion_percentage += 0
        
        if enrollments.count() > 0:
            completion_percentage = completion_percentage / enrollments.count()
        
        # Apply completion filter
        if completion_filter:
            if completion_filter == 'completed' and completion_percentage < 100:
                continue
            elif completion_filter == '80' and (completion_percentage < 80 or completion_percentage >= 100):
                continue
            elif completion_filter == '60' and (completion_percentage < 60 or completion_percentage >= 80):
                continue
            elif completion_filter == '50' and (completion_percentage < 50 or completion_percentage >= 60):
                continue
            elif completion_filter == 'under_50' and completion_percentage >= 50:
                continue
        
        # Get data
        latest_enrollment = enrollments.order_by('-created').first()
        enrollment_year = latest_enrollment.created.year if latest_enrollment else datetime.now().year
        name = user.profile.name if hasattr(user, 'profile') and user.profile.name else f"{user.first_name} {user.last_name}".strip()
        phone = user.profile.phone_number if hasattr(user, 'profile') else 'N/A'
        total_hours = round(total_estimated_hours * (completion_percentage / 100), 1)
        completion_pct = round(completion_percentage, 1)
        
        # Determine status
        if completion_pct >= 100:
            status = 'Đạt (100%)'
        elif completion_pct >= 80:
            status = '80%'
        elif completion_pct >= 60:
            status = '60%'
        elif completion_pct >= 50:
            status = '50%'
        else:
            status = 'Ít hơn 50%'
        
        writer.writerow([row_num, name, phone, enrollment_year, total_hours, completion_pct, status])
        row_num += 1
    
    return response
