"""
Dashboard views for Vietnamese CMS interface with role-based access control
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.models import F
import json
import uuid
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Local models
from cms.djangoapps.contentstore.models import (
    LocalCourse,
    LocalProgram,
    ProgramTopic,
    ChalixCourseMetadata,
    ChalixTopicEmotionAggregate,
)
from cms.djangoapps.contentstore.chalix_roles import (
    can_access_cms,
    require_cms_access,
    get_available_tabs,
    get_user_organization_display_name,
    get_user_primary_role,
    require_role,
    is_bo_user,
    can_author_survey,
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


def _normalize_correct_answer_token(raw_value):
    """Normalize Excel correct-answer token to one of A/B/C/D."""
    raw = str(raw_value).strip().upper()
    if not raw:
        return None

    numeric_map = {
        '1': 'A',
        '2': 'B',
        '3': 'C',
        '4': 'D',
    }
    if raw in numeric_map:
        return numeric_map[raw]

    if raw in ('A', 'B', 'C', 'D'):
        return raw

    compact = ''.join(ch for ch in raw if ch.isalnum())
    if compact in numeric_map:
        return numeric_map[compact]
    if compact in ('A', 'B', 'C', 'D'):
        return compact
    if compact and compact[-1] in ('A', 'B', 'C', 'D'):
        return compact[-1]

    return None


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

    # Add final evaluation topic
    final_evaluation_sequential = store.create_child(
        user_id,
        main_chapter.location,
        'sequential',
        fields={
            'display_name': 'Kiểm tra cuối khoá',
        }
    )
    
    # Create an empty unit for the final evaluation
    final_evaluation_vertical = store.create_child(
        user_id,
        final_evaluation_sequential.location,
        'vertical',
        fields={
            'display_name': 'Kiểm tra cuối khoá - Bài kiểm tra',
        }
    )
    
    # Publish the final evaluation components
    store.publish(final_evaluation_sequential.location, user_id)
    store.publish(final_evaluation_vertical.location, user_id)
    units_created += 1

    # Publish the main chapter
    store.publish(main_chapter.location, user_id)
    
    # Create FinalEvaluation record based on program settings
    try:
        from cms.djangoapps.contentstore.models import FinalEvaluation
        
        # Check which evaluation types the program allows
        if template_program.allow_practical_submission:
            FinalEvaluation.objects.create(
                course_key=course_key,
                program=template_program,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL
            )
        
        if template_program.allow_multiple_choice:
            FinalEvaluation.objects.create(
                course_key=course_key,
                program=template_program,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ
            )
            
        # If neither is set, default to practical
        if not template_program.allow_practical_submission and not template_program.allow_multiple_choice:
            FinalEvaluation.objects.create(
                course_key=course_key,
                program=template_program,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL
            )
    except Exception as e:
        logger.warning(f"Failed to create FinalEvaluation record for course {course_key}: {e}")
    
    return units_created


@login_required
@ensure_csrf_cookie
def cms_dashboard(request):
    """
    Displays the CMS dashboard.
    This is the main landing page after login with role-based tab access:
    - Thống kê (Statistics) - Bộ role only
    - Tạo tài khoản cán bộ (Create Staff Account) - Cơ quan only
    - Quản lý (Management) - Bộ, Cơ quan
    - Quản lý khóa học (Course Management) - Giảng viên, Cơ quan
    - Phê duyệt yêu cầu (Approve Requests) - Cơ quan only
    """
    user = request.user
    
    # Check if user can access CMS
    if not can_access_cms(user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Bạn không có quyền truy cập CMS. Vui lòng liên hệ quản trị viên.")
    
    # Get user permissions and role info
    is_staff = user.is_staff
    is_global_staff = GlobalStaff().has_user(user)
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
    
    # Get MFE URLs from settings for navigation
    from django.conf import settings
    mfe_config = getattr(settings, 'MFE_CONFIG', {})
    lms_base_url = mfe_config.get('LMS_BASE_URL') or getattr(settings, 'LMS_ROOT_URL', '')
    learning_base_url = mfe_config.get('LEARNING_BASE_URL', lms_base_url)
    learner_dashboard_url = mfe_config.get('LEARNER_DASHBOARD_URL', f'{lms_base_url}/dashboard')
    account_profile_url = mfe_config.get('ACCOUNT_PROFILE_URL', lms_base_url)
    
    # Prepare context for template
    context = {
        'user': user,
        'user_info': user_info,
        'account_url': account_url,
        'is_staff': is_staff,
        'is_global_staff': is_global_staff,
        'user_role': user_role,
        'user_role_code': user_role.role if user_role else '',  # Add role code for JavaScript
        'organization_name': organization_name,
        'available_tabs': available_tabs,
        'courses_count': len(courses_list),
        'in_process_count': len(in_process_course_actions),
        'page_title': 'CMS Dashboard',
        'active_tab': request.GET.get('tab', 'statistics'),  # Default to statistics tab
        # MFE URLs for navigation
        'learning_base_url': learning_base_url,
        'learner_dashboard_url': learner_dashboard_url,
        'account_profile_url': account_profile_url,
    }
    
    return render_to_response('dashboard.html', context)


@login_required
def dashboard_api(request):
    """
    API endpoint to get dashboard data via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': _('Yêu cầu đăng nhập')}, status=401)
    
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def survey_results(request, survey_id):
    """
    Return per-choice vote_count and percentage for a survey.
    Accessible only to users who can author surveys (bo / co_quan / global_staff).
    """
    if not can_author_survey(request.user):
        return Response({'error': 'Forbidden'}, status=403)

    try:
        from cms.djangoapps.contentstore.models import ChalixDemandSurvey, ChalixDemandSurveyChoice
        survey = ChalixDemandSurvey.objects.get(pk=survey_id, is_active=True)
    except ChalixDemandSurvey.DoesNotExist:
        return Response({'error': 'Survey not found'}, status=404)

    choices = ChalixDemandSurveyChoice.objects.filter(
        survey=survey, is_active=True
    ).order_by('group_order', 'order_index')

    total_votes = sum(c.vote_count for c in choices)

    choice_data = [
        {
            'id': c.id,
            'name': c.name,
            'group_name': c.group_name,
            'vote_count': c.vote_count,
            'percentage': round(c.vote_count / total_votes * 100, 1) if total_votes > 0 else 0,
        }
        for c in choices
    ]

    return Response({
        'success': True,
        'survey_id': survey.pk,
        'title': survey.title,
        'total_votes': total_votes,
        'choices': choice_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def survey_choice_respondents(request, choice_id):
    """
    Return a list of respondents who voted for a specific choice.
    Used for the "Chi tiết thành viên" popup in CMS.
    """
    if not can_author_survey(request.user):
        return Response({'error': 'Forbidden'}, status=403)

    try:
        from cms.djangoapps.contentstore.models import ChalixSurveyChoice
        choice = ChalixSurveyChoice.objects.get(pk=choice_id, is_active=True)
    except ChalixSurveyChoice.DoesNotExist:
        return Response({'error': 'Choice not found'}, status=404)
    except Exception as exc:
        logger.error('survey_choice_respondents model lookup failed: %s', exc, exc_info=True)
        return Response({'error': 'Choice model not available'}, status=500)

    # CMS runtime might not include the chalix_user_menu app, so query shared tables directly.
    table_pairs = [
        (
            'chalix_user_menu_chalixdemandsurveyresponsechoice',
            'chalix_user_menu_chalixdemandsurveyresponse',
        ),
        (
            'lms_djangoapps_chalix_user_menu_chalixdemandsurveyresponsechoice',
            'lms_djangoapps_chalix_user_menu_chalixdemandsurveyresponse',
        ),
    ]

    rows = None
    with connection.cursor() as cursor:
        for response_choice_table, response_table in table_pairs:
            sql = f"""
                SELECT r.full_name, r.email, r.phone_number, r.submitted_at
                FROM {response_choice_table} rc
                INNER JOIN {response_table} r ON rc.response_id = r.id
                WHERE rc.choice_id = %s
                ORDER BY r.submitted_at DESC
            """
            try:
                cursor.execute(sql, [choice_id])
                rows = cursor.fetchall()
                break
            except Exception:
                continue

    if rows is None:
        logger.error('survey_choice_respondents could not query response tables for choice_id=%s', choice_id)
        return Response({'error': 'Response data unavailable'}, status=500)

    respondents = [
        {
            'full_name': row[0] or '',
            'email': row[1] or '',
            'phone_number': row[2] or '',
            'submitted_at': row[3].isoformat() if hasattr(row[3], 'isoformat') else str(row[3] or ''),
        }
        for row in rows
    ]

    return Response({
        'success': True,
        'choice_id': choice_id,
        'choice_name': choice.name,
        'respondents': respondents
    })

    User = get_user_model()

    def _to_number(value, default=0):
        try:
            if value in (None, ''):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    if page < 1:
        page = 1

    per_page = 50
    year_value = 2026

    # Scope learners by current user's role visibility.
    current_role = get_user_primary_role(request.user)
    role_qs = ChalixUserRole.objects.filter(is_active=True).select_related('organization')

    if is_bo_user(request.user):
        pass
    elif current_role and getattr(current_role, 'organization_id', None):
        role_qs = role_qs.filter(organization_id=current_role.organization_id)
    else:
        role_qs = role_qs.none()

    visible_user_ids = role_qs.values_list('user_id', flat=True).distinct()
    users_qs = User.objects.filter(id__in=visible_user_ids).select_related('profile').order_by('id')

    name_query = (request.GET.get('name') or '').strip()
    if name_query:
        users_qs = users_qs.filter(
            Q(profile__name__icontains=name_query)
            | Q(username__icontains=name_query)
            | Q(email__icontains=name_query)
        )

    total_items = users_qs.count()
    start = (page - 1) * per_page
    end = start + per_page
    users_page = list(users_qs[start:end])

    learners = []
    completed_count = 0
    total_hours_sum = 0

    for user in users_page:
        profile = getattr(user, 'profile', None)
        full_name = None
        if profile and getattr(profile, 'name', None):
            full_name = profile.name
        else:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username

        meta = {}
        if profile:
            try:
                meta = profile.get_meta() if hasattr(profile, 'get_meta') else {}
            except Exception:
                meta = {}

        total_studied_time = _to_number(
            meta.get('total_studied_time', meta.get('total_hours', 0)),
            default=0,
        )
        completed_percentage = _to_number(
            meta.get('completed_percentage', meta.get('completion_percentage', 0)),
            default=0,
        )
        status_raw = meta.get('status', '')
        status_value = status_raw.strip() if isinstance(status_raw, str) else status_raw

        if completed_percentage >= 100:
            completed_count += 1
        total_hours_sum += total_studied_time

        learners.append({
            'name': full_name,
            'phone': '',
            'year': year_value,
            'total_studied_time': total_studied_time,
            'completed_percentage': completed_percentage,
            'status': status_value,
            # Backward-compatible aliases for older frontend code paths.
            'total_hours': total_studied_time,
            'completion_percentage': completed_percentage,
        })

    total_pages = (total_items + per_page - 1) // per_page if total_items else 0
    average_hours = (total_hours_sum / len(learners)) if learners else 0

    return {
        'summary': {
            'total_learners': total_items,
            'completed_learners': completed_count,
            'completion_rate': round((completed_count / len(learners)) * 100, 2) if learners else 0,
            'average_hours': round(average_hours, 2),
        },
        'course_completions': [],
        'organization_completions': [],
        'organization_courses': [],
        'learners': learners,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_items,
            'per_page': per_page,
        },
    }


def _get_create_account_data(request):
    """Get data for creating staff accounts"""
    from cms.djangoapps.contentstore.chalix_roles import can_import_users, get_user_primary_role
    
    # Check if user has permission to import users via Excel
    excel_import_enabled = can_import_users(request.user)
    
    # Debug logging
    primary_role = get_user_primary_role(request.user)
    logger.info(f"[Create Account Data] User: {request.user.username}, Primary role: {primary_role}, Excel import enabled: {excel_import_enabled}")
    if primary_role:
        logger.info(f"[Create Account Data] Role details - role: {primary_role.role}, is_active: {primary_role.is_active}")
    
    return {
        'pending_requests': 0,  # Will be implemented later
        'total_accounts': 0,    # Will be implemented later
        'excel_import_enabled': excel_import_enabled,
        'template_download_url': '/api/contentstore/v1/users/excel/template' if excel_import_enabled else None,
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
    
    Only users with giang_vien, co_quan, or bo roles can create courses.
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
        require_role(request.user, ['giang_vien', 'co_quan', 'bo'])
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
    course_category = _get_payload_value(payload, 'course_category', 'courseCategory', default='')
    online_course_link = _get_payload_value(payload, 'online_course_link', 'onlineCourseLink', default='')
    instructor = _get_payload_value(payload, 'instructor', default='')
    instructor_username = _get_payload_value(payload, 'instructor_username', 'instructorUsername', default='')
    professional_field_id = _get_payload_value(payload, 'professional_field_id', 'professionalFieldId', default='')
    estimated_hours_raw = _get_payload_value(payload, 'estimated_hours', 'estimatedHours', default=None)
    final_evaluation_type = _get_payload_value(payload, 'final_evaluation_type', 'finalEvaluationType', default='')

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
        # Get course_level from payload
        course_level = _get_payload_value(payload, 'course_level', 'courseLevel', default='')
        from cms.djangoapps.contentstore.chalix_roles import get_user_primary_role
        primary_role = get_user_primary_role(request.user)
        role_name = primary_role.role if primary_role else None

        # Normalize category and role permissions for mandatory/elective course creation.
        if course_category not in ('mandatory', 'elective'):
            course_category = ''
        if course_category and role_name not in ('bo', 'co_quan'):
            course_category = ''

        # Normalize professional field ID (optional)
        if professional_field_id in (None, ''):
            professional_field_id = ''
        else:
            try:
                professional_field_id = str(int(professional_field_id))
            except (TypeError, ValueError):
                return JsonResponse({'errMsg': 'Lĩnh vực chuyên môn không hợp lệ.'}, status=400)
        
        course_fields = {
            'display_name': title,
            'course_type': course_type,
            'course_level': course_level,
        }

        # Keep category/professional_field in Chalix metadata only.
        # Passing non-standard keys into create_new_course can fail course creation.
        
        # Set final_evaluation_type (from payload or inherit from template program)
        if final_evaluation_type:
            # Use direct value from payload if provided
            course_fields['final_evaluation_type'] = final_evaluation_type
            logger.info(f"[CHALIX] Setting final_evaluation_type on course block from payload: {final_evaluation_type}")
        elif template_program:
            # Determine evaluation type based on program settings
            if template_program.allow_practical_submission and template_program.allow_multiple_choice:
                # If both are allowed, default to quiz (could be changed later by instructor)
                course_fields['final_evaluation_type'] = 'quiz'
            elif template_program.allow_practical_submission:
                course_fields['final_evaluation_type'] = 'project'
            elif template_program.allow_multiple_choice:
                course_fields['final_evaluation_type'] = 'quiz'
            else:
                # Default to project if neither is explicitly set
                course_fields['final_evaluation_type'] = 'project'
            logger.info(f"[CHALIX] Setting final_evaluation_type on course block from template program: {course_fields['final_evaluation_type']}")
        else:
            # Default to empty if no template program
            course_fields['final_evaluation_type'] = ''
        
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
        
        # Create Chalix course metadata for visibility and access control
        is_public_course = False
        creator_role = None
        creator_org = None
        
        if primary_role:
            creator_role = primary_role.role
            creator_org = primary_role.organization
            # Courses created by 'bo' (ministry level) are public
            is_public_course = (creator_role == 'bo')

        selected_professional_field = None
        if professional_field_id:
            try:
                from cms.djangoapps.contentstore.models import ProfessionalField
                selected_professional_field = ProfessionalField.objects.filter(
                    id=int(professional_field_id),
                    is_active=True,
                ).first()
            except Exception:
                selected_professional_field = None

        metadata_defaults = {
            'creator': request.user,
            'creator_role': creator_role,
            'creator_organization': creator_org,
            'is_public': is_public_course,
            'is_mandatory_course': (course_category == 'mandatory'),
            'course_category': course_category or None,
            'publish_type': course_category or None,
            'professional_field': selected_professional_field,
        }

        metadata, created = ChalixCourseMetadata.objects.get_or_create(
            course_id=course_key,
            defaults=metadata_defaults,
        )

        if not created:
            metadata.creator = metadata.creator or request.user
            metadata.creator_role = creator_role
            metadata.creator_organization = creator_org
            metadata.is_public = is_public_course
            if course_category:
                metadata.course_category = course_category
                metadata.publish_type = course_category
                metadata.is_mandatory_course = (course_category == 'mandatory')

            if professional_field_id:
                metadata.professional_field = selected_professional_field or metadata.professional_field

            metadata.save()

        logger.info(f"[CHALIX] Created course metadata - Public: {is_public_course}, Role: {creator_role}, Org: {creator_org}")

        # Assign instructor if selected in form
        if instructor_username:
            try:
                from common.djangoapps.student.models import User
                from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
                from common.djangoapps.student.models import CourseEnrollment
                instructor_user = User.objects.get(username=instructor_username, is_active=True)
                CourseInstructorRole(course_key).add_users(instructor_user)
                CourseStaffRole(course_key).add_users(instructor_user)
                CourseEnrollment.enroll(instructor_user, course_key)
            except Exception as assign_error:
                logger.warning("[CHALIX] Failed to assign instructor '%s' to %s: %s", instructor_username, course_key, assign_error)
        
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
        if short_description or online_course_link or instructor or estimated_hours is not None or template_program:
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
                
                # Always include course_type and course_level to ensure they are saved
                course_update_data['course_type'] = course_type
                course_update_data['course_level'] = course_level
                
                # Set final_evaluation_type (from payload or inherit from template program)
                if final_evaluation_type:
                    # Use direct value from payload if provided
                    course_update_data['final_evaluation_type'] = final_evaluation_type
                    logger.info(f"[CHALIX] Setting final_evaluation_type from payload: {final_evaluation_type}")
                elif template_program:
                    # Determine evaluation type based on program settings
                    if template_program.allow_practical_submission and template_program.allow_multiple_choice:
                        # If both are allowed, default to quiz (could be changed later by instructor)
                        course_update_data['final_evaluation_type'] = 'quiz'
                    elif template_program.allow_practical_submission:
                        course_update_data['final_evaluation_type'] = 'project'
                    elif template_program.allow_multiple_choice:
                        course_update_data['final_evaluation_type'] = 'quiz'
                    else:
                        # Default to project if neither is explicitly set
                        course_update_data['final_evaluation_type'] = 'project'
                    logger.info(f"[CHALIX] Setting final_evaluation_type from template program: {course_update_data['final_evaluation_type']}")
                else:
                    # No template program, set empty
                    course_update_data['final_evaluation_type'] = ''
                    logger.info("[CHALIX] No final_evaluation_type specified and no template program")
                
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

    # Keep creator-created courses visible even if role/group index is temporarily stale.
    existing_ids = {str(getattr(course, 'id', '')) for course in courses_list}
    try:
        local_created_keys = list(
            LocalCourse.objects.filter(created_by=request.user)
            .exclude(course_key__isnull=True)
            .exclude(course_key='')
            .values_list('course_key', flat=True)
            .distinct()
        )
        if local_created_keys:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
            overview_map = {
                str(overview.id): overview
                for overview in CourseOverview.objects.filter(id__in=local_created_keys)
            }
            for key in local_created_keys:
                if key not in existing_ids and key in overview_map:
                    courses_list.append(overview_map[key])
                    existing_ids.add(key)
    except Exception as e:
        logger.warning("Could not append locally created course list fallback: %s", e)
    
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
                'course_category': None,  # Will be populated from metadata
                'creator_role': None,  # Will be populated from metadata
                'is_public': None,  # Will be populated from metadata
            }
            # Try to enrich with additional fields stored on the modulestore course block
            try:
                # Use CourseDetails.fetch which consolidates course block attributes
                try:
                    details = CourseDetails.fetch(course_key)
                    formatted_course['online_course_link'] = getattr(details, 'online_course_link', '')
                    formatted_course['instructor'] = getattr(details, 'instructor', '')
                    formatted_course['estimated_hours'] = getattr(details, 'estimated_hours', 0)
                    formatted_course['final_evaluation_type'] = getattr(details, 'final_evaluation_type', '')
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
                        formatted_course['final_evaluation_type'] = getattr(block, 'final_evaluation_type', '')
                        formatted_course['course_type'] = getattr(block, 'course_type', '')
                        formatted_course['course_level'] = getattr(block, 'course_level', '')
            except Exception:
                # If enrichment fails, continue without the extra fields
                pass
            
            # Get units/sections from the course
            units = []
            try:
                store = modulestore()
                course_block = store.get_course(course_key, depth=2)  # depth=2 to get sections and sequences
                if course_block and hasattr(course_block, 'get_children'):
                    for section in course_block.get_children():
                        if section.category == 'chapter':
                            for sequence in section.get_children():
                                if sequence.category == 'sequential':
                                    units.append({
                                        'title': sequence.display_name or 'Untitled',
                                        'name': sequence.display_name or 'Untitled',
                                        'usage_key': str(sequence.location)
                                    })
            except Exception:
                pass
            
            formatted_course['units'] = units
            
            # Get ChalixCourseMetadata fields (local import to avoid NameError if module reload hasn't occurred)
            try:
                from cms.djangoapps.contentstore.models import ChalixCourseMetadata
                metadata = ChalixCourseMetadata.objects.filter(course_id=course_key).first()
                if metadata:
                    formatted_course['course_category'] = metadata.course_category
                    formatted_course['creator_role'] = metadata.creator_role
                    formatted_course['is_public'] = metadata.is_public
                    logger.debug(f"Found metadata for {course_key}: category={metadata.course_category}, role={metadata.creator_role}, public={metadata.is_public}")
                else:
                    logger.warning(f"No metadata found for {course_key}")
            except Exception as e:
                # If metadata fetch fails, leave fields as None
                logger.error(f"Error fetching metadata for {course_key}: {e}", exc_info=True)
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
    
    Only users with giang_vien, co_quan, or bo roles can create programs.

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
        require_role(request.user, ['giang_vien', 'co_quan', 'bo'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền tạo chương trình học'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)

    title = payload.get('title', '').strip()
    short_description = payload.get('short_description', '').strip()
    icon = payload.get('icon', 'seed-of-life')
    update_topics = payload.get('update_topics', False)
    topics = payload.get('topics', [])
    
    # Get evaluation format options
    allow_practical_submission = payload.get('allow_practical_submission', True)
    allow_multiple_choice = payload.get('allow_multiple_choice', False)

    if not title:
        return JsonResponse({'error': _('Tiêu đề là bắt buộc')}, status=400)

    # Use database transaction to ensure atomicity
    from django.db import transaction
    from cms.djangoapps.contentstore.chalix_roles import get_user_organization
    from cms.djangoapps.contentstore.models import ChalixOrganization
    
    try:
        with transaction.atomic():
            # Get the user's organization
            user_organization = get_user_organization(request.user)
            
            # If user has no organization, use the default Bộ organization
            if not user_organization:
                user_organization, _ = ChalixOrganization.objects.get_or_create(
                    code='BO_DEFAULT',
                    defaults={
                        'name': 'bo_default',
                        'display_name': 'Bộ (Mặc định)',
                        'description': 'Tổ chức mặc định cho các chương trình học được tạo trước đây',
                        'is_active': True,
                    }
                )
            
            # Create the program
            program = LocalProgram.objects.create(
                title=title,
                short_description=short_description,
                icon=icon,
                update_topics=update_topics,
                allow_practical_submission=allow_practical_submission,
                allow_multiple_choice=allow_multiple_choice,
                organization=user_organization,
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
            'allow_practical_submission': program.allow_practical_submission,
            'allow_multiple_choice': program.allow_multiple_choice,
            'topics': topics_data,
            'created_at': program.created_at.isoformat(),
            'organization': {
                'id': program.organization.pk,
                'name': program.organization.name,
                'display_name': program.organization.display_name
            } if program.organization else None,
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
    
    Only users with giang_vien, co_quan, or bo roles can update programs.

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
        require_role(request.user, ['giang_vien', 'co_quan', 'bo'])
    except PermissionDenied:
        return JsonResponse({'error': 'Bạn không có quyền cập nhật chương trình học'}, status=403)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)

    program_id = payload.get('id')
    title = payload.get('title', '').strip()
    short_description = payload.get('short_description', '').strip()
    icon = payload.get('icon', 'seed-of-life')
    update_topics = payload.get('update_topics', False)
    topics = payload.get('topics', [])

    if not program_id:
        return JsonResponse({'error': _('Mã chương trình là bắt buộc')}, status=400)
    
    if not title:
        return JsonResponse({'error': _('Tiêu đề là bắt buộc')}, status=400)

    # Get the program to update
    try:
        program = LocalProgram.objects.get(pk=program_id)
    except LocalProgram.DoesNotExist:
        return JsonResponse({'error': _('Không tìm thấy chương trình')}, status=404)

    # Use database transaction to ensure atomicity
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Update the program fields
            program.title = title
            program.short_description = short_description
            program.icon = icon
            program.update_topics = update_topics
            # Update evaluation fields if provided
            if 'allow_practical_submission' in payload:
                try:
                    program.allow_practical_submission = bool(payload.get('allow_practical_submission'))
                except Exception:
                    program.allow_practical_submission = True
            if 'allow_multiple_choice' in payload:
                try:
                    program.allow_multiple_choice = bool(payload.get('allow_multiple_choice'))
                except Exception:
                    program.allow_multiple_choice = False
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
            'allow_practical_submission': getattr(program, 'allow_practical_submission', True),
            'allow_multiple_choice': getattr(program, 'allow_multiple_choice', False),
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
    from cms.djangoapps.contentstore.chalix_roles import get_user_organization, get_user_primary_role
    from common.djangoapps.student.roles import GlobalStaff
    import logging
    logger = logging.getLogger(__name__)
    
    # Filter programs based on user's role and organization
    if GlobalStaff().has_user(request.user):
        # Global staff can see all programs
        qs = LocalProgram.objects.all()
    else:
        user_org = get_user_organization(request.user)
        user_role = get_user_primary_role(request.user)
        
        if user_org:
            # Filter programs by user's organization
            qs = LocalProgram.objects.filter(organization=user_org)
            logger.info(f"User {request.user.username} with role {user_role.role if user_role else 'None'} in org {user_org.name} - filtering programs")
        else:
            # User has no organization - show programs from default Bộ organization
            from cms.djangoapps.contentstore.models import ChalixOrganization
            try:
                default_org = ChalixOrganization.objects.get(code='BO_DEFAULT')
                qs = LocalProgram.objects.filter(organization=default_org)
                logger.info(f"User {request.user.username} has no organization - showing default Bộ programs")
            except ChalixOrganization.DoesNotExist:
                qs = LocalProgram.objects.none()
                logger.warning(f"User {request.user.username} has no organization and default Bộ org doesn't exist - showing no programs")
    
    qs = qs.order_by('-created_at')[:100]
    programs = []
    
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
            'allow_practical_submission': getattr(p, 'allow_practical_submission', True),
            'allow_multiple_choice': getattr(p, 'allow_multiple_choice', False),
            'topics': topics_data,
            'topics_count': len(topics_data),
            'created_at': p.created_at.isoformat(),
            'created_by': getattr(p.created_by, 'username', None),
            'organization': {
                'id': p.organization.pk,
                'name': p.organization.name,
                'display_name': p.organization.display_name
            } if p.organization else None,
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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"course_detail_api called with course_key_string: {course_key_string}, method: {request.method}")
    
    try:
        course_key = CourseKey.from_string(course_key_string)
        logger.info(f"Parsed course_key: {course_key}")
    except Exception as e:
        logger.error(f"Failed to parse course key '{course_key_string}': {e}")
        return JsonResponse({'error': _('Mã khóa học không hợp lệ')}, status=400)
    
    # Check user access to the course
    if not has_studio_read_access(request.user, course_key):
        return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
    
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
            
            # Update ChalixCourseMetadata if metadata fields are provided
            metadata_fields = ['course_category', 'creator_role', 'is_public', 'is_mandatory_course']
            if any(field in data for field in metadata_fields):
                try:
                    metadata, created = ChalixCourseMetadata.objects.get_or_create(
                        course_id=course_key,
                        defaults={
                            'creator': request.user,
                            'creator_role': 'bo',
                            'is_public': True,
                            'course_category': 'elective',
                        }
                    )
                    
                    # Update metadata fields if provided
                    if 'course_category' in data:
                        metadata.course_category = data['course_category']
                        logger.info(f"Updating course_category to: {data['course_category']}")
                    if 'creator_role' in data:
                        metadata.creator_role = data['creator_role']
                        logger.info(f"Updating creator_role to: {data['creator_role']}")
                    if 'is_public' in data:
                        metadata.is_public = data['is_public']
                        logger.info(f"Updating is_public to: {data['is_public']}")
                    if 'is_mandatory_course' in data:
                        metadata.is_mandatory_course = data['is_mandatory_course']
                        logger.info(f"Updating is_mandatory_course to: {data['is_mandatory_course']}")
                    
                    metadata.save()
                    logger.info(f"Successfully {'created' if created else 'updated'} metadata for {course_key_string}")
                    
                except Exception as e:
                    logger.error(f"Error updating metadata for {course_key_string}: {e}", exc_info=True)
            
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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"course_detail_api_get called with course_key: {course_key}")
    
    try:
        # course_key is already parsed, no need to parse again
        pass
    except Exception:
        return JsonResponse({'error': _('Mã khóa học không hợp lệ')}, status=400)
    
    # Check user access to the course
    if not has_studio_read_access(request.user, course_key):
        return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
    
    try:
        store = modulestore()
        course = store.get_course(course_key)
        
        if not course:
            return JsonResponse({'error': _('Không tìm thấy khóa học')}, status=404)
        
        # Get course overview for additional data
        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
            course_overview = CourseOverview.get_from_id(course_key)
            created_date = course_overview.created.isoformat() if course_overview.created else ''
        except Exception:
            created_date = ''
        
        # Initialize course data with basic info
        course_data = {
            'id': str(course_key),
            'course_key': str(course_key),
            'title': getattr(course, 'display_name', '') or 'Untitled Course',
            # Get org, number, run from the course key, not the course object
            'org': course_key.org,
            'number': course_key.course,  # 'number' field is called 'course' in the key
            'run': course_key.run,
            'created': created_date,
            'url': f'/courses/{course_key}/',
            'studio_url': f'/course/{course_key}',
            'language': getattr(course, 'language', 'en'),
            'start_date': getattr(course, 'start', None).isoformat() if getattr(course, 'start', None) else None,
            'end_date': getattr(course, 'end', None).isoformat() if getattr(course, 'end', None) else None,
            'units': []  # Initialize empty units array
        }
        
        # Load CourseDetails first to get all custom fields
        try:
            details = CourseDetails.fetch(course_key)
            logger.info(f"CourseDetails fetched for {course_key}")
            
            # Debug: log what we get from details and course
            details_course_level = getattr(details, 'course_level', '')
            course_course_level = getattr(course, 'course_level', '')
            logger.info(f"DEBUG course_level: details='{details_course_level}', course_block='{course_course_level}'")
            
            # Update course_data with CourseDetails fields
            course_data.update({
                'short_description': getattr(details, 'short_description', '') or getattr(course, 'short_description', ''),
                'course_type': getattr(details, 'course_type', '') or getattr(course, 'course_type', ''),
                'course_level': details_course_level or course_course_level,
                'online_course_link': getattr(details, 'online_course_link', '') or getattr(course, 'online_course_link', ''),
                'instructor': getattr(details, 'instructor', '') or getattr(course, 'instructor', ''),
                'estimated_hours': getattr(details, 'estimated_hours', 0) or getattr(course, 'estimated_hours', 0),
                'final_evaluation_type': getattr(details, 'final_evaluation_type', '') or getattr(course, 'final_evaluation_type', ''),
                'final_evaluation_project_question': getattr(details, 'final_evaluation_project_question', '') or getattr(course, 'final_evaluation_project_question', '')
            })
            
            logger.info(f"Course details loaded: course_level='{course_data['course_level']}', course_type='{course_data['course_type']}', short_description='{course_data['short_description'][:50] if course_data['short_description'] else 'EMPTY'}...'")
            
        except Exception as e:
            logger.error(f"Error loading CourseDetails for {course_key}: {e}")
            # Fallback to course block attributes
            course_course_level = getattr(course, 'course_level', '')
            logger.info(f"DEBUG fallback course_level from course block: '{course_course_level}'")
            
            course_data.update({
                'short_description': getattr(course, 'short_description', ''),
                'course_type': getattr(course, 'course_type', ''),
                'course_level': course_course_level,
                'online_course_link': getattr(course, 'online_course_link', ''),
                'instructor': getattr(course, 'instructor', ''),
                'estimated_hours': getattr(course, 'estimated_hours', 0),
                'final_evaluation_type': getattr(course, 'final_evaluation_type', ''),
                'final_evaluation_project_question': getattr(course, 'final_evaluation_project_question', '')
            })

        # Try to get creator information from LocalCourse record
        try:
            local_course = LocalCourse.objects.get(course_key=str(course_key))
            course_data.update({
                'created_by': getattr(local_course.created_by, 'username', None) if local_course.created_by else None,
                'created_at': local_course.created_at.isoformat() if local_course.created_at else course_data.get('created', '')
            })
            logger.info(f"LocalCourse found for {course_key}, creator: {course_data.get('created_by')}")
        except LocalCourse.DoesNotExist:
            logger.info(f"No LocalCourse found for {course_key}, using fallback creator info")
            # Fallback to created date from course overview if available
            course_data.update({
                'created_by': None,
                'created_at': course_data.get('created', '')
            })
        except Exception as e:
            logger.error(f"Error getting LocalCourse for {course_key}: {e}")
            course_data.update({
                'created_by': None,
                'created_at': course_data.get('created', '')
            })
        
        # Try to get course_category and is_mandatory_course from ChalixCourseMetadata
        try:
            chalix_metadata = ChalixCourseMetadata.objects.filter(course_id=course_key).first()
            if chalix_metadata:
                course_data.update({
                    'course_category': chalix_metadata.course_category,
                    'is_mandatory_course': chalix_metadata.is_mandatory_course,
                    'creator_role': chalix_metadata.creator_role,
                    'is_public': chalix_metadata.is_public
                })
                logger.info(f"ChalixCourseMetadata found for {course_key}: category={chalix_metadata.course_category}, mandatory={chalix_metadata.is_mandatory_course}")
            else:
                logger.info(f"No ChalixCourseMetadata found for {course_key}")
                course_data.update({
                    'course_category': None,
                    'is_mandatory_course': False,
                    'creator_role': None,
                    'is_public': False
                })
        except Exception as e:
            logger.error(f"Error getting ChalixCourseMetadata for {course_key}: {e}")
            course_data.update({
                'course_category': None,
                'is_mandatory_course': False,
                'creator_role': None,
                'is_public': False
            })

        
        # Add course structure (chapters/sections as topics/units)
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Get course structure - chapters are the top level containers
            chapters = course.get_children() if hasattr(course, 'get_children') else []
            topics = []  # Renamed from units to topics for clarity (these are subsections)
            
            logger.info(f"Course {course_key} - course type: {type(course)}")
            logger.info(f"Course {course_key} has {len(chapters)} chapters")
            
            if chapters:
                for i, chapter in enumerate(chapters):
                    logger.info(f"Chapter {i}: type={type(chapter)}, display_name={getattr(chapter, 'display_name', 'N/A')}, location={getattr(chapter, 'location', 'N/A')}, category={getattr(chapter, 'category', 'N/A')}")
                    
                    # Skip chapters that don't have a display name or are template data
                    if not hasattr(chapter, 'display_name') or not chapter.display_name:
                        logger.warning(f"Skipping chapter without display_name")
                        continue
                    
                    # Check if this looks like template data but be less aggressive
                    is_template_data = (
                        'template' in chapter.display_name.lower() or
                        chapter.display_name.lower().strip() in ['sample', 'example', 'demo']
                    )
                    
                    if is_template_data:
                        logger.warning(f"Skipping template chapter: {chapter.display_name}")
                        continue
                    
                    # Get subsections (sequentials) - these are the actual "topics" (Chuyên đề)
                    if hasattr(chapter, 'get_children'):
                        try:
                            subsections = chapter.get_children()
                            logger.info(f"Chapter '{chapter.display_name}' has {len(subsections)} subsections")
                            
                            for j, subsection in enumerate(subsections):
                                logger.info(f"  Subsection {j}: type={type(subsection)}, display_name={getattr(subsection, 'display_name', 'N/A')}, category={getattr(subsection, 'category', 'N/A')}")
                                
                                # Subsections (sequentials) are the topics (Chuyên đề) that should appear in the list
                                if hasattr(subsection, 'display_name') and subsection.display_name:
                                    # Try to get description from multiple sources
                                    description = ''
                                    if hasattr(subsection, 'short_description') and subsection.short_description:
                                        description = subsection.short_description
                                    elif hasattr(subsection, 'description') and subsection.description:
                                        description = subsection.description
                                    else:
                                        # Try to get description from metadata
                                        try:
                                            if hasattr(subsection, 'fields') and 'metadata' in subsection.fields:
                                                metadata = subsection.fields.get('metadata', {})
                                                description = metadata.get('short_description', '') or metadata.get('description', '')
                                        except:
                                            pass
                                    
                                    topic_data = {
                                        'title': subsection.display_name,
                                        'name': subsection.display_name,
                                        'description': description or 'Chưa có mô tả',
                                        'chapter': chapter.display_name,  # Keep reference to parent chapter
                                        'category': getattr(subsection, 'category', 'sequential'),  # Should be 'sequential'
                                        'location': str(getattr(subsection, 'location', ''))
                                    }
                                    topics.append(topic_data)
                                    logger.info(f"  Added topic: '{topic_data['title']}' from chapter: '{chapter.display_name}'")
                                else:
                                    logger.warning(f"  Subsection has no display_name: {subsection}")
                        except Exception as e:
                            logger.error(f"Error getting subsections for chapter '{chapter.display_name}': {e}", exc_info=True)
                    else:
                        logger.warning(f"Chapter '{chapter.display_name}' has no get_children method")
            else:
                # No chapters found - this might be a newly created course
                logger.warning(f"Course {course_key} has no chapters. This might be a new course or an empty course.")
            
            # Set the units field with the topics
            course_data['units'] = topics
            logger.info(f"Course {course_key} topics/units loaded: {len(topics)} topics")
            
            # If no topics found, provide empty array (don't add fake data)
            if not topics:
                logger.info(f"No topics found for course {course_key}. Course may be empty or have only chapters without subsections.")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Could not load course topics for {course_key}: {str(e)}", exc_info=True)
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
        'allow_practical_submission': getattr(program, 'allow_practical_submission', False),
        'allow_multiple_choice': getattr(program, 'allow_multiple_choice', True),
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

    # Initialize units tracking
    units_created = 0
    units_updated = 0

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
        
        # Add final evaluation type field
        final_evaluation_type = payload.get('final_evaluation_type', '').strip()
        if final_evaluation_type:
            course_update_data['final_evaluation_type'] = final_evaluation_type
        
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
        logger.info(f"Update course API: course_key={course_key_string}, level='{level}', course_type='{course_type}', final_evaluation_type='{final_evaluation_type}'")
        logger.info(f"Full course update payload: {course_update_data}")

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
        
        # Update course_category in ChalixCourseMetadata if provided (for Bo role courses)
        course_category = payload.get('course_category', None)
        if course_category is not None:
            try:
                chalix_metadata, created = ChalixCourseMetadata.objects.get_or_create(
                    course_id=course_key,
                    defaults={
                        'creator': request.user,
                        'creator_role': None,
                        'creator_organization': None,
                        'is_public': False
                    }
                )
                
                # Update course_category if it's different
                if chalix_metadata.course_category != course_category:
                    chalix_metadata.course_category = course_category
                    # Update is_mandatory_course based on category
                    chalix_metadata.is_mandatory_course = (course_category == 'mandatory')
                    chalix_metadata.save()
                    logger.info(f"Updated ChalixCourseMetadata for {course_key}: category={course_category}, mandatory={chalix_metadata.is_mandatory_course}")
                    
            except Exception as e:
                logger.warning(f"Failed to update ChalixCourseMetadata course_category for {course_key}: {e}")
        
        # Handle units (chapters/sections) if provided
        units_data = payload.get('units', [])
        
        if units_data:
            logger.info(f"Processing {len(units_data)} units for course {course_key}")
            
            # Get or create main chapter for organizing units
            course = store.get_course(course_key)
            main_chapter = None
            
            # Try to find existing main chapter (the first chapter)
            if course.get_children():
                for child in course.get_children():
                    if child.category == 'chapter':
                        main_chapter = child
                        break
            
            # Create main chapter if it doesn't exist
            if not main_chapter:
                logger.info(f"Creating new main chapter for course {course_key}")
                main_chapter = store.create_child(
                    request.user.id,
                    course.location,
                    'chapter',
                    fields={
                        'display_name': title,  # Use course title as chapter name
                    }
                )
            
            # Process each unit - create subsection (sequential) with an empty vertical
            for unit_data in units_data:
                unit_title = unit_data.get('title', '').strip()
                unit_name = unit_data.get('name', unit_title).strip()
                unit_order = unit_data.get('order', 0)
                
                if not unit_title:
                    logger.warning(f"Skipping unit with no title: {unit_data}")
                    continue
                
                try:
                    # Create subsection (sequential) for the unit
                    sequential = store.create_child(
                        request.user.id,
                        main_chapter.location,
                        'sequential',
                        fields={
                            'display_name': unit_title,
                        }
                    )
                    
                    # Create an empty unit (vertical) under the subsection
                    vertical = store.create_child(
                        request.user.id,
                        sequential.location,
                        'vertical',
                        fields={
                            'display_name': f'{unit_title} - Bài học',
                        }
                    )
                    
                    # Publish the components
                    store.publish(sequential.location, request.user.id)
                    store.publish(vertical.location, request.user.id)
                    
                    units_created += 1
                    logger.info(f"Created unit '{unit_title}' for course {course_key}")
                    
                except Exception as unit_error:
                    logger.error(f"Failed to create unit '{unit_title}': {unit_error}")
            
            # Publish the main chapter
            if main_chapter and units_created > 0:
                store.publish(main_chapter.location, request.user.id)
                logger.info(f"Successfully created {units_created} units for course {course_key}")
        
        return JsonResponse({
            'course_key': str(course_key),
            'title': updated_course_details.title,
            'org': course_key.org,
            'number': course_key.course,
            'run': course_key.run,
            'short_description': updated_course_details.short_description,
            'course_type': getattr(updated_block, 'course_type', ''),
            'course_level': getattr(updated_block, 'course_level', ''),
            'course_category': course_category if course_category is not None else '',
            'online_course_link': getattr(updated_course_details, 'online_course_link', ''),
            'instructor': getattr(updated_course_details, 'instructor', ''),
            'estimated_hours': getattr(updated_course_details, 'estimated_hours', 0),
            'final_evaluation_type': getattr(updated_course_details, 'final_evaluation_type', ''),
            'start_date': updated_course_details.start_date.isoformat() if updated_course_details.start_date else None,
            'end_date': updated_course_details.end_date.isoformat() if updated_course_details.end_date else None,
            'units_created': units_created,
            'message': f'Đã cập nhật khóa học thành công! {units_created} chuyên đề đã được tạo.' if units_created > 0 else 'Đã cập nhật khóa học thành công!'
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

        # Permission check: only creator or Bộ user can delete LocalCourse
        if not (is_bo_user(request.user) or getattr(lc.created_by, 'id', None) == request.user.id):
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

    # Permission check: only creator or Bộ user can delete program
    if not (is_bo_user(request.user) or getattr(prog.created_by, 'id', None) == request.user.id):
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
    if tab == 'approve-requests':
        return _get_approve_requests_statistics_data(request)
    return JsonResponse({'error': 'Invalid tab specified'}, status=400)


def _get_approve_requests_statistics_data(request):
    """
    Build table data for the 'Phê duyệt yêu cầu' tab using emotion aggregates.

    Rule:
    - score_sum >= 0 => no adjustment required
    - score_sum < 0 => adjustment required
    """
    import re
    from django.db.models import Q

    try:
        role = get_user_primary_role(request.user)
        can_view = bool(is_bo_user(request.user) or (role and role.role == 'co_quan'))
        if not can_view:
            return JsonResponse({'error': 'Bạn không có quyền xem dữ liệu phê duyệt yêu cầu.'}, status=403)

        queryset = ChalixTopicEmotionAggregate.objects.all()

        # Keep course visibility aligned with learner-dashboard:
        # - Public courses are visible to everyone.
        # - Private courses are visible only to users in the same organization.
        user_org = getattr(role, 'organization', None) if role else None
        visibility_q = Q(is_public=True)
        if user_org:
            visibility_q |= Q(is_public=False, creator_organization=user_org)

        visible_course_ids = {
            str(course_id)
            for course_id in ChalixCourseMetadata.objects.filter(visibility_q).values_list('course_id', flat=True)
        }

        if visible_course_ids:
            queryset = queryset.filter(course_id__in=visible_course_ids)
        else:
            queryset = queryset.none()

        def normalize_topic_number(value):
            token = (value or '').strip()
            match = re.search(r'(\d+)', token)
            if match:
                return str(int(match.group(1)))
            return token or '0'

        rows_map = {}
        for row in queryset.values(
            'course_id',
            'course_name',
            'topic_number',
            'topic_name',
            'like_count',
            'neutral_count',
            'dislike_count',
            'score_sum',
            'adjust_required',
        ):
            normalized_topic = normalize_topic_number(row.get('topic_number'))
            key = (row.get('course_id'), normalized_topic)
            rows_map[key] = {
                'course_id': row.get('course_id'),
                'course_name': row.get('course_name') or row.get('course_id'),
                'topic_number': normalized_topic,
                'topic_name': row.get('topic_name') or f"Chuyên đề {normalized_topic}",
                'like_count': int(row.get('like_count') or 0),
                'neutral_count': int(row.get('neutral_count') or 0),
                'dislike_count': int(row.get('dislike_count') or 0),
                'score_sum': int(row.get('score_sum') or 0),
                'adjust_required': bool(row.get('adjust_required')),
            }

        store = modulestore()
        outline_cache = {}

        def get_course_outline_topic_meta(course_id):
            cached = outline_cache.get(course_id)
            if cached is not None:
                return cached

            try:
                course_key = CourseKey.from_string(course_id)
                course = store.get_course(course_key)
                if not course:
                    outline_cache[course_id] = {'course_name': course_id, 'unit_map': {}}
                    return outline_cache[course_id]

                course_name = getattr(course, 'display_name', None) or course_id
                unit_map = {}
                topic_index = 0

                course_children = store.get_children(course.location, depth=None) or []
                chapter_children = [child for child in course_children if getattr(child, 'category', None) == 'chapter']
                vertical_children = [child for child in course_children if getattr(child, 'category', None) == 'vertical']

                if chapter_children:
                    for chapter in chapter_children:
                        sequentials = store.get_children(chapter.location, depth=None) or []
                        for sequential in sequentials:
                            if getattr(sequential, 'category', None) != 'sequential':
                                continue
                            verticals = store.get_children(sequential.location, depth=None) or []
                            for unit_block in verticals:
                                if getattr(unit_block, 'category', None) != 'vertical':
                                    continue
                                topic_index += 1
                                unit_map[str(unit_block.location)] = {
                                    'topic_number': str(topic_index),
                                    'topic_name': getattr(unit_block, 'display_name', None) or f"Chuyên đề {topic_index}",
                                }
                else:
                    for unit_block in vertical_children:
                        topic_index += 1
                        unit_map[str(unit_block.location)] = {
                            'topic_number': str(topic_index),
                            'topic_name': getattr(unit_block, 'display_name', None) or f"Chuyên đề {topic_index}",
                        }

                outline_cache[course_id] = {'course_name': course_name, 'unit_map': unit_map}
                return outline_cache[course_id]
            except Exception:
                outline_cache[course_id] = {'course_name': course_id, 'unit_map': {}}
                return outline_cache[course_id]

        # CMS runtime may not load LMS review app into INSTALLED_APPS.
        # Query review table directly to avoid model import/app-label errors.
        live_rows = []
        review_table_candidates = [
            'course_home_api_courseemojireview',
            'lms_djangoapps_course_home_api_courseemojireview',
        ]
        with connection.cursor() as cursor:
            for review_table in review_table_candidates:
                try:
                    params = []
                    where_clause = "WHERE unit_usage_key IS NOT NULL AND unit_usage_key <> ''"
                    if visible_course_ids:
                        placeholders = ','.join(['%s'] * len(visible_course_ids))
                        where_clause += f" AND course_key IN ({placeholders})"
                        params.extend(sorted(visible_course_ids))

                    sql = f"""
                        SELECT course_key, unit_usage_key, rating, COUNT(id) AS total
                        FROM {review_table}
                        {where_clause}
                        GROUP BY course_key, unit_usage_key, rating
                    """
                    cursor.execute(sql, params)
                    raw_rows = cursor.fetchall()
                    live_rows = [
                        {
                            'course_key': row[0],
                            'unit_usage_key': row[1],
                            'rating': row[2],
                            'total': row[3],
                        }
                        for row in raw_rows
                    ]
                    break
                except Exception:
                    continue

        fallback_topic_index_map = {}
        rating_to_field = {
            'like': 'like_count',
            'neutral': 'neutral_count',
            'dislike': 'dislike_count',
        }

        for row in live_rows:
            course_id = row.get('course_key')
            unit_usage_key = row.get('unit_usage_key')
            rating = row.get('rating')
            total = int(row.get('total') or 0)

            target_field = rating_to_field.get(rating)
            if not course_id or not unit_usage_key or not target_field or total <= 0:
                continue

            outline_meta = get_course_outline_topic_meta(course_id)
            course_name = outline_meta.get('course_name') or course_id
            unit_meta = (outline_meta.get('unit_map') or {}).get(unit_usage_key)

            if unit_meta:
                topic_number = normalize_topic_number(unit_meta.get('topic_number'))
                topic_name = unit_meta.get('topic_name') or f"Chuyên đề {topic_number}"
            else:
                fallback_map = fallback_topic_index_map.setdefault(course_id, {})
                if unit_usage_key not in fallback_map:
                    fallback_map[unit_usage_key] = str(len(fallback_map) + 1)
                topic_number = fallback_map[unit_usage_key]
                topic_name = f"Chuyên đề {topic_number}"

            key = (course_id, topic_number)
            if key not in rows_map:
                rows_map[key] = {
                    'course_id': course_id,
                    'course_name': course_name,
                    'topic_number': topic_number,
                    'topic_name': topic_name,
                    'like_count': 0,
                    'neutral_count': 0,
                    'dislike_count': 0,
                    'score_sum': 0,
                    'adjust_required': False,
                }

            rows_map[key][target_field] += total
            rows_map[key]['course_name'] = rows_map[key].get('course_name') or course_name
            rows_map[key]['topic_name'] = rows_map[key].get('topic_name') or topic_name

        rows = []
        for row in rows_map.values():
            row['score_sum'] = int(row.get('like_count') or 0) - int(row.get('dislike_count') or 0)
            row['adjust_required'] = int(row.get('score_sum') or 0) < 0
            rows.append(row)

        def topic_sort_key(topic_number):
            match = re.search(r'(\d+)$', (topic_number or '').strip())
            if match:
                return int(match.group(1))
            return 999999

        topic_number_order = sorted({row['topic_number'] for row in rows}, key=topic_sort_key)

        course_map = {}
        for row in rows:
            course_id = row['course_id']
            entry = course_map.setdefault(course_id, {
                'course_id': course_id,
                'course_name': row.get('course_name') or course_id,
                'topics_by_number': {},
                'needs_adjustment': False,
                'recommendation': '',
            })
            needs_adjustment = bool(row.get('adjust_required')) or int(row.get('score_sum') or 0) < 0
            entry['topics_by_number'][row['topic_number']] = {
                'topic_number': row['topic_number'],
                'topic_name': row.get('topic_name') or row['topic_number'],
                'like_count': int(row.get('like_count') or 0),
                'neutral_count': int(row.get('neutral_count') or 0),
                'dislike_count': int(row.get('dislike_count') or 0),
                'score_sum': int(row.get('score_sum') or 0),
                'needs_adjustment': needs_adjustment,
            }
            entry['needs_adjustment'] = entry['needs_adjustment'] or needs_adjustment

        courses = []
        for data in course_map.values():
            topic_stats = []
            adjust_topic_labels = []

            for index, topic_number in enumerate(topic_number_order, start=1):
                topic_data = data['topics_by_number'].get(topic_number)
                if not topic_data:
                    topic_data = {
                        'topic_number': topic_number,
                        'topic_name': f'Chuyên đề {index}',
                        'like_count': 0,
                        'neutral_count': 0,
                        'dislike_count': 0,
                        'score_sum': 0,
                        'needs_adjustment': False,
                    }

                topic_stats.append(topic_data)
                if topic_data['needs_adjustment']:
                    topic_label_match = re.search(r'(\d+)$', topic_number or '')
                    topic_label = topic_label_match.group(1) if topic_label_match else topic_number
                    adjust_topic_labels.append(str(topic_label))

            if adjust_topic_labels:
                recommendation = f"Cần điều chỉnh chuyên đề {', '.join(adjust_topic_labels)}"
            else:
                recommendation = 'Không cần điều chỉnh'

            courses.append({
                'course_id': data['course_id'],
                'course_name': data['course_name'],
                'needs_adjustment': data['needs_adjustment'],
                'recommendation': recommendation,
                'topic_stats': topic_stats,
            })

        courses.sort(key=lambda item: (0 if item['needs_adjustment'] else 1, item['course_name']))

        topic_headers = []
        for index, topic_number in enumerate(topic_number_order, start=1):
            topic_headers.append({
                'topic_number': topic_number,
                'display_name': f'Chuyên đề {index}',
            })

        return JsonResponse({
            'courses': courses,
            'topic_headers': topic_headers,
            'total_courses': len(courses),
            'adjust_courses': sum(1 for course in courses if course['needs_adjustment']),
        })
    except Exception as exc:
        logger.exception('Failed to build approve-requests statistics: %s', exc)
        return JsonResponse({
            'error': 'Không thể tải dữ liệu phê duyệt yêu cầu.',
            'detail': str(exc),
        }, status=500)


def _get_statistics_data(request):
    """
    Table 4: THỐNG KÊ SỐ GIỜ HỌC CỦA CÔNG CHỨC, VIÊN CHỨC NĂM 2025
    
    Get statistics data for the dashboard with learner details and hours completed.
    
    This function provides learner statistics with filtering options:
    - Filter by learner phone
    - Filter by learner name  
    - Filter by year
    - Filter by completion status (calculated as total estimated hours / 40 hours)
    - Filter by organization for co_quan role (only show their organization's users)
    Column TT (row number) should be displayed as smaller column
    """
    from django.core.paginator import Paginator
    from django.db.models import Q, Avg, Max
    from common.djangoapps.student.models import User
    from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot
    from cms.djangoapps.contentstore.models import ChalixUserRole
    from cms.djangoapps.contentstore.chalix_roles import get_user_primary_role
    
    # Check if this is an export request
    if request.GET.get('export') == 'csv':
        return _export_statistics_csv(request)
    
    # Get filter parameters
    phone_filter = request.GET.get('phone', '').strip()
    name_filter = request.GET.get('name', '').strip()
    id_filter = request.GET.get('student_id', '').strip()
    # Requirement: year displayed for this statistics table is fixed to 2026.
    year_filter_int = 2026
    completion_filter = request.GET.get('completion', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = 10
    
    # Base queryset - only learner accounts (cong_chuc), excluding bo/co_quan role users.
    learner_role_qs = ChalixUserRole.objects.filter(
        role='cong_chuc',
        is_active=True,
    )

    snapshot_user_ids = StudentLearningProcessSnapshot.objects.filter(
        user_id__isnull=False,
    ).values_list('user_id', flat=True).distinct()

    users_query = User.objects.select_related('profile').filter(
        is_active=True,
        id__in=learner_role_qs.values_list('user_id', flat=True),
    ).filter(
        id__in=snapshot_user_ids,
    ).distinct()
    
    # Filter by organization for co_quan role
    user_role = get_user_primary_role(request.user)
    if user_role and user_role.role == 'co_quan' and user_role.organization:
        scoped_user_ids = learner_role_qs.filter(
            organization=user_role.organization,
        ).values_list('user_id', flat=True)
        users_query = users_query.filter(id__in=scoped_user_ids)
    
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
    
    # Apply student ID filter
    if id_filter:
        users_query = users_query.filter(
            Q(id__icontains=id_filter) |
            Q(username__icontains=id_filter)
        )
    
    # Get learner statistics
    learners_data = []
    total_learners = users_query.count()
    completed_learners = 0
    total_completion_sum = 0
    total_hours_sum = 0
    
    for user in users_query:
        user_snapshots = StudentLearningProcessSnapshot.objects.filter(user=user)
        if not user_snapshots.exists():
            continue

        agg = user_snapshots.aggregate(
            avg_completed=Avg('completed_percentage'),
        )
        completion_percentage = float(agg.get('avg_completed') or 0)

        # Source rows are expanded per enrolled course. To reconstruct the learner-level
        # total, take the latest/max hours per course and then sum across courses.
        per_course_hours = user_snapshots.values('course_id').annotate(
            course_hours=Max('total_studied_time'),
        )
        total_studied_time_from_snapshot = sum(
            float(row.get('course_hours') or 0)
            for row in per_course_hours
        )
        
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
        
        profile_meta = {}
        if hasattr(user, 'profile') and user.profile:
            try:
                profile_meta = user.profile.get_meta() if hasattr(user.profile, 'get_meta') else {}
            except Exception:
                profile_meta = {}

        calculated_total_hours = float(total_studied_time_from_snapshot or 0)
        # Snapshot values are course-analytics source of truth for this table.
        total_studied_time = calculated_total_hours
        completed_percentage = round(completion_percentage, 1)
        status_value = profile_meta.get('status', '')

        if not status_value:
            latest_snapshot = user_snapshots.order_by('-updated_at').first()
            status_value = (latest_snapshot.status if latest_snapshot else '') or ''

        learner_data = {
            'id': user.id,
            'name': user.profile.name if hasattr(user, 'profile') and user.profile.name else f"{user.first_name} {user.last_name}".strip(),
            # Requirement: keep phone column with no data.
            'phone': '',
            'year': 2026,
            'total_studied_time': total_studied_time,
            'completed_percentage': completed_percentage,
            'status': status_value,
            # Backward-compatible aliases for existing frontend code paths.
            'total_hours': total_studied_time,
            'completion_percentage': completed_percentage,
            'enrollments_count': user_snapshots.values('course_id').distinct().count(),
        }
        
        learners_data.append(learner_data)
        total_completion_sum += float(completed_percentage or 0)
        total_hours_sum += float(total_studied_time or 0)
        
        if float(completed_percentage or 0) >= 100:
            completed_learners += 1
    
    # Sort learners by completed percentage (descending)
    learners_data.sort(key=lambda x: x['completed_percentage'], reverse=True)
    
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
        },
        # Add three new tables data
        'course_completions': _get_course_completion_stats(request),
        'organization_completions': _get_organization_completion_stats(request),
        'organization_courses': _get_organization_courses_stats(request)
    }
    
    return JsonResponse(stats_data)


def _get_course_completion_stats(request):
    """
    Table 1: THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC KHÓA HỌC NĂM ...
    Statistics on how many learners completed each course
    Returns list of courses sorted by completion count (descending)
    For co_quan role: only count learners from their organization
    Column TT (row number) should be displayed as smaller column
    """
    from django.db.models import Count, Q
    from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from cms.djangoapps.contentstore.models import ChalixUserRole
    from cms.djangoapps.contentstore.chalix_roles import get_user_primary_role
    year_filter = request.GET.get('year', '').strip()
    year_filter_int = None
    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except (TypeError, ValueError):
            year_filter_int = None
    
    # Check user role for organization filtering
    user_role = get_user_primary_role(request.user)
    org_filter = None
    if user_role and user_role.role == 'co_quan' and user_role.organization:
        org_filter = user_role.organization

    learner_role_qs = ChalixUserRole.objects.filter(
        role='cong_chuc',
        is_active=True,
        user__is_active=True,
    )
    if org_filter:
        learner_role_qs = learner_role_qs.filter(organization=org_filter)
    learner_user_ids = learner_role_qs.values_list('user_id', flat=True)

    snapshot_qs = StudentLearningProcessSnapshot.objects.filter(user_id__in=learner_user_ids)

    # Aggregate by canonical course_id to guarantee exactly one row per course.
    # This avoids duplicated rows caused by iterating raw snapshot records.
    aggregated = list(
        snapshot_qs.exclude(course_id__isnull=True)
        .exclude(course_id='')
        .values('course_id')
        .annotate(
            current_learners=Count('user_id', distinct=True),
            completed_count=Count(
                'user_id',
                filter=Q(completed_percentage__gte=60),
                distinct=True,
            ),
        )
        .order_by('-completed_count', 'course_id')
    )

    course_ids = [row['course_id'] for row in aggregated]
    overview_map = {}
    if course_ids:
        for overview in CourseOverview.objects.filter(id__in=course_ids).only('id', 'display_name'):
            overview_map[str(overview.id)] = overview.display_name or str(overview.id)

    course_stats = []
    for row in aggregated:
        course_id = row['course_id']
        course_name = overview_map.get(str(course_id), course_id)
        course_stats.append({
            'course_name': course_name,
            'current_learners': row['current_learners'],
            'completed_count': row['completed_count'],
        })

    return course_stats


def _get_organization_completion_stats(request):
    """
    Table 2: THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC CƠ QUAN NĂM ...
    Statistics on how many learners from each organization completed courses
    Returns list of organizations with learner count and completion percentage
    Sorted by completion percentage (descending)
    Column TT (row number) should be displayed as smaller column
    """
    from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole
    from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot
    import logging

    year_filter = request.GET.get('year', '').strip()
    year_filter_int = None
    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except (TypeError, ValueError):
            year_filter_int = None
    
    logger = logging.getLogger(__name__)
    
    # Get all organizations
    organizations = ChalixOrganization.objects.all()
    logger.info(f"[Organization Stats] Found {organizations.count()} organizations")
    
    org_stats = []
    for org in organizations:
        # Get users in this organization
        org_users = ChalixUserRole.objects.filter(
            organization=org,
            role='cong_chuc',
            is_active=True,
            user__is_active=True,
        ).values_list('user_id', flat=True)
        
        logger.info(f"[Organization Stats] Org: {org.display_name}, Users: {len(org_users)}")
        
        if not org_users:
            continue
        
        snapshot_qs = StudentLearningProcessSnapshot.objects.filter(user_id__in=org_users)
        learner_count = snapshot_qs.values('user_id').distinct().count()

        completed_learners = snapshot_qs.filter(
            completed_percentage__gte=60,
        ).values('user_id').distinct().count()
        
        # Calculate completion percentage
        completion_percentage = round((completed_learners / learner_count * 100), 1) if learner_count > 0 else 0
        
        org_stats.append({
            'organization_name': org.display_name,
            'learner_count': learner_count,
            'completion_percentage': completion_percentage
        })
    
    logger.info(f"[Organization Stats] Returning {len(org_stats)} organization stats")
    
    # Sort by completion percentage (descending)
    org_stats.sort(key=lambda x: x['completion_percentage'], reverse=True)
    
    return org_stats


def _get_organization_courses_stats(request):
    """
    Table 3: THỐNG KÊ SỐ KHÓA HỌC CỦA CÁC CƠ QUAN
    Statistics on how many courses each organization has created
    Returns list of organizations with course count
    Sorted by course count (descending)
    Column TT (row number) should be displayed as smaller column
    """
    from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole
    from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot
    import logging

    year_filter = request.GET.get('year', '').strip()
    year_filter_int = None
    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except (TypeError, ValueError):
            year_filter_int = None
    
    logger = logging.getLogger(__name__)
    
    # Get all organizations
    organizations = ChalixOrganization.objects.all()
    logger.info(f"[Organization Courses Stats] Found {organizations.count()} organizations")
    
    org_stats = []
    for org in organizations:
        # Get users in this organization
        org_users = ChalixUserRole.objects.filter(
            organization=org,
            role='cong_chuc',
            is_active=True,
            user__is_active=True,
        ).values_list('user_id', flat=True)
        
        logger.info(f"[Organization Courses Stats] Org: {org.display_name}, Users: {len(org_users)}")
        
        if not org_users:
            continue
        
        # Count distinct courses that members of this organization have imported learning snapshots for.
        courses_count = StudentLearningProcessSnapshot.objects.filter(
            user_id__in=org_users,
        ).values('course_id').distinct().count()
        
        logger.info(f"[Organization Courses Stats] Org: {org.display_name}, Courses: {courses_count}")
        
        org_stats.append({
            'organization_name': org.display_name,
            'courses_count': courses_count
        })
    
    logger.info(f"[Organization Courses Stats] Returning {len(org_stats)} organization stats")
    
    # Sort by courses count (descending)
    org_stats.sort(key=lambda x: x['courses_count'], reverse=True)
    
    return org_stats


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
    year_filter_int = None
    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except (TypeError, ValueError):
            year_filter_int = None
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
    if year_filter_int:
        users_query = users_query.filter(courseenrollment__created__year=year_filter_int)
    
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
        if year_filter_int:
            enrollments = enrollments.filter(created__year=year_filter_int)
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


# Final Evaluation API endpoints

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_final_evaluation_api(request, course_key_string):
    """
    Get final evaluation for a course - returns both practical and quiz evaluations if available.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"get_final_evaluation_api called with course_key_string: {course_key_string}")
    
    try:
        from opaque_keys.edx.keys import CourseKey
        
        course_key = CourseKey.from_string(course_key_string)
        logger.info(f"Parsed course_key: {course_key}")
        
        # Check if course exists first
        store = modulestore()
        course = store.get_course(course_key)
        
        if not course:
            logger.warning(f"Course not found: {course_key}")
            return JsonResponse({
                'success': False,
                'error': f'Course not found: {course_key}'
            }, status=404)
        
        # Get final evaluation type from course details
        try:
            from cms.djangoapps.contentstore.models import FinalEvaluation
            
            details = CourseDetails.fetch(course_key)
            final_evaluation_type = getattr(details, 'final_evaluation_type', '')
            logger.info(f"Course {course_key} has final_evaluation_type: {final_evaluation_type}")
            
            if not final_evaluation_type:
                return JsonResponse({
                    'success': True,
                    'evaluation': {
                        'evaluation_type': None,
                        'practical_question': '',
                        'has_quiz_file': False
                    },
                    'has_evaluation': False
                })
            
            # Return evaluation based on type with database values
            evaluation_data = {
                'evaluation_type': final_evaluation_type,
                'practical_question': 'Hãy nộp bài thu hoạch của bạn theo yêu cầu của giảng viên.',
                'has_quiz_file': False
            }
            
            if final_evaluation_type == 'project':
                evaluation_data['evaluation_type'] = 'practical'
                # Try to get practical question from database
                try:
                    practical_eval = FinalEvaluation.objects.get(
                        course_key=course_key,
                        evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                        is_active=True
                    )
                    evaluation_data['practical_question'] = practical_eval.practical_question or evaluation_data['practical_question']
                except FinalEvaluation.DoesNotExist:
                    pass
                    
            elif final_evaluation_type == 'quiz':
                evaluation_data['evaluation_type'] = 'quiz'
                evaluation_data['has_quiz_file'] = True
                
                # Try to get quiz configuration from database
                try:
                    quiz_eval = FinalEvaluation.objects.get(
                        course_key=course_key,
                        evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                        is_active=True
                    )
                    evaluation_data['quiz_time_limit'] = quiz_eval.quiz_time_limit
                    evaluation_data['quiz_passing_score'] = float(quiz_eval.quiz_passing_score) if quiz_eval.quiz_passing_score else None
                    evaluation_data['quiz_max_attempts'] = quiz_eval.quiz_max_attempts or 0
                    evaluation_data['quiz_file_name'] = quiz_eval.quiz_file.name.split('/')[-1] if quiz_eval.quiz_file else None
                except FinalEvaluation.DoesNotExist:
                    # Set default values
                    evaluation_data['quiz_time_limit'] = None
                    evaluation_data['quiz_passing_score'] = None
                    evaluation_data['quiz_max_attempts'] = 0
            
            return JsonResponse({
                'success': True,
                'evaluation': evaluation_data,
                'has_evaluation': True
            })
            
        except Exception as e:
            logger.error(f"Error fetching course details for {course_key}: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error fetching course details: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error getting final evaluation for course {course_key_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_final_evaluation_api(request, course_key_string):
    """
    Update final evaluation content (practical question or quiz configuration).
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation
        
        course_key = CourseKey.from_string(course_key_string)
        data = json.loads(request.body.decode('utf-8'))
        
        # Check if updating practical question
        if 'practical_question' in data:
            practical_question = data.get('practical_question', '')
            
            # Get the practical evaluation specifically
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
            evaluation.practical_question = practical_question
            evaluation.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Practical question updated successfully'
            })
        
        # Check if updating quiz configuration
        elif any(key in data for key in ['quiz_time_limit', 'quiz_passing_score', 'quiz_max_attempts']):
            # Get the quiz evaluation specifically
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            
            # Update quiz configuration fields
            if 'quiz_time_limit' in data:
                evaluation.quiz_time_limit = data['quiz_time_limit']
            
            if 'quiz_passing_score' in data:
                passing_score = data['quiz_passing_score']
                # Validate passing score is between 0 and 100
                if passing_score is not None:
                    if passing_score < 0 or passing_score > 100:
                        return JsonResponse({
                            'success': False,
                            'error': 'Passing score must be between 0 and 100'
                        })
                evaluation.quiz_passing_score = passing_score
            
            if 'quiz_max_attempts' in data:
                max_attempts = int(data['quiz_max_attempts'])
                # Validate max attempts is one of the allowed values
                if max_attempts not in [0, 1, 3]:
                    return JsonResponse({
                        'success': False,
                        'error': 'Max attempts must be 0 (unlimited), 1, or 3'
                    })
                evaluation.quiz_max_attempts = max_attempts
            
            evaluation.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Quiz configuration updated successfully'
            })
        
        return JsonResponse({
            'success': False,
            'error': 'No valid update data provided'
        })
        
    except FinalEvaluation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Evaluation not found for this course'
        })
    except Exception as e:
        logger.error(f"Error updating final evaluation for course {course_key_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def upload_evaluation_quiz_api(request, course_key_string):
    """
    Upload excel file for quiz evaluation.
    """
    try:
        import pandas as pd
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, ChalixQuiz, ChalixQuizQuestion, ChalixQuizChoice
        
        course_key = CourseKey.from_string(course_key_string)
        
        if 'quiz_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            })
        
        quiz_file = request.FILES['quiz_file']
        
        # Validate file extension
        if not quiz_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'error': 'Please upload an Excel file (.xlsx or .xls)'
            })
        
        # Parse Excel file
        try:
            df = pd.read_excel(quiz_file)
            
            # Expected columns: Question, Choice_A, Choice_B, Choice_C, Choice_D, Correct_Answer
            required_columns = ['Question', 'Choice_A', 'Choice_B', 'Choice_C', 'Choice_D', 'Correct_Answer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required columns: {", ".join(missing_columns)}'
                })
            
            # Get quiz evaluation specifically
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            
            # Get or create ChalixQuiz with empty parent_locator for final evaluation
            chalix_quiz, created = ChalixQuiz.objects.get_or_create(
                course_key=course_key,
                parent_locator='',  # Empty string indicates final evaluation quiz
                defaults={
                    'title': f'Final Evaluation Quiz for {course_key}',
                    'description': 'Final evaluation quiz questions',
                    'created_by': request.user
                }
            )
            
            # Clear existing questions for this quiz
            ChalixQuizQuestion.objects.filter(quiz=chalix_quiz).delete()
            
            # Process each row and create questions
            questions_created = 0
            with transaction.atomic():
                for index, row in df.iterrows():
                    if pd.isna(row['Question']) or not str(row['Question']).strip():
                        continue
                        
                    question = ChalixQuizQuestion.objects.create(
                        quiz=chalix_quiz,
                        question_text=str(row['Question']).strip(),
                        question_type='multiple_choice',
                        order_index=index + 1
                    )
                    
                    # Create choices
                    choices = [
                        ('A', row['Choice_A']),
                        ('B', row['Choice_B']), 
                        ('C', row['Choice_C']),
                        ('D', row['Choice_D'])
                    ]
                    
                    correct_answer = _normalize_correct_answer_token(row['Correct_Answer'])
                    if correct_answer is None:
                        return JsonResponse({
                            'success': False,
                            'error': f'Giá trị Correct_Answer không hợp lệ tại dòng {index + 2}: "{row["Correct_Answer"]}". Hãy dùng A/B/C/D hoặc 1/2/3/4.'
                        })
                    
                    for choice_key, choice_text in choices:
                        if pd.isna(choice_text) or not str(choice_text).strip():
                            continue
                            
                        ChalixQuizChoice.objects.create(
                            question=question,
                            choice_text=str(choice_text).strip(),
                            is_correct=(choice_key == correct_answer),
                            order_index=ord(choice_key) - ord('A')
                        )
                    
                    questions_created += 1
                
                # Save the file to evaluation
                evaluation.quiz_file = quiz_file
                evaluation.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully uploaded quiz with {questions_created} questions',
                'questions_count': questions_created
            })
            
        except Exception as parse_error:
            logger.error(f"Error parsing Excel file: {parse_error}")
            return JsonResponse({
                'success': False,
                'error': f'Error parsing Excel file: {str(parse_error)}'
            })
            
    except FinalEvaluation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Evaluation not found for this course'
        })
    except Exception as e:
        logger.error(f"Error uploading quiz for course {course_key_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def upload_topic_quiz_api(request, unit_locator_string):
    """
    Upload Excel file for topic quiz (unit-level quiz).
    
    Topic quizzes have fixed settings:
    - Max attempts: 1
    - Time limit: None (no time limit)
    - Show correct answers: immediately after submission
    """
    try:
        import pandas as pd
        from opaque_keys.edx.locator import BlockUsageLocator
        from cms.djangoapps.contentstore.models import ChalixQuiz, ChalixQuizQuestion, ChalixQuizChoice
        from xmodule.modulestore.django import modulestore
        
        unit_locator = BlockUsageLocator.from_string(unit_locator_string)
        course_key = unit_locator.course_key
        
        # Verify unit exists
        store = modulestore()
        try:
            unit = store.get_item(unit_locator)
        except Exception:
            return JsonResponse({
                'success': False,
                'error': 'Unit not found'
            }, status=404)
        
        if 'quiz_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            })
        
        quiz_file = request.FILES['quiz_file']
        
        # Validate file extension
        if not quiz_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'error': 'Please upload an Excel file (.xlsx or .xls)'
            })
        
        # Parse Excel file
        try:
            df = pd.read_excel(quiz_file)
            
            # Expected columns: Question, Choice_A, Choice_B, Choice_C, Choice_D, Correct_Answer
            required_columns = ['Question', 'Choice_A', 'Choice_B', 'Choice_C', 'Choice_D', 'Correct_Answer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required columns: {", ".join(missing_columns)}'
                })
            
            # Get or create ChalixQuiz for this unit
            chalix_quiz, created = ChalixQuiz.objects.get_or_create(
                course_key=course_key,
                parent_locator=str(unit_locator),
                defaults={
                    'title': f'Topic Quiz: {unit.display_name}',
                    'description': 'Topic quiz questions',
                    'created_by': request.user
                }
            )
            
            # Clear existing questions for this quiz
            ChalixQuizQuestion.objects.filter(quiz=chalix_quiz).delete()
            
            # Process each row and create questions
            questions_created = 0
            with transaction.atomic():
                for index, row in df.iterrows():
                    if pd.isna(row['Question']) or not str(row['Question']).strip():
                        continue
                        
                    question = ChalixQuizQuestion.objects.create(
                        quiz=chalix_quiz,
                        question_text=str(row['Question']).strip(),
                        question_type='multiple_choice',
                        order_index=index + 1
                    )
                    
                    # Create choices
                    choices = [
                        ('A', row['Choice_A']),
                        ('B', row['Choice_B']), 
                        ('C', row['Choice_C']),
                        ('D', row['Choice_D'])
                    ]
                    
                    correct_answer = _normalize_correct_answer_token(row['Correct_Answer'])
                    if correct_answer is None:
                        return JsonResponse({
                            'success': False,
                            'error': f'Giá trị Correct_Answer không hợp lệ tại dòng {index + 2}: "{row["Correct_Answer"]}". Hãy dùng A/B/C/D hoặc 1/2/3/4.'
                        })
                    
                    for choice_key, choice_text in choices:
                        if pd.isna(choice_text) or not str(choice_text).strip():
                            continue
                            
                        ChalixQuizChoice.objects.create(
                            question=question,
                            choice_text=str(choice_text).strip(),
                            is_correct=(choice_key == correct_answer),
                            order_index=ord(choice_key) - ord('A')
                        )
                    
                    questions_created += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully uploaded topic quiz with {questions_created} questions',
                'questions_count': questions_created,
                'unit_locator': str(unit_locator)
            })
            
        except Exception as parse_error:
            logger.error(f"Error parsing Excel file for topic quiz: {parse_error}")
            return JsonResponse({
                'success': False,
                'error': f'Error parsing Excel file: {str(parse_error)}'
            })
            
    except Exception as e:
        logger.error(f"Error uploading topic quiz for unit {unit_locator_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
def get_topic_quiz_api(request, unit_locator_string):
    """
    Get topic quiz questions for a specific unit.
    """
    try:
        from opaque_keys.edx.locator import BlockUsageLocator
        from cms.djangoapps.contentstore.models import ChalixQuiz, ChalixQuizQuestion
        
        unit_locator = BlockUsageLocator.from_string(unit_locator_string)
        course_key = unit_locator.course_key
        
        # Get ChalixQuiz for this unit
        try:
            chalix_quiz = ChalixQuiz.objects.get(
                course_key=course_key,
                parent_locator=str(unit_locator),
                is_active=True
            )
            
            questions = ChalixQuizQuestion.objects.filter(
                quiz=chalix_quiz,
                is_active=True
            ).order_by('order_index')
            
            questions_data = []
            for question in questions:
                choices = question.choices.filter(is_active=True).order_by('order_index')
                questions_data.append({
                    'id': question.id,
                    'question_text': question.question_text,
                    'choices': [{
                        'id': choice.id,
                        'choice_text': choice.choice_text,
                        'is_correct': choice.is_correct
                    } for choice in choices]
                })
            
            return JsonResponse({
                'success': True,
                'quiz': {
                    'id': chalix_quiz.id,
                    'title': chalix_quiz.title,
                    'questions_count': len(questions_data),
                    'questions': questions_data
                }
            })
            
        except ChalixQuiz.DoesNotExist:
            return JsonResponse({
                'success': True,
                'quiz': None,
                'message': 'No quiz found for this unit'
            })
            
    except Exception as e:
        logger.error(f"Error getting topic quiz for unit {unit_locator_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["GET"])
def preview_evaluation_quiz_api(request, course_key_string):
    """
    Preview quiz questions for a course evaluation.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import ChalixQuiz, ChalixQuizQuestion
        
        course_key = CourseKey.from_string(course_key_string)
        
        # Get ChalixQuiz with empty parent_locator for final evaluation
        try:
            chalix_quiz = ChalixQuiz.objects.get(
                course_key=course_key,
                parent_locator='',
                is_active=True
            )
        except ChalixQuiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No quiz found for this course. Please upload quiz questions first.',
                'questions': [],
                'total_questions': 0
            })
        
        questions = ChalixQuizQuestion.objects.filter(
            quiz=chalix_quiz,
            is_active=True
        ).order_by('order_index').prefetch_related('choices')
        
        quiz_data = []
        for question in questions:
            choices_data = []
            for choice in question.choices.filter(is_active=True).order_by('order_index'):
                choices_data.append({
                    'id': choice.id,
                    'text': choice.choice_text,
                    'is_correct': choice.is_correct
                })
            
            quiz_data.append({
                'id': question.id,
                'question': question.question_text,
                'choices': choices_data,
                'order': question.order_index
            })
        
        return JsonResponse({
            'success': True,
            'questions': quiz_data,
            'total_questions': len(quiz_data)
        })
        
    except Exception as e:
        logger.error(f"Error previewing quiz for course {course_key_string}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ===========================
# Excel User Import Endpoints
# ===========================

@login_required
@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def download_user_template_api(request):
    """
    GET: Download Excel template for bulk user import (custom or default).
    POST: Upload custom Excel template (bo role only).
    
    Only users with 'bo' role can access this.
    
    Returns an Excel file with Vietnamese column headers for GET.
    Returns JSON response for POST.
    """
    from cms.djangoapps.contentstore.chalix_roles import can_import_users
    from cms.djangoapps.contentstore.excel_import import generate_excel_template
    import os
    from django.conf import settings
    
    try:
        # Check permission
        if not can_import_users(request.user):
            return JsonResponse({
                'error': 'Bạn không có quyền tải template import người dùng.'
            }, status=403)
        
        # Define custom template path
        custom_template_dir = os.path.join(settings.MEDIA_ROOT, 'chalix', 'templates')
        custom_template_path = os.path.join(custom_template_dir, 'custom_user_import_template.xlsx')
        
        if request.method == 'GET':
            # Check if this is just a status check (not a download)
            if request.GET.get('check') == 'true':
                has_custom = os.path.exists(custom_template_path)
                return JsonResponse({
                    'success': True,
                    'has_custom_template': has_custom
                })
            
            # Download template (custom if exists, otherwise default)
            try:
                # Check if custom template exists
                if os.path.exists(custom_template_path):
                    # Serve custom template
                    with open(custom_template_path, 'rb') as f:
                        excel_content = f.read()
                    logger.info(f"[CHALIX] User {request.user.username} downloaded custom user import template")
                else:
                    # Generate default Excel template
                    excel_content = generate_excel_template()
                    logger.info(f"[CHALIX] User {request.user.username} downloaded default user import template")
                
                # Create HTTP response with Excel file
                response = HttpResponse(
                    excel_content,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="template_import_nguoi_dung.xlsx"'
                
                return response
                
            except Exception as e:
                logger.error(f"[CHALIX] Error downloading user import template: {str(e)}")
                return JsonResponse({
                    'error': 'Có lỗi xảy ra khi tải file template. Vui lòng thử lại.'
                }, status=500)
        
        elif request.method == 'POST':
            # Upload custom template (bo role only)
            try:
                # Check if file was uploaded
                if 'file' not in request.FILES:
                    return JsonResponse({
                        'success': False,
                        'message': 'Vui lòng chọn file Excel để tải lên.'
                    }, status=400)
                
                template_file = request.FILES['file']
                
                # openpyxl only supports .xlsx in this flow
                if not template_file.name.lower().endswith('.xlsx'):
                    return JsonResponse({
                        'success': False,
                        'message': 'File phải có định dạng Excel .xlsx.'
                    }, status=400)
                
                # Validate file size (max 5MB for template)
                max_size = 5 * 1024 * 1024  # 5MB
                if template_file.size > max_size:
                    return JsonResponse({
                        'success': False,
                        'message': f'File quá lớn. Kích thước tối đa là {max_size / 1024 / 1024}MB.'
                    }, status=400)
                
                # Validate it's a valid Excel file by trying to open it
                try:
                    import openpyxl
                    from io import BytesIO
                    
                    # Try to load the workbook
                    wb = openpyxl.load_workbook(BytesIO(template_file.read()))
                    template_file.seek(0)  # Reset file pointer
                    
                    # Basic validation: check if it has at least one sheet
                    if len(wb.sheetnames) == 0:
                        return JsonResponse({
                            'success': False,
                            'message': 'File Excel không hợp lệ (không có sheet nào).'
                        }, status=400)
                    
                except Exception as e:
                    logger.error(f"[CHALIX] Error validating template file: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': 'File Excel không hợp lệ hoặc bị hỏng. Vui lòng kiểm tra lại file.'
                    }, status=400)
                
                # Create directory if it doesn't exist
                os.makedirs(custom_template_dir, exist_ok=True)
                
                # Save the custom template
                with open(custom_template_path, 'wb') as f:
                    for chunk in template_file.chunks():
                        f.write(chunk)
                
                logger.info(f"[CHALIX] User {request.user.username} uploaded custom user import template")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Template đã được cập nhật thành công.',
                    'has_custom_template': True
                })
                
            except Exception as e:
                logger.error(f"[CHALIX] Error uploading custom template: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': 'Có lỗi xảy ra khi tải template lên. Vui lòng thử lại.'
                }, status=500)
    
    except Exception as e:
        logger.error(f"[CHALIX] Error in download_user_template_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Có lỗi xảy ra. Vui lòng thử lại.'
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def import_users_from_excel_api(request):
    """
    Import users from uploaded Excel file.
    Only users with 'bo' role can access this.
    
    Expects multipart/form-data with 'excel_file' field.
    
    Returns JSON with import results:
    {
        "success": true/false,
        "total_rows": 10,
        "successful_imports": 8,
        "failed_imports": 2,
        "errors": ["Error message 1", ...],
        "warnings": ["Warning message 1", ...],
        "created_users": [{"username": "...", "email": "...", "name": "..."}, ...]
    }
    """
    from cms.djangoapps.contentstore.chalix_roles import can_import_users
    from cms.djangoapps.contentstore.excel_import import import_users_from_excel
    
    # Check permission
    if not can_import_users(request.user):
        return JsonResponse({
            'error': 'Bạn không có quyền import người dùng từ Excel.'
        }, status=403)
    
    # Check if file was uploaded
    if 'excel_file' not in request.FILES:
        return JsonResponse({
            'error': 'Vui lòng chọn file Excel để tải lên.'
        }, status=400)
    
    excel_file = request.FILES['excel_file']
    
    # openpyxl only supports .xlsx in this flow
    if not excel_file.name.lower().endswith('.xlsx'):
        return JsonResponse({
            'error': 'File phải có định dạng Excel .xlsx.'
        }, status=400)
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if excel_file.size > max_size:
        return JsonResponse({
            'error': f'File quá lớn. Kích thước tối đa là {max_size / 1024 / 1024}MB.'
        }, status=400)
    
    try:
        # Read file content
        file_content = excel_file.read()
        
        # Determine if we need to force org for org admins
        from cms.djangoapps.contentstore.chalix_roles import is_co_quan_user, get_user_primary_role
        force_org = None
        if is_co_quan_user(request.user):
            # Org admins should assign all imported users to their org
            primary_role = get_user_primary_role(request.user)
            if primary_role and primary_role.organization:
                force_org = primary_role.organization
        
        # Import users
        result = import_users_from_excel(file_content, request.user, force_org)
        
        # Log the import operation
        org_info = f" to org '{force_org.display_name}'" if force_org else ""
        logger.info(
            f"[CHALIX] User {request.user.username} imported users from Excel{org_info}. "
            f"Success: {result['successful_imports']}, Failed: {result['failed_imports']}"
        )
        
        # Return result
        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        logger.error(f"[CHALIX] Error importing users from Excel: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Có lỗi xảy ra khi import người dùng: {str(e)}'
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def update_course_metadata_api(request):
    """
    Update course metadata flags (is_mandatory_course, is_public).
    Only instructors (co_quan, giang_vien) can update course metadata.
    
    Expects JSON: {
        "course_id": "course-v1:org+course+run",
        "is_mandatory_course": true/false,  # optional
        "is_public": true/false  # optional
    }
    
    Returns JSON with updated metadata.
    """
    from cms.djangoapps.contentstore.chalix_roles import can_edit_course
    from opaque_keys.edx.keys import CourseKey
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Dữ liệu không hợp lệ.'}, status=400)
    
    course_id_str = data.get('course_id')
    if not course_id_str:
        return JsonResponse({'error': 'Thiếu course_id.'}, status=400)
    
    try:
        course_key = CourseKey.from_string(course_id_str)
    except Exception:
        return JsonResponse({'error': 'Course ID không hợp lệ.'}, status=400)
    
    # Check if user can edit this course
    if not can_edit_course(request.user, course_key):
        return JsonResponse({
            'error': 'Bạn không có quyền chỉnh sửa khóa học này.'
        }, status=403)
    
    # Get or create metadata
    metadata, created = ChalixCourseMetadata.objects.get_or_create(
        course_id=course_key,
        defaults={
            'creator': request.user,
            'is_public': False,
            'is_mandatory_course': False
        }
    )
    
    # Update fields if provided
    updated_fields = []
    if 'is_mandatory_course' in data:
        metadata.is_mandatory_course = bool(data['is_mandatory_course'])
        updated_fields.append('is_mandatory_course')
    
    if 'is_public' in data:
        metadata.is_public = bool(data['is_public'])
        updated_fields.append('is_public')
    
    if updated_fields:
        metadata.save()
        logger.info(
            f"Updated course metadata for {course_key}: {', '.join(updated_fields)}"
        )
    
    return JsonResponse({
        'success': True,
        'course_id': str(course_key),
        'is_mandatory_course': metadata.is_mandatory_course,
        'is_public': metadata.is_public,
        'visibility_description': metadata.visibility_description,
        'created': created,
        'updated_fields': updated_fields
    })


# ─── Survey Campaign API (non-course) ───────────────────────────────────────

def _survey_summary_payload(survey):
    choices_qs = survey.choices.filter(is_active=True)
    choice_count = choices_qs.count()
    return {
        'id': survey.id,
        'title': survey.title,
        'status': getattr(survey, 'status', ('published' if survey.public_token else 'draft')),
        'is_active': survey.is_active,
        'choice_count': choice_count,
        'public_token': survey.public_token,
        'starts_at': survey.starts_at.isoformat() if survey.starts_at else None,
        'ends_at': survey.ends_at.isoformat() if survey.ends_at else None,
        'allow_multiple_votes': bool(getattr(survey, 'allow_multiple_votes', False)),
        'allow_add_choice': bool(getattr(survey, 'allow_add_choice', False)),
        'created_at': survey.created_at.isoformat() if survey.created_at else None,
        'updated_at': survey.updated_at.isoformat() if survey.updated_at else None,
    }


def _empty_survey_course_key():
    """Return the CourseKeyField Empty sentinel for standalone (non-course) surveys."""
    from cms.djangoapps.contentstore.models import ChalixSurveyForm
    return ChalixSurveyForm._meta.get_field('course_key').Empty


@login_required
@require_http_methods(["GET"])
def list_surveys_api(request):
    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    surveys = ChalixSurveyForm.objects.filter(
        is_active=True,
        course_key=_empty_survey_course_key(),
    ).order_by('-updated_at')
    payload = [_survey_summary_payload(survey) for survey in surveys]
    return JsonResponse({'success': True, 'surveys': payload})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_survey_campaign_api(request):
    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    title = (data.get('title') or '').strip() or _('Khảo sát nhu cầu mới')

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    survey = ChalixSurveyForm.objects.create(
        title=title[:500],
        course_key=_empty_survey_course_key(),
        status='published',
        created_by=request.user,
        is_active=True,
    )
    return JsonResponse({'success': True, 'survey': _survey_summary_payload(survey)})


@login_required
@require_http_methods(["GET"])
def get_survey_campaign_api(request, survey_id):
    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    try:
        survey = ChalixSurveyForm.objects.get(
            id=survey_id,
            is_active=True,
            course_key=_empty_survey_course_key(),
        )
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy khảo sát')}, status=404)

    choices = list(
        survey.choices.filter(is_active=True).order_by('order_index').values(
            'id', 'name', 'detail_html', 'order_index'
        )
    )

    payload = _survey_summary_payload(survey)
    payload['choices'] = choices
    payload['link'] = request.build_absolute_uri(f'/survey/{survey.public_token}/') if survey.public_token else None
    return JsonResponse({'success': True, 'survey': payload})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_survey_campaign_api(request, survey_id):
    import bleach

    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON không hợp lệ')}, status=400)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice

    try:
        survey = ChalixSurveyForm.objects.get(
            id=survey_id,
            is_active=True,
            course_key=_empty_survey_course_key(),
        )
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy khảo sát')}, status=404)

    choices_data = data.get('choices', [])
    title = (data.get('title') or '').strip()[:500]
    starts_at_raw = data.get('starts_at')
    ends_at_raw = data.get('ends_at')
    allow_multiple_votes = bool(data.get('allow_multiple_votes', False))
    allow_add_choice = bool(data.get('allow_add_choice', False))

    def _parse_optional_datetime(raw_value, field_label):
        if raw_value in (None, ''):
            return None

        parsed = parse_datetime(str(raw_value))
        if parsed is None:
            raise ValueError(_(f'{field_label} không hợp lệ'))
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    starts_at = _parse_optional_datetime(starts_at_raw, 'Ngày bắt đầu')
    ends_at = _parse_optional_datetime(ends_at_raw, 'Ngày kết thúc')
    if starts_at and ends_at and ends_at < starts_at:
        return JsonResponse({'success': False, 'error': _('Ngày kết thúc phải sau ngày bắt đầu')}, status=400)

    if not choices_data:
        return JsonResponse({'success': False, 'error': _('Cần có ít nhất một chương trình')}, status=400)

    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'em',
        'i', 'li', 'ol', 'p', 'strong', 'u', 'ul',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'td', 'th', 'span',
    ]
    allowed_attrs = {'a': ['href', 'title', 'target'], '*': ['style', 'class']}

    try:
        with transaction.atomic():
            update_fields = []
            if title:
                survey.title = title
                update_fields.append('title')

            if survey.starts_at != starts_at:
                survey.starts_at = starts_at
                update_fields.append('starts_at')

            if survey.ends_at != ends_at:
                survey.ends_at = ends_at
                update_fields.append('ends_at')

            if survey.allow_multiple_votes != allow_multiple_votes:
                survey.allow_multiple_votes = allow_multiple_votes
                update_fields.append('allow_multiple_votes')

            if survey.allow_add_choice != allow_add_choice:
                survey.allow_add_choice = allow_add_choice
                update_fields.append('allow_add_choice')

            if getattr(survey, 'status', None) != 'published':
                survey.status = 'published'
                update_fields.append('status')

            if update_fields:
                survey.save(update_fields=update_fields + ['updated_at'])

            incoming_ids = set()
            for idx, choice in enumerate(choices_data):
                choice_name = (choice.get('name') or '').strip()
                choice_html = bleach.clean(
                    (choice.get('detail_html') or ''),
                    tags=allowed_tags,
                    attributes=allowed_attrs,
                )
                if not choice_name:
                    raise ValueError(_(f'Tên chương trình ở hàng {idx + 1} không được để trống'))
                if not choice_html.strip():
                    raise ValueError(_(f'Chi tiết mô tả ở hàng {idx + 1} không được để trống'))

                choice_id = choice.get('id')
                if choice_id:
                    obj = ChalixSurveyChoice.objects.get(id=int(choice_id), survey=survey)
                    obj.name = choice_name
                    obj.detail_html = choice_html
                    obj.order_index = idx
                    obj.is_active = True
                    obj.save()
                    incoming_ids.add(obj.id)
                else:
                    obj = ChalixSurveyChoice.objects.create(
                        survey=survey,
                        name=choice_name,
                        detail_html=choice_html,
                        order_index=idx,
                    )
                    incoming_ids.add(obj.id)

            survey.choices.exclude(id__in=incoming_ids).update(is_active=False)

        return JsonResponse({'success': True, 'survey_id': survey.id})
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    except ChalixSurveyChoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy lựa chọn')}, status=404)
    except Exception as exc:
        logger.error('save_survey_campaign_api error for survey %s: %s', survey_id, exc, exc_info=True)
        return JsonResponse({'success': False, 'error': _('Lỗi hệ thống')}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def publish_survey_campaign_api(request, survey_id):
    import secrets as _sec

    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    try:
        survey = ChalixSurveyForm.objects.get(
            id=survey_id,
            is_active=True,
            course_key=_empty_survey_course_key(),
        )
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy khảo sát')}, status=404)

    active_choices_count = survey.choices.filter(is_active=True).count()
    if active_choices_count < 1:
        return JsonResponse({'success': False, 'error': _('Cần có ít nhất một chương trình để phát hành khảo sát')}, status=400)

    survey.public_token = _sec.token_urlsafe(32)
    survey.save(update_fields=['public_token', 'updated_at'])
    link = request.build_absolute_uri(f'/survey/{survey.public_token}/')
    return JsonResponse({'success': True, 'survey_id': survey.id, 'link': link, 'token': survey.public_token})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def archive_survey_campaign_api(request, survey_id):
    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    try:
        survey = ChalixSurveyForm.objects.get(
            id=survey_id,
            is_active=True,
            course_key=_empty_survey_course_key(),
        )
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy khảo sát')}, status=404)

    survey.is_active = False
    survey.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True, 'survey_id': survey.id})


def _survey_results_payload(survey):
    choices = list(
        survey.choices.filter(is_active=True).order_by('order_index').values(
            'id', 'name', 'vote_count'
        )
    )
    total_votes = sum(choice.get('vote_count') or 0 for choice in choices)
    result_rows = []
    for choice in choices:
        vote_count = choice.get('vote_count') or 0
        percentage = round((vote_count * 100.0 / total_votes), 2) if total_votes > 0 else 0.0
        result_rows.append({
            'id': choice['id'],
            'name': choice['name'],
            'vote_count': vote_count,
            'percentage': percentage,
        })

    return {
        'survey_id': survey.id,
        'total_votes': total_votes,
        'choices': result_rows,
    }


@login_required
@require_http_methods(["GET"])
def get_survey_results_api(request, survey_id):
    if not can_author_survey(request.user):
        return JsonResponse({'success': False, 'error': _('Không có quyền truy cập')}, status=403)

    from cms.djangoapps.contentstore.models import ChalixSurveyForm

    try:
        survey = ChalixSurveyForm.objects.get(
            id=survey_id,
            is_active=True,
            course_key=_empty_survey_course_key(),
        )
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Không tìm thấy khảo sát')}, status=404)

    return JsonResponse({'success': True, 'results': _survey_results_payload(survey)})


@csrf_exempt
@require_http_methods(["POST"])
def submit_survey_vote_api(request, public_token):
    from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('JSON không hợp lệ')}, status=400)

    choice_id = payload.get('choice_id')
    if not choice_id:
        return JsonResponse({'success': False, 'error': _('Thiếu choice_id')}, status=400)

    try:
        survey = ChalixSurveyForm.objects.get(public_token=public_token, is_active=True)
    except ChalixSurveyForm.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Khảo sát không hợp lệ')}, status=404)

    try:
        with transaction.atomic():
            choice = ChalixSurveyChoice.objects.select_for_update().get(
                id=int(choice_id),
                survey=survey,
                is_active=True,
            )
            ChalixSurveyChoice.objects.filter(id=choice.id).update(vote_count=F('vote_count') + 1)
            choice.refresh_from_db(fields=['vote_count'])

        return JsonResponse({
            'success': True,
            'survey_id': survey.id,
            'choice_id': choice.id,
            'vote_count': choice.vote_count,
        })
    except ChalixSurveyChoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Lựa chọn không hợp lệ')}, status=404)
    except Exception as exc:
        logger.error('submit_survey_vote_api error for token %s: %s', public_token, exc, exc_info=True)
        return JsonResponse({'success': False, 'error': _('Lỗi hệ thống')}, status=500)
