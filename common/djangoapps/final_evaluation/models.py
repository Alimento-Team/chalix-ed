"""
Final Evaluation models shared between LMS and CMS.
These models are defined here to be accessible from both applications.
"""
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField


class FinalEvaluation(models.Model):
    """
    Model to store final evaluation content for courses based on programs.
    """
    EVALUATION_TYPE_PRACTICAL = 'practical'
    EVALUATION_TYPE_QUIZ = 'quiz'
    EVALUATION_TYPE_PROJECT = 'project'

    EVALUATION_TYPE_CHOICES = [
        (EVALUATION_TYPE_PRACTICAL, 'Nộp bài thu hoạch'),
        (EVALUATION_TYPE_QUIZ, 'Làm bài trắc nghiệm'),
        (EVALUATION_TYPE_PROJECT, 'Nộp bài dự án'),
    ]

    course_key = CourseKeyField(
        max_length=255,
        db_index=True,
        verbose_name=_("Course Key"),
        help_text=_("The course this evaluation belongs to")
    )

    # Reference to LocalProgram - we'll import it dynamically to avoid circular dependency
    # The actual field is program_id in the database (Django auto-creates this for ForeignKey)
    program_id = models.IntegerField(
        db_index=True,
        db_column='program_id',  # Explicitly set the column name
        verbose_name=_("Program ID"),
        help_text=_("The program this evaluation belongs to")
    )

    evaluation_type = models.CharField(
        max_length=20,
        choices=EVALUATION_TYPE_CHOICES,
        verbose_name=_("Evaluation Type")
    )

    # For practical/project assignments
    practical_question = models.TextField(
        blank=True,
        verbose_name=_("Practical Question"),
        help_text=_("The question/instructions for practical assignment submission")
    )

    # For quiz evaluations
    quiz_file = models.FileField(
        upload_to='course_evaluations/quizzes/',
        blank=True,
        validators=[FileExtensionValidator(['xlsx', 'xls'])],
        verbose_name=_("Quiz Excel File"),
        help_text=_("Excel file containing quiz questions and answers")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_final_evaluations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Final Evaluation")
        verbose_name_plural = _("Final Evaluations")
        unique_together = ['course_key', 'program_id', 'evaluation_type']
        db_table = 'contentstore_finalevaluation'  # Use existing CMS table

    def __str__(self):
        return f"{self.course_key} - {self.get_evaluation_type_display()}"


class LearnerSubmission(models.Model):
    """
    Model to store learner submissions for practical/project assignments.
    """
    evaluation = models.ForeignKey(
        FinalEvaluation,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='final_evaluation_submissions'
    )

    submission_file = models.FileField(
        upload_to='course_evaluations/submissions/',
        validators=[FileExtensionValidator(['docx', 'pptx', 'pdf'])],
        verbose_name=_("Submission File")
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    # Grading fields
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Grade")
    )

    feedback = models.TextField(
        blank=True,
        verbose_name=_("Teacher Feedback")
    )

    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_final_submissions'
    )

    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Learner Submission")
        verbose_name_plural = _("Learner Submissions")
        unique_together = ['evaluation', 'learner']
        db_table = 'contentstore_learnersubmission'  # Use existing CMS table

    def __str__(self):
        return f"{self.learner.username} - {self.evaluation.course_key}"


class ChalixQuiz(models.Model):
    """
    Model for quiz/assessment created in course authoring interface.
    Quizzes are attached to course sections/subsections.
    """
    course_key = CourseKeyField(
        max_length=255,
        help_text="Course key where this quiz belongs"
    )

    parent_locator = models.CharField(
        max_length=255,
        help_text="Locator string of the parent block (section/subsection) where quiz is attached"
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Quiz Title")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Quiz Description"),
        help_text=_("Optional description for the quiz")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this quiz is active (soft delete flag)")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_chalix_quizzes',
        verbose_name=_("Created By")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Chalix Quiz")
        verbose_name_plural = _("Chalix Quizzes")
        ordering = ['-created_at']
        db_table = 'contentstore_chalixquiz'  # Use existing CMS table

    def __str__(self):
        return f"{self.title} ({self.course_key})"

    @property
    def question_count(self):
        """Get the number of questions in this quiz"""
        return self.questions.filter(is_active=True).count()


class ChalixQuizQuestion(models.Model):
    """
    Individual question within a quiz.
    """
    QUESTION_TYPE_CHOICES = [
        ('single_choice', _('Single Choice')),
        ('multiple_choice', _('Multiple Choice')),
    ]

    quiz = models.ForeignKey(
        ChalixQuiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Quiz")
    )

    question_text = models.TextField(
        verbose_name=_("Question Text"),
        help_text=_("The question text displayed to students")
    )

    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='single_choice',
        verbose_name=_("Question Type"),
        help_text=_("Whether this is a single choice or multiple choice question")
    )

    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order Index"),
        help_text=_("Order of this question within the quiz")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this question is active (soft delete flag)")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Quiz Question")
        verbose_name_plural = _("Quiz Questions")
        ordering = ['quiz', 'order_index']
        db_table = 'contentstore_chalixquizquestion'  # Use existing CMS table

    def __str__(self):
        return f"Q{self.order_index + 1}: {self.question_text[:50]}..."

    @property
    def choice_count(self):
        """Get the number of choices for this question"""
        return self.choices.filter(is_active=True).count()

    @property
    def correct_choices(self):
        """Get all correct choices for this question"""
        return self.choices.filter(is_correct=True, is_active=True)


class ChalixQuizChoice(models.Model):
    """
    Individual choice/option for a quiz question.
    """
    question = models.ForeignKey(
        ChalixQuizQuestion,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name=_("Question")
    )

    choice_text = models.TextField(
        verbose_name=_("Choice Text"),
        help_text=_("The text of this choice option")
    )

    is_correct = models.BooleanField(
        default=False,
        verbose_name=_("Is Correct"),
        help_text=_("Whether this choice is a correct answer")
    )

    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order Index"),
        help_text=_("Order of this choice within the question")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this choice is active (soft delete flag)")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Quiz Choice")
        verbose_name_plural = _("Quiz Choices")
        ordering = ['question', 'order_index']
        db_table = 'contentstore_chalixquizchoice'  # Use existing CMS table

    def __str__(self):
        correct_mark = "✓" if self.is_correct else "✗"
        return f"{correct_mark} {self.choice_text[:30]}..."


class QuizAttempt(models.Model):
    """
    Model to store learner quiz attempts.
    """
    evaluation = models.ForeignKey(
        FinalEvaluation,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='final_quiz_attempts'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Score")
    )

    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)

    is_completed = models.BooleanField(default=False)

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")
        unique_together = ['evaluation', 'learner']
        db_table = 'contentstore_quizattempt'  # Use existing CMS table

    def __str__(self):
        return f"{self.learner.username} - {self.evaluation.course_key} - {self.score or 'In Progress'}"


class QuizAnswer(models.Model):
    """
    Model to store individual answers in a quiz attempt.
    """
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        ChalixQuizQuestion,
        on_delete=models.CASCADE
    )

    selected_choice = models.ForeignKey(
        ChalixQuizChoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'final_evaluation'
        verbose_name = _("Quiz Answer")
        verbose_name_plural = _("Quiz Answers")
        unique_together = ['attempt', 'question']
        db_table = 'contentstore_quizanswer'  # Use existing CMS table

    def __str__(self):
        return f"{self.attempt.learner.username} - Q{self.question.id} - {'✓' if self.is_correct else '✗'}"


# Always mark models as available since they're defined here
MODELS_AVAILABLE = True


def check_models_available():
    """Helper to check if models are available (always true in this module)"""
    return None


# Export all models
__all__ = [
    'FinalEvaluation',
    'LearnerSubmission',
    'QuizAttempt',
    'QuizAnswer',
    'ChalixQuiz',
    'ChalixQuizQuestion',
    'ChalixQuizChoice',
]
