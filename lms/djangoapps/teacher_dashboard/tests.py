"""
Tests for Teacher Dashboard.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TeacherDashboardTestCase(SharedModuleStoreTestCase):
    """
    Test cases for the teacher dashboard functionality.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testinstructor',
            email='test@example.com',
            password='testpass123'
        )
        self.course = CourseFactory.create()
        self.course_key = self.course.id

    def test_teacher_dashboard_access_denied_for_regular_user(self):
        """Test that regular users cannot access the teacher dashboard."""
        self.client.login(username='testinstructor', password='testpass123')
        url = reverse('teacher_dashboard:teacher_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_teacher_dashboard_access_for_instructor(self):
        """Test that course instructors can access the teacher dashboard."""
        CourseInstructorRole(self.course_key).add_users(self.user)
        self.client.login(username='testinstructor', password='testpass123')
        url = reverse('teacher_dashboard:teacher_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_dashboard_access_for_staff(self):
        """Test that course staff can access the teacher dashboard."""
        CourseStaffRole(self.course_key).add_users(self.user)
        self.client.login(username='testinstructor', password='testpass123')
        url = reverse('teacher_dashboard:teacher_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_dashboard_shows_instructor_courses(self):
        """Test that the teacher dashboard shows courses where user is instructor."""
        CourseInstructorRole(self.course_key).add_users(self.user)
        self.client.login(username='testinstructor', password='testpass123')
        url = reverse('teacher_dashboard:teacher_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'teacher-dashboard')
        self.assertContains(response, str(self.course_key))

    def test_unauthenticated_user_redirected(self):
        """Test that unauthenticated users are redirected to login."""
        url = reverse('teacher_dashboard:teacher_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
