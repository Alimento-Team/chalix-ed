"""
URLs for Final Evaluation API in Course Home API
"""
from django.conf import settings
from django.urls import re_path

from .views import (
    FinalEvaluationConfigView,
    FinalEvaluationQuizView,
    FinalEvaluationQuizSubmitView,
    FinalEvaluationResultView
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
    
    # Get final evaluation result
    re_path(
        fr'^{settings.COURSE_KEY_PATTERN}/result$',
        FinalEvaluationResultView.as_view(),
        name='result'
    ),
]