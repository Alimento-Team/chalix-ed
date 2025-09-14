# Generated migration to add LocalCourse model
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0041_add_course_type_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('short_description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_courses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Local Course',
                'verbose_name_plural': 'Local Courses',
            },
        ),
    ]
