

import uuid
from datetime import datetime, timezone

from config_models.models import ConfigurationModel
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Count, F, Q, QuerySet, Max
from django.db.models.fields import IntegerField, TextField
from django.db.models.functions import Coalesce
from django.db.models.lookups import GreaterThan
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField, ContainerKeyField, UsageKeyField
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryContainerLocator
from openedx_learning.api.authoring import get_published_version
from openedx_learning.api.authoring_models import Component, Container
from openedx_learning.lib.fields import (
    immutable_uuid_field,
    key_field,
    manual_date_time_field,
)


class CourseType(models.Model):
    """
    Model for managing different types of courses that can be selected
    during course creation.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Course Type Name"),
        help_text=_("The display name for this course type")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of this course type")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this course type is available for selection")
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort Order"),
        help_text=_("Order in which this type appears in the dropdown (lower numbers first)")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Course Type")
        verbose_name_plural = _("Course Types")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name





class VideoUploadConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    .. no_pii:
    """
    profile_whitelist = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include in video encoding downloads."
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]


class BackfillCourseTabsConfig(ConfigurationModel):
    """
    Manages configuration for a run of the backfill_course_tabs management command.

    .. no_pii:
    """

    class Meta:
        verbose_name = 'Arguments for backfill_course_tabs'
        verbose_name_plural = 'Arguments for backfill_course_tabs'

    start_index = IntegerField(
        help_text='Index of first course to start backfilling (in an alphabetically sorted list of courses)',
        default=0,
    )
    count = IntegerField(
        help_text='How many courses to backfill in this run (or zero for all courses)',
        default=0,
    )


class CleanStaleCertificateAvailabilityDatesConfig(ConfigurationModel):
    """
    Manages configuration for a run of the `clean_stale_certificate_availability_dates` management command.

    .. no_pii:
    """
    class Meta:
        app_label = "contentstore"
        verbose_name = "Arguments for 'clean_stale_certificate_availability_dates'"
        verbose_name_plural = "Arguments for 'clean_stale_certificate_availability_dates'"

    arguments = TextField(
        blank=True,
        help_text=(
            "A space seperated collection of arguments to be used when running the "
            "`clean_stale_certificate_available_dates` management command.' See the management command for options."
        )
    )


class EntityLinkBase(models.Model):
    """
    Abstract base class that defines fields and functions for storing link between two publishable entities
    or links between publishable entity and a course xblock.
    """
    uuid = immutable_uuid_field()
    # Search by library/upstream context key
    upstream_context_key = key_field(
        help_text=_("Upstream context key i.e., learning_package/library key"),
        db_index=True,
    )
    # A downstream entity can only link to single upstream entity
    # whereas an entity can be upstream for multiple downstream entities.
    downstream_usage_key = UsageKeyField(max_length=255, unique=True)
    # Search by course/downstream key
    downstream_context_key = CourseKeyField(max_length=255, db_index=True)
    version_synced = models.IntegerField()
    version_declined = models.IntegerField(null=True, blank=True)
    created = manual_date_time_field()
    updated = manual_date_time_field()

    class Meta:
        abstract = True


class ComponentLink(EntityLinkBase):
    """
    This represents link between any two publishable entities or link between publishable entity and a course
    XBlock. It helps in tracking relationship between XBlocks imported from libraries and used in different courses.
    """
    upstream_block = models.ForeignKey(
        Component,
        on_delete=models.SET_NULL,
        related_name="links",
        null=True,
        blank=True,
    )
    upstream_usage_key = UsageKeyField(
        max_length=255,
        help_text=_(
            "Upstream block usage key, this value cannot be null"
            " and useful to track upstream library blocks that do not exist yet"
        )
    )

    class Meta:
        verbose_name = _("Component Link")
        verbose_name_plural = _("Component Links")

    def __str__(self):
        return f"ComponentLink<{self.upstream_usage_key}->{self.downstream_usage_key}>"

    @property
    def upstream_version_num(self) -> int | None:
        """
        Returns upstream block version number if available.
        """
        published_version = get_published_version(self.upstream_block.publishable_entity.id)
        return published_version.version_num if published_version else None

    @property
    def upstream_context_title(self) -> str:
        """
        Returns upstream context title.
        """
        return self.upstream_block.publishable_entity.learning_package.title

    @classmethod
    def filter_links(
        cls,
        **link_filter,
    ) -> QuerySet["EntityLinkBase"]:
        """
        Get all links along with sync flag, upstream context title and version, with optional filtering.
        """
        ready_to_sync = link_filter.pop('ready_to_sync', None)
        result = cls.objects.filter(**link_filter).select_related(
            "upstream_block__publishable_entity__published__version",
            "upstream_block__publishable_entity__learning_package",
            "upstream_block__publishable_entity__published__publish_log_record__publish_log",
        ).annotate(
            ready_to_sync=(
                GreaterThan(
                    Coalesce("upstream_block__publishable_entity__published__version__version_num", 0),
                    Coalesce("version_synced", 0)
                ) & GreaterThan(
                    Coalesce("upstream_block__publishable_entity__published__version__version_num", 0),
                    Coalesce("version_declined", 0)
                )
            )
        )
        if ready_to_sync is not None:
            result = result.filter(ready_to_sync=ready_to_sync)
        return result

    @classmethod
    def summarize_by_downstream_context(cls, downstream_context_key: CourseKey) -> QuerySet:
        """
        Returns a summary of links by upstream context for given downstream_context_key.
        Example:
        [
            {
                "upstream_context_title": "CS problems 3",
                "upstream_context_key": "lib:OpenedX:CSPROB3",
                "ready_to_sync_count": 11,
                "total_count": 14,
                "last_published_at": "2025-05-02T20:20:44.989042Z"
            },
            {
                "upstream_context_title": "CS problems 2",
                "upstream_context_key": "lib:OpenedX:CSPROB2",
                "ready_to_sync_count": 15,
                "total_count": 24,
                "last_published_at": "2025-05-03T21:20:44.989042Z"
            },
        ]
        """
        result = cls.filter_links(downstream_context_key=downstream_context_key).values(
            "upstream_context_key",
            upstream_context_title=F("upstream_block__publishable_entity__learning_package__title"),
        ).annotate(
            ready_to_sync_count=Count("id", Q(ready_to_sync=True)),
            total_count=Count("id"),
            last_published_at=Max(
                "upstream_block__publishable_entity__published__publish_log_record__publish_log__published_at"
            )
        )
        return result

    @classmethod
    def update_or_create(
        cls,
        upstream_block: Component | None,
        /,
        upstream_usage_key: UsageKey,
        upstream_context_key: str,
        downstream_usage_key: UsageKey,
        downstream_context_key: CourseKey,
        version_synced: int,
        version_declined: int | None = None,
        created: datetime | None = None,
    ) -> "ComponentLink":
        """
        Update or create entity link. This will only update `updated` field if something has changed.
        """
        if not created:
            created = datetime.now(tz=timezone.utc)
        new_values = {
            'upstream_usage_key': upstream_usage_key,
            'upstream_context_key': upstream_context_key,
            'downstream_usage_key': downstream_usage_key,
            'downstream_context_key': downstream_context_key,
            'version_synced': version_synced,
            'version_declined': version_declined,
        }
        if upstream_block:
            new_values['upstream_block'] = upstream_block
        try:
            link = cls.objects.get(downstream_usage_key=downstream_usage_key)
            has_changes = False
            for key, new_value in new_values.items():
                prev_value = getattr(link, key)
                if prev_value != new_value:
                    has_changes = True
                    setattr(link, key, new_value)
            if has_changes:
                link.updated = created
                link.save()
        except cls.DoesNotExist:
            link = cls(**new_values)
            link.created = created
            link.updated = created
            link.save()
        return link


class ContainerLink(EntityLinkBase):
    """
    This represents link between any two publishable entities or link between publishable entity and a course
    xblock. It helps in tracking relationship between xblocks imported from libraries and used in different courses.
    """
    upstream_container = models.ForeignKey(
        Container,
        on_delete=models.SET_NULL,
        related_name="links",
        null=True,
        blank=True,
    )
    upstream_container_key = ContainerKeyField(
        max_length=255,
        help_text=_(
            "Upstream block key (e.g. lct:...), this value cannot be null "
            "and is useful to track upstream library blocks that do not exist yet "
            "or were deleted."
        )
    )

    class Meta:
        verbose_name = _("Container Link")
        verbose_name_plural = _("Container Links")

    def __str__(self):
        return f"ContainerLink<{self.upstream_container_key}->{self.downstream_usage_key}>"

    @property
    def upstream_version_num(self) -> int | None:
        """
        Returns upstream container version number if available.
        """
        published_version = get_published_version(self.upstream_container.publishable_entity.id)
        return published_version.version_num if published_version else None

    @property
    def upstream_context_title(self) -> str:
        """
        Returns upstream context title.
        """
        return self.upstream_container.publishable_entity.learning_package.title

    @classmethod
    def filter_links(
        cls,
        **link_filter,
    ) -> QuerySet["EntityLinkBase"]:
        """
        Get all links along with sync flag, upstream context title and version, with optional filtering.
        """
        ready_to_sync = link_filter.pop('ready_to_sync', None)
        result = cls.objects.filter(**link_filter).select_related(
            "upstream_container__publishable_entity__published__version",
            "upstream_container__publishable_entity__learning_package",
            "upstream_container__publishable_entity__published__publish_log_record__publish_log",
        ).annotate(
            ready_to_sync=(
                GreaterThan(
                    Coalesce("upstream_container__publishable_entity__published__version__version_num", 0),
                    Coalesce("version_synced", 0)
                ) & GreaterThan(
                    Coalesce("upstream_container__publishable_entity__published__version__version_num", 0),
                    Coalesce("version_declined", 0)
                )
            )
        )
        if ready_to_sync is not None:
            result = result.filter(ready_to_sync=ready_to_sync)
        return result

    @classmethod
    def summarize_by_downstream_context(cls, downstream_context_key: CourseKey) -> QuerySet:
        """
        Returns a summary of links by upstream context for given downstream_context_key.
        Example:
        [
            {
                "upstream_context_title": "CS problems 3",
                "upstream_context_key": "lib:OpenedX:CSPROB3",
                "ready_to_sync_count": 11,
                "total_count": 14,
                "last_published_at": "2025-05-02T20:20:44.989042Z"
            },
            {
                "upstream_context_title": "CS problems 2",
                "upstream_context_key": "lib:OpenedX:CSPROB2",
                "ready_to_sync_count": 15,
                "total_count": 24,
                "last_published_at": "2025-05-03T21:20:44.989042Z"
            },
        ]
        """
        result = cls.filter_links(downstream_context_key=downstream_context_key).values(
            "upstream_context_key",
            upstream_context_title=F("upstream_container__publishable_entity__learning_package__title"),
        ).annotate(
            ready_to_sync_count=Count("id", Q(ready_to_sync=True)),
            total_count=Count('id'),
            last_published_at=Max(
                "upstream_container__publishable_entity__published__publish_log_record__publish_log__published_at"
            )
        )
        return result

    @classmethod
    def update_or_create(
        cls,
        upstream_container_id: int | None,
        /,
        upstream_container_key: LibraryContainerLocator,
        upstream_context_key: str,
        downstream_usage_key: UsageKey,
        downstream_context_key: CourseKey,
        version_synced: int,
        version_declined: int | None = None,
        created: datetime | None = None,
    ) -> "ContainerLink":
        """
        Update or create entity link. This will only update `updated` field if something has changed.
        """
        if not created:
            created = datetime.now(tz=timezone.utc)
        new_values = {
            'upstream_container_key': upstream_container_key,
            'upstream_context_key': upstream_context_key,
            'downstream_usage_key': downstream_usage_key,
            'downstream_context_key': downstream_context_key,
            'version_synced': version_synced,
            'version_declined': version_declined,
        }
        if upstream_container_id:
            new_values['upstream_container_id'] = upstream_container_id
        try:
            link = cls.objects.get(downstream_usage_key=downstream_usage_key)
            has_changes = False
            for key, new_value in new_values.items():
                prev_value = getattr(link, key)
                if prev_value != new_value:
                    has_changes = True
                    setattr(link, key, new_value)
            if has_changes:
                link.updated = created
                link.save()
        except cls.DoesNotExist:
            link = cls(**new_values)
            link.created = created
            link.updated = created
            link.save()
        return link


class LearningContextLinksStatusChoices(models.TextChoices):
    """
    Enumerates the states that a LearningContextLinksStatus can be in.
    """
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    FAILED = "failed", _("Failed")
    COMPLETED = "completed", _("Completed")


class LearningContextLinksStatus(models.Model):
    """
    This table stores current processing status of upstream-downstream links in ComponentLink table for a
    course or a learning context.
    """
    context_key = CourseKeyField(
        max_length=255,
        # Single entry for a learning context or course
        unique=True,
        help_text=_("Linking status for course context key"),
    )
    status = models.CharField(
        max_length=20,
        choices=LearningContextLinksStatusChoices.choices,
        help_text=_("Status of links in given learning context/course."),
    )
    created = manual_date_time_field()
    updated = manual_date_time_field()

    class Meta:
        verbose_name = _("Learning Context Links status")
        verbose_name_plural = _("Learning Context Links status")

    def __str__(self):
        return f"{self.status}|{self.context_key}"

    @classmethod
    def get_or_create(cls, context_key: str, created: datetime | None = None) -> "LearningContextLinksStatus":
        """
        Get or create course link status row from LearningContextLinksStatus table for given course key.

        Args:
            context_key: Learning context or Course key

        Returns:
            LearningContextLinksStatus object
        """
        if not created:
            created = datetime.now(tz=timezone.utc)
        status, _ = cls.objects.get_or_create(
            context_key=context_key,
            defaults={
                'status': LearningContextLinksStatusChoices.PENDING,
                'created': created,
                'updated': created,
            },
        )
        return status

    def update_status(
        self,
        status: LearningContextLinksStatusChoices,
        updated: datetime | None = None
    ) -> None:
        """
        Updates entity links processing status of given learning context.
        """
        self.status = status
        self.updated = updated or datetime.now(tz=timezone.utc)
        self.save()


class LocalCourse(models.Model):
    """
    Lightweight model to store courses created from the Chalix dashboard (for prototyping).
    """
    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    template_program = models.ForeignKey(
        'contentstore.LocalProgram',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='template_courses',
        help_text="Program template used to create this course"
    )
    course_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of course (bat-buoc, tuy-chon, co-quan)"
    )
    # Persist the modulestore CourseKey string so we can link back to the course
    course_key = models.CharField(max_length=255, blank=True, null=True, help_text="Modulestore CourseKey string")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='local_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Local Course"
        verbose_name_plural = "Local Courses"

    def __str__(self):
        return self.title


class LocalProgram(models.Model):
    """
    Model to store learning programs created from the Chalix dashboard.
    Programs contain multiple topics/subjects and can have courses associated.
    """
    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True, help_text="Short description of the program")
    icon = models.CharField(max_length=100, blank=True, default='seed-of-life')  # Icon identifier
    update_topics = models.BooleanField(default=False, help_text="Whether to automatically update topics")

    # End-of-course evaluation format options
    allow_practical_submission = models.BooleanField(
        default=True,
        help_text="Allow learners to submit practical assignments as end-of-course evaluation"
    )
    allow_multiple_choice = models.BooleanField(
        default=False,
        help_text="Allow learners to take multiple choice tests as end-of-course evaluation"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='local_programs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Local Program"
        verbose_name_plural = "Local Programs"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProgramTopic(models.Model):
    """
    Topics/subjects within a learning program.
    """
    program = models.ForeignKey(
        LocalProgram,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Program Topic"
        verbose_name_plural = "Program Topics"
        ordering = ['program', 'order', 'title']
        unique_together = ['program', 'order']

    def __str__(self):
        return f"{self.program.title} - {self.title}"


class ChalixOrganization(models.Model):
    """
    Organization model for Chalix role system.
    Links users to organizations with proper hierarchy.
    """
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_organizations',
        help_text="Admin user responsible for this organization"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chalix Organization"
        verbose_name_plural = "Chalix Organizations"
        ordering = ['display_name']

    def __str__(self):
        return self.display_name


# Alias for backwards compatibility
Organization = ChalixOrganization


class ChalixUserRole(models.Model):
    """
    User role model for Chalix system.
    Defines 4 role types with proper permissions and organization association.
    """
    ROLE_CHOICES = [
        ('bo', 'Tài khoản Bộ'),  # Ministry level
        ('co_quan', 'Tài khoản Cơ quan'),  # Organization level
        ('giang_vien', 'Tài khoản Giảng viên'),  # Teacher level
        ('cong_chuc', 'Tài khoản Công chức/Viên chức'),  # Learner/Student level
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chalix_roles'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    organization = models.ForeignKey(
        ChalixOrganization,
        on_delete=models.CASCADE,
        related_name='user_roles',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_user_roles'
    )

    class Meta:
        verbose_name = "Chalix User Role"
        verbose_name_plural = "Chalix User Roles"
        unique_together = ['user', 'role', 'organization']

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} - {self.organization}"

    @property
    def can_access_cms(self):
        """Check if user role allows CMS access"""
        return self.role in ['bo', 'co_quan', 'giang_vien']

    @property
    def can_see_all_tabs(self):
        """Check if user can see all dashboard tabs"""
        return self.role == 'bo'  # Only department level can see all tabs

    @property
    def available_tabs(self):
        """Get list of available tabs for this role"""
        if self.role == 'bo':  # Department level - single account with full access
            return ['statistics', 'create-account', 'management', 'learning-management', 'approve-requests']
        elif self.role == 'co_quan':  # Organization level - multiple accounts with management access
            return ['statistics', 'management', 'learning-management']
        elif self.role == 'giang_vien':  # Teacher/Instructor level - multiple accounts with teaching access
            return ['statistics', 'learning-management']
        else:  # cong_chuc - Learner/Student level - no CMS access
            return []


class ChalixCourseMetadata(models.Model):
    """
    Chalix-specific course metadata for managing course visibility and access control.
    Tracks who created the course and applies visibility rules based on creator's role.
    """
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)
    
    # Creator information
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses',
        help_text=_("User who created this course")
    )
    creator_role = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=ChalixUserRole.ROLE_CHOICES,
        help_text=_("Role of the creator at the time of course creation")
    )
    creator_organization = models.ForeignKey(
        ChalixOrganization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text=_("Organization of the creator at the time of course creation")
    )
    
    # Visibility settings
    is_public = models.BooleanField(
        default=False,
        help_text=_("If True, all learners can see this course. If False, only learners from the same organization can see it.")
    )
    
    # Course flags
    is_mandatory_course = models.BooleanField(
        default=False,
        verbose_name=_("Khóa học bắt buộc"),
        help_text=_("Indicates whether this course is mandatory for learners")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chalix Course Metadata"
        verbose_name_plural = "Chalix Course Metadata"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course_id} - {'Public' if self.is_public else 'Organization Only'}"

    @property
    def visibility_description(self):
        """Human-readable description of course visibility"""
        if self.is_public:
            return "Công khai - Tất cả học viên có thể truy cập"
        elif self.creator_organization:
            return f"Riêng tư - Chỉ học viên thuộc {self.creator_organization.display_name}"
        else:
            return "Riêng tư - Không có tổ chức"


class UnitMediaFile(models.Model):
    """
    Model for storing media files (videos and slides) attached to specific course units.
    This replaces course-level media attachments with unit-level attachments for better UX.
    """

    # Media type choices
    MEDIA_TYPE_CHOICES = [
        ('video', _('Video')),
        ('slide', _('Slide')),
    ]

    # File extension validators
    VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'wmv', 'mkv']
    SLIDE_EXTENSIONS = ['pdf', 'docx']

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("Media File ID")
    )

    # Unit and course relationship
    unit_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("Unit ID"),
        help_text=_("The unique identifier of the course unit this media belongs to")
    )

    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        verbose_name=_("Course ID"),
        help_text=_("The course key this media belongs to")
    )

    # Media type and metadata
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        db_index=True,
        verbose_name=_("Media Type"),
        help_text=_("Type of media file (video or slide)")
    )

    file_name = models.CharField(
        max_length=255,
        verbose_name=_("File Name"),
        help_text=_("Original filename as uploaded by user")
    )

    display_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Display Name"),
        help_text=_("User-friendly name for the media file")
    )

    file_size = models.BigIntegerField(
        verbose_name=_("File Size"),
        help_text=_("Size of the file in bytes")
    )

    file_type = models.CharField(
        max_length=100,
        verbose_name=_("File Type"),
        help_text=_("MIME type of the file (e.g., video/mp4, application/pdf)")
    )

    # Storage information
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("File Path"),
        help_text=_("Relative path to the stored file (empty for external videos)")
    )

    upload_url = models.URLField(
        max_length=500,  # Increased from default 200 to handle longer URLs
        blank=True,
        null=True,
        verbose_name=_("Upload URL"),
        help_text=_("Public URL for accessing the uploaded file (empty for external videos)")
    )

    # External video URL fields (for YouTube, Google Drive, etc.)
    external_url = models.URLField(
        max_length=1000,  # Support longer URLs
        blank=True,
        null=True,
        verbose_name=_("External Video URL"),
        help_text=_("URL for external video sources like YouTube or Google Drive")
    )

    # Convenience fields for compatibility with the video model frontend
    # and for easier consumption by other parts of the system. For external
    # videos these will be set to the same value as `external_url`.
    public_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_("Public URL"),
        help_text=_("Publicly accessible URL for this media (for external videos this maps to external_url)")
    )

    url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_("URL"),
        help_text=_("Alternate URL field retained for compatibility with consumers that expect `url`")
    )

    video_source_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Video Source Type"),
        help_text=_("Type of video source: youtube, google_drive, upload, etc.")
    )

    client_video_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Client Video ID"),
        help_text=_("Unique identifier for the video on the client side")
    )

    upload_status = models.CharField(
        max_length=50,
        default='pending',
        verbose_name=_("Upload Status"),
        help_text=_("Status of the upload: pending, ready, failed, etc.")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_unit_media',
        verbose_name=_("Created By"),
        help_text=_("User who created this media record")
    )

    # User tracking
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_unit_media',
        verbose_name=_("Uploaded By"),
        help_text=_("User who uploaded this media file")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Unit Media File")
        verbose_name_plural = _("Unit Media Files")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['unit_id', 'media_type']),
            models.Index(fields=['course_id', 'media_type']),
            models.Index(fields=['media_type', 'created_at']),
        ]
        # Prevent duplicate filenames per unit/type combination
        unique_together = ['unit_id', 'file_name', 'media_type']

    def __str__(self):
        return f"{self.get_media_type_display()}: {self.display_name or self.file_name} ({self.unit_id})"

    @property
    def file_extension(self):
        """Get the file extension from the filename"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    @property
    def is_video(self):
        """Check if this is a video file"""
        return self.media_type == 'video'

    @property
    def is_slide(self):
        """Check if this is a slide file"""
        return self.media_type == 'slide'

    @property
    def formatted_file_size(self):
        """Return human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    def clean(self):
        """Validate the model before saving"""
        from django.core.exceptions import ValidationError

        # Skip validation for external videos (YouTube, Google Drive, etc.)
        if self.file_type == 'video/external':
            # External videos don't need file validation
            # Set display_name if not provided
            if not self.display_name:
                self.display_name = self.file_name
            return

        # Validate file extension based on media type
        extension = self.file_extension
        if self.media_type == 'video' and extension not in self.VIDEO_EXTENSIONS:
            raise ValidationError({
                'file_name': _(f'Video files must have one of these extensions: {", ".join(self.VIDEO_EXTENSIONS)}')
            })
        elif self.media_type == 'slide' and extension not in self.SLIDE_EXTENSIONS:
            raise ValidationError({
                'file_name': _(f'Slide files must have one of these extensions: {", ".join(self.SLIDE_EXTENSIONS)}')
            })

        # Set display_name to file_name if not provided
        if not self.display_name:
            self.display_name = self.file_name

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_unit_media(cls, unit_id, media_type=None):
        """Get all media files for a specific unit"""
        queryset = cls.objects.filter(unit_id=unit_id)
        if media_type:
            queryset = queryset.filter(media_type=media_type)
        return queryset.order_by('created_at')

    @classmethod
    def get_course_media(cls, course_id, media_type=None):
        """Get all media files for a specific course"""
        queryset = cls.objects.filter(course_id=course_id)
        if media_type:
            queryset = queryset.filter(media_type=media_type)
        return queryset.order_by('unit_id', 'created_at')


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
        related_name='created_quizzes',
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
        verbose_name = _("Chalix Quiz")
        verbose_name_plural = _("Chalix Quizzes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_key', 'is_active']),
            models.Index(fields=['parent_locator', 'is_active']),
            models.Index(fields=['created_at']),
        ]

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
        verbose_name = _("Quiz Question")
        verbose_name_plural = _("Quiz Questions")
        ordering = ['quiz', 'order_index']
        indexes = [
            models.Index(fields=['quiz', 'order_index']),
            models.Index(fields=['quiz', 'is_active']),
        ]

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
        verbose_name = _("Quiz Choice")
        verbose_name_plural = _("Quiz Choices")
        ordering = ['question', 'order_index']
        indexes = [
            models.Index(fields=['question', 'order_index']),
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        correct_mark = "✓" if self.is_correct else "✗"
        return f"{correct_mark} {self.choice_text[:30]}..."


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

    program = models.ForeignKey(
        LocalProgram,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_("Program")
    )

    evaluation_type = models.CharField(
        max_length=20,
        choices=EVALUATION_TYPE_CHOICES,
        verbose_name=_("Evaluation Type")
    )

    # For practical assignments
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

    # Quiz configuration fields
    quiz_time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Quiz Time Limit (minutes)"),
        help_text=_("Time limit for completing the quiz in minutes. Leave blank for no time limit.")
    )

    quiz_passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Passing Score (%)"),
        help_text=_("Minimum score percentage required to pass the quiz (0-100)")
    )

    QUIZ_ATTEMPTS_CHOICES = [
        (1, '1 lần'),
        (3, '3 lần'),
        (0, 'Không giới hạn'),
    ]

    quiz_max_attempts = models.PositiveIntegerField(
        choices=QUIZ_ATTEMPTS_CHOICES,
        default=0,
        verbose_name=_("Maximum Quiz Attempts"),
        help_text=_("Number of times a learner can attempt the quiz. 0 means unlimited.")
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
        related_name='created_evaluations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Final Evaluation")
        verbose_name_plural = _("Final Evaluations")
        unique_together = ['course_key', 'program', 'evaluation_type']

    def __str__(self):
        return f"{self.course_key} - {self.get_evaluation_type_display()}"


class LearnerSubmission(models.Model):
    """
    Model to store learner submissions for practical assignments.
    """
    evaluation = models.ForeignKey(
        FinalEvaluation,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluation_submissions'
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
        related_name='graded_submissions'
    )

    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Learner Submission")
        verbose_name_plural = _("Learner Submissions")
        unique_together = ['evaluation', 'learner']

    def __str__(self):
        return f"{self.learner.username} - {self.evaluation.course_key}"


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
        related_name='quiz_attempts'
    )

    attempt_number = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Attempt Number"),
        help_text=_("The sequential attempt number for this learner")
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
    passed = models.BooleanField(
        default=False,
        verbose_name=_("Passed"),
        help_text=_("Whether the learner passed based on the minimum score requirement")
    )

    class Meta:
        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")
        # Remove unique_together to allow multiple attempts
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.learner.username} - {self.evaluation.course_key} - Attempt {self.attempt_number} - {self.score or 'In Progress'}"


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
        verbose_name = _("Quiz Answer")
        verbose_name_plural = _("Quiz Answers")
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.learner.username} - Q{self.question.id} - {'✓' if self.is_correct else '✗'}"
