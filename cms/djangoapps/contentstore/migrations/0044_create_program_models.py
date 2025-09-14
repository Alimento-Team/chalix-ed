# Generated migration for Program models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0043_create_chalix_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalProgram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('icon', models.CharField(blank=True, default='seed-of-life', max_length=100)),
                ('update_topics', models.BooleanField(default=False, help_text='Whether to automatically update topics')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_programs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Local Program',
                'verbose_name_plural': 'Local Programs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProgramTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='contentstore.localprogram')),
            ],
            options={
                'verbose_name': 'Program Topic',
                'verbose_name_plural': 'Program Topics',
                'ordering': ['program', 'order', 'title'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='programtopic',
            unique_together={('program', 'order')},
        ),
    ]
