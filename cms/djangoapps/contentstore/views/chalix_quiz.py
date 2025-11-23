"""
Quiz API views for Chalix course authoring interface.
Handles quiz creation, management, and CRUD operations.
"""
import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.db import transaction

from opaque_keys.edx.keys import CourseKey, UsageKey
try:
    from xmodule.modulestore.django import modulestore
    from xmodule.modulestore.exceptions import ItemNotFoundError
    from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
except ImportError:
    # For development/testing when OpenEdX modules aren't available
    def modulestore():
        return None
    
    class ItemNotFoundError(Exception):
        pass
    
    def has_studio_read_access(user, course_key):
        return True
    
    def has_studio_write_access(user, course_key):
        return True

from cms.djangoapps.contentstore.models import ChalixQuiz, ChalixQuizQuestion, ChalixQuizChoice

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
@require_POST
def create_quiz_api(request):
    """
    Create a new quiz for a course section/subsection.
    
    Expected POST data:
    {
        "course_key": "course-v1:Org+Course+Run",
        "parent_locator": "block-v1:...",  # The section or subsection where quiz will be attached
        "quiz_title": "Quiz Title",
        "quiz_description": "Optional description",
        "questions": [
            {
                "question_text": "What is...?",
                "question_type": "single_choice" | "multiple_choice",
                "choices": [
                    {"text": "Choice A", "is_correct": true},
                    {"text": "Choice B", "is_correct": false}
                ]
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        course_key_string = data.get('course_key')
        parent_locator = data.get('parent_locator')
        quiz_title = data.get('quiz_title', '').strip()
        quiz_description = data.get('quiz_description', '').strip()
        questions_data = data.get('questions', [])
        
        if not course_key_string or not parent_locator or not quiz_title:
            return JsonResponse({
                'error': _('Thiếu các trường bắt buộc: course_key, parent_locator, quiz_title')
            }, status=400)
        
        # Parse course key and validate access
        try:
            course_key = CourseKey.from_string(course_key_string)
            parent_key = UsageKey.from_string(parent_locator)
        except Exception as e:
            return JsonResponse({'error': _('Định dạng key không hợp lệ: %(error)s') % {'error': str(e)}}, status=400)
        
        if not has_studio_write_access(request.user, course_key):
            return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
        
        # Verify parent block exists
        store = modulestore()
        try:
            parent_block = store.get_item(parent_key)
        except ItemNotFoundError:
            return JsonResponse({'error': _('Không tìm thấy khối cha')}, status=404)
        
        # Validate questions
        if not questions_data:
            return JsonResponse({'error': _('Cần có ít nhất một câu hỏi')}, status=400)
        
        with transaction.atomic():
            # Create quiz record
            quiz = ChalixQuiz.objects.create(
                course_key=course_key,
                parent_locator=parent_locator,
                title=quiz_title,
                description=quiz_description,
                created_by=request.user,
                is_active=True
            )
            
            # Create questions and choices
            for q_index, question_data in enumerate(questions_data):
                question_text = question_data.get('question_text', '').strip()
                question_type = question_data.get('question_type', 'single_choice')
                choices_data = question_data.get('choices', [])
                
                if not question_text or not choices_data:
                    raise ValidationError(f'Question {q_index + 1} is missing text or choices')
                
                if question_type not in ['single_choice', 'multiple_choice']:
                    raise ValidationError(f'Invalid question type: {question_type}')
                
                # Create question
                question = ChalixQuizQuestion.objects.create(
                    quiz=quiz,
                    question_text=question_text,
                    question_type=question_type,
                    order_index=q_index
                )
                
                # Validate choices
                correct_choices = [c for c in choices_data if c.get('is_correct', False)]
                if not correct_choices:
                    raise ValidationError(f'Question {q_index + 1} must have at least one correct answer')
                
                if question_type == 'single_choice' and len(correct_choices) > 1:
                    raise ValidationError(f'Single choice question {q_index + 1} cannot have multiple correct answers')
                
                # Create choices
                for c_index, choice_data in enumerate(choices_data):
                    choice_text = choice_data.get('text', '').strip()
                    is_correct = choice_data.get('is_correct', False)
                    
                    if not choice_text:
                        raise ValidationError(f'Choice {c_index + 1} in question {q_index + 1} cannot be empty')
                    
                    ChalixQuizChoice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct,
                        order_index=c_index
                    )
        
        # Return success response with quiz data
        return JsonResponse({
            'success': True,
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'question_count': len(questions_data),
                'created_at': quiz.created_at.isoformat()
            }
        })
        
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)
    except Exception as e:
        logger.error(f'Error creating quiz: {str(e)}', exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)


@login_required
def get_quiz_api(request, quiz_id):
    """
    Get detailed information about a specific quiz.
    
    Returns quiz data with questions and choices.
    """
    try:
        quiz = ChalixQuiz.objects.get(id=quiz_id, is_active=True)
        
        # Check access permissions
        course_key = CourseKey.from_string(str(quiz.course_key))
        if not has_studio_read_access(request.user, course_key):
            return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
        
        # Build quiz data with questions and choices
        questions = []
        for question in quiz.questions.all().order_by('order_index'):
            choices = []
            for choice in question.choices.all().order_by('order_index'):
                choices.append({
                    'id': choice.id,
                    'text': choice.choice_text,
                    'is_correct': choice.is_correct
                })
            
            questions.append({
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'choices': choices
            })
        
        quiz_data = {
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'parent_locator': quiz.parent_locator,
            'questions': questions,
            'created_at': quiz.created_at.isoformat(),
            'updated_at': quiz.updated_at.isoformat()
        }
        
        return JsonResponse({'success': True, 'quiz': quiz_data})
        
    except ChalixQuiz.DoesNotExist:
        return JsonResponse({'error': _('Không tìm thấy bài quiz')}, status=404)
    except Exception as e:
        logger.error(f'Error getting quiz {quiz_id}: {str(e)}', exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)


@login_required
def list_quizzes_api(request, course_key_string):
    """
    List all quizzes for a specific course.
    
    Optional query parameters:
    - parent_locator: Filter quizzes by parent block
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
        
        if not has_studio_read_access(request.user, course_key):
            return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
        
        # Get query parameters
        parent_locator = request.GET.get('parent_locator')
        
        # Build query
        queryset = ChalixQuiz.objects.filter(
            course_key=course_key,
            is_active=True
        ).order_by('-created_at')
        
        if parent_locator:
            queryset = queryset.filter(parent_locator=parent_locator)
        
        # Build response data
        quizzes = []
        for quiz in queryset:
            question_count = quiz.questions.count()
            quizzes.append({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'parent_locator': quiz.parent_locator,
                'question_count': question_count,
                'created_at': quiz.created_at.isoformat(),
                'updated_at': quiz.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'quizzes': quizzes,
            'count': len(quizzes)
        })
        
    except Exception as e:
        logger.error(f'Error listing quizzes for course {course_key_string}: {str(e)}', exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)


@csrf_exempt
@login_required
@require_POST
def update_quiz_api(request, quiz_id):
    """
    Update an existing quiz.
    
    Expected POST data same as create_quiz_api.
    """
    try:
        data = json.loads(request.body)
        quiz_title = data.get('quiz_title', '').strip()
        quiz_description = data.get('quiz_description', '').strip()
        questions_data = data.get('questions', [])
        
        # Get existing quiz
        quiz = ChalixQuiz.objects.get(id=quiz_id, is_active=True)
        
        # Check access permissions
        course_key = CourseKey.from_string(str(quiz.course_key))
        if not has_studio_write_access(request.user, course_key):
            return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
        
        if not quiz_title:
            return JsonResponse({'error': _('Tiêu đề bài quiz là bắt buộc')}, status=400)
        
        if not questions_data:
            return JsonResponse({'error': _('Cần có ít nhất một câu hỏi')}, status=400)
        
        with transaction.atomic():
            # Update quiz metadata
            quiz.title = quiz_title
            quiz.description = quiz_description
            quiz.save()
            
            # Delete existing questions and choices (cascade will handle choices)
            quiz.questions.all().delete()
            
            # Create new questions and choices
            for q_index, question_data in enumerate(questions_data):
                question_text = question_data.get('question_text', '').strip()
                question_type = question_data.get('question_type', 'single_choice')
                choices_data = question_data.get('choices', [])
                
                if not question_text or not choices_data:
                    raise ValidationError(f'Question {q_index + 1} is missing text or choices')
                
                if question_type not in ['single_choice', 'multiple_choice']:
                    raise ValidationError(f'Invalid question type: {question_type}')
                
                # Create question
                question = ChalixQuizQuestion.objects.create(
                    quiz=quiz,
                    question_text=question_text,
                    question_type=question_type,
                    order_index=q_index
                )
                
                # Validate choices
                correct_choices = [c for c in choices_data if c.get('is_correct', False)]
                if not correct_choices:
                    raise ValidationError(f'Question {q_index + 1} must have at least one correct answer')
                
                if question_type == 'single_choice' and len(correct_choices) > 1:
                    raise ValidationError(f'Single choice question {q_index + 1} cannot have multiple correct answers')
                
                # Create choices
                for c_index, choice_data in enumerate(choices_data):
                    choice_text = choice_data.get('text', '').strip()
                    is_correct = choice_data.get('is_correct', False)
                    
                    if not choice_text:
                        raise ValidationError(f'Choice {c_index + 1} in question {q_index + 1} cannot be empty')
                    
                    ChalixQuizChoice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct,
                        order_index=c_index
                    )
        
        return JsonResponse({
            'success': True,
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'question_count': len(questions_data),
                'updated_at': quiz.updated_at.isoformat()
            }
        })
        
    except ChalixQuiz.DoesNotExist:
        return JsonResponse({'error': _('Không tìm thấy bài quiz')}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)
    except Exception as e:
        logger.error(f'Error updating quiz {quiz_id}: {str(e)}', exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)


@csrf_exempt
@login_required
@require_POST
def delete_quiz_api(request, quiz_id):
    """
    Delete (soft delete) a quiz.
    """
    try:
        data = json.loads(request.body)
        
        # Get existing quiz
        quiz = ChalixQuiz.objects.get(id=quiz_id, is_active=True)
        
        # Check access permissions
        course_key = CourseKey.from_string(str(quiz.course_key))
        if not has_studio_write_access(request.user, course_key):
            return JsonResponse({'error': _('Không có quyền truy cập')}, status=403)
        
        # Soft delete
        quiz.is_active = False
        quiz.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Đã xóa bài quiz thành công')
        })
        
    except ChalixQuiz.DoesNotExist:
        return JsonResponse({'error': _('Không tìm thấy bài quiz')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)
    except Exception as e:
        logger.error(f'Error deleting quiz {quiz_id}: {str(e)}', exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)