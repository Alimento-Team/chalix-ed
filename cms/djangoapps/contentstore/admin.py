"""
Admin site bindings for contentstore
"""

import logging

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.utils.translation import gettext as _
from edx_django_utils.admin.mixins import ReadOnlyAdminMixin

from cms.djangoapps.contentstore.models import (
    BackfillCourseTabsConfig,
    ChalixOrganization,
    ChalixUserRole,
    CleanStaleCertificateAvailabilityDatesConfig,
    ComponentLink,
    ContainerLink,
    CourseType,
    LearningContextLinksStatus,
    VideoUploadConfig,
)
from cms.djangoapps.contentstore.outlines_regenerate import CourseOutlineRegenerate
from openedx.core.djangoapps.content.learning_sequences.api import key_supports_outlines

from .tasks import update_all_outlines_from_modulestore_task, update_outline_from_modulestore_task

log = logging.getLogger(__name__)


def regenerate_course_outlines_subset(modeladmin, request, queryset):
    """
    Create a celery task to regenerate a single course outline for each passed-in course key.

    If the number of passed-in course keys is above a threshold, then instead create a celery task which
    will then create a celery task to regenerate a single course outline for each passed-in course key.
    """
    all_course_keys_qs = queryset.values_list('id', flat=True)

    # Create a separate celery task for each course outline requested.
    regenerates = 0
    for course_key in all_course_keys_qs:
        if key_supports_outlines(course_key):
            log.info("Queuing outline creation for %s", course_key)
            update_outline_from_modulestore_task.delay(str(course_key))
            regenerates += 1
        else:
            log.info("Outlines not supported for %s - skipping", course_key)
    msg = _("Number of course outline regenerations successfully requested: {regenerates}").format(
        regenerates=regenerates
    )
    modeladmin.message_user(request, msg)


regenerate_course_outlines_subset.short_description = _("Regenerate selected course outlines")


def regenerate_course_outlines_all(modeladmin, request, queryset):  # pylint: disable=unused-argument
    """
    Custom admin action which regenerates *all* the course outlines - no matter which CourseOverviews are selected.
    """
    update_all_outlines_from_modulestore_task.delay()
    modeladmin.message_user(request, _("All course outline regenerations successfully requested."))


regenerate_course_outlines_all.short_description = _("Regenerate *all* course outlines")


class CourseOutlineRegenerateAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """
    Regenerates the course outline for each selected course key.
    """
    list_display = ['id']
    ordering = ['id']
    search_fields = ['id']

    actions = [regenerate_course_outlines_subset, regenerate_course_outlines_all]

    def changelist_view(self, request, extra_context=None):
        """
        Overrides the admin's changelist_view & selects at least one of the CourseOverviews
        when the custom regenerate_course_outlines_all action is selected.
        """
        if 'action' in request.POST and request.POST['action'] == 'regenerate_course_outlines_all':
            # Slight hack: Ensure that at least one CourseOverview course key is selected.
            # The selection will be ignored, but the action will fail if *nothing* is selected.
            post = request.POST.copy()
            post.setlist(ACTION_CHECKBOX_NAME, self.model.get_course_outline_ids()[:1])
            request._set_post(post)  # pylint: disable=protected-access
        return super().changelist_view(request, extra_context)


class CleanStaleCertificateAvailabilityDatesConfigAdmin(ConfigurationModelAdmin):
    pass


@admin.register(ComponentLink)
class ComponentLinkAdmin(admin.ModelAdmin):
    """
    ComponentLink admin.
    """
    fields = (
        "uuid",
        "upstream_block",
        "upstream_usage_key",
        "upstream_context_key",
        "downstream_usage_key",
        "downstream_context_key",
        "version_synced",
        "version_declined",
        "created",
        "updated",
    )
    readonly_fields = fields
    list_display = [
        "upstream_block",
        "upstream_usage_key",
        "downstream_usage_key",
        "version_synced",
        "updated",
    ]
    search_fields = [
        "upstream_usage_key",
        "upstream_context_key",
        "downstream_usage_key",
        "downstream_context_key",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContainerLink)
class ContainerLinkAdmin(admin.ModelAdmin):
    """
    ContainerLink admin.
    """
    fields = (
        "uuid",
        "upstream_container",
        "upstream_container_key",
        "upstream_context_key",
        "downstream_usage_key",
        "downstream_context_key",
        "version_synced",
        "version_declined",
        "created",
        "updated",
    )
    readonly_fields = fields
    list_display = [
        "upstream_container",
        "upstream_container_key",
        "downstream_usage_key",
        "version_synced",
        "updated",
    ]
    search_fields = [
        "upstream_container_key",
        "upstream_context_key",
        "downstream_usage_key",
        "downstream_context_key",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LearningContextLinksStatus)
class LearningContextLinksStatusAdmin(admin.ModelAdmin):
    """
    LearningContextLinksStatus admin.
    """
    fields = (
        "context_key",
        "status",
        "created",
        "updated",
    )
    readonly_fields = ("created", "updated")
    list_display = (
        "context_key",
        "status",
        "created",
        "updated",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for CourseType model
    """
    list_display = ('name', 'is_active', 'sort_order', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', 'name')

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'is_active')
        }),
        (_('Display Options'), {
            'fields': ('sort_order',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """
        Only allow deletion if the course type is not being used by any courses.
        This can be extended later to check for actual course usage.
        """
        return True  # For now, allow deletion


@admin.register(ChalixOrganization)
class ChalixOrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for ChalixOrganization model
    """
    list_display = ('display_name', 'name', 'code', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'display_name', 'code', 'description')
    list_editable = ('is_active',)
    ordering = ('display_name',)

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'display_name', 'code', 'description')
        }),
        (_('Hierarchy'), {
            'fields': ('parent',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('parent')


from django import forms
from cms.djangoapps.contentstore.chalix_roles import enforce_single_bo_account, get_role_constraints


class ChalixUserRoleForm(forms.ModelForm):
    """Custom form for ChalixUserRole with validation"""

    class Meta:
        model = ChalixUserRole
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for role constraints
        role_constraints = get_role_constraints()
        role_choices = []
        for role, label in ChalixUserRole.ROLE_CHOICES:
            constraint = role_constraints.get(role, {})
            max_accounts = constraint.get('max_accounts', 'Unlimited')
            description = constraint.get('description', '')
            help_text = f"{label} - {description} (Max accounts: {max_accounts if max_accounts else 'Unlimited'})"
            role_choices.append((role, help_text))

        self.fields['role'].help_text = "Select the role type. Note: Only one 'bo' (Department) account is allowed."
    
    def clean_user(self):
        """Validate user field"""
        user = self.cleaned_data.get('user')
        if not user:
            raise forms.ValidationError("User is required.")
        return user

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        role = cleaned_data.get('role')
        organization = cleaned_data.get('organization')

        # Only validate if we have both user and role
        if not user or not role:
            return cleaned_data

        # Check bo constraint only for new instances or role changes
        if role == 'bo':
            if not self.instance.pk or (self.instance.pk and self.instance.role != 'bo'):
                try:
                    enforce_single_bo_account(user, role, organization, exclude_instance=self.instance)
                except PermissionDenied as e:
                    raise forms.ValidationError(str(e))

        return cleaned_data


@admin.register(ChalixUserRole)
class ChalixUserRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for ChalixUserRole model with role constraints
    """
    form = ChalixUserRoleForm
    list_display = ('user', 'get_role_display', 'organization', 'is_active', 'created_at', 'created_by')
    list_filter = ('role', 'is_active', 'organization', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'organization__display_name')
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    # Use raw_id_fields for created_by (admin user), but keep user as regular select for easier assignment
    raw_id_fields = ('created_by',)
    autocomplete_fields = ('organization',)

    fieldsets = (
        (_('User Information'), {
            'fields': ('user', 'role'),
            'description': 'Assign roles with the following constraints:<br>'
            '• <strong>bo (Department)</strong>: Only ONE account allowed<br>'
            '• <strong>co_quan (Organization)</strong>: Multiple accounts allowed<br>'
            '• <strong>giang_vien (Instructor)</strong>: Multiple accounts allowed<br>'
            '• <strong>cong_chuc (Learner)</strong>: Multiple accounts allowed'
        }),
        (_('Organization'), {
            'fields': ('organization',)
        }),
        (_('Status & Audit'), {
            'fields': ('is_active', 'created_by')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'user', 'organization', 'created_by'
        ).prefetch_related('user__profile')

    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set and apply constraints"""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        """Allow deletion but preserve audit trail by deactivating"""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Make created_by readonly after creation"""
        if obj:  # Editing existing object
            return ('created_by', 'created_at', 'updated_at')
        return ('created_at', 'updated_at')

    def changelist_view(self, request, extra_context=None):
        """Add role statistics to changelist"""
        extra_context = extra_context or {}

        # Get role statistics
        role_stats = {}
        constraints = get_role_constraints()
        for role, label in ChalixUserRole.ROLE_CHOICES:
            active_count = ChalixUserRole.objects.filter(role=role, is_active=True).count()
            max_allowed = constraints.get(role, {}).get('max_accounts', 'Unlimited')
            role_stats[role] = {
                'label': label,
                'active_count': active_count,
                'max_allowed': max_allowed,
                'at_limit': max_allowed == 1 and active_count >= 1 if max_allowed else False
            }

        extra_context['role_statistics'] = role_stats
        return super().changelist_view(request, extra_context)


# Custom User admin integration (optional - extends Django's user admin)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class ChalixUserRoleInline(admin.TabularInline):
    """Inline admin for user roles"""
    model = ChalixUserRole
    extra = 0
    fields = ('role', 'organization', 'is_active')
    autocomplete_fields = ('organization',)


class ChalixUserAdmin(BaseUserAdmin):
    """Extended User admin with Chalix roles"""
    inlines = list(BaseUserAdmin.inlines) + [ChalixUserRoleInline]

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).prefetch_related('chalix_roles__organization')


# Replace the default User admin
admin.site.unregister(User)
admin.site.register(User, ChalixUserAdmin)


admin.site.register(BackfillCourseTabsConfig, ConfigurationModelAdmin)
# Organization is now an alias to ChalixOrganization, which is already registered above
admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)


# ─── Survey authoring admin ───────────────────────────────────────────────────
from .models import ChalixSurveyForm, ChalixSurveyChoice  # noqa: E402


class SurveyChoiceInline(admin.TabularInline):
    model = ChalixSurveyChoice
    extra = 0
    fields = ('name', 'order_index', 'is_active')
    ordering = ('order_index',)


@admin.register(ChalixSurveyForm)
class ChalixSurveyFormAdmin(admin.ModelAdmin):
    list_display = ['course_key', 'title', 'is_active', 'created_by', 'created_at', 'public_token']
    list_filter = ['is_active']
    search_fields = ['course_key', 'title', 'public_token']
    readonly_fields = ['public_token', 'created_at', 'updated_at']
    inlines = [SurveyChoiceInline]


admin.site.register(CourseOutlineRegenerate, CourseOutlineRegenerateAdmin)
admin.site.register(CleanStaleCertificateAvailabilityDatesConfig, ConfigurationModelAdmin)
