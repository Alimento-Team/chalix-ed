# Generated migration for final evaluation models

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contentstore', '0046_add_template_fields_to_localcourse'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinalEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', CourseKeyField(db_index=True, help_text='The course this evaluation belongs to', max_length=255, verbose_name='Course Key')),
                ('evaluation_type', models.CharField(choices=[('practical', 'Nộp bài thu hoạch'), ('quiz', 'Làm bài trắc nghiệm')], max_length=20, verbose_name='Evaluation Type')),
                ('practical_question', models.TextField(blank=True, help_text='The question/instructions for practical assignment submission', verbose_name='Practical Question')),
                ('quiz_file', models.FileField(blank=True, help_text='Excel file containing quiz questions and answers', upload_to='course_evaluations/quizzes/', validators=[django.core.validators.FileExtensionValidator(['xlsx', 'xls'])], verbose_name='Quiz Excel File')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_evaluations', to=settings.AUTH_USER_MODEL)),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='contentstore.localprogram', verbose_name='Program')),
            ],
            options={
                'verbose_name': 'Final Evaluation',
                'verbose_name_plural': 'Final Evaluations',
            },
        ),
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Score')),
                ('total_questions', models.PositiveIntegerField(default=0)),
                ('correct_answers', models.PositiveIntegerField(default=0)),
                ('is_completed', models.BooleanField(default=False)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to='contentstore.finalevaluation')),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quiz Attempt',
                'verbose_name_plural': 'Quiz Attempts',
            },
        ),
        migrations.CreateModel(
            name='LearnerSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_file', models.FileField(upload_to='course_evaluations/submissions/', validators=[django.core.validators.FileExtensionValidator(['docx', 'pptx', 'pdf'])], verbose_name='Submission File')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('grade', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Grade')),
                ('feedback', models.TextField(blank=True, verbose_name='Teacher Feedback')),
                ('graded_at', models.DateTimeField(blank=True, null=True)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='contentstore.finalevaluation')),
                ('graded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='graded_submissions', to=settings.AUTH_USER_MODEL)),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Learner Submission',
                'verbose_name_plural': 'Learner Submissions',
            },
        ),
        migrations.CreateModel(
            name='QuizAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField(default=False)),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='contentstore.quizattempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contentstore.chalixquizquestion')),
                ('selected_choice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contentstore.chalixquizchoice')),
            ],
            options={
                'verbose_name': 'Quiz Answer',
                'verbose_name_plural': 'Quiz Answers',
            },
        ),
        migrations.AddConstraint(
            model_name='quizattempt',
            constraint=models.UniqueConstraint(fields=('evaluation', 'learner'), name='unique_quiz_attempt'),
        ),
        migrations.AddConstraint(
            model_name='quizanswer',
            constraint=models.UniqueConstraint(fields=('attempt', 'question'), name='unique_quiz_answer'),
        ),
        migrations.AddConstraint(
            model_name='learnersubmission',
            constraint=models.UniqueConstraint(fields=('evaluation', 'learner'), name='unique_learner_submission'),
        ),
        migrations.AddConstraint(
            model_name='finalevaluation',
            constraint=models.UniqueConstraint(fields=('course_key', 'program'), name='unique_course_evaluation'),
        ),
    ]