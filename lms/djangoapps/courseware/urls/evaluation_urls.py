"""
URL patterns for final evaluation in LMS
"""
from django.urls import path, re_path
from . import evaluation

urlpatterns = [
    # Get evaluation data
    re_path(
        r'^evaluation/(?P<course_id>.+)/$',
        evaluation.get_course_evaluation,
        name='get_course_evaluation'
    ),
    
    # Submit practical assignment
    re_path(
        r'^evaluation/(?P<course_id>.+)/submit/$',
        evaluation.submit_practical_assignment,
        name='submit_practical_assignment'
    ),
    
    # Get quiz questions
    re_path(
        r'^evaluation/(?P<course_id>.+)/quiz/$',
        evaluation.get_quiz_questions,
        name='get_quiz_questions'
    ),
    
    # Submit quiz answer
    re_path(
        r'^evaluation/(?P<course_id>.+)/submit-answer/$',
        evaluation.submit_quiz_answer,
        name='submit_quiz_answer'
    ),
    
    # Complete quiz
    re_path(
        r'^evaluation/(?P<course_id>.+)/complete-quiz/$',
        evaluation.complete_quiz_attempt,
        name='complete_quiz_attempt'
    ),
]