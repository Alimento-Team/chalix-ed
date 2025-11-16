# Generated migration for adding ProfessionalField model and linking it to ChalixCourseMetadata

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0068_add_course_category_to_chalix_course_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfessionalField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the professional field (e.g., \'Y tế\', \'Giáo dục\')', max_length=200, verbose_name='Professional Field Name')),
                ('org', models.CharField(db_index=True, help_text='Organization that this professional field belongs to', max_length=255, verbose_name='Organization')),
                ('description', models.TextField(blank=True, help_text='Optional description of this professional field', verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this professional field is available for selection', verbose_name='Is Active')),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='Order in which this field appears in dropdowns (lower numbers first)', verbose_name='Sort Order')),
                ('created_by', models.CharField(help_text='Username of the user who created this field', max_length=255, verbose_name='Created By')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Professional Field',
                'verbose_name_plural': 'Professional Fields',
                'ordering': ['org', 'sort_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='chalixcoursemetadata',
            name='professional_field',
            field=models.ForeignKey(blank=True, help_text='Professional field/domain that this course belongs to', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='contentstore.professionalfield', verbose_name='Lĩnh vực chuyên môn'),
        ),
        migrations.AlterUniqueTogether(
            name='professionalfield',
            unique_together={('name', 'org')},
        ),
    ]
