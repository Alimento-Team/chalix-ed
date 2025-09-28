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
    file_path = models.CharField(max_length=500)
    upload_url = models.CharField(max_length=500)
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
        qs = cls.objects.filter(unit_id=unit_id)
        if media_type:
            qs = qs.filter(media_type=media_type)
        return qs.order_by('created_at')


class ChalixQuizLMS(models.Model):
    """
    Unmanaged model mapping to CMS contentstore ChalixQuiz table so LMS can
    read quizzes created via authoring without depending on the CMS app being
    installed in this Django site.

    NOTE: Do not create migrations for this model.
    """
    
    id = models.AutoField(primary_key=True)
    course_key = models.CharField(max_length=255, db_index=True)
    parent_locator = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contentstore_chalixquiz'
        indexes = [
            models.Index(fields=['course_key', 'is_active']),
            models.Index(fields=['parent_locator', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.course_key})"


class ChalixQuizQuestionLMS(models.Model):
    """
    Unmanaged model mapping to CMS ChalixQuizQuestion
    """
    id = models.AutoField(primary_key=True)
    quiz_id = models.IntegerField(db_index=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20)
    order_index = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contentstore_chalixquizquestion'
        ordering = ['quiz_id', 'order_index']


class ChalixQuizChoiceLMS(models.Model):
    """
    Unmanaged model mapping to CMS ChalixQuizChoice
    """
    id = models.AutoField(primary_key=True)
    question_id = models.IntegerField(db_index=True)
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order_index = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contentstore_chalixquizchoice'
        ordering = ['question_id', 'order_index']
