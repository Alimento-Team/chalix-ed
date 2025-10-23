"""
LMS views for final evaluation (practical assignments and quizzes)
"""
import json
import logging
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.db import transaction
from datetime import datetime

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_final_evaluation_config(request, course_id):
    """
    Get final evaluation configuration for a course.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation
        
        course_key = CourseKey.from_string(course_id)
        
        try:
            # Check for quiz evaluation
            quiz_evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
                is_active=True
            )
            return JsonResponse({
                'evaluation_type': 'quiz',
                'id': quiz_evaluation.id,
                'title': 'Kiểm tra cuối khóa',
                'description': 'Bài kiểm tra đánh giá kiến thức toàn khóa học'
            })
        except FinalEvaluation.DoesNotExist:
            pass
        
        try:
            # Check for project evaluation
            project_evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PROJECT,
                is_active=True
            )
            return JsonResponse({
                'evaluation_type': 'project', 
                'id': project_evaluation.id,
                'title': 'Nộp bài dự án',
                'description': project_evaluation.practical_question or 'Hãy nộp file bài dự án của bạn (DOCX/PDF)'
            })
        except FinalEvaluation.DoesNotExist:
            pass
            
        try:
            # Check for practical evaluation (legacy support)
            practical_evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                is_active=True
            )
            return JsonResponse({
                'evaluation_type': 'practical', 
                'id': practical_evaluation.id,
                'title': 'Nộp bài thu hoạch',
                'description': practical_evaluation.practical_question
            })
        except FinalEvaluation.DoesNotExist:
            pass
        
        return JsonResponse({
            'evaluation_type': None,
            'message': 'No final evaluation configured for this course'
        }, status=404)
            
    except Exception as e:
        logger.error(f"Error getting final evaluation config for {course_id}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_course_evaluation(request, course_id):
    """
    Get final evaluation data for a course.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, LearnerSubmission, QuizAttempt
        
        course_key = CourseKey.from_string(course_id)
        
        evaluations = FinalEvaluation.objects.filter(course_key=course_key, is_active=True)
        
        if not evaluations.exists():
            return JsonResponse({
                'success': False,
                'error': 'No evaluation found for this course'
            })
            
        # Process both practical, project, and quiz evaluations
        practical_data = None
        project_data = None
        quiz_data = None
        
        for evaluation in evaluations:
            if evaluation.evaluation_type == FinalEvaluation.EVALUATION_TYPE_PRACTICAL:
                submission = None
                try:
                    submission = LearnerSubmission.objects.get(evaluation=evaluation, learner=request.user)
                except LearnerSubmission.DoesNotExist:
                    pass
                
                practical_data = {
                    'id': evaluation.id,
                    'practical_question': evaluation.practical_question,
                    'has_submission': submission is not None,
                    'submission_file': submission.submission_file.url if submission and submission.submission_file else None,
                    'submission_grade': float(submission.grade) if submission and submission.grade else None,
                    'teacher_feedback': submission.feedback if submission else None,
                    'can_submit': submission is None
                }
                
            elif evaluation.evaluation_type == FinalEvaluation.EVALUATION_TYPE_PROJECT:
                submission = None
                try:
                    submission = LearnerSubmission.objects.get(evaluation=evaluation, learner=request.user)
                except LearnerSubmission.DoesNotExist:
                    pass
                
                project_data = {
                    'id': evaluation.id,
                    'project_question': evaluation.practical_question or 'Hãy nộp file bài dự án của bạn (DOCX/PDF)',
                    'has_submission': submission is not None,
                    'submission_file': submission.submission_file.url if submission and submission.submission_file else None,
                    'submission_file_name': submission.submission_file.name.split('/')[-1] if submission and submission.submission_file else None,
                    'submitted_at': submission.submitted_at.isoformat() if submission else None,
                    'submission_grade': float(submission.grade) if submission and submission.grade else None,
                    'teacher_feedback': submission.feedback if submission else None,
                    'can_submit': True  # Always allow resubmission for projects
                }
                
            elif evaluation.evaluation_type == FinalEvaluation.EVALUATION_TYPE_QUIZ:
                attempt = None
                try:
                    attempt = QuizAttempt.objects.get(evaluation=evaluation, learner=request.user)
                except QuizAttempt.DoesNotExist:
                    pass
                
                quiz_data = {
                    'id': evaluation.id,
                    'has_quiz_attempt': attempt is not None,
                    'quiz_completed': attempt.is_completed if attempt else False,
                    'quiz_score': float(attempt.score) if attempt and attempt.score else None,
                    'can_start': attempt is None or not attempt.is_completed
                }
        
        return JsonResponse({
            'success': True,
            'practical_evaluation': practical_data,
            'project_evaluation': project_data,
            'quiz_evaluation': quiz_data,
            'has_practical': practical_data is not None,
            'has_project': project_data is not None,
            'has_quiz': quiz_data is not None
        })
            
    except Exception as e:
        logger.error(f"Error getting course evaluation for {course_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@csrf_exempt
@require_POST
def submit_practical_assignment(request, course_id):
    """
    Submit practical assignment or project file.
    Supports both practical and project evaluation types.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, LearnerSubmission
        
        course_key = CourseKey.from_string(course_id)
        
        if 'submission_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            })
        
        submission_file = request.FILES['submission_file']
        
        # Try to find evaluation (first project, then practical for backward compatibility)
        evaluation = None
        evaluation_type_name = None
        
        try:
            evaluation = FinalEvaluation.objects.get(
                course_key=course_key, 
                evaluation_type=FinalEvaluation.EVALUATION_TYPE_PROJECT,
                is_active=True
            )
            evaluation_type_name = 'project'
            # For project type, only allow DOCX and PDF
            allowed_extensions = ['docx', 'pdf']
        except FinalEvaluation.DoesNotExist:
            # Fall back to practical type
            try:
                evaluation = FinalEvaluation.objects.get(
                    course_key=course_key, 
                    evaluation_type=FinalEvaluation.EVALUATION_TYPE_PRACTICAL,
                    is_active=True
                )
                evaluation_type_name = 'practical'
                # For practical type, allow DOCX, PPTX, and PDF
                allowed_extensions = ['docx', 'pptx', 'pdf']
            except FinalEvaluation.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No evaluation found for this course'
                })
        
        # Validate file extension
        file_extension = submission_file.name.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
            })
        
        # Check if user already submitted
        submission, created = LearnerSubmission.objects.get_or_create(
            evaluation=evaluation,
            learner=request.user,
            defaults={'submission_file': submission_file}
        )
        
        if not created:
            # Update existing submission
            submission.submission_file = submission_file
            submission.submitted_at = datetime.now()
            submission.grade = None  # Reset grade
            submission.feedback = ''  # Reset feedback
            submission.save()
            message = f'{evaluation_type_name.capitalize()} resubmitted successfully'
        else:
            message = f'{evaluation_type_name.capitalize()} submitted successfully'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'submission_file': submission.submission_file.url,
            'submission_file_name': submission_file.name,
            'evaluation_type': evaluation_type_name
        })
        
    except Exception as e:
        logger.error(f"Error submitting assignment for {course_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required  
@require_http_methods(["GET"])
def get_final_evaluation_quiz(request, course_id):
    """
    Get final evaluation quiz questions.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, ChalixQuizQuestion, QuizAttempt
        
        course_key = CourseKey.from_string(course_id)
        
        evaluation = FinalEvaluation.objects.get(
            course_key=course_key,
            evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
            is_active=True
        )
        
        # Check if user already has a completed attempt
        try:
            attempt = QuizAttempt.objects.get(evaluation=evaluation, learner=request.user)
            if attempt.is_completed:
                return JsonResponse({
                    'error': 'You have already completed this quiz',
                    'completed': True,
                    'score': float(attempt.score) if attempt.score else 0
                }, status=400)
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
        
        return JsonResponse(quiz_data)
        
    except FinalEvaluation.DoesNotExist:
        return JsonResponse({
            'error': 'No quiz evaluation found for this course'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting final evaluation quiz for {course_id}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt  
@require_POST
def submit_final_evaluation_quiz(request, course_id):
    """
    Submit final evaluation quiz answers.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, ChalixQuizQuestion, ChalixQuizChoice, QuizAttempt, QuizAnswer
        
        course_key = CourseKey.from_string(course_id)
        data = json.loads(request.body.decode('utf-8'))
        answers = data.get('answers', {})
        
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
            return JsonResponse({
                'error': 'You have already completed this quiz'
            }, status=400)
        
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
        
        return JsonResponse({
            'score': score,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'completed': True
        })
        
    except FinalEvaluation.DoesNotExist:
        return JsonResponse({
            'error': 'No quiz evaluation found for this course'
        }, status=404)
    except Exception as e:
        logger.error(f"Error submitting final evaluation quiz for {course_id}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_final_evaluation_result(request, course_id):
    """
    Get final evaluation quiz result.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, QuizAttempt
        
        course_key = CourseKey.from_string(course_id)
        
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
        
        return JsonResponse({
            'completed': True,
            'score': float(attempt.score) if attempt.score else 0,
            'correct_answers': attempt.correct_answers,
            'total_questions': attempt.total_questions,
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None
        })
        
    except (FinalEvaluation.DoesNotExist, QuizAttempt.DoesNotExist):
        return JsonResponse({
            'completed': False
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting final evaluation result for {course_id}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_quiz_questions(request, course_id):
    """
    Get quiz questions for evaluation.
    """
    try:
        from opaque_keys.edx.keys import CourseKey
        from cms.djangoapps.contentstore.models import FinalEvaluation, ChalixQuizQuestion, QuizAttempt
        
        course_key = CourseKey.from_string(course_id)
        
        evaluation = FinalEvaluation.objects.get(
            course_key=course_key,
            evaluation_type=FinalEvaluation.EVALUATION_TYPE_QUIZ,
            is_active=True
        )
        
        # Check if user already has an attempt
        try:
            attempt = QuizAttempt.objects.get(evaluation=evaluation, learner=request.user)
            if attempt.is_completed:
                return JsonResponse({
                    'success': False,
                    'error': 'You have already completed this quiz',
                    'completed': True,
                    'score': float(attempt.score) if attempt.score else 0
                })
        except QuizAttempt.DoesNotExist:
            # Create new attempt
            attempt = QuizAttempt.objects.create(
                evaluation=evaluation,
                learner=request.user
            )
        
        # Get questions
        questions = ChalixQuizQuestion.objects.filter(
            course_key=course_key,
            is_active=True
        ).order_by('order_index').prefetch_related('choices')
        
        quiz_data = []
        for question in questions:
            choices_data = []
            for choice in question.choices.filter(is_active=True).order_by('order_index'):
                choices_data.append({
                    'id': choice.id,
                    'text': choice.choice_text
                    # Don't include is_correct for security
                })
            
            quiz_data.append({
                'id': question.id,
                'question': question.question_text,
                'choices': choices_data,
                'order': question.order_index
            })
        
        # Update attempt with total questions
        attempt.total_questions = len(quiz_data)
        attempt.save()
        
        return JsonResponse({
            'success': True,
            'attempt_id': attempt.id,
            'questions': quiz_data,
            'total_questions': len(quiz_data)
        })
        
    except FinalEvaluation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No quiz evaluation found for this course'
        })
    except Exception as e:
        logger.error(f"Error getting quiz questions for {course_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@csrf_exempt
@require_POST
def submit_quiz_answer(request, course_id):
    """
    Submit answer for a quiz question.
    """
    try:
        from cms.djangoapps.contentstore.models import QuizAttempt, QuizAnswer, ChalixQuizQuestion, ChalixQuizChoice
        
        data = json.loads(request.body.decode('utf-8'))
        attempt_id = data.get('attempt_id')
        question_id = data.get('question_id')
        choice_id = data.get('choice_id')
        
        attempt = QuizAttempt.objects.get(id=attempt_id, learner=request.user)
        question = ChalixQuizQuestion.objects.get(id=question_id)
        choice = ChalixQuizChoice.objects.get(id=choice_id) if choice_id else None
        
        # Create or update answer
        answer, created = QuizAnswer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'selected_choice': choice,
                'is_correct': choice.is_correct if choice else False
            }
        )
        
        if not created:
            answer.selected_choice = choice
            answer.is_correct = choice.is_correct if choice else False
            answer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Answer saved'
        })
        
    except Exception as e:
        logger.error(f"Error submitting quiz answer for {course_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@csrf_exempt
@require_POST
def complete_quiz_attempt(request, course_id):
    """
    Complete quiz attempt and calculate score.
    """
    try:
        from cms.djangoapps.contentstore.models import QuizAttempt
        
        data = json.loads(request.body.decode('utf-8'))
        attempt_id = data.get('attempt_id')
        
        attempt = QuizAttempt.objects.get(id=attempt_id, learner=request.user, is_completed=False)
        
        # Calculate score
        total_questions = attempt.total_questions
        correct_answers = attempt.answers.filter(is_correct=True).count()
        
        if total_questions > 0:
            score = (correct_answers / total_questions) * 100
        else:
            score = 0
        
        # Update attempt
        attempt.correct_answers = correct_answers
        attempt.score = score
        attempt.is_completed = True
        attempt.completed_at = datetime.now()
        attempt.save()
        
        return JsonResponse({
            'success': True,
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'message': f'Quiz completed! Score: {score:.1f}%'
        })
        
    except QuizAttempt.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Quiz attempt not found or already completed'
        })
    except Exception as e:
        logger.error(f"Error completing quiz for {course_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })