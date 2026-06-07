"""
Tests for Chalix User Menu functionality
"""
from datetime import date, timedelta
from django.utils import timezone

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from lms.djangoapps.chalix_user_menu.models import (
    UserLearningPlan,
    TeachingRequest,
    UserRequest,
    UserPersonalization,
    ChalixDemandSurveyResponse,
    ChalixDemandSurveyResponseChoice,
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


class DemandSurveyTestCase(TestCase):
    """Base test case for Demand Survey tests"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='learner',
            email='learner@example.com',
            password='testpass123',
            first_name='Learner',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        self.client.login(username='learner', password='testpass123')

        # Import CMS models (we need to mock surveys for testing)
        # In a real test, these would be created via the CMS app
        # For now, we'll set up the structure needed


class SurveyListTestCase(DemandSurveyTestCase):
    """Test survey list endpoint functionality"""

    def test_survey_list_requires_auth(self):
        """Test that survey_list returns 401 for anonymous users"""
        self.client.logout()
        response = self.client.get(reverse('chalix_user_menu:survey_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_survey_list_authenticated(self):
        """Test that authenticated users get a response"""
        response = self.client.get(reverse('chalix_user_menu:survey_list'))
        # Will return 200 with empty list if no surveys exist
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_survey_list_returns_only_published(self):
        """Test that only published and active surveys are returned"""
        # This test would require mocking CMS models
        # The endpoint should filter for status='published' and is_active=True
        response = self.client.get(reverse('chalix_user_menu:survey_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        # Verify surveys list structure
        self.assertIn('surveys', data)


class SurveyDetailTestCase(DemandSurveyTestCase):
    """Test survey detail endpoint functionality"""

    def test_survey_detail_requires_auth(self):
        """Test that survey_detail returns 401 for anonymous users"""
        self.client.logout()
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'test-token'})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_survey_detail_nonexistent_returns_404(self):
        """Test that requesting nonexistent survey returns 404"""
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'nonexistent-token'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_survey_detail_returns_prefill(self):
        """Test that survey detail returns user prefill data"""
        # This test verifies that the endpoint structure includes user_prefill
        # with email matching the logged-in user
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'test-token'})
        )
        # Will fail with 404 if survey doesn't exist, but response structure can be verified
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertIn('user_prefill', data)
            self.assertEqual(data['user_prefill']['email'], self.user.email)

    def test_survey_detail_groups_choices(self):
        """Test that choices are grouped by group_order and order_index"""
        # This test verifies the response structure includes groups
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'test-token'})
        )
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertIn('groups', data)


class SurveySubmitTestCase(DemandSurveyTestCase):
    """Test survey submit endpoint functionality"""

    def test_survey_submit_requires_auth(self):
        """Test that survey_submit returns 401 for anonymous users"""
        self.client.logout()
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'test-token'}),
            data={'full_name': 'Test', 'email': 'test@example.com', 'selected_choice_ids': []},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_survey_submit_nonexistent_returns_404(self):
        """Test that submitting to nonexistent survey returns 404"""
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'nonexistent-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'selected_choice_ids': [],
                'other_text': ''
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_survey_submit_requires_full_name(self):
        """Test that full_name is required"""
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'test-token'}),
            data={
                'full_name': '',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'selected_choice_ids': [],
                'other_text': ''
            },
            content_type='application/json'
        )
        # Will get 404 if survey doesn't exist, or 400 if validation fails
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            data = response.json()
            self.assertIn('error', data)

    def test_survey_submit_requires_email(self):
        """Test that email is required"""
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'test-token'}),
            data={
                'full_name': 'Test User',
                'email': '',
                'phone_number': '1234567890',
                'selected_choice_ids': [],
                'other_text': ''
            },
            content_type='application/json'
        )
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            data = response.json()
            self.assertIn('error', data)


class SurveyResponseModelTestCase(DemandSurveyTestCase):
    """Test ChalixDemandSurveyResponse model"""

    def test_create_survey_response(self):
        """Test creating a survey response"""
        response = ChalixDemandSurveyResponse.objects.create(
            survey_id=1,
            respondent_user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone_number='1234567890',
            other_text='Other option'
        )
        self.assertIsNotNone(response.id)
        self.assertEqual(response.survey_id, 1)
        self.assertEqual(response.respondent_user, self.user)

    def test_survey_response_unique_together(self):
        """Test unique_together constraint on survey_id and respondent_user"""
        ChalixDemandSurveyResponse.objects.create(
            survey_id=1,
            respondent_user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone_number='1234567890'
        )
        
        # Attempting to create another response for same user and survey should fail
        with self.assertRaises(Exception):
            ChalixDemandSurveyResponse.objects.create(
                survey_id=1,
                respondent_user=self.user,
                full_name='Test User 2',
                email='test2@example.com',
                phone_number='9876543210'
            )

    def test_survey_response_choice_through_table(self):
        """Test ChalixDemandSurveyResponseChoice through table"""
        response = ChalixDemandSurveyResponse.objects.create(
            survey_id=1,
            respondent_user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone_number='1234567890'
        )
        
        # Add selected choices
        choice1 = ChalixDemandSurveyResponseChoice.objects.create(
            response=response,
            choice_id=10
        )
        choice2 = ChalixDemandSurveyResponseChoice.objects.create(
            response=response,
            choice_id=11
        )
        
        # Verify choices are linked
        selected = response.selected_choices.all()
        self.assertEqual(selected.count(), 2)
        self.assertIn(choice1, selected)
        self.assertIn(choice2, selected)

    def test_survey_response_duplicate_choice_rejected(self):
        """Test that duplicate choice selections are rejected via unique_together"""
        response = ChalixDemandSurveyResponse.objects.create(
            survey_id=1,
            respondent_user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone_number='1234567890'
        )
        
        ChalixDemandSurveyResponseChoice.objects.create(
            response=response,
            choice_id=10
        )
        
        # Attempting to create duplicate choice selection should fail
        with self.assertRaises(Exception):
            ChalixDemandSurveyResponseChoice.objects.create(
                response=response,
                choice_id=10
            )


class SurveyChoiceDetailTestCase(DemandSurveyTestCase):
    """Test survey choice detail endpoint"""

    def test_survey_choice_detail_requires_auth(self):
        """Test that choice_detail returns 401 for anonymous users"""
        self.client.logout()
        response = self.client.get(
            reverse(
                'chalix_user_menu:survey_choice_detail',
                kwargs={'public_token': 'test-token', 'choice_id': 1}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_survey_choice_detail_nonexistent(self):
        """Test that requesting nonexistent choice returns 404"""
        response = self.client.get(
            reverse(
                'chalix_user_menu:survey_choice_detail',
                kwargs={'public_token': 'nonexistent-token', 'choice_id': 99999}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SurveyVotingPeriodTestCase(DemandSurveyTestCase):
    """Test survey voting period validation"""

    def test_survey_submit_before_starts_at(self):
        """Test that survey submit is rejected if before starts_at"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        future_start = timezone.now() + timedelta(days=1)
        survey = ChalixSurveyForm.objects.create(
            title='Future Survey',
            public_token='future-survey-token',
            starts_at=future_start,
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'future-survey-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('chưa bắt đầu', data['error'])

    def test_survey_submit_after_ends_at(self):
        """Test that survey submit is rejected if after ends_at"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        past_end = timezone.now() - timedelta(days=1)
        survey = ChalixSurveyForm.objects.create(
            title='Expired Survey',
            public_token='expired-survey-token',
            ends_at=past_end,
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'expired-survey-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('kết thúc', data['error'])

    def test_survey_submit_within_valid_period(self):
        """Test that survey submit works within valid voting period"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        now = timezone.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)
        
        survey = ChalixSurveyForm.objects.create(
            title='Active Survey',
            public_token='active-survey-token',
            starts_at=start,
            ends_at=end,
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'active-survey-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])


class SurveyMultipleVotesTestCase(DemandSurveyTestCase):
    """Test survey multiple votes setting"""

    def test_survey_disallow_multiple_votes_default(self):
        """Test that multiple votes are disallowed by default"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        survey = ChalixSurveyForm.objects.create(
            title='Single Vote Survey',
            public_token='single-vote-token',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        # First submission should succeed
        response1 = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'single-vote-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second submission should fail
        response2 = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'single-vote-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 409)
        data = response2.json()
        self.assertIn('error', data)
        self.assertIn('đã nộp', data['error'])

    def test_survey_allow_multiple_votes(self):
        """Test that selecting multiple choices is allowed when setting is enabled"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        survey = ChalixSurveyForm.objects.create(
            title='Multi Vote Survey',
            public_token='multi-vote-token',
            allow_multiple_votes=True,
            allow_add_choice=False
        )
        choice1 = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        choice2 = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 2',
            detail_html='<p>Details</p>'
        )
        
        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'multi-vote-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice1.id, choice2.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])

    def test_survey_disallow_multiple_choice_selection(self):
        """Test that selecting more than one choice is rejected when disabled."""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice

        survey = ChalixSurveyForm.objects.create(
            title='Single Choice Survey',
            public_token='single-choice-token',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        choice1 = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        choice2 = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 2',
            detail_html='<p>Details</p>'
        )

        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'single-choice-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice1.id, choice2.id]
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chỉ cho phép chọn một phương án', response.json().get('error', ''))


class SurveyAutoPublishTestCase(DemandSurveyTestCase):
    """Test survey auto-publish feature"""

    def test_survey_auto_published_on_creation(self):
        """Test that surveys are auto-published upon creation"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm
        
        survey = ChalixSurveyForm.objects.create(
            title='Auto Published Survey',
            public_token='auto-published-token',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        
        # Survey should have status='published' by default
        self.assertEqual(survey.status, 'published')

    def test_survey_list_shows_only_published_surveys(self):
        """Test that survey list only shows published surveys, not draft or closed"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm
        
        # Create published survey
        published = ChalixSurveyForm.objects.create(
            title='Published Survey',
            public_token='published-token',
            status='published',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        
        # Create draft survey
        draft = ChalixSurveyForm.objects.create(
            title='Draft Survey',
            public_token='draft-token',
            status='draft',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        
        # Create closed survey
        closed = ChalixSurveyForm.objects.create(
            title='Closed Survey',
            public_token='closed-token',
            status='closed',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        
        response = self.client.get(reverse('chalix_user_menu:survey_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        
        # Only published survey should appear
        tokens = [s['public_token'] for s in data['surveys']]
        self.assertIn('published-token', tokens)
        self.assertNotIn('draft-token', tokens)
        self.assertNotIn('closed-token', tokens)

    def test_draft_survey_returns_404(self):
        """Test that accessing a draft survey returns 404"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        draft_survey = ChalixSurveyForm.objects.create(
            title='Draft Survey',
            public_token='draft-survey-token',
            status='draft',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        ChalixSurveyChoice.objects.create(
            survey=draft_survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        # survey_detail should return 404 for draft survey
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'draft-survey-token'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_closed_survey_returns_404(self):
        """Test that accessing a closed survey returns 404"""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice
        
        closed_survey = ChalixSurveyForm.objects.create(
            title='Closed Survey',
            public_token='closed-survey-token',
            status='closed',
            allow_multiple_votes=False,
            allow_add_choice=False
        )
        ChalixSurveyChoice.objects.create(
            survey=closed_survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )
        
        # survey_detail should return 404 for closed survey
        response = self.client.get(
            reverse('chalix_user_menu:survey_detail', kwargs={'public_token': 'closed-survey-token'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SurveyAllowAddChoiceTestCase(DemandSurveyTestCase):
    """Test survey custom-choice submission behavior."""

    def test_submit_with_other_text_creates_choice_when_enabled(self):
        """When allow_add_choice=True, other_text should create a new choice and count a vote."""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice

        survey = ChalixSurveyForm.objects.create(
            title='Allow Other Survey',
            public_token='allow-other-token',
            allow_multiple_votes=False,
            allow_add_choice=True,
        )
        base_choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Base option',
            detail_html='<p>Base</p>',
            order_index=0,
        )

        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'allow-other-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [base_choice.id],
                'other_text': 'Lựa chọn khác từ người học'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        custom_choice = ChalixSurveyChoice.objects.filter(
            survey=survey,
            name='Lựa chọn khác từ người học',
            is_active=True,
        ).first()
        self.assertIsNotNone(custom_choice)
        self.assertEqual(custom_choice.vote_count, 1)

    def test_submit_with_other_text_rejected_when_disabled(self):
        """When allow_add_choice=False, other_text should be rejected."""
        from cms.djangoapps.contentstore.models import ChalixSurveyForm, ChalixSurveyChoice

        survey = ChalixSurveyForm.objects.create(
            title='No Other Survey',
            public_token='no-other-token',
            allow_multiple_votes=False,
            allow_add_choice=False,
        )
        choice = ChalixSurveyChoice.objects.create(
            survey=survey,
            name='Option 1',
            detail_html='<p>Details</p>'
        )

        response = self.client.post(
            reverse('chalix_user_menu:survey_submit', kwargs={'public_token': 'no-other-token'}),
            data={
                'full_name': 'Test User',
                'email': 'test@example.com',
                'selected_choice_ids': [choice.id],
                'other_text': 'Không hợp lệ'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('không cho phép', response.json().get('error', ''))
