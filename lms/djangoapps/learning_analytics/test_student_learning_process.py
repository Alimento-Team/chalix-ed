"""Tests for student learning-process snapshot feature."""

import json
import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.learning_analytics.models import StudentLearningProcessSnapshot
from lms.djangoapps.learning_analytics.models import LearnerBehavior
from lms.djangoapps.courseware.models import StudentModule
from common.djangoapps.student.models.course_enrollment import CourseEnrollment
from common.djangoapps.student.models import UserProfile


class StudentLearningProcessImportCommandTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_chalix_tables()

    @classmethod
    def _ensure_chalix_tables(cls):
        existing_tables = set(connection.introspection.table_names())
        with connection.cursor() as cursor:
            if 'contentstore_chalixorganization' not in existing_tables:
                cursor.execute(
                    """
                    CREATE TABLE contentstore_chalixorganization (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        display_name VARCHAR(255) NOT NULL,
                        code VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT NOT NULL DEFAULT '',
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        admin_id INTEGER NULL,
                        parent_id INTEGER NULL,
                        created_at DATETIME NULL,
                        updated_at DATETIME NULL
                    )
                    """
                )
            if 'contentstore_chalixuserrole' not in existing_tables:
                cursor.execute(
                    """
                    CREATE TABLE contentstore_chalixuserrole (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        organization_id INTEGER NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NULL,
                        updated_at DATETIME NULL,
                        created_by_id INTEGER NULL
                    )
                    """
                )

    def setUp(self):
        self.user = User.objects.create_user(username='student_001', email='s1@example.com')
        self.course_id = 'course-v1:chalix+course_6f694e29+2024'

    def test_import_creates_snapshot(self):
        csv_content = (
            'course_id,student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'chalix+course_6f694e29+2024,student_001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
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
        self.assertEqual(snapshot.course_id, self.course_id)
        self.assertEqual(snapshot.position_code, 0)
        self.assertEqual(snapshot.location_code, 9)
        self.assertEqual(float(snapshot.final_score), 4.0)

    def test_import_real_header_syncs_account_org_and_progress_fields(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO contentstore_chalixorganization
                    (name, display_name, code, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    'Học viện chiến lược, bồi dưỡng cán bộ xây dựng',
                    'Học viện chiến lược, bồi dưỡng cán bộ xây dựng',
                    '40000000',
                    '',
                    True,
                    timezone.now(),
                    timezone.now(),
                ],
            )
        csv_content = (
            'course_id,id,username,name,date_of_birth,position,gender,location,email,age,job_title,experience,co_quan,total_studied_time,completed_percentage,status,week_1,week_2,week_3,video_1,quiz_1,resource_1,video_2,quiz_2,resource_2,video_3,quiz_3,resource_3,final_score\n'
            'chalix+course_6f694e29+2024,20260001,20260001,Đoàn Xuân Hòa,1979,Nhân viên,Nữ,Điện Biên,20260001@itg-acst.edu.vn,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,"Học viện chiến lược, bồi dưỡng cán bộ xây dựng",40,100%,Hoàn thành,2.5,2.25,1,5,14,34,12,1,4,20,7,75,4\n'
        )
        schema = {
            'fields': [
                {'name': 'position', 'values': {'0': 'Nhân viên'}},
                {'name': 'gender', 'values': {'1': 'Nữ'}},
                {'name': 'location', 'all_possible_values': {'22': 'Điện Biên'}},
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
            '--create-missing-users',
        )

        snapshot = StudentLearningProcessSnapshot.objects.get(student_id='20260001')
        self.assertEqual(snapshot.external_user_id, '20260001')
        self.assertEqual(snapshot.course_id, 'course-v1:chalix+course_6f694e29+2024')
        self.assertEqual(snapshot.vle_1, 53)
        self.assertEqual(snapshot.vle_2, 17)
        self.assertEqual(snapshot.vle_3, 102)
        self.assertEqual(float(snapshot.total_studied_time), 40.0)
        self.assertEqual(snapshot.completed_percentage, 100)
        self.assertEqual(snapshot.status, 'Hoàn thành')

        imported_user = User.objects.get(username='20260001')
        self.assertEqual(imported_user.email, '20260001@itg-acst.edu.vn')

        profile = UserProfile.objects.get(user=imported_user)
        self.assertEqual(profile.name, 'Đoàn Xuân Hòa')
        self.assertEqual(profile.year_of_birth, 1979)
        self.assertEqual(profile.get_meta()['ngay_sinh'], '1979')
        self.assertEqual(profile.get_meta()['ten_co_quan'], 'Học viện chiến lược, bồi dưỡng cán bộ xây dựng')
        self.assertEqual(profile.get_meta()['don_vi_cong_tac'], 'Học viện chiến lược, bồi dưỡng cán bộ xây dựng')

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM contentstore_chalixuserrole ur
                INNER JOIN contentstore_chalixorganization org ON org.id = ur.organization_id
                WHERE ur.user_id = %s AND ur.role = %s AND ur.is_active = TRUE AND org.name = %s
                """,
                [imported_user.id, 'cong_chuc', 'Học viện chiến lược, bồi dưỡng cán bộ xây dựng'],
            )
            role_count = cursor.fetchone()[0]
        self.assertEqual(role_count, 1)
        self.assertTrue(
            CourseEnrollment.objects.filter(
                user=imported_user,
                course_id=CourseKey.from_string('course-v1:chalix+course_6f694e29+2024'),
                is_active=True,
            ).exists()
        )

    def test_import_prepared_input_creates_snapshot_and_enrollment_only(self):
        prepared_user = User.objects.create_user(username='prepared_001', email='prepared@example.com')
        UserProfile.objects.create(user=prepared_user, name='Prepared User', year_of_birth=1980)

        csv_content = (
            'course_id,student_id,external_user_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,total_studied_time,completed_percentage,status,final_score,source_row_number\n'
            'chalix+course_6f694e29+2024,prepared_001,raw-001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,40,100,Hoàn thành,4.0,88\n'
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
            '--prepared-input',
        )

        snapshot = StudentLearningProcessSnapshot.objects.get(student_id='prepared_001')
        self.assertEqual(snapshot.external_user_id, 'raw-001')
        self.assertEqual(snapshot.source_row_number, 88)
        self.assertEqual(float(snapshot.total_studied_time), 40.0)
        self.assertEqual(snapshot.completed_percentage, 100)

        prepared_user.refresh_from_db()
        self.assertEqual(prepared_user.email, 'prepared@example.com')
        self.assertEqual(prepared_user.profile.name, 'Prepared User')
        self.assertTrue(
            CourseEnrollment.objects.filter(
                user=prepared_user,
                course_id=CourseKey.from_string('course-v1:chalix+course_6f694e29+2024'),
                is_active=True,
            ).exists()
        )

    def test_import_derives_vle_creates_profile_and_enrollment(self):
        csv_content = (
            'course_id,student_id,name,date_of_birth,position,gender,location,age,job_title,experience,week_1,week_2,week_3,video_1,quiz_1,resource_1,video_2,quiz_2,resource_2,video_3,quiz_3,resource_3,final_score\n'
            'chalix+course_6f694e29+2024,student_900,,,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,5,14,34,12,1,4,20,7,75,4.0\n'
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
            '--create-missing-users',
        )

        snapshot = StudentLearningProcessSnapshot.objects.get(student_id='student_900')
        self.assertEqual(snapshot.course_id, 'course-v1:chalix+course_6f694e29+2024')
        self.assertEqual(snapshot.vle_1, 53)
        self.assertEqual(snapshot.vle_2, 17)
        self.assertEqual(snapshot.vle_3, 102)

        imported_user = User.objects.get(username='student_900')
        profile = UserProfile.objects.get(user=imported_user)
        self.assertEqual(profile.name, 'student_900')
        self.assertEqual(profile.year_of_birth, min(UserProfile.VALID_YEARS))
        self.assertTrue(
            CourseEnrollment.objects.filter(
                user=imported_user,
                course_id=CourseKey.from_string('course-v1:chalix+course_6f694e29+2024'),
                is_active=True,
            ).exists()
        )

    def test_replace_existing_replaces_rows_for_imported_students(self):
        StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_001',
            course_id='course-v1:test+old+2026',
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
            week_1='1.00',
            week_2='1.00',
            week_3='1.00',
            vle_1=1,
            vle_2=1,
            vle_3=1,
            final_score='1.00',
            source_file='dataset/log.csv',
            source_row_number=1,
        )

        other_user = User.objects.create_user(username='student_777', email='s777@example.com')
        StudentLearningProcessSnapshot.objects.create(
            user=other_user,
            student_id='student_777',
            course_id='course-v1:test+keep+2026',
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
            week_1='1.00',
            week_2='1.00',
            week_3='1.00',
            vle_1=1,
            vle_2=1,
            vle_3=1,
            final_score='1.00',
            source_file='dataset/log.csv',
            source_row_number=1,
        )

        csv_content = (
            'course_id,student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'chalix+course_6f694e29+2024,student_001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
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
            '--replace-existing',
        )

        self.assertEqual(
            StudentLearningProcessSnapshot.objects.filter(student_id='student_001').count(),
            1,
        )
        self.assertEqual(
            StudentLearningProcessSnapshot.objects.get(student_id='student_001').course_id,
            'course-v1:chalix+course_6f694e29+2024',
        )
        self.assertTrue(StudentLearningProcessSnapshot.objects.filter(student_id='student_777').exists())

    def test_import_skips_when_user_mapping_missing(self):
        csv_content = (
            'course_id,student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'chalix+course_6f694e29+2024,student_999,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
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

    def test_import_allows_multiple_courses_for_same_student(self):
        csv_content = (
            'course_id,student_id,position,gender,location,age,job_title,experience,week_1,week_2,week_3,vle_1,vle_2,vle_3,final_score\n'
            'course-v1:test+alpha+2026,student_001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,2.5,2.25,1.0,53,17,102,4.0\n'
            'course-v1:test+beta+2026,student_001,Chuyên viên,Nữ,Thái Bình,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,3.5,3.25,2.0,63,27,112,6.0\n'
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

        rows = StudentLearningProcessSnapshot.objects.filter(student_id='student_001').order_by('course_id')
        self.assertEqual(rows.count(), 2)
        self.assertEqual(rows[0].course_id, 'course-v1:test+alpha+2026')
        self.assertEqual(rows[1].course_id, 'course-v1:test+beta+2026')


class StudentLearningProcessAPIServiceSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_001', email='s1@example.com')
        self.staff = User.objects.create_user(username='admin_1', email='a1@example.com', is_staff=True)
        self.course_id = 'chalix+course_6f694e29+2024'
        StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_001',
            course_id=self.course_id,
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
        response = self.client.get(
            '/api/learning_analytics/student-learning-process/me/',
            {'course_id': self.course_id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['student_id'], 'student_001')
        self.assertEqual(response.json()['course_id'], self.course_id)
        self.assertEqual(response.json()['score_type'], 'actual')

    def test_self_endpoint_without_course_id_returns_empty_payload(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/learning_analytics/student-learning-process/me/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, 'null')

    def test_staff_list_endpoint_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/learning_analytics/student-learning-process/')
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.staff)
        response = self.client.get('/api/learning_analytics/student-learning-process/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)


class StudentLearningProcessVLEAutoTrackingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_002', email='s2@example.com')
        self.course_key = CourseKey.from_string('course-v1:test+learning+2026')
        CourseEnrollment.enroll(self.user, self.course_key, check_access=False)

        self.snapshot = StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_002',
            course_id=str(self.course_key),
            position_code=0,
            position_text='Chuyen vien',
            gender_code=1,
            gender_text='Nu',
            location_code=9,
            location_text='Thai Binh',
            age_code=2,
            age_text='Tren 25 tuoi',
            job_title_code=1,
            job_title_text='Vien chuc',
            experience_code=1,
            experience_text='Tu 5 den 10 nam',
            week_1='2.00',
            week_2='2.00',
            week_3='2.00',
            vle_1=10,
            vle_2=20,
            vle_3=30,
            final_score='4.00',
            source_file='dataset/log.csv',
            source_row_number=2,
        )

    def _open_material(self, block_type, block_id):
        StudentModule.objects.create(
            module_type=block_type,
            module_state_key=self.course_key.make_usage_key(block_type, block_id),
            student=self.user,
            course_id=self.course_key,
        )

    def test_opening_material_increments_week_1_vle(self):
        self._open_material('html', 'unit-week-1')
        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.vle_1, 11)
        self.assertEqual(self.snapshot.vle_2, 20)
        self.assertEqual(self.snapshot.vle_3, 30)

    def test_opening_material_increments_week_2_vle(self):
        CourseEnrollment.objects.filter(user=self.user, course_id=self.course_key).update(
            created=timezone.now() - timezone.timedelta(days=8)
        )

        self._open_material('video', 'unit-week-2')
        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.vle_1, 10)
        self.assertEqual(self.snapshot.vle_2, 21)
        self.assertEqual(self.snapshot.vle_3, 30)

    def test_opening_material_increments_week_3_vle(self):
        CourseEnrollment.objects.filter(user=self.user, course_id=self.course_key).update(
            created=timezone.now() - timezone.timedelta(days=15)
        )

        self._open_material('problem', 'unit-week-3')
        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.vle_1, 10)
        self.assertEqual(self.snapshot.vle_2, 20)
        self.assertEqual(self.snapshot.vle_3, 31)

    def test_non_tracked_module_type_does_not_increment_vle(self):
        self._open_material('sequential', 'unit-seq')
        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.vle_1, 10)
        self.assertEqual(self.snapshot.vle_2, 20)
        self.assertEqual(self.snapshot.vle_3, 30)


class MaterialOpenEventAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_003', email='s3@example.com')
        self.course_key = CourseKey.from_string('course-v1:test+material+2026')
        CourseEnrollment.enroll(self.user, self.course_key, check_access=False)
        self.snapshot = StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_003',
            course_id=str(self.course_key),
            position_code=0,
            position_text='Chuyen vien',
            gender_code=1,
            gender_text='Nu',
            location_code=9,
            location_text='Thai Binh',
            age_code=2,
            age_text='Tren 25 tuoi',
            job_title_code=1,
            job_title_text='Vien chuc',
            experience_code=1,
            experience_text='Tu 5 den 10 nam',
            week_1='2.00',
            week_2='2.00',
            week_3='2.00',
            vle_1=1,
            vle_2=2,
            vle_3=3,
            final_score='4.00',
            source_file='dataset/log.csv',
            source_row_number=2,
        )
        self.client.force_login(self.user)

    def test_every_call_increments_weekly_vle(self):
        endpoint = '/api/learning_analytics/material-open/'
        payload = {
            'course_id': str(self.course_key),
            'module_type': 'video',
        }

        first = self.client.post(endpoint, payload, content_type='application/json')
        self.assertEqual(first.status_code, 200)
        second = self.client.post(endpoint, payload, content_type='application/json')
        self.assertEqual(second.status_code, 200)

        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.vle_1, 3)
        self.assertEqual(self.snapshot.vle_2, 2)
        self.assertEqual(self.snapshot.vle_3, 3)

    def test_missing_course_id_returns_400(self):
        response = self.client.post(
            '/api/learning_analytics/material-open/',
            {'module_type': 'html'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class LearningAnalyticsDashboardBreakdownTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_004', email='s4@example.com')
        self.client.force_login(self.user)
        StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_004',
            course_id='chalix+course_6f694e29+2024',
            position_code=0,
            position_text='Chuyen vien',
            gender_code=1,
            gender_text='Nu',
            location_code=9,
            location_text='Thai Binh',
            age_code=2,
            age_text='Tren 25 tuoi',
            job_title_code=1,
            job_title_text='Vien chuc',
            experience_code=1,
            experience_text='Tu 5 den 10 nam',
            week_1='2.00',
            week_2='2.00',
            week_3='2.00',
            vle_1=10,
            vle_2=12,
            vle_3=8,
            final_score='4.00',
            source_file='dataset/log.csv',
            source_row_number=2,
        )
        LearnerBehavior.objects.create(
            user=self.user,
            course_id='course-v1:test+sample+2026',
            videos_watched=7,
            problems_attempted=5,
        )

    def test_dashboard_returns_vle_breakdown(self):
        response = self.client.get('/api/learning_analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('vle_breakdown', payload)
        self.assertEqual(payload['vle_breakdown']['total_vle'], 30)
        self.assertEqual(payload['vle_breakdown']['videos_opened'], 7)
        self.assertEqual(payload['vle_breakdown']['quizzes_opened'], 5)
        self.assertEqual(payload['vle_breakdown']['materials_opened'], 18)


class StudentLearningProcessPredictionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_pred', email='sp@example.com')
        self.client.force_login(self.user)
        self.course_id = 'chalix+course_6f694e29+2024'
        self.snapshot = StudentLearningProcessSnapshot.objects.create(
            user=self.user,
            student_id='student_pred',
            course_id=self.course_id,
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
            final_score=None,
            source_file='dataset/log.csv',
            source_row_number=2,
        )

    @patch('lms.djangoapps.learning_analytics.services.requests.post')
    def test_self_endpoint_refreshes_prediction_when_enabled(self, mock_post):
        with self.settings(
            LEARNING_ANALYTICS_PREDICTION_ENABLED=True,
            LEARNING_ANALYTICS_PREDICTION_MODE='mla',
            LEARNING_ANALYTICS_MLA_PREDICTION_URL='http://predictor/mla-prediction',
            LEARNING_ANALYTICS_PREDICTION_TIMEOUT_SECONDS=3,
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                'week_number': 3,
                'predicted_score': 7.45,
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.get(
                '/api/learning_analytics/student-learning-process/me/',
                {'course_id': self.course_id},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['score_type'], 'predicted')
        self.assertEqual(float(payload['predicted_final_score']), 7.45)
        self.assertEqual(float(payload['effective_final_score']), 7.45)

        self.snapshot.refresh_from_db()
        self.assertEqual(float(self.snapshot.predicted_final_score), 7.45)
        self.assertEqual(self.snapshot.prediction_source, 'mla')
        self.assertEqual(self.snapshot.prediction_week, 3)
        self.assertEqual(mock_post.call_count, 1)

    @patch('lms.djangoapps.learning_analytics.services.requests.post')
    def test_self_endpoint_skips_prediction_call_when_input_unchanged(self, mock_post):
        with self.settings(
            LEARNING_ANALYTICS_PREDICTION_ENABLED=True,
            LEARNING_ANALYTICS_PREDICTION_MODE='mla',
            LEARNING_ANALYTICS_MLA_PREDICTION_URL='http://predictor/mla-prediction',
            LEARNING_ANALYTICS_PREDICTION_TIMEOUT_SECONDS=3,
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                'week_number': 3,
                'predicted_score': 6.4,
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            first = self.client.get(
                '/api/learning_analytics/student-learning-process/me/',
                {'course_id': self.course_id},
            )
            second = self.client.get(
                '/api/learning_analytics/student-learning-process/me/',
                {'course_id': self.course_id},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(mock_post.call_count, 1)

    @patch('lms.djangoapps.learning_analytics.services.requests.post')
    def test_self_endpoint_retries_prediction_after_snapshot_change(self, mock_post):
        with self.settings(
            LEARNING_ANALYTICS_PREDICTION_ENABLED=True,
            LEARNING_ANALYTICS_PREDICTION_MODE='mla',
            LEARNING_ANALYTICS_MLA_PREDICTION_URL='http://predictor/mla-prediction',
            LEARNING_ANALYTICS_PREDICTION_TIMEOUT_SECONDS=3,
        ):
            mock_response_1 = Mock()
            mock_response_1.json.return_value = {
                'week_number': 3,
                'predicted_score': 6.0,
            }
            mock_response_1.raise_for_status.return_value = None

            mock_response_2 = Mock()
            mock_response_2.json.return_value = {
                'week_number': 3,
                'predicted_score': 6.8,
            }
            mock_response_2.raise_for_status.return_value = None

            mock_post.side_effect = [mock_response_1, mock_response_2]

            self.client.get(
                '/api/learning_analytics/student-learning-process/me/',
                {'course_id': self.course_id},
            )
            self.snapshot.refresh_from_db()
            self.snapshot.vle_3 = self.snapshot.vle_3 + 1
            self.snapshot.save(update_fields=['vle_3', 'updated_at'])

            response = self.client.get(
                '/api/learning_analytics/student-learning-process/me/',
                {'course_id': self.course_id},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_post.call_count, 2)
        self.snapshot.refresh_from_db()
        self.assertEqual(float(self.snapshot.predicted_final_score), 6.8)
