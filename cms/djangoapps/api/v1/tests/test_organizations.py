from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from cms.djangoapps.contentstore.models import Organization
from django.contrib.auth.models import User


class OrganizationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        self.non_admin = User.objects.create_user(username='user', email='user@example.com', password='pass')
        self.url = '/api/v1/organizations/'

    def test_admin_can_list_and_create_organization(self):
        self.client.force_authenticate(self.admin_user)
        # initially none
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        resp = self.client.post(self.url, {'name': 'Cơ quan A'}, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['name'], 'Cơ quan A')

        # now list should contain one
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.json()), 1)

    def test_non_admin_cannot_create(self):
        self.client.force_authenticate(self.non_admin)
        resp = self.client.post(self.url, {'name': 'Cơ quan B'}, format='json')
        self.assertIn(resp.status_code, (401, 403))
