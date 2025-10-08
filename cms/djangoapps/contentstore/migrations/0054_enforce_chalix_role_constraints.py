# Generated manually for Chalix role system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0053_rename_contentstore_chalixquiz_course_key_is_active_idx_contentstor_course__eee874_idx_and_more'),
    ]

    operations = [
        # No changes needed - the model already has the correct Vietnamese role choices
        # This migration ensures the role system is properly documented
        
        # Note: Database-level constraint for single 'bo' account removed due to MySQL limitations
        # Constraint is enforced at application level in ChalixUserRole model and admin
        
        # Add helpful comments
        migrations.RunSQL(
            """
            ALTER TABLE contentstore_chalixuserrole 
            MODIFY COLUMN role VARCHAR(20) COMMENT 'Role types: bo (Department-1 account), co_quan (Organization-multiple), giang_vien (Instructor-multiple), cong_chuc (Learner-multiple)';
            """,
            reverse_sql=""
        ),
    ]