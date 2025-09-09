"""
Tests for learning analytics models and services.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from lms.djangoapps.learning_analytics.models import (
    LearnerBehavior, 
    LearningHoursRequirement, 
    LearningHoursApproval
)
from lms.djangoapps.learning_analytics.services import LearningHoursService


class LearnerBehaviorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
    def test_create_learner_behavior(self):
        behavior = LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course+2024',
            total_time_spent_minutes=120,
            completion_percentage=75.0
        )
        
        self.assertEqual(behavior.user, self.user)
        self.assertEqual(behavior.total_time_spent_minutes, 120)
        self.assertEqual(behavior.completion_percentage, 75.0)
        
    def test_unique_constraint(self):
        # Create first behavior
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course+2024',
            total_time_spent_minutes=60
        )
        
        # Creating second behavior with same user and course should fail
        with self.assertRaises(Exception):
            LearnerBehavior.objects.create(
                user=self.user,
                course_id='course-v1:test+course+2024',
                total_time_spent_minutes=90
            )


class LearningHoursRequirementTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.requirement = LearningHoursRequirement.objects.create(
            user=self.user,
            year=2024,
            required_hours=40,
            deadline=date.today() + timedelta(days=30)
        )
        
    def test_get_completed_hours(self):
        # Create some learning behavior
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course1+2024',
            total_time_spent_minutes=120  # 2 hours
        )
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course2+2024',
            total_time_spent_minutes=180  # 3 hours
        )
        
        completed_hours = self.requirement.get_completed_hours()
        self.assertEqual(completed_hours, 5.0)
        
    def test_get_progress_percentage(self):
        # Create learning behavior for 20 hours (50% of 40 required)
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course+2024',
            total_time_spent_minutes=1200  # 20 hours
        )
        
        progress = self.requirement.get_progress_percentage()
        self.assertEqual(progress, 50.0)
        
    def test_is_completed(self):
        # Initially not completed
        self.assertFalse(self.requirement.is_completed())
        
        # Add enough hours to complete
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course+2024',
            total_time_spent_minutes=2400  # 40 hours
        )
        
        self.assertTrue(self.requirement.is_completed())
        
    def test_is_overdue(self):
        # Not overdue initially
        self.assertFalse(self.requirement.is_overdue())
        
        # Make it overdue
        self.requirement.deadline = date.today() - timedelta(days=1)
        self.requirement.save()
        
        self.assertTrue(self.requirement.is_overdue())


class LearningHoursApprovalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.approver = User.objects.create_user(
            username='approver',
            email='approver@example.com'
        )
        self.requirement = LearningHoursRequirement.objects.create(
            user=self.user,
            year=2024,
            required_hours=40,
            deadline=date.today() + timedelta(days=30)
        )
        
    def test_create_approval_request(self):
        approval = LearningHoursApproval.objects.create(
            user=self.user,
            learning_requirement=self.requirement,
            requested_hours=5.0,
            notes="Attended external workshop"
        )
        
        self.assertEqual(approval.status, 'pending')
        self.assertEqual(approval.requested_hours, 5.0)
        self.assertIsNone(approval.approved_hours)
        
    def test_approve_request(self):
        approval = LearningHoursApproval.objects.create(
            user=self.user,
            learning_requirement=self.requirement,
            requested_hours=5.0
        )
        
        # Approve the request
        approval.status = 'approved'
        approval.approved_hours = 5.0
        approval.approver = self.approver
        approval.approved_date = timezone.now()
        approval.save()
        
        self.assertEqual(approval.status, 'approved')
        self.assertEqual(approval.approved_hours, 5.0)
        self.assertEqual(approval.approver, self.approver)
        self.assertIsNotNone(approval.approved_date)


class LearningHoursServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
    def test_track_time_spent(self):
        # Track time for a course
        LearningHoursService.track_time_spent(
            user=self.user,
            course_id='course-v1:test+course+2024',
            minutes_spent=60
        )
        
        behavior = LearnerBehavior.objects.get(
            user=self.user,
            course_id='course-v1:test+course+2024'
        )
        self.assertEqual(behavior.total_time_spent_minutes, 60)
        
        # Track more time for the same course
        LearningHoursService.track_time_spent(
            user=self.user,
            course_id='course-v1:test+course+2024',
            minutes_spent=30
        )
        
        behavior.refresh_from_db()
        self.assertEqual(behavior.total_time_spent_minutes, 90)
        
    def test_get_user_learning_hours(self):
        # Create some learning behaviors
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course1+2024',
            total_time_spent_minutes=120
        )
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+course2+2024',
            total_time_spent_minutes=180
        )
        
        total_hours = LearningHoursService.get_user_learning_hours(self.user)
        self.assertEqual(total_hours, 5.0)  # 300 minutes = 5 hours
        
    def test_request_hours_approval(self):
        # Create a requirement
        requirement = LearningHoursRequirement.objects.create(
            user=self.user,
            year=2024,
            required_hours=40,
            deadline=date.today() + timedelta(days=30)
        )
        
        # Request approval
        approval = LearningHoursService.request_hours_approval(
            user=self.user,
            learning_requirement=requirement,
            requested_hours=8.0,
            notes="External training course"
        )
        
        self.assertEqual(approval.user, self.user)
        self.assertEqual(approval.learning_requirement, requirement)
        self.assertEqual(approval.requested_hours, 8.0)
        self.assertEqual(approval.status, 'pending')
        self.assertEqual(approval.notes, "External training course")
