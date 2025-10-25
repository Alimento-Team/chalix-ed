# Generated migration for quiz configuration fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0064_alter_organization_options'),
    ]

    operations = [
        # Add quiz_time_limit field
        migrations.AddField(
            model_name='finalevaluation',
            name='quiz_time_limit',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                verbose_name='Quiz Time Limit (minutes)',
                help_text='Time limit for completing the quiz in minutes. Leave blank for no time limit.'
            ),
        ),
        
        # Add quiz_passing_score field
        migrations.AddField(
            model_name='finalevaluation',
            name='quiz_passing_score',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                null=True,
                blank=True,
                verbose_name='Minimum Passing Score (%)',
                help_text='Minimum score percentage required to pass the quiz (0-100)'
            ),
        ),
        
        # Add quiz_max_attempts field
        migrations.AddField(
            model_name='finalevaluation',
            name='quiz_max_attempts',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='Maximum Quiz Attempts',
                help_text='Number of times a learner can attempt the quiz. 0 means unlimited.'
            ),
        ),
        
        # Add attempt_number field to QuizAttempt
        migrations.AddField(
            model_name='quizattempt',
            name='attempt_number',
            field=models.PositiveIntegerField(
                default=1,
                verbose_name='Attempt Number',
                help_text='The sequential attempt number for this learner'
            ),
        ),
        
        # Add passed field to QuizAttempt
        migrations.AddField(
            model_name='quizattempt',
            name='passed',
            field=models.BooleanField(
                default=False,
                verbose_name='Passed',
                help_text='Whether the learner passed based on the minimum score requirement'
            ),
        ),
        
        # Remove unique_together constraint from QuizAttempt to allow multiple attempts
        migrations.AlterUniqueTogether(
            name='quizattempt',
            unique_together=set(),
        ),
        
        # Add ordering to QuizAttempt
        migrations.AlterModelOptions(
            name='quizattempt',
            options={
                'verbose_name': 'Quiz Attempt',
                'verbose_name_plural': 'Quiz Attempts',
                'ordering': ['-started_at']
            },
        ),
    ]
