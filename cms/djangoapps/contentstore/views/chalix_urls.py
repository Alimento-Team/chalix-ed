"""
URL patterns for Chalix unit types.
"""

from django.urls import path, re_path
from . import chalix_unit_types

app_name = 'chalix'

urlpatterns = [
    # Get available content types
    path(
        'content-types/<str:course_id>',
        chalix_unit_types.get_chalix_content_types,
        name='chalix_content_types'
    ),

    # Create unit type (simplified endpoint)
    path(
        'unit_types/',
        chalix_unit_types.create_unit_type,
        name='chalix_unit_types'
    ),

    # Create new unit with content type
    path(
        'units/create/<str:course_id>',
        chalix_unit_types.create_chalix_unit,
        name='chalix_create_unit'
    ),

    # Update unit content
    re_path(
        r'^units/update/(?P<course_id>[^/]+)/(?P<unit_locator>.+)$',
        chalix_unit_types.update_chalix_unit_content,
        name='chalix_update_unit'
    ),

    # Update online class configuration
    re_path(
        r'^online-class/update/(?P<course_id>.+)$',
        chalix_unit_types.update_online_class_config,
        name='chalix_update_online_class'
    ),
]
