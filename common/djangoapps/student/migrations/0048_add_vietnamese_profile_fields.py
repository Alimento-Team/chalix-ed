"""
Migration to support Vietnamese user profile fields in UserProfile.meta.

This migration doesn't change the schema - it documents that we're now storing
additional Vietnamese-specific fields in the existing UserProfile.meta JSON field:

Fields to be stored in meta:
- ngay_sinh: Date of birth (full date, not just year)
- cccd: Citizen ID number
- ngay_cap_cccd: Date CCCD was issued
- don_vi_cong_tac: Work unit/organization
- que_quan: Hometown/Place of origin
- dan_toc: Ethnicity
- ghi_chu: Notes
- avatar_url: Avatar image URL
- vi_tri_viec_lam: Job position
- chuc_vu: Job title/rank
- nguoi_nhan_bang: Certificate recipient name
- so_chung_chi: Certificate number
- ten_khoa_hoc: Course name
- thoi_gian_hoc: Study duration
- nam_tot_nghiep: Graduation year
- so_tiet_quy_doi: Converted credit hours
- loai_hinh_dao_tao: Training type
- noi_sinh: Place of birth
- dia_chi: Full address
- so_nam_cong_tac: Years of service
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0047_migrate_custom_profile_fields_to_meta'),
    ]

    operations = [
        # This is a data migration - no schema changes needed
        # The UserProfile.meta field already exists and can store our JSON data
    ]
