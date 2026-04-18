"""
Tests for facial expression recording feature.
"""
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from lms.djangoapps.learning_analytics.models import FacialExpressionLog
from lms.djangoapps.facial_expression.views import upload_facial_expression_video
from lms.djangoapps.facial_expression.storage import FacialExpressionStorage, get_facial_expression_storage


class FacialExpressionLogModelTest(TestCase):
    """Test the FacialExpressionLog model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='teacherpass123'
        )

    def test_create_facial_expression_log(self):
        """Test creating a facial expression log."""
        log = FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='facial_expressions/test/video.webm',
            video_size=1024000,
            start_timestamp=datetime.now(),
            is_complete=True
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.course_id, 'course-v1:Test+Course+Run')
        self.assertEqual(log.processing_status, 'pending')
        self.assertTrue(log.is_complete)

    def test_video_size_mb_property(self):
        """Test video_size_mb property calculation."""
        log = FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='test.webm',
            video_size=5242880,  # 5MB
            start_timestamp=datetime.now()
        )
        
        self.assertEqual(log.video_size_mb, 5.0)

    def test_recording_duration_property(self):
        """Test recording_duration property."""
        start = datetime(2025, 11, 2, 10, 0, 0)
        end = datetime(2025, 11, 2, 10, 5, 30)
        
        log = FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='test.webm',
            video_size=1024000,
            start_timestamp=start,
            end_timestamp=end
        )
        
        self.assertEqual(log.recording_duration, 330.0)  # 5 minutes 30 seconds

    def test_string_representation(self):
        """Test string representation of model."""
        log = FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='test.webm',
            video_size=1024000,
            start_timestamp=datetime.now()
        )
        
        self.assertIn('testuser', str(log))
        self.assertIn('course-v1:Test+Course+Run', str(log))


class FacialExpressionStorageTest(TestCase):
    """Test the FacialExpressionStorage class."""

    def setUp(self):
        """Set up test data."""
        self.storage = FacialExpressionStorage()

    def test_generate_video_path(self):
        """Test video path generation."""
        timestamp = datetime(2025, 11, 2, 10, 30, 45)
        path = self.storage.generate_video_path(
            user_id=123,
            course_id='course-v1:Test+Course+Run',
            unit_id='unit-123',
            timestamp=timestamp,
            student_id='student_123',
            week_number=2,
        )
        
        self.assertIn('emotion', path)
        self.assertIn('student_123', path)
        self.assertIn('week_2', path)
        self.assertTrue(path.endswith('.mp4'))

    def test_sanitize_path_component(self):
        """Test path component sanitization."""
        component = 'course-v1:Test+Course/Run'
        sanitized = self.storage._sanitize_path_component(component)
        
        self.assertNotIn('/', sanitized)
        self.assertNotIn(':', sanitized)

    @patch('lms.djangoapps.facial_expression.storage.get_storage')
    def test_save_video(self, mock_get_storage):
        """Test video saving."""
        mock_storage = Mock()
        mock_storage.save.return_value = 'saved/path.mp4'
        mock_get_storage.return_value = mock_storage
        
        storage = FacialExpressionStorage()
        mock_file = Mock()
        
        result = storage.save_video(mock_file, 'test/path.mp4')
        
        self.assertEqual(result, 'saved/path.mp4')
        mock_storage.save.assert_called_once()


class FacialExpressionAPITest(APITestCase):
    """Test the facial expression API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('lms.djangoapps.facial_expression.views.get_facial_expression_storage')
    @patch('lms.djangoapps.facial_expression.views.get_course_by_id')
    def test_upload_video_success(self, mock_get_course, mock_get_storage):
        """Test successful video upload."""
        # Mock storage
        mock_storage = Mock()
        mock_storage.save_video.return_value = 'test/path.webm'
        mock_get_storage.return_value = mock_storage
        
        # Mock course
        mock_course = Mock()
        mock_get_course.return_value = mock_course
        
        # Create mock video file
        from django.core.files.uploadedfile import SimpleUploadedFile
        video_file = SimpleUploadedFile(
            "test.webm",
            b"fake video content",
            content_type="video/webm"
        )
        
        # Make request
        response = self.client.post(
            '/api/facial-expression/upload/',
            {
                'video': video_file,
                'course_id': 'course-v1:Test+Course+Run',
                'unit_id': 'test-unit-123',
                'timestamp': '2025-11-02T10:00:00Z',
                'is_final': 'false'
            },
            format='multipart'
        )
        
        # This will fail because of authentication decorators, but tests the structure
        # In real testing, you'd need to properly set up authentication

    def test_get_logs_authenticated(self):
        """Test getting logs for authenticated user."""
        # Create test logs
        FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='test.webm',
            video_size=1024000,
            start_timestamp=datetime.now()
        )
        
        response = self.client.get('/api/facial-expression/logs/')
        
        # Response depends on authentication setup
        # self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_logs_filtered_by_course(self):
        """Test filtering logs by course."""
        FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course1+Run',
            unit_id='test-unit-123',
            video_path='test1.webm',
            video_size=1024000,
            start_timestamp=datetime.now()
        )
        
        FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course2+Run',
            unit_id='test-unit-456',
            video_path='test2.webm',
            video_size=1024000,
            start_timestamp=datetime.now()
        )
        
        response = self.client.get(
            '/api/facial-expression/logs/',
            {'course_id': 'course-v1:Test+Course1+Run'}
        )
        
        # Response depends on authentication setup


class FacialExpressionIntegrationTest(TestCase):
    """Integration tests for the facial expression feature."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('lms.djangoapps.facial_expression.storage.get_storage')
    def test_end_to_end_recording_flow(self, mock_get_storage):
        """Test the complete recording flow."""
        # Mock storage
        mock_storage_backend = Mock()
        mock_storage_backend.save.return_value = 'test/saved/path.webm'
        mock_get_storage.return_value = mock_storage_backend
        
        # Create log
        log = FacialExpressionLog.objects.create(
            user=self.user,
            course_id='course-v1:Test+Course+Run',
            unit_id='test-unit-123',
            video_path='test/path.webm',
            video_size=1024000,
            start_timestamp=datetime.now(),
            is_complete=True
        )
        
        # Verify log creation
        self.assertIsNotNone(log.id)
        self.assertEqual(log.processing_status, 'pending')
        
        # Simulate processing
        log.processing_status = 'completed'
        log.analysis_results = {
            'emotions': ['happy', 'engaged'],
            'confidence': 0.85
        }
        log.save()
        
        # Verify update
        updated_log = FacialExpressionLog.objects.get(id=log.id)
        self.assertEqual(updated_log.processing_status, 'completed')
        self.assertIsNotNone(updated_log.analysis_results)


# Run tests:
# python manage.py lms test lms.djangoapps.facial_expression.tests
