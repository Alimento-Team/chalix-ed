"""
Models for Chalix User Menu functionality
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from opaque_keys.edx.django.models import CourseKeyField


class UserLearningPlan(models.Model):
    """
    Model for storing user's personal learning plans
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_plans')
    title = models.CharField(max_length=255, verbose_name=_("Tiêu đề kế hoạch"))
    description = models.TextField(blank=True, verbose_name=_("Mô tả"))
    target_hours = models.PositiveIntegerField(verbose_name=_("Số giờ mục tiêu"))
    completed_hours = models.PositiveIntegerField(default=0, verbose_name=_("Số giờ đã hoàn thành"))
    start_date = models.DateField(verbose_name=_("Ngày bắt đầu"))
    end_date = models.DateField(verbose_name=_("Ngày kết thúc"))
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', _('Bản nháp')),
            ('active', _('Đang thực hiện')),
            ('completed', _('Hoàn thành')),
            ('cancelled', _('Đã hủy')),
        ],
        default='draft',
        verbose_name=_("Trạng thái")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Kế hoạch học tập")
        verbose_name_plural = _("Kế hoạch học tập")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def progress_percentage(self):
        """Calculate the completion percentage"""
        if self.target_hours == 0:
            return 0
        return min(100, (self.completed_hours / self.target_hours) * 100)


class TeachingRequest(models.Model):
    """
    Model for storing teaching registration requests
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_requests')
    course_title = models.CharField(max_length=255, verbose_name=_("Tiêu đề khóa học"))
    course_description = models.TextField(verbose_name=_("Mô tả khóa học"))
    teaching_experience = models.TextField(verbose_name=_("Kinh nghiệm giảng dạy"))
    qualifications = models.TextField(verbose_name=_("Trình độ chuyên môn"))
    proposed_duration = models.PositiveIntegerField(verbose_name=_("Thời lượng dự kiến (giờ)"))
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Chờ phê duyệt')),
            ('approved', _('Đã phê duyệt')),
            ('rejected', _('Từ chối')),
            ('in_review', _('Đang xem xét')),
        ],
        default='pending',
        verbose_name=_("Trạng thái")
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chalix_reviewed_teaching_requests'
    )
    review_notes = models.TextField(blank=True, verbose_name=_("Ghi chú phê duyệt"))

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Đăng ký giảng dạy")
        verbose_name_plural = _("Đăng ký giảng dạy")
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.course_title}"


class UserRequest(models.Model):
    """
    Model for general user requests
    """
    REQUEST_TYPES = [
        ('course_access', _('Yêu cầu truy cập khóa học')),
        ('certificate', _('Yêu cầu chứng chỉ')),
        ('grade_review', _('Xem xét điểm số')),
        ('technical_support', _('Hỗ trợ kỹ thuật')),
        ('account_issue', _('Vấn đề tài khoản')),
        ('other', _('Khác')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name=_("Loại yêu cầu"))
    title = models.CharField(max_length=255, verbose_name=_("Tiêu đề"))
    description = models.TextField(verbose_name=_("Mô tả chi tiết"))
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', _('Mở')),
            ('in_progress', _('Đang xử lý')),
            ('resolved', _('Đã giải quyết')),
            ('closed', _('Đã đóng')),
        ],
        default='open',
        verbose_name=_("Trạng thái")
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', _('Thấp')),
            ('medium', _('Trung bình')),
            ('high', _('Cao')),
            ('urgent', _('Khẩn cấp')),
        ],
        default='medium',
        verbose_name=_("Độ ưu tiên")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chalix_assigned_requests'
    )
    resolution_notes = models.TextField(blank=True, verbose_name=_("Ghi chú giải quyết"))

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Yêu cầu của người dùng")
        verbose_name_plural = _("Yêu cầu của người dùng")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserPersonalization(models.Model):
    """
    Model for storing user personalization preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personalization')
    learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', _('Thị giác')),
            ('auditory', _('Thính giác')),
            ('kinesthetic', _('Vận động')),
            ('reading', _('Đọc/Viết')),
        ],
        blank=True,
        verbose_name=_("Phong cách học tập")
    )
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('vi', _('Tiếng Việt')),
            ('en', _('English')),
        ],
        default='vi',
        verbose_name=_("Ngôn ngữ ưa thích")
    )
    notification_preferences = models.JSONField(
        default=dict,
        verbose_name=_("Tùy chọn thông báo")
    )
    accessibility_preferences = models.JSONField(
        default=dict,
        verbose_name=_("Tùy chọn trợ năng")
    )
    theme_preference = models.CharField(
        max_length=20,
        choices=[
            ('light', _('Sáng')),
            ('dark', _('Tối')),
            ('auto', _('Tự động')),
        ],
        default='light',
        verbose_name=_("Chủ đề giao diện")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Cá nhân hóa")
        verbose_name_plural = _("Cá nhân hóa")

    def __str__(self):
        return f"{self.user.username} - Personalization"


class NotificationType(models.Model):
    """
    Model for defining different types of notifications
    """
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Tên loại"))
    display_name = models.CharField(max_length=100, verbose_name=_("Tên hiển thị"))
    description = models.TextField(blank=True, verbose_name=_("Mô tả"))
    is_active = models.BooleanField(default=True, verbose_name=_("Kích hoạt"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Loại thông báo")
        verbose_name_plural = _("Loại thông báo")
        ordering = ['display_name']

    def __str__(self):
        return self.display_name


class Notification(models.Model):
    """
    Model for storing user notifications
    """
    PRIORITY_CHOICES = [
        ('low', _('Thấp')),
        ('medium', _('Trung bình')),
        ('high', _('Cao')),
        ('urgent', _('Khẩn cấp')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chalix_notifications')
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        verbose_name=_("Loại thông báo")
    )
    title = models.CharField(max_length=255, verbose_name=_("Tiêu đề"))
    message = models.TextField(verbose_name=_("Nội dung"))
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_("Độ ưu tiên")
    )
    is_read = models.BooleanField(default=False, verbose_name=_("Đã đọc"))
    is_archived = models.BooleanField(default=False, verbose_name=_("Đã lưu trữ"))
    action_url = models.URLField(blank=True, verbose_name=_("Liên kết hành động"))
    action_text = models.CharField(max_length=100, blank=True, verbose_name=_("Văn bản hành động"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Hết hạn vào"))
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Thời gian đọc"))

    # Additional metadata for rich notifications
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Dữ liệu bổ sung"))

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Thông báo")
        verbose_name_plural = _("Thông báo")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def time_since_created(self):
        """Get human-readable time since creation"""
        now = timezone.now()
        time_diff = now - self.created_at

        if time_diff.days > 0:
            if time_diff.days == 1:
                return _("1 ngày trước")
            elif time_diff.days <= 7:
                return _(f"{time_diff.days} ngày trước")
            else:
                return self.created_at.strftime("%d/%m/%Y")
        else:
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds // 60) % 60

            if hours > 0:
                if hours == 1:
                    return _("1 giờ trước")
                else:
                    return _(f"{hours} giờ trước")
            elif minutes > 0:
                if minutes == 1:
                    return _("1 phút trước")
                else:
                    return _(f"{minutes} phút trước")
            else:
                return _("Vừa xong")

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """
    Model for user notification preferences
    """
    DELIVERY_METHODS = [
        ('web', _('Web')),
        ('email', _('Email')),
        ('push', _('Push notification')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chalix_notification_preferences')
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, verbose_name=_("Phương thức"))
    is_enabled = models.BooleanField(default=True, verbose_name=_("Kích hoạt"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Tùy chọn thông báo")
        verbose_name_plural = _("Tùy chọn thông báo")
        unique_together = ['user', 'notification_type', 'delivery_method']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type.display_name} - {self.get_delivery_method_display()}"


class ChalixDemandSurveyResponse(models.Model):
    """
    Records a student's submission to a demand survey.
    One response per user per survey is enforced via unique_together.
    """

    survey_id = models.IntegerField(
        db_index=True,
        verbose_name=_("Survey ID"),
        help_text=_("PK of the survey model in the contentstore app."),
    )

    respondent_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demand_survey_responses',
        verbose_name=_("Respondent"),
    )

    full_name = models.CharField(max_length=500, verbose_name=_("Họ và tên"))
    email = models.EmailField(verbose_name=_("Email"))
    phone_number = models.CharField(max_length=50, blank=True, verbose_name=_("Điện thoại"))
    other_text = models.CharField(max_length=500, blank=True, verbose_name=_("Khác"))
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Submitted At"))

    class Meta:
        app_label = 'chalix_user_menu'
        verbose_name = _("Demand Survey Response")
        verbose_name_plural = _("Demand Survey Responses")
        unique_together = [['survey_id', 'respondent_user']]
        indexes = [
            models.Index(fields=['survey_id', 'submitted_at']),
        ]

    def __str__(self):
        return f"Response survey={self.survey_id} user={self.respondent_user_id}"


class ChalixDemandSurveyResponseChoice(models.Model):
    """
    Through table mapping each response row to selected survey choice IDs.
    """

    response = models.ForeignKey(
        ChalixDemandSurveyResponse,
        on_delete=models.CASCADE,
        related_name='selected_choices',
    )
    choice_id = models.IntegerField(db_index=True, verbose_name=_("Choice ID"))

    class Meta:
        app_label = 'chalix_user_menu'
        unique_together = [['response', 'choice_id']]


# --- Shadow models for CMS survey data (Shared DB) ---

class ChalixSurveyForm(models.Model):
    """
    Shadow model for ChalixSurveyForm in contentstore (CMS).
    Managed by CMS; LMS has read-only/vote-increment access via shared DB.
    """
    course_key = CourseKeyField(max_length=255, null=True, blank=True, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    public_token = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    allow_multiple_votes = models.BooleanField(default=False)
    allow_add_choice = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='published')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'contentstore_chalixsurveyform'

    def __str__(self):
        return f"Survey (Shadow) {self.public_token}"


class ChalixSurveyChoice(models.Model):
    """
    Shadow model for ChalixSurveyChoice in contentstore (CMS).
    """
    survey = models.ForeignKey(ChalixSurveyForm, on_delete=models.DO_NOTHING, related_name="choices")
    name = models.CharField(max_length=500)
    detail_html = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)
    group_name = models.CharField(max_length=300, blank=True, default='')
    group_order = models.PositiveIntegerField(default=0)
    vote_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'contentstore_chalixsurveychoice'
        ordering = ["group_order", "order_index"]
