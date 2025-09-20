"""
Views related to the slide upload feature
"""

import logging

from cms.djangoapps.contentstore.slide_storage_handlers import handle_slides
from common.djangoapps.util.json_request import expect_json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

__all__ = [
    'slides_handler',
]

LOGGER = logging.getLogger(__name__)

SLIDE_SUPPORTED_FILE_FORMATS = {
    '.pdf': 'application/pdf',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt': 'application/vnd.ms-powerpoint',
}

SLIDE_UPLOAD_MAX_FILE_SIZE_MB = 100


@expect_json
@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def slides_handler(request, course_key_string, slide_id=None):
    """
    The restful handler for slide uploads.

    GET
        html: return an HTML page to display previous slide uploads and allow
            new ones
        json: return json representing the slides that have been uploaded and
            their statuses
    POST
        json: create a new slide upload; the actual files should not be provided
            to this endpoint but rather PUT to the respective upload_url values
            contained in the response. Example payload:
                {
                    "files": [{
                        "file_name": "slides.pdf",
                        "content_type": "application/pdf"
                    }]
                }
    DELETE
        soft deletes a slide for particular course
    """
    return handle_slides(request, course_key_string, slide_id)