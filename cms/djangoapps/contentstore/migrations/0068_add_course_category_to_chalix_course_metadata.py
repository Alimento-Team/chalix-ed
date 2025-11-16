# Generated manually on 2025-11-16
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0067_add_publish_type_to_chalix_course_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='chalixcoursemetadata',
            name='course_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('elective', 'Khoá học tự chọn CC, VC Bộ'),
                    ('mandatory', 'Khoá học bắt buộc cho CC, VC Bộ')
                ],
                help_text="Course category for 'bộ' role courses - determines course classification",
                max_length=20,
                null=True,
                verbose_name='Loại khoá học'
            ),
        ),
        # Update existing publish_type choices to match new terminology
        migrations.AlterField(
            model_name='chalixcoursemetadata',
            name='publish_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('elective', 'Khoá học tự chọn CC, VC Bộ'),
                    ('mandatory', 'Khoá học bắt buộc cho CC, VC Bộ')
                ],
                help_text="Type of course publish requirement for 'bộ' role courses (legacy field)",
                max_length=20,
                null=True,
                verbose_name='Loại yêu cầu khoá học'
            ),
        ),
        # Migrate data from publish_type to course_category
        migrations.RunSQL(
            sql="""
                UPDATE contentstore_chalixcoursemetadata 
                SET course_category = publish_type 
                WHERE publish_type IS NOT NULL AND course_category IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
