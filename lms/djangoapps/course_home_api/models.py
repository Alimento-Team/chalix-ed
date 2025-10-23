"""
Course home api models file
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


class DisableProgressPageStackedConfig(StackedConfigurationModel):
    """
    Stacked Config Model for disabling the frontend-app-learning progress page

    .. no_pii:
    """

    STACKABLE_FIELDS = ('disabled',)
    # Since this config disables the progress page,
    # it seemed it would be clearer to use a disabled flag instead of an enabled flag.
    # The enabled field still exists but is not used or shown in the admin.
    disabled = models.BooleanField(default=None, verbose_name=_("Disabled"), null=True)

    def __str__(self):
        return "DisableProgressPageStackedConfig(disabled={!r})".format(
            self.disabled
        )


class UnitMediaFileLMS(models.Model):
    """
    Unmanaged model mapping to CMS contentstore UnitMediaFile table so LMS can
    read unit media (videos/slides) uploaded via authoring without depending on
    the CMS app being installed in this Django site.

    NOTE: Do not create migrations for this model.
    """

    id = models.UUIDField(primary_key=True, editable=False)
    unit_id = models.CharField(max_length=255, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    media_type = models.CharField(max_length=10, db_index=True)  # 'video' | 'slide'
    file_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    upload_url = models.CharField(max_length=500, blank=True, null=True)
    
    # External video URL fields (for YouTube, Google Drive, etc.)
    external_url = models.URLField(max_length=1000, blank=True, null=True)
    public_url = models.URLField(max_length=1000, blank=True, null=True)
    url = models.URLField(max_length=1000, blank=True, null=True)
    video_source_type = models.CharField(max_length=50, blank=True, null=True)
    client_video_id = models.CharField(max_length=255, blank=True, null=True)
    
    uploaded_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contentstore_unitmediafile'
        indexes = [
            models.Index(fields=['unit_id', 'media_type']),
            models.Index(fields=['course_id', 'media_type']),
        ]

    @classmethod
    def get_unit_media(cls, unit_id: str, media_type: str):
        """Return media records for a unit. Keep implementation minimal for LMS.

        This is an unmanaged mirror of the CMS model; avoid heavy logging here.
        """
        qs = cls.objects.filter(unit_id=unit_id)
        if media_type:
            qs = qs.filter(media_type=media_type)
        return qs.order_by('created_at')


# Unmanaged models for Final Evaluation - mirror CMS contentstore tables

class FinalEvaluationLMS(models.Model):
    """Unmanaged model for FinalEvaluation"""
    # Evaluation type constants
    EVALUATION_TYPE_PRACTICAL = 'practical'
    EVALUATION_TYPE_QUIZ = 'quiz'
    EVALUATION_TYPE_PROJECT = 'project'
    
    id = models.BigAutoField(primary_key=True)
    course_key = models.CharField(max_length=255, db_index=True)
    program_id = models.IntegerField(db_index=True)
    evaluation_type = models.CharField(max_length=20)
    practical_question = models.TextField(blank=True)
    quiz_file = models.FileField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_finalevaluation'
    
    class DoesNotExist(Exception):
        pass


class LearnerSubmissionLMS(models.Model):
    """Unmanaged model for LearnerSubmission"""
    id = models.BigAutoField(primary_key=True)
    evaluation_id = models.BigIntegerField()
    learner_id = models.IntegerField()
    submission_file = models.FileField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by_id = models.IntegerField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_learnersubmission'


class QuizAttemptLMS(models.Model):
    """Unmanaged model for QuizAttempt"""
    id = models.BigAutoField(primary_key=True)
    evaluation_id = models.BigIntegerField()
    learner_id = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        managed = False
        db_table = 'contentstore_quizattempt'


class QuizAnswerLMS(models.Model):
    """Unmanaged model for QuizAnswer"""
    id = models.BigAutoField(primary_key=True)
    attempt_id = models.BigIntegerField()
    question_id = models.BigIntegerField()
    selected_choice_id = models.BigIntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_quizanswer'


class ChalixQuizLMS(models.Model):
    """Unmanaged model for ChalixQuiz"""
    id = models.BigAutoField(primary_key=True)
    course_key = models.CharField(max_length=255)
    parent_locator = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_chalixquiz'


class ChalixQuizQuestionLMS(models.Model):
    """Unmanaged model for ChalixQuizQuestion"""
    id = models.BigAutoField(primary_key=True)
    quiz_id = models.BigIntegerField()
    question_text = models.TextField()
    question_type = models.CharField(max_length=20)
    order_index = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_chalixquizquestion'


class ChalixQuizChoiceLMS(models.Model):
    """Unmanaged model for ChalixQuizChoice"""
    id = models.BigAutoField(primary_key=True)
    question_id = models.BigIntegerField()
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order_index = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'contentstore_chalixquizchoice'


class FinalEvaluationProjectSubmission(models.Model):
    """
    Managed LMS model for storing learner project submissions for final evaluations
    configured in Studio (CourseDetails) that don't have a database evaluation record.
    
    This stores the uploaded file and submission metadata for each learner per course.
    """
    course_key = models.CharField(max_length=255, db_index=True, help_text="Course identifier")
    learner = models.ForeignKey('auth.User', on_delete=models.CASCADE, help_text="The learner who submitted")
    submission_file = models.FileField(upload_to='final_evaluation_projects/', help_text="Uploaded project file")
    file_name = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Submission timestamp")
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Score (0-100)")
    feedback = models.TextField(blank=True, help_text="Instructor feedback")
    graded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='graded_submissions', help_text="Instructor who graded")
    graded_at = models.DateTimeField(null=True, blank=True, help_text="Grading timestamp")
    
    class Meta:
        managed = True
        db_table = 'course_home_api_final_eval_project_submission'
        unique_together = [['course_key', 'learner']]  # One submission per learner per course
        indexes = [
            models.Index(fields=['course_key', 'learner']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.learner.username} - {self.course_key} - {self.submitted_at}"
