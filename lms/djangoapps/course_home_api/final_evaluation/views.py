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

from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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
        try:
            from cms.djangoapps.contentstore.models import FinalEvaluation
            
            course_key = CourseKey.from_string(course_key_string)
            
            try:
                # Check for quiz evaluation
                quiz_evaluation = FinalEvaluation.objects.get(
                    course_key=course_key, 
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                    is_active=True
                )
                return Response({
                    'evaluation_type': 'quiz',
                    'id': quiz_evaluation.id,
                    'title': 'Kiểm tra cuối khóa',
                    'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học'
                })
            except FinalEvaluation.DoesNotExist:
                pass
                
            try:
                # Check for practical evaluation
                practical_evaluation = FinalEvaluation.objects.get(
                    course_key=course_key, 
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                    is_active=True
                )
                return Response({
                    'evaluation_type': 'practical', 
                    'id': practical_evaluation.id,
                    'title': 'Nộp bài thu hoạch',
                    'description': practical_evaluation.practical_question
                })
            except FinalEvaluation.DoesNotExist:
                pass
            
            return Response({
                'evaluation_type': None,
                'message': 'No final evaluation configured for this course'
            }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error getting final evaluation config for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            from cms.djangoapps.contentstore.models import FinalEvaluation, ChalixQuizQuestion, QuizAttempt
            
            course_key = CourseKey.from_string(course_key_string)
            
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            
            # Check if user already has a completed attempt
            try:
                attempt = QuizAttempt.objects.get(evaluation=evaluation, learner=request.user)
                if attempt.is_completed:
                    return Response({
                        'error': 'You have already completed this quiz',
                        'completed': True,
                        'score': float(attempt.score) if attempt.score else 0
                    }, status=status.HTTP_400_BAD_REQUEST)
            except QuizAttempt.DoesNotExist:
                pass
            
            # Get questions for this course
            questions = ChalixQuizQuestion.objects.filter(
                course_key=course_key,
                is_active=True
            ).order_by('order_index').prefetch_related('choices')
            
            quiz_data = {
                'title': 'Kiểm tra cuối khóa',
                'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học',
                'questions': []
            }
            
            for question in questions:
                choices_data = []
                for choice in question.choices.filter(is_active=True).order_by('order_index'):
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
            
        except FinalEvaluation.DoesNotExist:
            return Response({
                'error': 'No quiz evaluation found for this course'
            }, status=status.HTTP_404_NOT_FOUND)
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
            from cms.djangoapps.contentstore.models import (
                FinalEvaluation, ChalixQuizQuestion, ChalixQuizChoice, QuizAttempt, QuizAnswer
            )
            
            course_key = CourseKey.from_string(course_key_string)
            answers = request.data.get('answers', {})
            
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            
            # Get or create attempt
            attempt, created = QuizAttempt.objects.get_or_create(
                evaluation=evaluation,
                learner=request.user,
                defaults={'is_completed': False}
            )
            
            if attempt.is_completed:
                return Response({
                    'error': 'You have already completed this quiz'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Clear existing answers for this attempt
            QuizAnswer.objects.filter(attempt=attempt).delete()
            
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
                        correct_choices = set(question.choices.filter(is_correct=True).values_list('id', flat=True))
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
            score = (correct_count / total_questions * 100) if total_questions > 0 else 0
            
            # Update attempt
            attempt.correct_answers = correct_count
            attempt.total_questions = total_questions
            attempt.score = score
            attempt.is_completed = True
            attempt.completed_at = datetime.now()
            attempt.save()
            
            return Response({
                'score': score,
                'correct_answers': correct_count,
                'total_questions': total_questions,
                'completed': True
            })
            
        except FinalEvaluation.DoesNotExist:
            return Response({
                'error': 'No quiz evaluation found for this course'
            }, status=status.HTTP_404_NOT_FOUND)
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
            from cms.djangoapps.contentstore.models import FinalEvaluation, QuizAttempt
            
            course_key = CourseKey.from_string(course_key_string)
            
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key,
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            
            attempt = QuizAttempt.objects.get(
                evaluation=evaluation,
                learner=request.user,
                is_completed=True
            )
            
            return Response({
                'completed': True,
                'score': float(attempt.score) if attempt.score else 0,
                'correct_answers': attempt.correct_answers,
                'total_questions': attempt.total_questions,
                'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None
            })
            
        except (FinalEvaluation.DoesNotExist, QuizAttempt.DoesNotExist):
            return Response({
                'completed': False
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting final evaluation result for {course_key_string}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)