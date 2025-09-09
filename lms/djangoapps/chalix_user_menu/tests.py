"""
Tests for Chalix User Menu functionality
"""
from datetime import date, timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from lms.djangoapps.chalix_user_menu.models import (
    UserLearningPlan,
    TeachingRequest,
    UserRequest,
    UserPersonalization
)


class ChalixUserMenuTestCase(TestCase):
    """Base test case for Chalix User Menu tests"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(username='testuser', password='testpass123')


class UserPersonalizationTestCase(ChalixUserMenuTestCase):
    """Test user personalization functionality"""

    def test_get_personalization_settings(self):
        """Test getting user personalization settings"""
        # Create personalization settings
        UserPersonalization.objects.create(
            user=self.user,
            learning_style='visual',
            preferred_language='vi',
            theme_preference='light'
        )

        response = self.client.get(reverse('chalix_user_menu:user_personalization'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['personalization']['learning_style'], 'visual')
        self.assertEqual(data['personalization']['preferred_language'], 'vi')

    def test_update_personalization_settings(self):
        """Test updating user personalization settings"""
        response = self.client.post(
            reverse('chalix_user_menu:user_personalization'),
            data={
                'learning_style': 'auditory',
                'preferred_language': 'vi',
                'theme_preference': 'dark'
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify settings were updated
        personalization = UserPersonalization.objects.get(user=self.user)
        self.assertEqual(personalization.learning_style, 'auditory')
        self.assertEqual(personalization.theme_preference, 'dark')


class UserRequestTestCase(ChalixUserMenuTestCase):
    """Test user request functionality"""

    def test_create_user_request(self):
        """Test creating a new user request"""
        response = self.client.post(
            reverse('chalix_user_menu:user_requests'),
            data={
                'request_type': 'technical_support',
                'title': 'Test Request',
                'description': 'This is a test request',
                'priority': 'medium'
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify request was created
        user_request = UserRequest.objects.get(user=self.user)
        self.assertEqual(user_request.title, 'Test Request')
        self.assertEqual(user_request.request_type, 'technical_support')

    def test_get_user_requests(self):
        """Test getting user requests"""
        # Create test requests
        UserRequest.objects.create(
            user=self.user,
            request_type='technical_support',
            title='Test Request 1',
            description='Description 1',
            priority='high'
        )
        UserRequest.objects.create(
            user=self.user,
            request_type='course_access',
            title='Test Request 2',
            description='Description 2',
            priority='low'
        )

        response = self.client.get(reverse('chalix_user_menu:user_requests'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['requests']), 2)
        self.assertEqual(data['total_requests'], 2)


class LearningPlanTestCase(ChalixUserMenuTestCase):
    """Test learning plan functionality"""

    def test_create_learning_plan(self):
        """Test creating a new learning plan"""
        start_date = date.today()
        end_date = start_date + timedelta(days=365)

        response = self.client.post(
            reverse('chalix_user_menu:learning_plans'),
            data={
                'title': 'Test Learning Plan',
                'description': 'This is a test learning plan',
                'target_hours': 100,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify plan was created
        plan = UserLearningPlan.objects.get(user=self.user)
        self.assertEqual(plan.title, 'Test Learning Plan')
        self.assertEqual(plan.target_hours, 100)

    def test_learning_plan_progress_calculation(self):
        """Test learning plan progress calculation"""
        plan = UserLearningPlan.objects.create(
            user=self.user,
            title='Test Plan',
            description='Test description',
            target_hours=100,
            completed_hours=25,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        )

        self.assertEqual(plan.progress_percentage, 25.0)

        # Test with completed hours exceeding target
        plan.completed_hours = 150
        plan.save()
        self.assertEqual(plan.progress_percentage, 100.0)


class TeachingRequestTestCase(ChalixUserMenuTestCase):
    """Test teaching request functionality"""

    def test_create_teaching_request(self):
        """Test creating a teaching request"""
        response = self.client.post(
            reverse('chalix_user_menu:teaching_registration'),
            data={
                'course_title': 'Advanced Python Programming',
                'course_description': 'A comprehensive course on Python programming',
                'teaching_experience': '5 years of Python development',
                'qualifications': 'MS in Computer Science',
                'proposed_duration': 40
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify request was created
        teaching_request = TeachingRequest.objects.get(user=self.user)
        self.assertEqual(teaching_request.course_title, 'Advanced Python Programming')
        self.assertEqual(teaching_request.status, 'pending')


class HelpResourcesTestCase(ChalixUserMenuTestCase):
    """Test help resources functionality"""

    def test_get_help_resources(self):
        """Test getting help resources"""
        response = self.client.get(reverse('chalix_user_menu:help_resources'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('categories', data['help_data'])
        self.assertIn('contact', data['help_data'])

        # Verify help categories are present
        categories = data['help_data']['categories']
        self.assertGreater(len(categories), 0)

        # Check if contact information is present
        contact = data['help_data']['contact']
        self.assertIn('email', contact)
        self.assertIn('phone', contact)


class UserLogoutTestCase(ChalixUserMenuTestCase):
    """Test user logout functionality"""

    def test_user_logout(self):
        """Test user logout"""
        response = self.client.post(reverse('chalix_user_menu:user_logout'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data['success'])

        # Verify user is logged out (subsequent requests should fail)
        response = self.client.get(reverse('chalix_user_menu:user_personalization'))
        # Should be redirected or get 401/403 status due to authentication requirement
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


class ModelTestCase(ChalixUserMenuTestCase):
    """Test model functionality"""

    def test_user_learning_plan_str(self):
        """Test UserLearningPlan string representation"""
        plan = UserLearningPlan.objects.create(
            user=self.user,
            title='Test Plan',
            description='Test description',
            target_hours=50,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180)
        )
        expected_str = f"{self.user.username} - Test Plan"
        self.assertEqual(str(plan), expected_str)

    def test_teaching_request_str(self):
        """Test TeachingRequest string representation"""
        request = TeachingRequest.objects.create(
            user=self.user,
            course_title='Test Course',
            course_description='Test description',
            teaching_experience='Test experience',
            qualifications='Test qualifications',
            proposed_duration=30
        )
        expected_str = f"{self.user.username} - Test Course"
        self.assertEqual(str(request), expected_str)

    def test_user_request_str(self):
        """Test UserRequest string representation"""
        user_request = UserRequest.objects.create(
            user=self.user,
            request_type='technical_support',
            title='Test Request',
            description='Test description'
        )
        expected_str = f"{self.user.username} - Test Request"
        self.assertEqual(str(user_request), expected_str)

    def test_user_personalization_str(self):
        """Test UserPersonalization string representation"""
        personalization = UserPersonalization.objects.create(
            user=self.user,
            learning_style='visual',
            preferred_language='vi'
        )
        expected_str = f"{self.user.username} - Personalization"
        self.assertEqual(str(personalization), expected_str)
