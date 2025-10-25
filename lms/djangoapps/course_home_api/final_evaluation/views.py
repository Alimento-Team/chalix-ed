"""
Final Evaluation API Views for Course Home API
"""
import json
import logging
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from datetime import datetime
from decimal import Decimal

from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Import unmanaged models from local models
from lms.djangoapps.course_home_api.models import (
    FinalEvaluationLMS as FinalEvaluation,
    LearnerSubmissionLMS as LearnerSubmission,
    QuizAttemptLMS as QuizAttempt,
    QuizAnswerLMS as QuizAnswer,
    ChalixQuizQuestionLMS as ChalixQuizQuestion,
    ChalixQuizChoiceLMS as ChalixQuizChoice,
)

logger = logging.getLogger(__name__)


class FinalEvaluationConfigView(APIView):
    """
    API view to get final evaluation configuration for a course.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_key_string):
        """
        Get final evaluation configuration for a course.
        """
        # Parse course key
        try:
            course_key = CourseKey.from_string(course_key_string)
        except Exception:
            logger.exception(f"Invalid course key: {course_key_string}")
            return Response({'error': 'Invalid course key'}, status=status.HTTP_400_BAD_REQUEST)

        # Priority 1: Read final evaluation config from Studio (CourseDetails)
        try:
            from openedx.core.djangoapps.models.course_details import CourseDetails
            course_details = CourseDetails.fetch(course_key)
            eval_type = getattr(course_details, 'final_evaluation_type', None)
            
            if eval_type == 'quiz':
                return Response({
                    'evaluation_type': 'quiz',
                    'title': 'Kiểm tra cuối khóa',
                    'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học'
                })
            elif eval_type == 'project':
                question = getattr(course_details, 'final_evaluation_project_question', '')
                return Response({
                    'evaluation_type': 'project',
                    'title': 'Nộp bài thu hoạch',
                    'description': question or 'Nộp bài thu hoạch của bạn'
                })
            else:
                # If no type configured in Studio, check database as fallback
                logger.info(f"No final_evaluation_type in CourseDetails for {course_key}, checking database")
        except Exception as e:
            logger.warning(f"Error reading CourseDetails for {course_key}: {e}, checking database")

        # Priority 2 (Fallback): Try to get evaluation from database
        try:
            quiz_evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True,
            )
            return Response({
                'evaluation_type': 'quiz',
                'id': quiz_evaluation.id,
                'title': 'Kiểm tra cuối khóa',
                'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học'
            })
        except (FinalEvaluation.DoesNotExist, RuntimeError, AttributeError):
            pass

        try:
            practical_evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True,
            )
            # Get the question from practical_question field
            question = getattr(practical_evaluation, 'practical_question', '') or getattr(practical_evaluation, 'description', '')
            logger.info(f"Practical evaluation question for {course_key}: {question}")
            
            return Response({
                'evaluation_type': 'project',
                'id': practical_evaluation.id,
                'title': 'Nộp bài thu hoạch',
                'description': question,
            })
        except (FinalEvaluation.DoesNotExist, RuntimeError, AttributeError) as e:
            logger.warning(f"No practical evaluation found for {course_key}: {e}")
            pass

        # No configuration found anywhere
        return Response({
            'evaluation_type': None, 
            'message': 'No final evaluation configured for this course'
        }, status=status.HTTP_404_NOT_FOUND)


class FinalEvaluationQuizView(APIView):
    """
    API view to get final evaluation quiz questions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_key_string):
        """
        Get final evaluation quiz questions.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
            
            try:
                evaluation = FinalEvaluation.objects.get(
                    course_key=course_key,
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                    is_active=True
                )
            except (FinalEvaluation.DoesNotExist, RuntimeError, AttributeError):
                return Response({
                    'error': 'No quiz evaluation found for this course'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check number of attempts for this user
            user_attempts = QuizAttempt.objects.filter(
                evaluation=evaluation, 
                learner=request.user
            ).order_by('-started_at')
            
            attempts_count = user_attempts.count()
            max_attempts = evaluation.quiz_max_attempts or 0  # 0 means unlimited
            
            # Check if user has exceeded max attempts
            if max_attempts > 0 and attempts_count >= max_attempts:
                last_attempt = user_attempts.first()
                return Response({
                    'error': f'Bạn đã sử dụng hết số lần làm bài ({max_attempts} lần)',
                    'completed': True,
                    'attempts_used': attempts_count,
                    'max_attempts': max_attempts,
                    'score': float(last_attempt.score) if last_attempt and last_attempt.score else 0,
                    'passed': last_attempt.passed if last_attempt else False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already has a completed attempt (and can't retake)
            if max_attempts == 1 and attempts_count > 0:
                last_attempt = user_attempts.first()
                if last_attempt.is_completed:
                    return Response({
                        'error': 'Bạn đã hoàn thành bài kiểm tra này',
                        'completed': True,
                        'attempts_used': attempts_count,
                        'max_attempts': max_attempts,
                        'score': float(last_attempt.score) if last_attempt.score else 0,
                        'passed': last_attempt.passed
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get questions for this course
            questions = ChalixQuizQuestion.objects.filter(
                course_key=course_key,
                is_active=True
            ).order_by('order_index').prefetch_related('choices')
            
            quiz_data = {
                'title': 'Kiểm tra cuối khóa',
                'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học',
                'time_limit': evaluation.quiz_time_limit,  # in minutes, None means no limit
                'passing_score': float(evaluation.quiz_passing_score) if evaluation.quiz_passing_score else None,
                'max_attempts': max_attempts,
                'attempts_used': attempts_count,
                'attempts_remaining': (max_attempts - attempts_count) if max_attempts > 0 else None,
                'questions': []
            }
            
            for question in questions:
                choices_data = []
                # Query choices manually since these are unmanaged models
                choices = ChalixQuizChoice.objects.filter(
                    question_id=question.id,
                    is_active=True
                ).order_by('order_index')
                for choice in choices:
                    choices_data.append({
                        'id': choice.id,
                        'choice_text': choice.choice_text
                        # Don't include is_correct for security
                    })
                
                quiz_data['questions'].append({
                    'id': question.id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'choices': choices_data
                })
            
            return Response(quiz_data)
            
        except Exception as e:
            logger.error(f"Error getting final evaluation quiz for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalEvaluationQuizSubmitView(APIView):
    """
    API view to submit final evaluation quiz answers.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, course_key_string):
        """
        Submit final evaluation quiz answers.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
            answers = request.data.get('answers', {})
            
            try:
                evaluation = FinalEvaluation.objects.get(
                    course_key=course_key,
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                    is_active=True
                )
            except (FinalEvaluation.DoesNotExist, RuntimeError, AttributeError):
                return Response({
                    'error': 'No quiz evaluation found for this course'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check attempt limits
            existing_attempts = QuizAttempt.objects.filter(
                evaluation=evaluation,
                learner=request.user
            ).order_by('-started_at')
            
            attempts_count = existing_attempts.count()
            max_attempts = evaluation.quiz_max_attempts or 0
            
            # Check if user has exceeded max attempts
            if max_attempts > 0 and attempts_count >= max_attempts:
                return Response({
                    'error': f'Bạn đã sử dụng hết số lần làm bài ({max_attempts} lần)',
                    'attempts_used': attempts_count,
                    'max_attempts': max_attempts
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new attempt with proper attempt number
            attempt = QuizAttempt.objects.create(
                evaluation=evaluation,
                learner=request.user,
                attempt_number=attempts_count + 1,
                is_completed=False
            )
            
            # Process submitted answers
            correct_count = 0
            total_questions = 0
            
            for question_id_str, choice_ids in answers.items():
                try:
                    question_id = int(question_id_str)
                    question = ChalixQuizQuestion.objects.get(id=question_id, course_key=course_key)
                    total_questions += 1
                    
                    # Handle multiple choice questions
                    if question.question_type == 'multiple_choice_multiple_answer':
                        # For multiple choice, all selected answers must be correct
                        # Query choices manually since these are unmanaged models
                        correct_choices = set(ChalixQuizChoice.objects.filter(
                            question_id=question.id,
                            is_correct=True
                        ).values_list('id', flat=True))
                        selected_choices = set(int(cid) for cid in choice_ids if cid)
                        is_correct = correct_choices == selected_choices
                        
                        # Save all selected choices
                        for choice_id in choice_ids:
                            if choice_id:
                                choice = ChalixQuizChoice.objects.get(id=int(choice_id))
                                QuizAnswer.objects.create(
                                    attempt=attempt,
                                    question=question,
                                    selected_choice=choice,
                                    is_correct=is_correct
                                )
                        
                        if is_correct:
                            correct_count += 1
                            
                    else:
                        # Single choice question
                        if choice_ids and choice_ids[0]:
                            choice = ChalixQuizChoice.objects.get(id=int(choice_ids[0]))
                            is_correct = choice.is_correct
                            
                            QuizAnswer.objects.create(
                                attempt=attempt,
                                question=question,
                                selected_choice=choice,
                                is_correct=is_correct
                            )
                            
                            if is_correct:
                                correct_count += 1
                                
                except (ValueError, ChalixQuizQuestion.DoesNotExist, ChalixQuizChoice.DoesNotExist):
                    continue
            
            # Calculate score
            from decimal import Decimal
            score = Decimal(str((correct_count / total_questions * 100) if total_questions > 0 else 0))
            
            # Check if passed based on minimum passing score
            passing_score = evaluation.quiz_passing_score
            passed = True  # Default to True if no passing score is set
            if passing_score is not None:
                passed = score >= passing_score
            
            # Update attempt
            attempt.correct_answers = correct_count
            attempt.total_questions = total_questions
            attempt.score = score
            attempt.passed = passed
            attempt.is_completed = True
            attempt.completed_at = datetime.now()
            attempt.save()
            
            response_data = {
                'score': float(score),
                'correct_answers': correct_count,
                'total_questions': total_questions,
                'completed': True,
                'passed': passed,
                'attempt_number': attempt.attempt_number,
                'attempts_used': attempts_count + 1,
            }
            
            # Include passing score info if configured
            if passing_score is not None:
                response_data['passing_score'] = float(passing_score)
                response_data['message'] = f'{"Chúc mừng! Bạn đã đạt" if passed else "Bạn chưa đạt"} điểm tối thiểu ({float(passing_score)}%)'
            
            # Include attempts remaining if limited
            if max_attempts > 0:
                response_data['max_attempts'] = max_attempts
                response_data['attempts_remaining'] = max(0, max_attempts - (attempts_count + 1))
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error submitting final evaluation quiz for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalEvaluationResultView(APIView):
    """
    API view to get final evaluation quiz result.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_key_string):
        """
        Get final evaluation quiz result.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
            
            try:
                evaluation = FinalEvaluation.objects.get(
                    course_key=course_key,
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                    is_active=True
                )
            except (FinalEvaluation.DoesNotExist, RuntimeError, AttributeError):
                return Response({
                    'completed': False
                }, status=status.HTTP_404_NOT_FOUND)
            
            try:
                attempt = QuizAttempt.objects.get(
                    evaluation=evaluation,
                    learner=request.user,
                    is_completed=True
                )
            except QuizAttempt.DoesNotExist:
                return Response({
                    'completed': False
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'completed': True,
                'score': float(attempt.score) if attempt.score else 0,
                'correct_answers': attempt.correct_answers,
                'total_questions': attempt.total_questions,
                'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None
            })
            
        except Exception as e:
            logger.error(f"Error getting final evaluation result for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalEvaluationProjectSubmitView(APIView):
    """
    API view to submit final evaluation project (upload DOCX/PDF file).
    Works for courses configured in Studio (CourseDetails) without database evaluation records.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, course_key_string):
        """
        Submit final evaluation project by uploading a file.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
        except Exception:
            logger.exception(f"Invalid course key: {course_key_string}")
            return Response({'error': 'Invalid course key'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the file from request
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'pptx']
        file_extension = uploaded_file.name.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            return Response({
                'error': f'Invalid file type. Only PDF, DOCX, and PPTX files are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if uploaded_file.size > max_size:
            return Response({
                'error': 'File size exceeds 50MB limit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Import the managed model for project submissions
        from lms.djangoapps.course_home_api.models import FinalEvaluationProjectSubmission
        
        # Check if user already submitted
        existing_submission = FinalEvaluationProjectSubmission.objects.filter(
            course_key=str(course_key),
            learner=request.user
        ).first()
        
        if existing_submission:
            return Response({
                'error': 'You have already submitted your project',
                'submission': {
                    'file_name': existing_submission.file_name,
                    'submitted_at': existing_submission.submitted_at.isoformat()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create submission
        try:
            submission = FinalEvaluationProjectSubmission.objects.create(
                course_key=str(course_key),
                learner=request.user,
                submission_file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size
            )
            
            logger.info(f"Project submission created: {submission.id} for user {request.user.username} in course {course_key}")
            
            return Response({
                'success': True,
                'submission_id': submission.id,
                'file_name': submission.file_name,
                'submitted_at': submission.submitted_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error submitting final evaluation project for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)