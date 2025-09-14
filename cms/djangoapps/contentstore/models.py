"""
Models for contentstore
"""


from datetime import datetime, timezone

from config_models.models import ConfigurationModel
from django.conf import settings
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
    icon = models.CharField(max_length=100, blank=True, default='seed-of-life')  # Icon identifier
    update_topics = models.BooleanField(default=False, help_text="Whether to automatically update topics")
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
        return self.role == 'co_quan'

    @property
    def available_tabs(self):
        """Get list of available tabs for this role"""
        if self.role == 'bo':
            return ['statistics', 'management']
        elif self.role == 'co_quan':
            return ['statistics', 'create-account', 'management', 'learning-management', 'approve-requests']
        elif self.role == 'giang_vien':
            return ['statistics', 'learning-management']
        else:  # cong_chuc
            return []
