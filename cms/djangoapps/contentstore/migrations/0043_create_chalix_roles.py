# Generated migration to add Chalix role system
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0042_create_localcourse'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChalixOrganization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('display_name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='contentstore.ChalixOrganization')),
            ],
            options={
                'verbose_name': 'Chalix Organization',
                'verbose_name_plural': 'Chalix Organizations',
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='ChalixUserRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('bo', 'Tài khoản Bộ'), ('co_quan', 'Tài khoản Cơ quan'), ('giang_vien', 'Tài khoản Giảng viên'), ('cong_chuc', 'Tài khoản Công chức/Viên chức')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_user_roles', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_roles', to='contentstore.ChalixOrganization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chalix_roles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Chalix User Role',
                'verbose_name_plural': 'Chalix User Roles',
            },
        ),
        migrations.AlterUniqueTogether(
            name='chalixuserrole',
            unique_together={('user', 'role', 'organization')},
        ),
    ]
