"""
Simplified Course Creation and Management Utilities.

This module provides utilities to create and manage courses with the simplified structure:
- Course → Modules → Units → Content (video/slide/questions only)
"""

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.course_block import CourseBlock
from xmodule.seq_block import SequenceBlock
from xmodule.vertical_block import VerticalBlock
from xmodule.video_block import VideoBlock
from xmodule.html_block import HtmlBlock
from xmodule.problem_block import ProblemBlock
import logging

log = logging.getLogger(__name__)


class SimplifiedCourseManager:
    """
    Manager for creating and maintaining simplified course structures.
    """

    ALLOWED_CONTENT_TYPES = ['video', 'slide', 'questions']

    def __init__(self):
        self.store = modulestore()

    def create_simplified_course(self, course_key, course_data):
        """
        Create a new course with the simplified structure.

        Args:
            course_key: CourseKey object
            course_data: Dictionary containing course metadata

        Returns:
            Created course object
        """
        try:
            # Create the course
            course = self.store.create_course(
                course_key.org,
                course_key.course,
                course_key.run,
                user_id=course_data.get('user_id'),
                display_name=course_data.get('title', 'New Course'),
                metadata={
                    'instructor_info': course_data.get('instructor_info', {}),
                    'simplified_structure': True,  # Mark as simplified
                }
            )

            log.info(f"Created simplified course: {course_key}")
            return course

        except Exception as e:
            log.error(f"Error creating simplified course {course_key}: {e}")
            raise

    def add_module_to_course(self, course_key, module_data):
        """
        Add a module (formerly chapter) to a course.

        Args:
            course_key: CourseKey object
            module_data: Dictionary containing module metadata

        Returns:
            Created module object
        """
        try:
            course = self.store.get_course(course_key)
            if not course:
                raise ValueError(f"Course {course_key} not found")

            # Create module (chapter)
            module_location = course.location.replace(
                category='chapter',
                name=module_data.get('name', f'module_{len(course.children)}')
            )

            module = self.store.create_item(
                module_data.get('user_id'),
                module_location,
                display_name=module_data.get('title', 'New Module'),
                metadata={
                    'simplified_module': True,
                }
            )

            # Add module to course
            course.children.append(module_location)
            self.store.update_item(course, module_data.get('user_id'))

            log.info(f"Added module {module_location} to course {course_key}")
            return module

        except Exception as e:
            log.error(f"Error adding module to course {course_key}: {e}")
            raise

    def add_unit_to_module(self, module_location, unit_data):
        """
        Add a unit (formerly sequential) to a module.

        Args:
            module_location: UsageKey of the module
            unit_data: Dictionary containing unit metadata

        Returns:
            Created unit object
        """
        try:
            module = self.store.get_item(module_location)
            if not module:
                raise ValueError(f"Module {module_location} not found")

            # Validate content type
            content_type = unit_data.get('content_type')
            if content_type not in self.ALLOWED_CONTENT_TYPES:
                raise ValueError(f"Invalid content type: {content_type}. Allowed: {self.ALLOWED_CONTENT_TYPES}")

            # Create unit (sequential)
            unit_location = module_location.replace(
                category='sequential',
                name=unit_data.get('name', f'unit_{len(module.children)}')
            )

            unit = self.store.create_item(
                unit_data.get('user_id'),
                unit_location,
                display_name=unit_data.get('title', 'New Unit'),
                metadata={
                    'simplified_unit': True,
                    'content_type': content_type,
                }
            )

            # Add unit to module
            module.children.append(unit_location)
            self.store.update_item(module, unit_data.get('user_id'))

            # Create a vertical container for the unit
            vertical_location = unit_location.replace(
                category='vertical',
                name='vertical'
            )

            vertical = self.store.create_item(
                unit_data.get('user_id'),
                vertical_location,
                display_name=unit_data.get('title', 'Content'),
                metadata={
                    'simplified_vertical': True,
                }
            )

            # Add vertical to unit
            unit.children.append(vertical_location)
            self.store.update_item(unit, unit_data.get('user_id'))

            # Add content based on type
            self._add_content_to_vertical(vertical_location, unit_data)

            log.info(f"Added unit {unit_location} to module {module_location}")
            return unit

        except Exception as e:
            log.error(f"Error adding unit to module {module_location}: {e}")
            raise

    def _add_content_to_vertical(self, vertical_location, unit_data):
        """
        Add content blocks to a vertical based on the unit's content type.
        """
        content_type = unit_data.get('content_type')
        user_id = unit_data.get('user_id')

        vertical = self.store.get_item(vertical_location)

        if content_type == 'video':
            self._add_video_content(vertical, vertical_location, unit_data, user_id)
        elif content_type == 'slide':
            self._add_slide_content(vertical, vertical_location, unit_data, user_id)
        elif content_type == 'questions':
            self._add_question_content(vertical, vertical_location, unit_data, user_id)

    def _add_video_content(self, vertical, vertical_location, unit_data, user_id):
        """Add video content to a vertical."""
        video_location = vertical_location.replace(
            category='video',
            name='video_content'
        )

        video_data = unit_data.get('content_data', {})

        video = self.store.create_item(
            user_id,
            video_location,
            display_name=video_data.get('title', 'Video'),
            metadata={
                'youtube_id_1_0': video_data.get('youtube_id', ''),
                'video_url': video_data.get('video_url', ''),
                'simplified_content': True,
                'content_type': 'video',
            }
        )

        vertical.children.append(video_location)
        self.store.update_item(vertical, user_id)

        log.info(f"Added video content to {vertical_location}")

    def _add_slide_content(self, vertical, vertical_location, unit_data, user_id):
        """Add slide content (HTML/PDF) to a vertical."""
        html_location = vertical_location.replace(
            category='html',
            name='slide_content'
        )

        slide_data = unit_data.get('content_data', {})

        # Create HTML content for slides
        slide_html = self._generate_slide_html(slide_data)

        html_block = self.store.create_item(
            user_id,
            html_location,
            display_name=slide_data.get('title', 'Slides'),
            data=slide_html,
            metadata={
                'simplified_content': True,
                'content_type': 'slide',
            }
        )

        vertical.children.append(html_location)
        self.store.update_item(vertical, user_id)

        log.info(f"Added slide content to {vertical_location}")

    def _add_question_content(self, vertical, vertical_location, unit_data, user_id):
        """Add question content to a vertical."""
        problem_location = vertical_location.replace(
            category='problem',
            name='question_content'
        )

        question_data = unit_data.get('content_data', {})

        # Generate problem XML based on question type
        problem_xml = self._generate_problem_xml(question_data)

        problem = self.store.create_item(
            user_id,
            problem_location,
            display_name=question_data.get('title', 'Questions'),
            data=problem_xml,
            metadata={
                'simplified_content': True,
                'content_type': 'questions',
                'max_attempts': question_data.get('max_attempts', 3),
            }
        )

        vertical.children.append(problem_location)
        self.store.update_item(vertical, user_id)

        log.info(f"Added question content to {vertical_location}")

    def _generate_slide_html(self, slide_data):
        """
        Generate HTML content for slides.
        """
        if slide_data.get('file_url'):
            # For PDF or PowerPoint files
            file_url = slide_data['file_url']
            if file_url.endswith('.pdf'):
                return f'''
                <div class="slide-content">
                    <iframe src="{file_url}" width="100%" height="600px" frameborder="0">
                        <p>Your browser does not support iframes. 
                        <a href="{file_url}" target="_blank">Click here to view the slides</a></p>
                    </iframe>
                </div>
                '''
            else:
                return f'''
                <div class="slide-content">
                    <p><a href="{file_url}" target="_blank" class="btn btn-primary">
                        View Slides
                    </a></p>
                </div>
                '''
        else:
            # For custom HTML content
            return slide_data.get('html_content', '<p>Slide content not available</p>')

    def _generate_problem_xml(self, question_data):
        """
        Generate problem XML for questions.
        """
        question_type = question_data.get('type', 'multiple_choice')

        if question_type == 'multiple_choice':
            return self._generate_multiple_choice_xml(question_data)
        elif question_type == 'open_response':
            return self._generate_open_response_xml(question_data)
        else:
            return self._generate_multiple_choice_xml(question_data)  # Default

    def _generate_multiple_choice_xml(self, question_data):
        """Generate XML for multiple choice questions."""
        question_text = question_data.get('question', 'Sample question')
        choices = question_data.get('choices', [])
        correct_answer = question_data.get('correct_answer', '')

        choices_xml = ''
        for choice in choices:
            is_correct = choice.get('id') == correct_answer
            choices_xml += f'''
            <choice correct="{str(is_correct).lower()}">{choice.get('text', '')}</choice>
            '''

        return f'''
        <problem>
            <multiplechoiceresponse>
                <p>{question_text}</p>
                <choicegroup type="MultipleChoice">
                    {choices_xml}
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        '''

    def _generate_open_response_xml(self, question_data):
        """Generate XML for open response questions."""
        question_text = question_data.get('question', 'Sample question')

        return f'''
        <problem>
            <stringresponse answer=".*" type="ci regexp">
                <p>{question_text}</p>
                <textline size="40"/>
            </stringresponse>
        </problem>
        '''

    def validate_course_structure(self, course_key):
        """
        Validate that a course follows the simplified structure.

        Returns:
            Dictionary with validation results
        """
        try:
            course = self.store.get_course(course_key)
            if not course:
                return {'valid': False, 'error': 'Course not found'}

            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'modules_count': 0,
                'units_count': 0,
                'content_breakdown': {'video': 0, 'slide': 0, 'questions': 0, 'other': 0}
            }

            # Check each module (chapter)
            for module_id in course.children:
                module = self.store.get_item(module_id)
                if module.category != 'chapter':
                    validation_results['errors'].append(f"Invalid module type: {module.category}")
                    continue

                validation_results['modules_count'] += 1

                # Check each unit (sequential)
                for unit_id in module.children:
                    unit = self.store.get_item(unit_id)
                    if unit.category != 'sequential':
                        validation_results['errors'].append(f"Invalid unit type: {unit.category}")
                        continue

                    validation_results['units_count'] += 1

                    # Check unit content
                    content_type = self._analyze_unit_content_type(unit)
                    if content_type in validation_results['content_breakdown']:
                        validation_results['content_breakdown'][content_type] += 1
                    else:
                        validation_results['content_breakdown']['other'] += 1
                        validation_results['warnings'].append(f"Unit {unit.display_name} has unknown content type")

            if validation_results['errors']:
                validation_results['valid'] = False

            return validation_results

        except Exception as e:
            log.error(f"Error validating course structure {course_key}: {e}")
            return {'valid': False, 'error': str(e)}

    def _analyze_unit_content_type(self, unit):
        """
        Analyze a unit to determine its primary content type.
        """
        if not unit.children:
            return 'other'

        # Look at the vertical's children
        vertical = self.store.get_item(unit.children[0])
        if not vertical.children:
            return 'other'

        video_count = 0
        slide_count = 0
        question_count = 0

        for child_id in vertical.children:
            child = self.store.get_item(child_id)
            if child.category == 'video':
                video_count += 1
            elif child.category == 'html':
                slide_count += 1
            elif child.category in ['problem', 'openassessment']:
                question_count += 1

        # Return the most prominent content type
        if video_count > 0:
            return 'video'
        elif question_count > 0:
            return 'questions'
        elif slide_count > 0:
            return 'slide'
        else:
            return 'other'


# Utility functions for course management

def create_simplified_course(org, course, run, user_id, course_data):
    """
    Create a new simplified course.

    Args:
        org: Organization identifier
        course: Course identifier
        run: Course run identifier
        user_id: User creating the course
        course_data: Dictionary with course metadata

    Returns:
        Created course object
    """
    course_key = CourseKey.from_string(f"{org}/{course}/{run}")
    manager = SimplifiedCourseManager()

    course_data['user_id'] = user_id
    return manager.create_simplified_course(course_key, course_data)


def add_module_to_course(course_key_string, user_id, module_data):
    """
    Add a module to an existing course.
    """
    course_key = CourseKey.from_string(course_key_string)
    manager = SimplifiedCourseManager()

    module_data['user_id'] = user_id
    return manager.add_module_to_course(course_key, module_data)


def add_unit_to_module(module_location_string, user_id, unit_data):
    """
    Add a unit to an existing module.
    """
    module_location = UsageKey.from_string(module_location_string)
    manager = SimplifiedCourseManager()

    unit_data['user_id'] = user_id
    return manager.add_unit_to_module(module_location, unit_data)
