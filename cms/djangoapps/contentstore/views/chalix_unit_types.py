"""
Chalix Unit Types - Custom unit content types for the Chalix platform.

This module provides specialized unit content types:
1. Online Class: Zoom/Meet            import json
            data = json.loads(request.body.decode('utf-8'))

        content_data = data.get('content', {})live sessions
2. Unit Video: Recorded lesson videos
3. Slide: Presentation slides (PDF/PPTX)
4. Quiz: Interactive assessments
"""

import logging
import json
from uuid import uuid4
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from cms.djangoapps.contentstore.api import course_author_access_required
from cms.djangoapps.contentstore.helpers import xblock_studio_url
from cms.djangoapps.contentstore.xblock_storage_handlers.create_xblock import create_xblock
from cms.djangoapps.contentstore.utils import has_studio_write_access
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

# Constants for Chalix content types
CHALIX_CONTENT_TYPES = {
    'online_class': {
        'display_name': 'Online Class',
        'icon': 'fa-video-camera',
        'description': 'Live online class session with meeting link',
        'category': 'html',
        'template': 'chalix_online_class'
    },
    'unit_video': {
        'display_name': 'Unit Video',
        'icon': 'fa-film',
        'description': 'Recorded lesson video',
        'category': 'video',
        'template': 'chalix_unit_video'
    },
    'slide': {
        'display_name': 'Lesson Slides',
        'icon': 'fa-file-powerpoint-o',
        'description': 'Presentation slides (PDF/PPTX)',
        'category': 'html',
        'template': 'chalix_slides'
    },
    'quiz': {
        'display_name': 'Unit Quiz',
        'icon': 'fa-question-circle',
        'description': 'Interactive assessment quiz',
        'category': 'problem',
        'template': 'chalix_quiz'
    }
}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@course_author_access_required
def get_chalix_content_types(request, course_id):
    """
    Get available Chalix content types for unit creation.
    """
    return JsonResponse({
        'content_types': CHALIX_CONTENT_TYPES
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unit_type(request):
    """
    Create a new Chalix unit type with content block directly in an existing unit.

    Expected payload:
    {
        "unit_locator": "block-v1:...",
        "content_type": "online_class|unit_video|slide|quiz",
        "config": {
            // Content-specific configuration
        }
    }
    """
    try:
        # Handle both JSON and form data
        if hasattr(request, 'data'):
            data = request.data
        else:
            import json
            data = json.loads(request.body.decode('utf-8'))

        unit_locator = data.get('unit_locator')
        content_type = data.get('content_type')
        config = data.get('config', {})

        if not unit_locator:
            return JsonResponse({'error': 'unit_locator is required'}, status=400)

        if content_type not in CHALIX_CONTENT_TYPES:
            return JsonResponse({
                'error': f'Invalid content_type. Must be one of: {list(CHALIX_CONTENT_TYPES.keys())}'
            }, status=400)

        # Parse the unit locator to get the unit
        try:
            unit_key = BlockUsageLocator.from_string(unit_locator)
            store = modulestore()
            unit = store.get_item(unit_key)
        except Exception as e:
            log.error(f"Invalid unit_locator: {e}")
            return JsonResponse({'error': f'Invalid unit_locator: {e}'}, status=400)

        # Create content block in the existing unit
        content_block = create_chalix_content_block(unit, content_type, config, user)

        return JsonResponse({
            'unit_locator': str(unit.location),
            'content_locator': str(content_block.location) if content_block else None,
            'content_type': content_type,
            'status': 'success'
        })

    except Exception as e:
        log.exception(f"Error creating unit type: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@course_author_access_required
def create_chalix_unit(request, course_id):
    """
    Create a new unit with Chalix content types.

    Expected payload:
    {
        "parent_locator": "block-v1:...",
        "content_type": "online_class|unit_video|slide|quiz",
        "display_name": "Unit Title",
        "content_data": {
            // Content-specific data based on content_type
        }
    }
    """
    try:
        # Handle both JSON and form data
        if hasattr(request, 'data'):
            data = request.data
        else:
            import json
            data = json.loads(request.body.decode('utf-8'))

        parent_locator = data.get('parent_locator')
        content_type = data.get('content_type')
        display_name = data.get('display_name', 'New Unit')
        content_data = data.get('content_data', {})

        if not parent_locator:
            return JsonResponse({'error': 'parent_locator is required'}, status=400)

        if content_type not in CHALIX_CONTENT_TYPES:
            return JsonResponse({
                'error': f'Invalid content_type. Must be one of: {list(CHALIX_CONTENT_TYPES.keys())}'
            }, status=400)

        # Create the unit (vertical)
        unit = create_xblock(
            parent_locator=parent_locator,
            user=request.user,
            category='vertical',
            display_name=display_name
        )

        # Add content based on type
        content_block = _create_content_block(
            unit.location,
            content_type,
            content_data,
            request.user
        )

        return JsonResponse({
            'unit_locator': str(unit.location),
            'content_locator': str(content_block.location) if content_block else None,
            'content_type': content_type,
            'status': 'success'
        })

    except Exception as e:
        log.exception(f"Error creating Chalix unit: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def _create_content_block_in_unit(unit, content_type, config, user):
    """
    Create the appropriate content block in an existing unit.
    """
    if content_type == 'online_class':
        return _create_online_class_block(unit, config, user)
    elif content_type == 'unit_video':
        return _create_unit_video_block(unit, config, user)
    elif content_type == 'slide':
        return _create_slide_block(unit, config, user)
    elif content_type == 'quiz':
        return _create_quiz_block(unit, config, user)


def _create_content_block(unit_locator, content_type, content_data, user):
    """
    Create the appropriate content block for the specified content type.
    """
    store = modulestore()
    unit = store.get_item(unit_locator)

    content_config = CHALIX_CONTENT_TYPES[content_type]
    block_category = content_config['category']

    if content_type == 'online_class':
        return _create_online_class_block(unit, content_data, user)
    elif content_type == 'unit_video':
        return _create_unit_video_block(unit, content_data, user)
    elif content_type == 'slide':
        return _create_slide_block(unit, content_data, user)
    elif content_type == 'quiz':
        return _create_quiz_block(unit, content_data, user)


def create_online_class_block(unit, meeting_link, meeting_time=None, duration=None, user=None):
    """Create an online class content block"""
    store = modulestore()

    html_content = f"""


def _create_unit_video_block(unit, content_data, user):
    """Create a unit video content block."""
    content_block = create_xblock(
        parent_locator=str(unit.location),
        user=user,
        category='video',
        display_name=content_data.get('title', 'Unit Video')
    )

    # Update video metadata
    content_block.metadata.update({
        'chalix_content_type': 'unit_video',
        'youtube_id_1_0': content_data.get('youtube_id', ''),
        'video_url': content_data.get('video_url', ''),
        'download_video': content_data.get('download_video', False),
    })

    store = modulestore()
    store.update_item(content_block, user.id)

    return content_block


def _create_slide_block(unit, content_data, user):
    """Create a slide content block."""
    file_url = content_data.get('file_url', '')
    file_type = content_data.get('file_type', 'pdf')

    # Generate embed code based on file type
    if file_type.lower() == 'pdf':
        embed_html = f'<iframe src="{file_url}" width="100%" height="600px" frameborder="0"></iframe>'
    else:
        # For PPTX or other formats, use generic iframe
        embed_html = f'<iframe src="{file_url}" width="100%" height="600px" frameborder="0"></iframe>'

    html_content = f"""
    <div class = "chalix-slides" >
        <div class = "slides-header" >
            <i class = "fa fa-file-powerpoint-o" > </i >
            <h3 > Lesson Slides < /h3 >
        </div >
        <div class = "slides-content" >
            {embed_html if file_url else '<p class="no-slides">No slides available</p>'}
        </div >
    </div >

    <style >
    .chalix-slides {{
        border: 2px solid  # 28a745;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        background:  # f8f9fa;
    }}
    .slides-header {{
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }}
    .slides-header i {{
        font-size: 24px;
        color:  # 28a745;
        margin-right: 10px;
    }}
    .slides-header h3 {{
        margin: 0;
        color:  # 333;
    }}
    .no-slides {{
        text-align: center;
        color:  # 666;
        font-style: italic;
        padding: 40px;
    }}
    </style >
    """

    content_block = create_xblock(
        parent_locator=str(unit.location),
        user=user,
        category='html',
        display_name=content_data.get('title', 'Lesson Slides')
    )

    # Update the HTML content
    content_block.data = html_content
    content_block.metadata.update({
        'chalix_content_type': 'slide',
        'file_url': file_url,
        'file_type': file_type
    })

    store = modulestore()
    store.update_item(content_block, user.id)

    return content_block


def _create_quiz_block(unit, content_data, user):
    """Create a quiz content block."""
    questions = content_data.get('questions', [])
    instructions = content_data.get('instructions', 'Complete the following quiz:')

    # Generate problem XML
    problem_xml = '<problem>\n'
    problem_xml += f'<p class="quiz-instructions">{instructions}</p>\n'

    for i, question in enumerate(questions):
        problem_xml += f"""
        <multiplechoiceresponse >
            <p class = "question-text" > {question.get('question', f'Question {i+1}')} < /p >
            <choicegroup type = "MultipleChoice" >
        """

        for choice in question.get('choices', []):
            correct = 'correct="true"' if choice.get('correct', False) else ''
            problem_xml += f'                <choice {correct}>{choice.get("text", "")}</choice>\n'

        problem_xml += """
            </choicegroup >
        </multiplechoiceresponse >
        """

    problem_xml += '</problem>'

    content_block = create_xblock(
        parent_locator=str(unit.location),
        user=user,
        category='problem',
        display_name=content_data.get('title', 'Unit Quiz')
    )

    # Update the problem data
    content_block.data = problem_xml
    content_block.metadata.update({
        'chalix_content_type': 'quiz',
        'question_count': len(questions)
    })

    store = modulestore()
    store.update_item(content_block, user.id)

    return content_block


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@course_author_access_required
@csrf_exempt
def update_chalix_unit_content(request, course_id, unit_locator):
    """
    Update the content of a Chalix unit.
    """
    try:
        data = request.data
        content_data = data.get('content_data', {})

        store = modulestore()
        unit = store.get_item(unit_locator)

        # Get the content block (first child)
        if unit.children:
            content_block = store.get_item(unit.children[0])
            content_type = content_block.metadata.get('chalix_content_type')

            if content_type == 'online_class':
                _update_online_class_block(content_block, content_data, request.user)
            elif content_type == 'unit_video':
                _update_unit_video_block(content_block, content_data, request.user)
            elif content_type == 'slide':
                _update_slide_block(content_block, content_data, request.user)
            elif content_type == 'quiz':
                _update_quiz_block(content_block, content_data, request.user)

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'No content block found'}, status=404)

    except Exception as e:
        log.exception(f"Error updating Chalix unit content: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def _update_online_class_block(content_block, content_data, user):
    """Update online class content block."""
    meeting_link = content_data.get('meeting_link', '')
    meeting_time = content_data.get('meeting_time', '')
    duration = content_data.get('duration', '')

    # Update HTML content with new data
    html_content = f"""
    <div class = "chalix-online-class" >
        <div class = "online-class-header" >
            <i class = "fa fa-video-camera" > </i >
            <h3 > Online Class Session < /h3 >
        </div >
        <div class = "meeting-info" >
            <div class = "info-item" >
                <strong > Meeting Time: < /strong > {meeting_time}
            </div >
            <div class = "info-item" >
                <strong > Duration: < /strong > {duration}
            </div >
            {f'<div class="meeting-link"><a href="{meeting_link}" target="_blank" class="btn btn-primary btn-lg"><i class="fa fa-external-link"></i> Join Online Class</a></div>' if meeting_link else ''}
        </div >
    </div >
    """

    content_block.data = html_content
    content_block.metadata.update({
        'meeting_link': meeting_link,
        'meeting_time': meeting_time,
        'duration': duration
    })

    store = modulestore()
    store.update_item(content_block, user.id)


def _update_unit_video_block(content_block, content_data, user):
    """Update unit video content block."""
    content_block.metadata.update({
        'youtube_id_1_0': content_data.get('youtube_id', ''),
        'video_url': content_data.get('video_url', ''),
        'download_video': content_data.get('download_video', False),
    })

    store = modulestore()
    store.update_item(content_block, user.id)


def _update_slide_block(content_block, content_data, user):
    """Update slide content block."""
    file_url = content_data.get('file_url', '')
    file_type = content_data.get('file_type', 'pdf')

    # Generate updated embed code
    if file_type.lower() == 'pdf':
        embed_html = f'<iframe src="{file_url}" width="100%" height="600px" frameborder="0"></iframe>'
    else:
        embed_html = f'<iframe src="{file_url}" width="100%" height="600px" frameborder="0"></iframe>'

    html_content = f"""
    <div class = "chalix-slides" >
        <div class = "slides-header" >
            <i class = "fa fa-file-powerpoint-o" > </i >
            <h3 > Lesson Slides < /h3 >
        </div >
        <div class = "slides-content" >
            {embed_html if file_url else '<p class="no-slides">No slides available</p>'}
        </div >
    </div >
    """

    content_block.data = html_content
    content_block.metadata.update({
        'file_url': file_url,
        'file_type': file_type
    })

    store = modulestore()
    store.update_item(content_block, user.id)


def _update_quiz_block(content_block, content_data, user):
    """Update quiz content block."""
    questions = content_data.get('questions', [])
    instructions = content_data.get('instructions', 'Complete the following quiz:')

    # Generate updated problem XML
    problem_xml = '<problem>\n'
    problem_xml += f'<p class="quiz-instructions">{instructions}</p>\n'

    for i, question in enumerate(questions):
        problem_xml += f"""
        <multiplechoiceresponse >
            <p class = "question-text" > {question.get('question', f'Question {i+1}')} < /p >
            <choicegroup type = "MultipleChoice" >
        """

        for choice in question.get('choices', []):
            correct = 'correct="true"' if choice.get('correct', False) else ''
            problem_xml += f'                <choice {correct}>{choice.get("text", "")}</choice>\n'

        problem_xml += """
            </choicegroup >
        </multiplechoiceresponse >
        """

    problem_xml += '</problem>'

    content_block.data = problem_xml
    content_block.metadata.update({
        'question_count': len(questions)
    })

    store = modulestore()
    store.update_item(content_block, user.id)

    return content_block


@api_view(['POST'])
def update_online_class_config(request, course_id):
    """
    Update online class configuration for a unit.
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        course_key = CourseKey.from_string(course_id)

        # Check if user has access to edit this course
        if not has_studio_write_access(request.user, course_key):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Get the unit locator and configuration data
        unit_locator_string = request.data.get('unit_locator')
        meeting_link = request.data.get('meeting_link', '')
        meeting_time = request.data.get('meeting_time', '')
        duration = request.data.get('duration', '')

        if not unit_locator_string:
            return JsonResponse({'error': 'unit_locator is required'}, status=400)

        unit_locator = BlockUsageLocator.from_string(unit_locator_string)

        # Get the unit and find its online class content block
        store = modulestore()
        unit = store.get_item(unit_locator)

        online_class_block = None
        for child_location in unit.children:
            try:
                child_block = store.get_item(child_location)

                # Check for metadata first (new blocks)
                has_metadata = (hasattr(child_block, 'metadata') and
                                child_block.metadata and
                                child_block.metadata.get('chalix_content_type') == 'online_class')

                # Check for content pattern (existing blocks)
                has_content_pattern = False
                if hasattr(child_block, 'data') and child_block.data and child_block.category == 'html':
                    content_lower = child_block.data.lower()
                    has_content_pattern = (
                        'lớp học trực tuyến' in content_lower or
                        'online class' in content_lower or
                        'chalix-online-class' in content_lower
                    )

                # Also check unit display name for legacy detection
                unit_name_pattern = False
                if hasattr(unit, 'display_name') and unit.display_name:
                    unit_name_lower = unit.display_name.lower()
                    unit_name_pattern = (
                        'lớp học trực tuyến' in unit_name_lower or
                        'online class' in unit_name_lower
                    )

                if has_metadata or has_content_pattern or unit_name_pattern:
                    online_class_block = child_block
                    # Add metadata if missing (for legacy blocks)
                    if not has_metadata:
                        if not hasattr(child_block, 'metadata'):
                            child_block.metadata = {}
                        child_block.metadata['chalix_content_type'] = 'online_class'
                    break
            except:
                continue

        if not online_class_block:
            return JsonResponse({'error': 'Online class block not found in unit'}, status=404)

        # Update the HTML content
        html_content = f"""
        <div class = "chalix-online-class" >
            <h3 > <i class = "fa fa-video-camera" > </i > Online Class Session < /h3 >
            {f'<p><strong>Meeting Time:</strong> {meeting_time}</p>' if meeting_time else ''}
            {f'<p><strong>Duration:</strong> {duration} minutes</p>' if duration else ''}
            {f'<p><strong>Meeting Link:</strong> <a href="{meeting_link}" target="_blank">{meeting_link}</a></p>' if meeting_link else '<p><strong>Meeting Link:</strong> Will be provided later</p>'}
        </div >
        """

        # Update the block
        online_class_block.data = html_content
        online_class_block.metadata.update({
            'chalix_content_type': 'online_class',
            'meeting_link': meeting_link,
            'meeting_time': meeting_time,
            'duration': duration
        })

        store.update_item(online_class_block, request.user.id)

        return JsonResponse({
            'success': True,
            'meeting_link': meeting_link,
            'meeting_time': meeting_time,
            'duration': duration
        })

    except Exception as e:
        log.exception(f"Error updating online class config: {e}")
        return JsonResponse({'error': str(e)}, status=500)
