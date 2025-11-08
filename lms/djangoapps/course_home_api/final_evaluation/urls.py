"""
URLs for Final Evaluation API in Course Home API
"""
from django.conf import settings
from django.urls import re_path

from .views import (
    FinalEvaluationConfigView,
    FinalEvaluationQuizView,
    FinalEvaluationQuizSubmitView,
    FinalEvaluationAttemptStatusView,
    FinalEvaluationResultView,
    FinalEvaluationProjectSubmitView,
    TopicQuizView,
    TopicQuizSubmitView
)

app_name = 'final_evaluation'

urlpatterns = [
    # Final evaluation configuration
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/config$',
        FinalEvaluationConfigView.as_view(),
        name='config'
    ),
    
    # Final evaluation quiz questions
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/quiz$',
        FinalEvaluationQuizView.as_view(),
        name='quiz'
    ),
    
    # Submit final evaluation quiz
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/quiz/submit$',
        FinalEvaluationQuizSubmitView.as_view(),
        name='quiz_submit'
    ),
    
    # Get/manage attempt status
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/attempt-status$',
        FinalEvaluationAttemptStatusView.as_view(),
        name='attempt_status'
    ),
    
    # Get final evaluation result
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/result$',
        FinalEvaluationResultView.as_view(),
        name='result'
    ),
    
    # Submit final evaluation project
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/project/submit$',
        FinalEvaluationProjectSubmitView.as_view(),
        name='project_submit'
    ),
    
    # Topic quiz endpoints
    # Get topic quiz questions for a specific unit
    re_path(
        r'^topic-quiz/(?P<unit_locator_string>.+)/quiz$',
        TopicQuizView.as_view(),
        name='topic_quiz'
    ),
    
    # Submit topic quiz answers
    re_path(
        r'^topic-quiz/(?P<unit_locator_string>.+)/submit$',
        TopicQuizSubmitView.as_view(),
        name='topic_quiz_submit'
    ),
]