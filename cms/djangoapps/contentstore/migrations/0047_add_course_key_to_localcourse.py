# Generated migration to add course_key to LocalCourse
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0046_add_template_fields_to_localcourse'),
    ]

    operations = [
        migrations.AddField(
            model_name='localcourse',
            name='course_key',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Modulestore CourseKey string'),
        ),
    ]
