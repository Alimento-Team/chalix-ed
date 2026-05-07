"""
API views for facial expression recording.
"""
import logging
from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.view_utils import view_auth_classes

from lms.djangoapps.learning_analytics.models import FacialExpressionLog
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.learning_analytics.services import LearningHoursService, StudentLearningProcessService
from .serializers import FacialExpressionUploadSerializer, FacialExpressionLogSerializer
from .storage import get_facial_expression_storage

logger = logging.getLogger(__name__)


@api_view(['POST'])
@view_auth_classes(is_authenticated=True)
def upload_facial_expression_video(request):
    """
    Upload facial expression video recording.
    
    POST /api/facial-expression/upload/
    
    Request body:
        - video: Video file (multipart/form-data)
        - course_id: Course ID
        - unit_id: Unit/Block ID
        - topic_id: Topic ID (optional)
        - timestamp: Recording timestamp (ISO format)
        - is_final: Boolean indicating if this is the final chunk
    
    Returns:
        - 201 Created: Video uploaded successfully
        - 400 Bad Request: Invalid data
        - 500 Internal Server Error: Server error
    """
    serializer = FacialExpressionUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        video_file = serializer.validated_data['video']
        course_id = serializer.validated_data['course_id']
        unit_id = serializer.validated_data['unit_id']
        topic_id = serializer.validated_data.get('topic_id')
        timestamp = serializer.validated_data['timestamp']
        is_final = serializer.validated_data.get('is_final', False)
        duration_seconds = serializer.validated_data.get('duration_seconds', 0)
        
        user = request.user
        snapshot = StudentLearningProcessService.get_for_user(user)
        student_id = snapshot.student_id if snapshot else user.username
        week_number = LearningHoursService.resolve_learning_week(user, course_id)
        
        # Get course information
        try:
            course_key = CourseKey.from_string(course_id)
            course = get_course_by_id(course_key)
            org_id = course_key.org
        except Exception as e:
            logger.error(f"Error getting course info: {e}")
            org_id = None
        
        # Get storage instance
        storage = get_facial_expression_storage()
        
        # Generate unique path for video
        video_path = storage.generate_video_path(
            user_id=user.id,
            course_id=course_id,
            unit_id=unit_id,
            timestamp=timestamp,
            student_id=student_id,
            week_number=week_number,
        )
        
        # Save video to storage
        saved_path = storage.save_video(video_file, video_path)
        
        # Create database record
        facial_log = FacialExpressionLog.objects.create(
            user=user,
            course_id=course_id,
            unit_id=unit_id,
            topic_id=topic_id,
            org_id=org_id,
            video_path=saved_path,
            video_size=video_file.size,
            duration_seconds=duration_seconds,
            start_timestamp=timestamp,
            end_timestamp=timezone.now() if is_final else None,
            is_complete=is_final,
            processing_status='pending'
        )

        week_segment = f'/week_{week_number}/'
        stale_logs = FacialExpressionLog.objects.filter(
            user=user,
            course_id=course_id,
            is_complete=True,
            video_path__contains=week_segment,
        ).exclude(id=facial_log.id)

        for stale_log in stale_logs:
            storage.delete_video(stale_log.video_path)
            stale_log.delete()
        
        # Try to get teacher/instructor info
        try:
            # This would need to be implemented based on your course structure
            # For now, we'll leave it as None
            pass
        except Exception as e:
            logger.warning(f"Could not get teacher info: {e}")
        
        log_serializer = FacialExpressionLogSerializer(facial_log)

        # For new accounts without an imported snapshot, auto-create a live stub
        # so that the emotion-score API can still be called on final upload.
        if is_final:
            StudentLearningProcessService.get_or_create_live_snapshot(user, course_id)

        refreshed_snapshot = StudentLearningProcessService.get_for_user(
            user,
            refresh_prediction=is_final,
            course_id=course_id,
            week_number=week_number,
        )
        predicted_score = None
        if refreshed_snapshot and refreshed_snapshot.predicted_final_score is not None:
            predicted_score = float(refreshed_snapshot.predicted_final_score)
        
        logger.info(
            f"Facial expression video uploaded successfully. "
            f"User: {user.username}, Course: {course_id}, Unit: {unit_id}, "
            f"Path: {saved_path}, Size: {video_file.size} bytes, "
            f"Duration: {duration_seconds} seconds, Is Final: {is_final}"
        )
        
        return Response(
            {
                'message': 'Video uploaded successfully',
                'log': log_serializer.data,
                'prediction': {
                    'week_number': week_number,
                    'predicted_score': predicted_score,
                    'source': 'emotion',
                },
            },
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error uploading facial expression video: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to upload video', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def get_facial_expression_logs(request):
    """
    Get facial expression logs for the authenticated user.
    
    GET /api/facial-expression/logs/
    
    Query parameters:
        - course_id: Filter by course ID (optional)
        - unit_id: Filter by unit ID (optional)
        - limit: Number of results to return (default: 50)
    
    Returns:
        - 200 OK: List of logs
    """
    try:
        user = request.user
        course_id = request.GET.get('course_id')
        unit_id = request.GET.get('unit_id')
        limit = int(request.GET.get('limit', 50))
        
        # Build query
        queryset = FacialExpressionLog.objects.filter(user=user)
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        # Limit results
        logs = queryset[:limit]
        
        serializer = FacialExpressionLogSerializer(logs, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching facial expression logs: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to fetch logs', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def get_facial_expression_log_detail(request, log_id):
    """
    Get detailed information about a specific facial expression log.
    
    GET /api/facial-expression/logs/{log_id}/
    
    Returns:
        - 200 OK: Log details
        - 404 Not Found: Log not found
    """
    try:
        user = request.user
        
        # Get log and verify ownership
        try:
            log = FacialExpressionLog.objects.get(id=log_id, user=user)
        except FacialExpressionLog.DoesNotExist:
            return Response(
                {'error': 'Log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = FacialExpressionLogSerializer(log)
        
        # Get video URL if available
        storage = get_facial_expression_storage()
        video_url = storage.get_video_url(log.video_path)
        
        response_data = serializer.data
        response_data['video_url'] = video_url
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching facial expression log detail: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to fetch log detail', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def check_valid_recording(request):
    """
    Check if user has a valid recording for a specific course unit.
    
    GET /api/facial-expression/check-recording/
    
    Query parameters:
        - course_id: Course ID (required)
        - unit_id: Unit ID (required)
        - min_duration: Minimum duration in seconds (default: 300 = 5 minutes)
    
    Returns:
        - 200 OK: { "has_valid_recording": true/false, "duration": seconds }
    """
    try:
        user = request.user
        course_id = request.GET.get('course_id')
        unit_id = request.GET.get('unit_id')
        min_duration = int(request.GET.get('min_duration', 300))  # Default 5 minutes
        
        if not course_id or not unit_id:
            return Response(
                {'error': 'course_id and unit_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for recent valid recording (within last 24 hours)
        from datetime import timedelta
        time_threshold = timezone.now() - timedelta(hours=24)
        
        # Find the most recent complete recording for this course-unit
        recent_log = FacialExpressionLog.objects.filter(
            user=user,
            course_id=course_id,
            unit_id=unit_id,
            is_complete=True,
            created_at__gte=time_threshold,
            duration_seconds__gte=min_duration
        ).order_by('-created_at').first()
        
        if recent_log:
            return Response({
                'has_valid_recording': True,
                'duration': recent_log.duration_seconds,
                'recorded_at': recent_log.created_at.isoformat(),
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'has_valid_recording': False,
                'duration': 0,
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking valid recording: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to check recording', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

