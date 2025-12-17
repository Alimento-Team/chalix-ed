"""
Management command to generate LearningContext and CourseOutline for courses.
"""
import logging
import sys
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generate LearningContext and CourseOutline for courses that don't have them.
    
    Usage:
        python manage.py lms generate_course_outlines
        python manage.py lms generate_course_outlines --course-id course-v1:org+course+run
        python manage.py lms generate_course_outlines --all
    """
    help = 'Generate learning sequence data for courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-id',
            type=str,
            help='Process a specific course by ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all courses (may take a long time)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate even if outline already exists'
        )

    def handle(self, *args, **options):
        course_id = options.get('course_id')
        process_all = options.get('all')
        force = options.get('force')
        
        if not course_id and not process_all:
            self.stdout.write(self.style.ERROR(
                'Please specify --course-id or --all'
            ))
            return
        
        store = modulestore()
        
        # Get courses to process
        if course_id:
            try:
                course_key = CourseKey.from_string(course_id)
                courses = [store.get_course(course_key)]
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Invalid course ID: {e}'))
                return
        else:
            self.stdout.write('Processing all courses...')
            courses = store.get_courses()
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for course in courses:
            if not course:
                continue
            
            course_key = course.id
            
            # Check if outline exists
            if not force:
                from openedx.core.djangoapps.content.learning_sequences.models import LearningContext
                if LearningContext.objects.filter(context_key=course_key).exists():
                    skipped_count += 1
                    self.stdout.write(f'✓ Skipping {course_key} (already has outline)')
                    continue
            
            # Generate outline by triggering course publish signal
            try:
                from xmodule.modulestore.django import SignalHandler
                from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
                
                # First regenerate the CourseOverview
                CourseOverview.load_from_module_store(course_key)
                
                # Then send the course_published signal to trigger learning sequences creation
                SignalHandler.course_published.send_robust(
                    sender=self.__class__,
                    course_key=course_key
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Generated outline for {course_key}'
                ))
                success_count += 1
            except Exception as e:
                import traceback
                self.stdout.write(self.style.ERROR(
                    f'✗ Failed to generate outline for {course_key}: {e}'
                ))
                if force or '--verbose' in sys.argv or '-v' in sys.argv:
                    traceback.print_exc()
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'Success: {success_count}, Errors: {error_count}, Skipped: {skipped_count}'
        ))
        self.stdout.write('='*60)
