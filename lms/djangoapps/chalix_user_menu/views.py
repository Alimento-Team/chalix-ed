"""
API Views for Chalix User Menu functionality
"""
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Max
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.courseware.courses import get_courses, get_course_by_id
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.models.course_details import CourseDetails
from django.conf import settings
import requests

from .models import (
    UserLearningPlan, TeachingRequest, UserRequest, UserPersonalization, Notification, NotificationType, NotificationPreference,
    ChalixDemandSurveyResponse, ChalixDemandSurveyResponseChoice, ChalixSurveyForm, ChalixSurveyChoice
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_courses(request):
    """
    Get all courses for the current user with progress information
    """
    try:
        user = request.user
        user_enrollments = user.courseenrollment_set.all()

        courses_data = []
        for enrollment in user_enrollments:
            course = enrollment.course
            course_overview = get_object_or_404(CourseOverview, id=course.id)

            # Get user's grade for the course
            try:
                grade = CourseGradeFactory().read(user, course_key=course.id)
                progress_percentage = grade.percent * 100 if grade else 0
            except Exception as e:
                logger.error(f"Error getting grade for user {user.id} in course {course.id}: {e}")
                progress_percentage = 0

            courses_data.append({
                'course_id': str(course.id),
                'course_name': course_overview.display_name,
                'course_image': course_overview.course_image_url,
                'progress_percentage': progress_percentage,
                'enrollment_status': enrollment.mode,
                'is_active': enrollment.is_active,
                'start_date': course_overview.start,
                'end_date': course_overview.end,
            })

        return Response({
            'success': True,
            'courses': courses_data,
            'total_courses': len(courses_data)
        })

    except Exception as e:
        logger.error(f"Error in get_user_courses for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tải danh sách khóa học')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_personalization(request):
    """
    Get or update user personalization settings
    """
    try:
        user = request.user
        personalization, created = UserPersonalization.objects.get_or_create(user=user)

        if request.method == 'GET':
            return Response({
                'success': True,
                'personalization': {
                    'learning_style': personalization.learning_style,
                    'preferred_language': personalization.preferred_language,
                    'notification_preferences': personalization.notification_preferences,
                    'accessibility_preferences': personalization.accessibility_preferences,
                    'theme_preference': personalization.theme_preference,
                }
            })

        elif request.method == 'POST':
            data = request.data

            if 'learning_style' in data:
                personalization.learning_style = data['learning_style']
            if 'preferred_language' in data:
                personalization.preferred_language = data['preferred_language']
            if 'notification_preferences' in data:
                personalization.notification_preferences = data['notification_preferences']
            if 'accessibility_preferences' in data:
                personalization.accessibility_preferences = data['accessibility_preferences']
            if 'theme_preference' in data:
                personalization.theme_preference = data['theme_preference']

            personalization.save()

            return Response({
                'success': True,
                'message': _('Cài đặt cá nhân hóa đã được cập nhật thành công')
            })

    except Exception as e:
        logger.error(f"Error in user_personalization for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể cập nhật cài đặt cá nhân hóa')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_requests(request):
    """
    Get user's requests or create a new request
    """
    try:
        user = request.user

        if request.method == 'GET':
            requests_queryset = UserRequest.objects.filter(user=user)
            paginator = Paginator(requests_queryset, 10)
            page = request.GET.get('page', 1)
            user_requests_page = paginator.get_page(page)

            requests_data = []
            for user_request in user_requests_page:
                requests_data.append({
                    'id': user_request.id,
                    'request_type': user_request.request_type,
                    'title': user_request.title,
                    'description': user_request.description,
                    'status': user_request.status,
                    'priority': user_request.priority,
                    'created_at': user_request.created_at.isoformat(),
                    'updated_at': user_request.updated_at.isoformat(),
                })

            return Response({
                'success': True,
                'requests': requests_data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_requests': paginator.count
            })

        elif request.method == 'POST':
            data = request.data

            user_request = UserRequest.objects.create(
                user=user,
                request_type=data.get('request_type'),
                title=data.get('title'),
                description=data.get('description'),
                priority=data.get('priority', 'medium')
            )

            return Response({
                'success': True,
                'message': _('Yêu cầu đã được tạo thành công'),
                'request_id': user_request.id
            })

    except Exception as e:
        logger.error(f"Error in user_requests for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể xử lý yêu cầu')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def learning_results(request):
    """
    Get user's learning progress and results
    """
    try:
        user = request.user
        user_enrollments = user.courseenrollment_set.filter(is_active=True)

        results_data = []
        total_completed_hours = 0
        total_courses = user_enrollments.count()
        completed_courses = 0

        for enrollment in user_enrollments:
            course = enrollment.course
            course_overview = get_object_or_404(CourseOverview, id=course.id)

            try:
                grade = CourseGradeFactory().read(user, course_key=course.id)
                progress_percentage = grade.percent * 100 if grade else 0

                if progress_percentage >= 80:  # Consider 80% as completed
                    completed_courses += 1

                # Estimate hours based on course duration (simplified calculation)
                estimated_hours = 40  # Default course duration
                completed_hours = (progress_percentage / 100) * estimated_hours
                total_completed_hours += completed_hours

                results_data.append({
                    'course_id': str(course.id),
                    'course_name': course_overview.display_name,
                    'progress_percentage': progress_percentage,
                    'completed_hours': round(completed_hours, 1),
                    'grade': grade.letter_grade if grade else None,
                    'completion_status': 'completed' if progress_percentage >= 80 else 'in_progress',
                    'enrollment_date': enrollment.created.isoformat() if enrollment.created else None,
                })
            except Exception as e:
                logger.error(f"Error processing course {course.id} for user {user.id}: {e}")
                continue

        return Response({
            'success': True,
            'summary': {
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'total_completed_hours': round(total_completed_hours, 1),
                'average_progress': round(sum(result['progress_percentage'] for result in results_data) / max(len(results_data), 1), 1)
            },
            'courses': results_data
        })

    except Exception as e:
        logger.error(f"Error in learning_results for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tải kết quả học tập')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def learning_plans(request):
    """
    Get user's learning plans or create a new one
    """
    try:
        user = request.user

        if request.method == 'GET':
            plans = UserLearningPlan.objects.filter(user=user)
            plans_data = []

            for plan in plans:
                plans_data.append({
                    'id': plan.id,
                    'title': plan.title,
                    'description': plan.description,
                    'target_hours': plan.target_hours,
                    'completed_hours': plan.completed_hours,
                    'progress_percentage': plan.progress_percentage,
                    'start_date': plan.start_date.isoformat(),
                    'end_date': plan.end_date.isoformat(),
                    'status': plan.status,
                    'created_at': plan.created_at.isoformat(),
                })

            return Response({
                'success': True,
                'plans': plans_data,
                'total_plans': len(plans_data)
            })

        elif request.method == 'POST':
            data = request.data

            plan = UserLearningPlan.objects.create(
                user=user,
                title=data.get('title'),
                description=data.get('description', ''),
                target_hours=data.get('target_hours'),
                start_date=data.get('start_date'),
                end_date=data.get('end_date')
            )

            return Response({
                'success': True,
                'message': _('Kế hoạch học tập đã được tạo thành công'),
                'plan_id': plan.id
            })

    except Exception as e:
        logger.error(f"Error in learning_plans for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể xử lý kế hoạch học tập')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teaching_registration(request):
    """
    Get teaching requests or register for teaching
    """
    try:
        user = request.user

        if request.method == 'GET':
            teaching_requests = TeachingRequest.objects.filter(user=user)
            requests_data = []

            for teaching_request in teaching_requests:
                requests_data.append({
                    'id': teaching_request.id,
                    'course_title': teaching_request.course_title,
                    'course_description': teaching_request.course_description,
                    'status': teaching_request.status,
                    'proposed_duration': teaching_request.proposed_duration,
                    'submitted_at': teaching_request.submitted_at.isoformat(),
                    'review_notes': teaching_request.review_notes,
                })

            return Response({
                'success': True,
                'teaching_requests': requests_data,
                'total_requests': len(requests_data)
            })

        elif request.method == 'POST':
            data = request.data

            teaching_request = TeachingRequest.objects.create(
                user=user,
                course_title=data.get('course_title'),
                course_description=data.get('course_description'),
                teaching_experience=data.get('teaching_experience'),
                qualifications=data.get('qualifications'),
                proposed_duration=data.get('proposed_duration')
            )

            return Response({
                'success': True,
                'message': _('Đăng ký giảng dạy đã được gửi thành công'),
                'request_id': teaching_request.id
            })

    except Exception as e:
        logger.error(f"Error in teaching_registration for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể xử lý đăng ký giảng dạy')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def help_resources(request):
    """
    Get help resources and documentation
    """
    try:
        help_data = {
            'categories': [
                {
                    'id': 'getting-started',
                    'title': _('Bắt đầu'),
                    'description': _('Hướng dẫn cơ bản để sử dụng hệ thống'),
                    'articles': [
                        {'title': _('Cách đăng ký khóa học'), 'url': '/help/course-enrollment'},
                        {'title': _('Cách sử dụng giao diện người dùng'), 'url': '/help/user-interface'},
                        {'title': _('Cách theo dõi tiến độ học tập'), 'url': '/help/progress-tracking'},
                    ]
                },
                {
                    'id': 'courses',
                    'title': _('Khóa học'),
                    'description': _('Hướng dẫn về khóa học và việc học'),
                    'articles': [
                        {'title': _('Cách tham gia lớp học trực tuyến'), 'url': '/help/online-classes'},
                        {'title': _('Cách nộp bài tập'), 'url': '/help/assignments'},
                        {'title': _('Cách thi trực tuyến'), 'url': '/help/online-exams'},
                    ]
                },
                {
                    'id': 'account',
                    'title': _('Tài khoản'),
                    'description': _('Quản lý thông tin tài khoản'),
                    'articles': [
                        {'title': _('Cập nhật thông tin cá nhân'), 'url': '/help/profile-update'},
                        {'title': _('Thay đổi mật khẩu'), 'url': '/help/password-change'},
                        {'title': _('Cài đặt thông báo'), 'url': '/help/notifications'},
                    ]
                },
                {
                    'id': 'technical',
                    'title': _('Hỗ trợ kỹ thuật'),
                    'description': _('Giải quyết vấn đề kỹ thuật'),
                    'articles': [
                        {'title': _('Khắc phục lỗi đăng nhập'), 'url': '/help/login-issues'},
                        {'title': _('Yêu cầu hỗ trợ kỹ thuật'), 'url': '/help/technical-support'},
                        {'title': _('Yêu cầu hệ thống'), 'url': '/help/system-requirements'},
                    ]
                },
            ],
            'contact': {
                'email': 'support@chalix.edu.vn',
                'phone': '1900-1234',
                'hours': _('Thứ 2 - Thứ 6, 8:00 - 17:00'),
            }
        }

        return Response({
            'success': True,
            'help_data': help_data
        })

    except Exception as e:
        logger.error(f"Error in help_resources: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tải tài liệu hỗ trợ')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """
    Logout the current user
    """
    try:
        logout(request)
        return Response({
            'success': True,
            'message': _('Đăng xuất thành công')
        })

    except Exception as e:
        logger.error(f"Error in user_logout: {e}")
        return Response({
            'success': False,
            'error': _('Không thể đăng xuất')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get user notifications with pagination
    """
    try:
        user = request.user
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

        notifications_queryset = Notification.objects.filter(user=user, is_archived=False)

        if unread_only:
            notifications_queryset = notifications_queryset.filter(is_read=False)

        notifications_queryset = notifications_queryset.select_related('notification_type')[offset:offset + limit]

        notifications_data = []
        for notification in notifications_queryset:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'time_since_created': notification.time_since_created,
                'notification_type': {
                    'name': notification.notification_type.name,
                    'display_name': notification.notification_type.display_name,
                },
                'action_url': notification.action_url,
                'action_text': notification.action_text,
                'metadata': notification.metadata,
            })

        # Get unread count
        unread_count = Notification.objects.filter(user=user, is_read=False, is_archived=False).count()

        return Response({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
            'has_more': len(notifications_data) == limit
        })

    except Exception as e:
        logger.error(f"Error in get_notifications for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tải thông báo')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read
    """
    try:
        user = request.user
        notification = get_object_or_404(Notification, id=notification_id, user=user)

        notification.mark_as_read()

        return Response({
            'success': True,
            'message': _('Thông báo đã được đánh dấu là đã đọc')
        })

    except Exception as e:
        logger.error(f"Error in mark_notification_read for user {request.user.id}, notification {notification_id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể cập nhật trạng thái thông báo')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """
    Mark all unread notifications as read for the user
    """
    try:
        user = request.user
        updated_count = Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=datetime.now()
        )

        return Response({
            'success': True,
            'message': _('Tất cả thông báo đã được đánh dấu là đã đọc'),
            'updated_count': updated_count
        })

    except Exception as e:
        logger.error(f"Error in mark_all_notifications_read for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể cập nhật trạng thái thông báo')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """
    Get count of unread notifications for the user
    """
    try:
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False, is_archived=False).count()

        return Response({
            'success': True,
            'unread_count': unread_count
        })

    except Exception as e:
        logger.error(f"Error in get_unread_count for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tải số thông báo chưa đọc')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    """
    Create a new notification for the user (usually called by system)
    """
    try:
        data = request.data
        notification_type = get_object_or_404(NotificationType, name=data.get('type'))

        notification = Notification.objects.create(
            user=request.user,
            notification_type=notification_type,
            title=data.get('title'),
            message=data.get('message'),
            priority=data.get('priority', 'medium'),
            action_url=data.get('action_url', ''),
            action_text=data.get('action_text', ''),
            metadata=data.get('metadata', {}),
        )

        return Response({
            'success': True,
            'message': _('Thông báo đã được tạo thành công'),
            'notification_id': notification.id
        })

    except Exception as e:
        logger.error(f"Error in create_notification for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể tạo thông báo')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """
    Get or update user notification preferences
    """
    try:
        user = request.user

        if request.method == 'GET':
            preferences = NotificationPreference.objects.filter(user=user).select_related('notification_type')
            notification_types = NotificationType.objects.filter(is_active=True)

            preferences_data = {}
            for pref in preferences:
                type_name = pref.notification_type.name
                if type_name not in preferences_data:
                    preferences_data[type_name] = {}
                preferences_data[type_name][pref.delivery_method] = pref.is_enabled

            types_data = []
            for nt in notification_types:
                types_data.append({
                    'name': nt.name,
                    'display_name': nt.display_name,
                    'description': nt.description,
                    'preferences': preferences_data.get(nt.name, {'web': True, 'email': True})
                })

            return Response({
                'success': True,
                'notification_types': types_data
            })

        elif request.method == 'POST':
            data = request.data.get('preferences', {})

            for type_name, methods in data.items():
                try:
                    notification_type = NotificationType.objects.get(name=type_name)
                    for method, enabled in methods.items():
                        NotificationPreference.objects.update_or_create(
                            user=user,
                            notification_type=notification_type,
                            delivery_method=method,
                            defaults={'is_enabled': enabled}
                        )
                except NotificationType.DoesNotExist:
                    logger.warning(f"Unknown notification type: {type_name}")

            return Response({
                'success': True,
                'message': _('Tùy chọn thông báo đã được cập nhật')
            })

    except Exception as e:
        logger.error(f"Error in notification_preferences for user {request.user.id}: {e}")
        return Response({
            'success': False,
            'error': _('Không thể xử lý tùy chọn thông báo')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def course_detail_api(request, course_key_string):
    """Get detailed information about a specific OpenEDX course by course key.
    
    URL: /api/chalix/user-menu/course-detail/<course_key>/
    Returns JSON with course details accessible to learner.
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except Exception:
        return JsonResponse({'error': 'Invalid course key'}, status=400)
    
    # Learners should be able to view course metadata before registration.
    # Enrollment checks should gate content access, not metadata display.
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        store = modulestore()
        course = store.get_course(course_key)
        
        if not course:
            return JsonResponse({'error': 'Course not found'}, status=404)
        
        # Get course overview for additional data
        try:
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
        
        return JsonResponse(course_data)
        
    except Exception as e:
        logger.error(f"Error getting course details for {course_key}: {str(e)}")
        return JsonResponse({'error': 'Course not found or inaccessible'}, status=404)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def professional_fields_proxy(request):
    """
    Fetch professional fields directly from the database.
    Since LMS and CMS share the same database, we can query it directly.
    """
    try:
        from django.db import connection

        def _has_professional_field_permission(user):
            if user.is_superuser or user.is_staff:
                return True
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1
                    FROM contentstore_chalixuserrole
                    WHERE user_id = %s
                      AND is_active = 1
                      AND role IN ('bo', 'co_quan')
                    LIMIT 1
                    """,
                    [user.id],
                )
                return cursor.fetchone() is not None

        can_manage = _has_professional_field_permission(request.user)

        if request.method == 'POST':
            if not can_manage:
                return Response(
                    {'error': _('Bạn không có quyền thêm lĩnh vực chuyên môn')},
                    status=status.HTTP_403_FORBIDDEN,
                )

            name = (request.data.get('name') or '').strip()
            description = (request.data.get('description') or '').strip()

            if not name:
                return Response(
                    {'error': _('Tên lĩnh vực chuyên môn không được để trống')},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(name) > 200:
                return Response(
                    {'error': _('Tên lĩnh vực chuyên môn không được vượt quá 200 ký tự')},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM contentstore_professionalfield
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                    """,
                    [name],
                )
                if cursor.fetchone() is not None:
                    return Response(
                        {'error': _('Lĩnh vực chuyên môn này đã tồn tại')},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                cursor.execute(
                    """
                    SELECT COALESCE(MAX(sort_order), 0) + 1
                    FROM contentstore_professionalfield
                    """
                )
                next_sort_order = cursor.fetchone()[0]

                now = timezone.now()
                cursor.execute(
                    """
                    INSERT INTO contentstore_professionalfield
                    (name, description, is_active, sort_order, created_by, created_at, updated_at)
                    VALUES (%s, %s, 1, %s, %s, %s, %s)
                    """,
                    [name, description, next_sort_order, request.user.username, now, now],
                )
                new_id = cursor.lastrowid

            return Response(
                {
                    'id': new_id,
                    'name': name,
                    'description': description,
                    'is_active': True,
                    'sort_order': next_sort_order,
                    'created_by': request.user.username,
                    'created_at': now.isoformat(),
                    'updated_at': now.isoformat(),
                },
                status=status.HTTP_201_CREATED,
            )

        # Query the contentstore_professionalfield table directly
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, is_active, sort_order, created_by, created_at, updated_at
                FROM contentstore_professionalfield
                WHERE is_active = 1
                ORDER BY sort_order, name
            """)

            columns = [col[0] for col in cursor.description]
            fields = []

            for row in cursor.fetchall():
                field_dict = dict(zip(columns, row))
                # Convert datetime objects to ISO format strings
                if field_dict.get('created_at'):
                    field_dict['created_at'] = field_dict['created_at'].isoformat()
                if field_dict.get('updated_at'):
                    field_dict['updated_at'] = field_dict['updated_at'].isoformat()
                fields.append(field_dict)

        logger.info(f"[Professional Fields] Retrieved {len(fields)} fields from database")

        return Response({
            'professional_fields': fields,
            'can_manage': can_manage,
            'is_bo': can_manage,
        })

    except Exception as e:
        logger.error(f"[Professional Fields] Error fetching professional fields: {e}", exc_info=True)
        # Return empty list on error to not break the frontend
        return Response({
            'professional_fields': [],
            'can_manage': False,
            'is_bo': False,
        })


# --- Survey API Endpoints ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def survey_list(request):
    """
    List all active and non-expired surveys for the learner.
    Only shows surveys that:
    1. Are marked as active (is_active=True)
    2. Have status='published'
    3. Have either:
       - No ends_at date set (open-ended), OR
       - ends_at is in the future
    Returns:
        - surveys: list of {public_token, title, created_at, has_responded, starts_at, ends_at}
    """
    try:
        from django.db.models import Q
        
        now = timezone.now()
        # Show only published surveys with no expiration or future expiration
        surveys = ChalixSurveyForm.objects.filter(
            is_active=True,
            status='published'
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        ).order_by('-created_at')
        
        # Check if user has already responded to each survey
        survey_ids_responded = set(ChalixDemandSurveyResponse.objects.filter(
            respondent_user=request.user
        ).values_list('survey_id', flat=True))

        data = []
        for s in surveys:
            data.append({
                'public_token': s.public_token,
                'title': s.title or f"Khảo sát {s.course_key}",
                'course_key': str(s.course_key) if s.course_key else None,
                'starts_at': s.starts_at.isoformat() if s.starts_at else None,
                'ends_at': s.ends_at.isoformat() if s.ends_at else None,
                'created_at': s.created_at.isoformat(),
                'has_responded': s.id in survey_ids_responded
            })

        return Response({
            'success': True,
            'surveys': data
        })
    except Exception as e:
        logger.error(f"Error in survey_list: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def survey_detail(request, public_token):
    """
    Get detailed information for a specific published survey including choices grouped by group_name,
    plus user pre-fill data and already_submitted flag.
    """
    try:
        from common.djangoapps.student.models_api import get_phone_number
        
        survey = get_object_or_404(ChalixSurveyForm, public_token=public_token, is_active=True, status='published')
        
        # Fetch active choices and group them
        choices = ChalixSurveyChoice.objects.filter(
            survey=survey, 
            is_active=True
        ).order_by('group_order', 'order_index')

        groups = []
        group_map = {}  # group_name -> index in groups list
        
        for choice in choices:
            gname = choice.group_name or ''
            if gname not in group_map:
                group_map[gname] = len(groups)
                groups.append({
                    'group_name': gname,
                    'group_order': choice.group_order,
                    'choices': []
                })
            
            groups[group_map[gname]]['choices'].append({
                'id': choice.id,
                'name': choice.name,
                'has_detail': bool(choice.detail_html and choice.detail_html.strip())
            })

        # Check if user has already responded
        response_obj = ChalixDemandSurveyResponse.objects.filter(
            survey_id=survey.id, 
            respondent_user=request.user
        ).first()

        # Pre-fill user data
        try:
            profile_name = request.user.profile.name
        except Exception:
            profile_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        phone = get_phone_number(request.user.id) or ''

        data = {
            'id': survey.id,
            'public_token': survey.public_token,
            'title': survey.title,
            'starts_at': survey.starts_at.isoformat() if survey.starts_at else None,
            'ends_at': survey.ends_at.isoformat() if survey.ends_at else None,
            'allow_multiple_votes': bool(survey.allow_multiple_votes),
            'allow_add_choice': bool(survey.allow_add_choice),
            'groups': groups,
            'user_prefill': {
                'full_name': profile_name,
                'email': request.user.email,
                'phone_number': phone,
            },
            'already_submitted': response_obj is not None,
            'responded_at': response_obj.submitted_at.isoformat() if response_obj else None,
            'selected_choice_ids': list(ChalixDemandSurveyResponseChoice.objects.filter(
                response=response_obj
            ).values_list('choice_id', flat=True)) if response_obj else []
        }

        return Response({
            'success': True,
            'survey': data,
            'groups': groups,
            'user_prefill': data['user_prefill'],
            'already_submitted': response_obj is not None
        })
    except Exception as e:
        logger.error(f"Error in survey_detail: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def survey_submit(request, public_token):
    """
    Submit learner response for a published survey.
    Expects JSON: {
        "full_name": "...",
        "email": "...",
        "phone_number": "...",
        "selected_choice_ids": [1, 2, 3],
        "other_text": "..."
    }
    """
    try:
        def _parse_choice_ids(data):
            """Normalize choice IDs from list/string/int payload shapes."""
            raw_value = data.get('selected_choice_ids', None)
            if raw_value is None:
                raw_value = data.get('choice_id', [])

            if raw_value in (None, ''):
                return []

            if isinstance(raw_value, (list, tuple, set)):
                raw_ids = list(raw_value)
            elif isinstance(raw_value, str):
                # Accept comma-separated values for backward compatibility.
                raw_ids = [part.strip() for part in raw_value.split(',') if part.strip()]
            else:
                raw_ids = [raw_value]

            try:
                return [int(cid) for cid in raw_ids]
            except (TypeError, ValueError):
                raise ValueError('selected_choice_ids phải là số hoặc danh sách số')
        
        survey = get_object_or_404(ChalixSurveyForm, public_token=public_token, is_active=True, status='published')
        
        # Check if survey is within voting period
        now = timezone.now()
        if survey.starts_at and now < survey.starts_at:
            return Response({
                'success': False,
                'error': 'Khảo sát chưa bắt đầu'
            }, status=400)
        if survey.ends_at and now > survey.ends_at:
            return Response({
                'success': False,
                'error': 'Thời gian khảo sát đã kết thúc'
            }, status=400)
        
        try:
            choice_ids = _parse_choice_ids(request.data)
        except ValueError as exc:
            return Response({'success': False, 'error': str(exc)}, status=400)

        existing_response = ChalixDemandSurveyResponse.objects.filter(
            survey_id=survey.id,
            respondent_user=request.user
        ).exists()
        if existing_response:
            return Response({
                'success': False,
                'error': 'Bạn đã nộp khảo sát này rồi'
            }, status=409)

        if not survey.allow_multiple_votes and len(choice_ids) > 1:
            return Response({
                'success': False,
                'error': 'Khảo sát này chỉ cho phép chọn một phương án'
            }, status=400)

        # Get and validate form data
        full_name = str(request.data.get('full_name', '')).strip()[:500]
        email = str(request.data.get('email', '')).strip()[:254]
        phone_number = str(request.data.get('phone_number', '')).strip()[:50]
        other_text = str(request.data.get('other_text', '')).strip()[:500]

        if not full_name:
            return Response({'success': False, 'error': 'Họ và tên không được để trống'}, status=400)
        if not email:
            return Response({'success': False, 'error': 'Email không được để trống'}, status=400)

        if other_text and not survey.allow_add_choice:
            return Response({'success': False, 'error': 'Khảo sát này không cho phép thêm lựa chọn khác'}, status=400)

        # Validate choice IDs belong to this survey
        if choice_ids:
            valid_ids = set(
                ChalixSurveyChoice.objects.filter(
                    survey=survey, is_active=True, pk__in=choice_ids
                ).values_list('pk', flat=True)
            )
            invalid = set(choice_ids) - valid_ids
            if invalid:
                return Response(
                    {'success': False, 'error': f'Invalid choice IDs: {invalid}'},
                    status=400
                )

        with transaction.atomic():
            # Create response with correct field names
            response_obj = ChalixDemandSurveyResponse.objects.create(
                survey_id=survey.id,
                respondent_user=request.user,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                other_text=other_text
            )

            selected_choice_ids = list(choice_ids)

            if survey.allow_add_choice and other_text:
                next_order = (ChalixSurveyChoice.objects.filter(survey=survey)
                    .aggregate(max_idx=Max('order_index'))
                    .get('max_idx') or 0) + 1
                custom_choice = ChalixSurveyChoice.objects.create(
                    survey=survey,
                    name=other_text,
                    detail_html='',
                    order_index=next_order,
                    is_active=True,
                    vote_count=0,
                )
                selected_choice_ids.append(custom_choice.id)
            
            # Record choices and increment vote_counts
            if selected_choice_ids:
                ChalixDemandSurveyResponseChoice.objects.bulk_create([
                    ChalixDemandSurveyResponseChoice(response=response_obj, choice_id=int(cid))
                    for cid in selected_choice_ids
                ])
                # Atomic increment — safe under concurrent requests
                ChalixSurveyChoice.objects.filter(pk__in=selected_choice_ids).update(vote_count=F('vote_count') + 1)

        return Response({
            'success': True,
            'message': 'Cảm ơn bạn đã tham gia khảo sát!'
        })
    except Exception as e:
        logger.error(f"Error in survey_submit: {str(e)}")
        return Response({'success': False, 'error': 'Không thể ghi nhận phiếu khảo sát'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def survey_choice_detail(request, public_token, choice_id):
    """
    Get full HTML details for a specific choice (lazy-loaded on "Chi tiết" click).
    Used for the detail modal popup in the survey taker UI.
    """
    try:
        survey = get_object_or_404(ChalixSurveyForm, public_token=public_token, is_active=True, status='published')
        choice = get_object_or_404(ChalixSurveyChoice, id=choice_id, survey=survey, is_active=True)
        return Response({
            'success': True,
            'choice': {
                'id': choice.id,
                'name': choice.name,
                'detail_html': choice.detail_html
            }
        })
    except Exception as e:
        logger.error(f"Error in survey_choice_detail: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=404)
