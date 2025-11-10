"""
API views for course progress and learner submission grading.

These views allow teachers to:
- View list of learners enrolled in a course
- View learner submissions for practical evaluations  
- Grade submissions with feedback
- Send grade notifications to learners
"""
import logging
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from opaque_keys.edx.keys import CourseKey
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from cms.djangoapps.contentstore.models import FinalEvaluation, LearnerSubmission
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@require_http_methods(["GET"])
def list_course_learners(request, course_id):
    """
    List all learners enrolled in a course with their submission status.
    
    Returns:
        {
            'success': True,
            'learners': [
                {
                    'id': user_id,
                    'username': 'username',
                    'email': 'email@example.com',
                    'full_name': 'Full Name',
                    'enrollment_date': '2024-01-01',
                    'has_submission': True/False,
                    'submission_date': '2024-01-15' or None,
                    'grade': 85.5 or None,
                    'graded': True/False
                },
                ...
            ],
            'total': 25
        }
    """
    try:
        course_key = CourseKey.from_string(course_id)
        
        # Check if user has staff access to course
        if not has_access(request.user, 'staff', course_key):
            return Response({
                'success': False,
                'error': 'You do not have permission to view course progress'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all enrollments for this course
        enrollments = CourseEnrollment.objects.filter(
            course_id=course_key,
            is_active=True
        ).select_related('user').order_by('user__username')
        
        # Get evaluation for this course (if exists)
        try:
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
        except FinalEvaluation.DoesNotExist:
            # No practical evaluation for this course
            evaluation = None
        
        # Get all submissions if evaluation exists
        submissions_map = {}
        if evaluation:
            submissions = LearnerSubmission.objects.filter(
                evaluation=evaluation
            ).select_related('learner')
            submissions_map = {sub.learner_id: sub for sub in submissions}
        
        # Build learner list with submission status
        learners_data = []
        for enrollment in enrollments:
            user = enrollment.user
            submission = submissions_map.get(user.id)
            
            # Get full name from profile
            full_name = user.get_full_name() or user.username
            try:
                if hasattr(user, 'profile') and user.profile.name:
                    full_name = user.profile.name
            except:
                pass
            
            learner_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': full_name,
                'enrollment_date': enrollment.created.isoformat() if enrollment.created else None,
                'has_submission': submission is not None,
                'submission_date': submission.submitted_at.isoformat() if submission else None,
                'grade': float(submission.grade) if submission and submission.grade else None,
                'graded': submission is not None and submission.grade is not None
            }
            learners_data.append(learner_data)
        
        return Response({
            'success': True,
            'learners': learners_data,
            'total': len(learners_data),
            'has_evaluation': evaluation is not None
        })
        
    except Exception as e:
        logger.error(f"Error listing learners for course {course_id}: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@require_http_methods(["GET"])
def get_learner_submission(request, course_id, user_id):
    """
    Get detailed submission information for a specific learner.
    
    Returns:
        {
            'success': True,
            'submission': {
                'id': submission_id,
                'learner': {
                    'id': user_id,
                    'username': 'username',
                    'email': 'email@example.com',
                    'full_name': 'Full Name'
                },
                'submission_file_url': '/path/to/file',
                'submission_file_name': 'assignment.docx',
                'submitted_at': '2024-01-15T10:30:00',
                'grade': 85.5 or None,
                'feedback': 'Good work!' or '',
                'graded_by': 'teacher_username' or None,
                'graded_at': '2024-01-20T14:00:00' or None,
                'practical_question': 'Question text here'
            }
        }
    """
    try:
        course_key = CourseKey.from_string(course_id)
        
        # Check if user has staff access
        if not has_access(request.user, 'staff', course_key):
            return Response({
                'success': False,
                'error': 'You do not have permission to view submissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the learner
        try:
            learner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Learner not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get evaluation
        try:
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
        except FinalEvaluation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No practical evaluation found for this course'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get submission
        try:
            submission = LearnerSubmission.objects.get(
                evaluation=evaluation,
                learner=learner
            )
        except LearnerSubmission.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No submission found for this learner'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get learner full name
        full_name = learner.get_full_name() or learner.username
        try:
            if hasattr(learner, 'profile') and learner.profile.name:
                full_name = learner.profile.name
        except:
            pass
        
        submission_data = {
            'id': submission.id,
            'learner': {
                'id': learner.id,
                'username': learner.username,
                'email': learner.email,
                'full_name': full_name
            },
            'submission_file_url': submission.submission_file.url if submission.submission_file else None,
            'submission_file_name': submission.submission_file.name.split('/')[-1] if submission.submission_file else None,
            'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
            'grade': float(submission.grade) if submission.grade else None,
            'feedback': submission.feedback or '',
            'graded_by': submission.graded_by.username if submission.graded_by else None,
            'graded_at': submission.graded_at.isoformat() if submission.graded_at else None,
            'practical_question': evaluation.practical_question or ''
        }
        
        return Response({
            'success': True,
            'submission': submission_data
        })
        
    except Exception as e:
        logger.error(f"Error getting submission for user {user_id} in course {course_id}: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@require_http_methods(["POST"])
def grade_submission(request, course_id, user_id):
    """
    Grade a learner's submission and send notification.
    
    Expected POST data:
        {
            'grade': 85.5,  # Score out of 100
            'feedback': 'Excellent work! Keep it up.'
        }
    
    Returns:
        {
            'success': True,
            'message': 'Submission graded successfully',
            'submission': {
                'grade': 85.5,
                'feedback': 'Excellent work!',
                'graded_by': 'teacher_username',
                'graded_at': '2024-01-20T14:00:00'
            }
        }
    """
    try:
        course_key = CourseKey.from_string(course_id)
        
        # Check if user has staff access
        if not has_access(request.user, 'staff', course_key):
            return Response({
                'success': False,
                'error': 'You do not have permission to grade submissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input
        grade = request.data.get('grade')
        feedback = request.data.get('feedback', '')
        
        if grade is None:
            return Response({
                'success': False,
                'error': 'Grade is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            grade = float(grade)
            if grade < 0 or grade > 100:
                raise ValueError("Grade must be between 0 and 100")
        except (ValueError, TypeError) as e:
            return Response({
                'success': False,
                'error': f'Invalid grade value: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the learner
        try:
            learner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Learner not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get evaluation
        try:
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
        except FinalEvaluation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No practical evaluation found for this course'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get submission
        try:
            submission = LearnerSubmission.objects.get(
                evaluation=evaluation,
                learner=learner
            )
        except LearnerSubmission.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No submission found for this learner'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update submission with grade and feedback
        with transaction.atomic():
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_by = request.user
            submission.graded_at = datetime.now()
            submission.save()
        
        # Send notification email to learner
        try:
            course_overview = CourseOverview.objects.get(id=course_key)
            course_name = course_overview.display_name
        except CourseOverview.DoesNotExist:
            course_name = str(course_key)
        
        # Send email notification
        try:
            subject = f'Bài nộp của bạn đã được chấm điểm - {course_name}'
            message = f"""
Xin chào {learner.get_full_name() or learner.username},

Bài nộp thu hoạch của bạn cho khóa học "{course_name}" đã được chấm điểm.

Điểm số: {grade}/100

Nhận xét từ giáo viên:
{feedback}

Bạn có thể xem chi tiết tại trang khóa học.

Trân trọng,
Hệ thống Chalix
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [learner.email],
                fail_silently=True,  # Don't fail the grading if email fails
            )
            logger.info(f"Sent grade notification email to {learner.email} for course {course_id}")
        except Exception as email_error:
            logger.error(f"Failed to send grade notification email: {email_error}")
            # Continue anyway, grading was successful
        
        return Response({
            'success': True,
            'message': 'Submission graded successfully',
            'submission': {
                'grade': float(submission.grade),
                'feedback': submission.feedback,
                'graded_by': request.user.username,
                'graded_at': submission.graded_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error grading submission for user {user_id} in course {course_id}: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@require_http_methods(["GET"])
def download_submission_file(request, course_id, user_id):
    """
    Download a learner's submission file.
    
    Returns the file for download.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        
        # Check if user has staff access
        if not has_access(request.user, 'staff', course_key):
            return Response({
                'success': False,
                'error': 'You do not have permission to download submissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the learner
        try:
            learner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404("Learner not found")
        
        # Get evaluation
        try:
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
        except FinalEvaluation.DoesNotExist:
            raise Http404("No practical evaluation found for this course")
        
        # Get submission
        try:
            submission = LearnerSubmission.objects.get(
                evaluation=evaluation,
                learner=learner
            )
        except LearnerSubmission.DoesNotExist:
            raise Http404("No submission found for this learner")
        
        if not submission.submission_file:
            raise Http404("No file attached to this submission")
        
        # Return file response
        response = FileResponse(submission.submission_file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{submission.submission_file.name.split("/")[-1]}"'
        return response
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error downloading submission file for user {user_id} in course {course_id}: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
