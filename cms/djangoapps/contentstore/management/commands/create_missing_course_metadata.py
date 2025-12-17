"""
Management command to create ChalixCourseMetadata for courses that don't have it.
"""
import logging
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from cms.djangoapps.contentstore.models import ChalixCourseMetadata, ChalixOrganization

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create ChalixCourseMetadata records for courses that don't have metadata.
    
    Usage:
        python manage.py cms create_missing_course_metadata
        python manage.py cms create_missing_course_metadata --course-id course-v1:org+course+run
        python manage.py cms create_missing_course_metadata --dry-run
    """
    help = 'Create ChalixCourseMetadata for courses without metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-id',
            type=str,
            help='Process a specific course by ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it'
        )
        parser.add_argument(
            '--default-category',
            type=str,
            default='elective',
            choices=['elective', 'mandatory'],
            help='Default category for courses without metadata (default: elective)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        course_id = options.get('course_id')
        default_category = options['default_category']
        
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
            courses = store.get_courses()
        
        # Get default Bo organization
        try:
            default_org = ChalixOrganization.objects.filter(short_name='bo').first()
            if not default_org:
                self.stdout.write(self.style.WARNING('No "bo" organization found, metadata will have no organization'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not get default organization: {e}'))
            default_org = None
        
        created_count = 0
        skipped_count = 0
        
        for course in courses:
            if not course:
                continue
                
            course_key = course.id
            
            # Check if metadata exists
            if ChalixCourseMetadata.objects.filter(course_id=course_key).exists():
                skipped_count += 1
                self.stdout.write(f'✓ Skipping {course_key} (metadata exists)')
                continue
            
            # Create metadata
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'[DRY RUN] Would create metadata for {course_key} '
                    f'(category: {default_category}, public: True)'
                ))
                created_count += 1
            else:
                try:
                    metadata = ChalixCourseMetadata.objects.create(
                        course_id=course_key,
                        creator=None,  # Unknown creator for existing courses
                        creator_role='bo',  # Default to Bo role
                        creator_organization=default_org,
                        is_public=True,  # Make existing courses visible to all
                        is_mandatory_course=(default_category == 'mandatory'),
                        course_category=default_category,
                        publish_type=default_category,
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created metadata for {course_key} '
                        f'(category: {default_category}, public: True)'
                    ))
                    created_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'✗ Failed to create metadata for {course_key}: {e}'
                    ))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes were made'))
        self.stdout.write(self.style.SUCCESS(
            f'Created: {created_count}, Skipped: {skipped_count}'
        ))
        self.stdout.write('='*60)
