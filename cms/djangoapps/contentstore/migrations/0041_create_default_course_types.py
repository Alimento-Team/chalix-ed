# Generated manually
from django.db import migrations


def create_default_course_types(apps, schema_editor):
    """Create default course types for Vietnamese education system"""
    CourseType = apps.get_model('contentstore', 'CourseType')

    default_types = [
        {
            'name': 'Khóa học chung',
            'description': 'Khóa học cơ bản dành cho tất cả học viên',
            'sort_order': 1,
            'is_active': True
        },
        {
            'name': 'Khóa học chuyên biệt',
            'description': 'Khóa học chuyên sâu cho một lĩnh vực cụ thể',
            'sort_order': 2,
            'is_active': True
        },
        {
            'name': 'Khóa học nâng cao',
            'description': 'Khóa học nâng cao cho học viên có kinh nghiệm',
            'sort_order': 3,
            'is_active': True
        },
        {
            'name': 'Khóa học thực hành',
            'description': 'Khóa học tập trung vào thực hành và ứng dụng',
            'sort_order': 4,
            'is_active': True
        },
        {
            'name': 'Khóa học nghiên cứu',
            'description': 'Khóa học dành cho nghiên cứu và phát triển',
            'sort_order': 5,
            'is_active': True
        }
    ]

    for course_type_data in default_types:
        CourseType.objects.get_or_create(
            name=course_type_data['name'],
            defaults=course_type_data
        )


def remove_default_course_types(apps, schema_editor):
    """Remove default course types"""
    CourseType = apps.get_model('contentstore', 'CourseType')
    CourseType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0041_add_course_type_model'),
    ]

    operations = [
        migrations.RunPython(
            create_default_course_types,
            remove_default_course_types,
        ),
    ]
