"""Tests for Chalix survey authoring APIs."""

import json

from django.test import TestCase

from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixSurveyChoice, ChalixUserRole
from common.djangoapps.student.tests.factories import UserFactory


class ChalixSurveyApiTests(TestCase):
    """Covers permission, validation, sanitization, and link behavior for survey endpoints."""

    def setUp(self):
        self.org = ChalixOrganization.objects.create(
            name='Test Organization',
            display_name='Test Organization',
            code='TESTORG',
            is_active=True,
        )

        self.bo_user = UserFactory()
        ChalixUserRole.objects.create(user=self.bo_user, role='bo', is_active=True)

        self.co_quan_user = UserFactory()
        ChalixUserRole.objects.create(
            user=self.co_quan_user,
            role='co_quan',
            organization=self.org,
            is_active=True,
        )

        self.giang_vien_user = UserFactory()
        ChalixUserRole.objects.create(
            user=self.giang_vien_user,
            role='giang_vien',
            organization=self.org,
            is_active=True,
        )

        self.course_key = 'course-v1:TestOrg+Survey101+2026'
        self.get_url = f'/api/chalix/dashboard/survey/get/{self.course_key}/'
        self.save_url = f'/api/chalix/dashboard/survey/save/{self.course_key}/'
        self.generate_link_url = f'/api/chalix/dashboard/survey/generate-link/{self.course_key}/'

    def _post_json(self, user, url, data):
        self.client.force_login(user)
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_unauthenticated_requests_are_rejected(self):
        response = self.client.get(self.get_url)
        self.assertIn(response.status_code, [302, 403])

    def test_bo_can_save_and_read_survey(self):
        save_response = self._post_json(
            self.bo_user,
            self.save_url,
            {
                'title': 'Nhu cau hoc tap',
                'choices': [
                    {'name': 'Chuong trinh A', 'detail_html': '<p>Mo ta A</p>'},
                    {'name': 'Chuong trinh B', 'detail_html': '<p>Mo ta B</p>'},
                ],
            },
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(save_response.json()['success'])

        self.client.force_login(self.bo_user)
        get_response = self.client.get(self.get_url)
        self.assertEqual(get_response.status_code, 200)
        data = get_response.json()
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['survey'])
        self.assertEqual(len(data['survey']['choices']), 2)

    def test_co_quan_can_save_survey(self):
        response = self._post_json(
            self.co_quan_user,
            self.save_url,
            {
                'choices': [
                    {'name': 'Chuong trinh co_quan', 'detail_html': '<p>Hop le</p>'},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_giang_vien_cannot_save_or_generate_link(self):
        save_response = self._post_json(
            self.giang_vien_user,
            self.save_url,
            {
                'choices': [
                    {'name': 'Chuong trinh GV', 'detail_html': '<p>No access</p>'},
                ],
            },
        )
        self.assertEqual(save_response.status_code, 403)

        link_response = self._post_json(self.giang_vien_user, self.generate_link_url, {})
        self.assertEqual(link_response.status_code, 403)

    def test_save_rejects_empty_name(self):
        response = self._post_json(
            self.bo_user,
            self.save_url,
            {
                'choices': [
                    {'name': '', 'detail_html': '<p>Co mo ta</p>'},
                ],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_save_rejects_empty_detail(self):
        response = self._post_json(
            self.bo_user,
            self.save_url,
            {
                'choices': [
                    {'name': 'Chuong trinh', 'detail_html': ''},
                ],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_generate_link_returns_tokenized_url(self):
        response = self._post_json(self.bo_user, self.generate_link_url, {})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('/survey/', data['link'])
        self.assertIn(data['token'], data['link'])

    def test_save_sanitizes_xss_in_detail_html(self):
        response = self._post_json(
            self.bo_user,
            self.save_url,
            {
                'choices': [
                    {'name': 'CT XSS', 'detail_html': '<script>alert("xss")</script><p>ok</p>'},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)

        saved_choice = ChalixSurveyChoice.objects.get(name='CT XSS')
        self.assertNotIn('<script', saved_choice.detail_html)
        self.assertIn('<p>ok</p>', saved_choice.detail_html)
