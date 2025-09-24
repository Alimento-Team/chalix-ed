# Generated manually for quiz models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contentstore', '0051_increase_unit_media_upload_url_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChalixQuiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', CourseKeyField(help_text='Course key where this quiz belongs', max_length=255)),
                ('parent_locator', models.CharField(help_text='Locator string of the parent block (section/subsection) where quiz is attached', max_length=255)),
                ('title', models.CharField(max_length=255, verbose_name='Quiz Title')),
                ('description', models.TextField(blank=True, help_text='Optional description for the quiz', verbose_name='Quiz Description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this quiz is active (soft delete flag)', verbose_name='Is Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_quizzes', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
            ],
            options={
                'verbose_name': 'Chalix Quiz',
                'verbose_name_plural': 'Chalix Quizzes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChalixQuizQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField(help_text='The question text displayed to students', verbose_name='Question Text')),
                ('question_type', models.CharField(choices=[('single_choice', 'Single Choice'), ('multiple_choice', 'Multiple Choice')], default='single_choice', help_text='Whether this is a single choice or multiple choice question', max_length=20, verbose_name='Question Type')),
                ('order_index', models.PositiveIntegerField(default=0, help_text='Order of this question within the quiz', verbose_name='Order Index')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this question is active (soft delete flag)', verbose_name='Is Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='contentstore.chalixquiz', verbose_name='Quiz')),
            ],
            options={
                'verbose_name': 'Quiz Question',
                'verbose_name_plural': 'Quiz Questions',
                'ordering': ['quiz', 'order_index'],
            },
        ),
        migrations.CreateModel(
            name='ChalixQuizChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice_text', models.TextField(help_text='The text of this choice option', verbose_name='Choice Text')),
                ('is_correct', models.BooleanField(default=False, help_text='Whether this choice is a correct answer', verbose_name='Is Correct')),
                ('order_index', models.PositiveIntegerField(default=0, help_text='Order of this choice within the question', verbose_name='Order Index')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this choice is active (soft delete flag)', verbose_name='Is Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='contentstore.chalixquizquestion', verbose_name='Question')),
            ],
            options={
                'verbose_name': 'Quiz Choice',
                'verbose_name_plural': 'Quiz Choices',
                'ordering': ['question', 'order_index'],
            },
        ),
        migrations.AddIndex(
            model_name='chalixquiz',
            index=models.Index(fields=['course_key', 'is_active'], name='contentstore_chalixquiz_course_key_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquiz',
            index=models.Index(fields=['parent_locator', 'is_active'], name='contentstore_chalixquiz_parent_locator_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquiz',
            index=models.Index(fields=['created_at'], name='contentstore_chalixquiz_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquizquestion',
            index=models.Index(fields=['quiz', 'order_index'], name='contentstore_chalixquizquestion_quiz_order_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquizquestion',
            index=models.Index(fields=['quiz', 'is_active'], name='contentstore_chalixquizquestion_quiz_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquizchoice',
            index=models.Index(fields=['question', 'order_index'], name='contentstore_chalixquizchoice_question_order_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixquizchoice',
            index=models.Index(fields=['question', 'is_correct'], name='contentstore_chalixquizchoice_question_is_correct_idx'),
        ),
    ]