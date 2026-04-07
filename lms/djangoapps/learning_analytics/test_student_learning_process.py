"""Tests for student learning-process snapshot feature."""

import json
import tempfile

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot


class StudentLearningProcessImportCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_001', email='s1@example.com')

    def test_import_creates_snapshot(self):
        csv_content = (
            'student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'student_001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
        )
        schema = {
            'fields': [
                {'name': 'position', 'values': {'0': 'Chuyên viên'}},
                {'name': 'gender', 'values': {'1': 'Nữ'}},
                {'name': 'location', 'all_possible_values': {'9': 'Thái Bình'}},
                {'name': 'age', 'values': {'2': 'Trên 25 tuổi'}},
                {'name': 'job_title', 'values': {'1': 'Viên chức'}},
                {'name': 'experience', 'values': {'1': 'Từ 5 đến 10 năm'}},
            ]
        }

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as csv_file:
            csv_file.write(csv_content)
            csv_path = csv_file.name

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as schema_file:
            schema_file.write(json.dumps(schema, ensure_ascii=False))
            schema_path = schema_file.name

        call_command(
            'import_student_learning_process',
            '--csv-path',
            csv_path,
            '--schema-path',
            schema_path,
        )

        snapshot = StudentLearningProcessSnapshot.objects.get(student_id='student_001')
        self.assertEqual(snapshot.user, self.user)
        self.assertEqual(snapshot.position_code, 0)
        self.assertEqual(snapshot.location_code, 9)
        self.assertEqual(float(snapshot.final_score), 4.0)

    def test_import_skips_when_user_mapping_missing(self):
        csv_content = (
            'student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'student_999,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
        )
        schema = {
            'fields': [
                {'name': 'position', 'values': {'0': 'Chuyên viên'}},
                {'name': 'gender', 'values': {'1': 'Nữ'}},
                {'name': 'location', 'all_possible_values': {'9': 'Thái Bình'}},
                {'name': 'age', 'values': {'2': 'Trên 25 tuổi'}},
                {'name': 'job_title', 'values': {'1': 'Viên chức'}},
                {'name': 'experience', 'values': {'1': 'Từ 5 đến 10 năm'}},
            ]
        }

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as csv_file:
            csv_file.write(csv_content)
            csv_path = csv_file.name

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as schema_file:
            schema_file.write(json.dumps(schema, ensure_ascii=False))
            schema_path = schema_file.name

        call_command(
            'import_student_learning_process',
            '--csv-path',
            csv_path,
            '--schema-path',
            schema_path,
        )

        self.assertFalse(StudentLearningProcessSnapshot.objects.filter(student_id='student_999').exists())


class StudentLearningProcessAPIServiceSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_001', email='s1@example.com')
        self.staff = User.objects.create_user(username='admin_1', email='a1@example.com', is_staff=True)
        StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_001',
            position_code=0,
            position_text='Chuyên viên',
            gender_code=1,
            gender_text='Nữ',
            location_code=9,
            location_text='Thái Bình',
            age_code=2,
            age_text='Trên 25 tuổi',
            job_title_code=1,
            job_title_text='Viên chức',
            experience_code=1,
            experience_text='Từ 5 đến 10 năm',
            week_1='2.50',
            week_2='2.25',
            week_3='1.00',
            vle_1=53,
            vle_2=17,
            vle_3=102,
            final_score='4.00',
            source_file='dataset/log.csv',
            source_row_number=2,
        )

    def test_self_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/learning_analytics/student-learning-process/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['student_id'], 'student_001')

    def test_staff_list_endpoint_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/learning_analytics/student-learning-process/')
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.staff)
        response = self.client.get('/api/learning_analytics/student-learning-process/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
