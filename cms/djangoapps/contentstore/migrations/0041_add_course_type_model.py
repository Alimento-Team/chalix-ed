# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0011_enable_markdown_editor_flag_by_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The display name for this course type', max_length=100, verbose_name='Course Type Name')),
                ('description', models.TextField(blank=True, help_text='Optional description of this course type', verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this course type is available for selection', verbose_name='Is Active')),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='Order in which this type appears in the dropdown (lower numbers first)', verbose_name='Sort Order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Course Type',
                'verbose_name_plural': 'Course Types',
                'ordering': ['sort_order', 'name'],
            },
        ),
    ]
