"""
Management command to auto-enroll all students in a course or all courses.
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Auto-enroll all students in specified course(s).
    
    Example usage:
        # Enroll all students in a specific course
        python manage.py cms auto_enroll_students --course-key course-v1:edX+DemoX+Demo_Course
        
        # Enroll all students in all courses
        python manage.py cms auto_enroll_students --all-courses
        
        # Enroll all students in courses from a specific organization
        python manage.py cms auto_enroll_students --org edX
    """
    
    help = 'Auto-enroll all students in specified course(s)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-key',
            type=str,
            help='Course key to enroll students in (e.g., course-v1:edX+DemoX+Demo_Course)'
        )
        parser.add_argument(
            '--all-courses',
            action='store_true',
            help='Enroll students in all existing courses'
        )
        parser.add_argument(
            '--org',
            type=str,
            help='Enroll students in all courses from the specified organization'
        )
        parser.add_argument(
            '--mode',
            type=str,
            default='audit',
            choices=['audit', 'honor', 'verified', 'professional'],
            help='Enrollment mode (default: audit)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be enrolled without actually enrolling'
        )

    def handle(self, *args, **options):
        if not any([options['course_key'], options['all_courses'], options['org']]):
            raise CommandError('You must specify --course-key, --all-courses, or --org')
        
        if sum(bool(x) for x in [options['course_key'], options['all_courses'], options['org']]) > 1:
            raise CommandError('You can only specify one of --course-key, --all-courses, or --org')

        # Get courses to process
        courses = []
        if options['course_key']:
            try:
                course_key = CourseKey.from_string(options['course_key'])
                courses = [CourseOverview.objects.get(id=course_key)]
            except (ValueError, CourseOverview.DoesNotExist) as e:
                raise CommandError(f'Invalid or non-existent course key: {options["course_key"]}') from e
        elif options['all_courses']:
            courses = CourseOverview.objects.all()
        elif options['org']:
            courses = CourseOverview.objects.filter(org=options['org'])
            if not courses.exists():
                raise CommandError(f'No courses found for organization: {options["org"]}')

        # Get all students (non-staff, non-superuser users)
        students = User.objects.filter(
            is_active=True,
            is_staff=False,
            is_superuser=False
        ).exclude(
            # Exclude users who have instructor/staff roles in any course
            courseaccessrole__role__in=['instructor', 'staff']
        ).distinct()

        total_enrolled = 0
        total_already_enrolled = 0
        total_errors = 0

        self.stdout.write(
            self.style.SUCCESS(f'Found {students.count()} students and {len(courses)} course(s) to process')
        )

        for course in courses:
            enrolled_count = 0
            already_enrolled_count = 0
            error_count = 0
            
            self.stdout.write(f'\nProcessing course: {course.id} ({course.display_name})')
            
            for student in students:
                try:
                    # Check if student is already enrolled
                    if CourseEnrollment.is_enrolled(student, course.id):
                        already_enrolled_count += 1
                        continue
                    
                    if options['dry_run']:
                        self.stdout.write(f'  Would enroll: {student.username}')
                        enrolled_count += 1
                    else:
                        # Enroll student
                        CourseEnrollment.enroll(
                            user=student,
                            course_key=course.id,
                            mode=options['mode'],
                            check_access=False
                        )
                        enrolled_count += 1
                        if enrolled_count % 100 == 0:  # Progress indicator
                            self.stdout.write(f'  Enrolled {enrolled_count} students...')
                
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  Error enrolling {student.username}: {str(e)}')
                    )
            
            total_enrolled += enrolled_count
            total_already_enrolled += already_enrolled_count
            total_errors += error_count
            
            action = "Would enroll" if options['dry_run'] else "Enrolled"
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {action}: {enrolled_count}, Already enrolled: {already_enrolled_count}, '
                    f'Errors: {error_count}'
                )
            )

        # Summary
        action = "Would enroll" if options['dry_run'] else "Enrolled"
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'  {action}: {total_enrolled} enrollments\n'
                f'  Already enrolled: {total_already_enrolled}\n'
                f'  Errors: {total_errors}'
            )
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('This was a dry run. Use without --dry-run to actually enroll students.')
            )