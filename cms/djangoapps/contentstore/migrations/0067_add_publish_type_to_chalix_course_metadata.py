# Generated manually on 2025-11-10
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0066_alter_finalevaluation_evaluation_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chalixcoursemetadata',
            name='publish_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('elective', 'Khoá học chung cho công chức, viên chức của bộ'),
                    ('mandatory', 'Khoá học bắt buộc cho toàn bộ')
                ],
                help_text="Type of course publish requirement for 'bộ' role courses",
                max_length=20,
                null=True,
                verbose_name='Loại yêu cầu khoá học'
            ),
        ),
    ]
