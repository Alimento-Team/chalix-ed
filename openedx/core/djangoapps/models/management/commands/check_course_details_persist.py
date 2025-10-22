import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from openedx.core.djangoapps.models.course_details import CourseDetails
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    help = 'Check persistence of final_evaluation_project_question via CourseDetails.update_from_json and fetch.'

    def add_arguments(self, parser):
        parser.add_argument('course_key', help='Course key string, e.g. course-v1:edX+DemoX+2021')
        parser.add_argument('question', help='Question text to save')

    def handle(self, *args, **options):
        # Ensure logging prints to console for this command.
        # Remove any existing handlers that may have incompatible formatters
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)

        # Attach a simple StreamHandler with a safe formatter so that
        # debug/info logging from modulestore and update_about_item will
        # reliably appear on the console and won't trigger formatter errors.
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        root_logger.addHandler(stream_handler)
        root_logger.setLevel(logging.DEBUG)

        logger = logging.getLogger(__name__)

        course_key = CourseKey.from_string(options['course_key'])
        question = options['question']

        self.stdout.write('Updating course %s with final_evaluation_project_question="%s"' % (course_key, question))
        # Prepare payload like the API
        payload = {'final_evaluation_project_question': question}

        # Resolve a user to run as (update_from_json expects a user object with .id)
        User = get_user_model()
        user = None
        try:
            # Prefer a superuser, then any staff, then first user
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Could not resolve a Django user from DB: %s', exc)

        if not user:
            # If no user is available, abort with guidance
            self.stderr.write('No Django users found; please run this command in a dev environment with users, or pass a valid user.')
            return

        logger.debug('Using user id=%s username=%s for update', user.id, getattr(user, 'username', None))

        # Verify the course exists in the modulestore
        ms = modulestore()
        course_block = ms.get_course(course_key)
        if course_block is None:
            logger.error('Course not found in modulestore for key=%s. Aborting.', course_key)
            self.stderr.write('Course not found in modulestore for key=%s. Ensure the course_key is correct and the modulestore contains the course.' % course_key)
            return

        try:
            # Use update_from_json to write
            CourseDetails.update_from_json(course_key, payload, user)
        except Exception as exc:
            logger.exception('Exception while calling update_from_json: %s', exc)
            self.stderr.write('update_from_json raised an exception: %s' % exc)
            return

        # Fetch back
        try:
            details = CourseDetails.fetch(course_key)
            value = getattr(details, 'final_evaluation_project_question', None)
            self.stdout.write('Fetched value: %s' % (value,))
        except Exception as exc:
            logger.exception('Exception while fetching CourseDetails: %s', exc)
            self.stderr.write('CourseDetails.fetch raised an exception: %s' % exc)
