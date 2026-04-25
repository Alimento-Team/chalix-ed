"""Tests for the CMS prep command that normalizes learning-process import data."""

import csv
import tempfile

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole
from common.djangoapps.student.models import UserProfile


class PrepareStudentLearningProcessImportCommandTests(TestCase):
    def setUp(self):
        ChalixOrganization.objects.create(
            code='40000000',
            name='Học viện chiến lược, bồi dưỡng cán bộ xây dựng',
            display_name='Học viện chiến lược, bồi dưỡng cán bộ xây dựng',
            is_active=True,
        )

    def test_prepare_command_syncs_user_and_writes_normalized_csv(self):
        csv_content = (
            'course_id,id,username,name,date_of_birth,position,gender,location,email,age,job_title,experience,co_quan,total_studied_time,completed_percentage,status,week_1,week_2,week_3,video_1,quiz_1,resource_1,video_2,quiz_2,resource_2,video_3,quiz_3,resource_3,final_score\n'
            'chalix+course_6f694e29+2024,20260001,20260001,Đoàn Xuân Hòa,1979,Nhân viên,Nữ,Điện Biên,20260001@itg-acst.edu.vn,Trên 25 tuổi,Viên chức,Từ 5 đến 10 năm,"Học viện chiến lược, bồi dưỡng cán bộ xây dựng",40,100%,Hoàn thành,2.5,2.25,1,5,14,34,12,1,4,20,7,75,4\n'
        )

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as csv_file:
            csv_file.write(csv_content)
            csv_path = csv_file.name

        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as output_file:
            output_path = output_file.name

        call_command(
            'prepare_student_learning_process_import',
            '--csv-path',
            csv_path,
            '--output-path',
            output_path,
            '--create-missing-users',
        )

        user = User.objects.get(username='20260001')
        self.assertEqual(user.email, '20260001@itg-acst.edu.vn')

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.name, 'Đoàn Xuân Hòa')
        self.assertEqual(profile.year_of_birth, 1979)
        self.assertEqual(profile.get_meta()['ngay_sinh'], '1979')
        self.assertEqual(profile.get_meta()['ten_co_quan'], 'Học viện chiến lược, bồi dưỡng cán bộ xây dựng')
        self.assertEqual(profile.get_meta()['don_vi_cong_tac'], 'Học viện chiến lược, bồi dưỡng cán bộ xây dựng')

        self.assertTrue(
            ChalixUserRole.objects.filter(
                user=user,
                role='cong_chuc',
                organization__name='Học viện chiến lược, bồi dưỡng cán bộ xây dựng',
                is_active=True,
            ).exists()
        )

        with open(output_path, 'r', encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['student_id'], '20260001')
        self.assertEqual(rows[0]['external_user_id'], '20260001')
        self.assertEqual(rows[0]['vle_1'], '53')
        self.assertEqual(rows[0]['vle_2'], '17')
        self.assertEqual(rows[0]['vle_3'], '102')
        self.assertEqual(rows[0]['completed_percentage'], '100')
        self.assertEqual(rows[0]['status'], 'Hoàn thành')