# Generated migration to add evaluation fields to LocalProgram

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0046_add_template_fields_to_localcourse'),
    ]

    operations = [
        migrations.AddField(
            model_name='localprogram',
            name='allow_practical_submission',
            field=models.BooleanField(default=True, help_text='Allow practical assignment submissions for this program', verbose_name='Allow Practical Submission'),
        ),
        migrations.AddField(
            model_name='localprogram',
            name='allow_multiple_choice',
            field=models.BooleanField(default=True, help_text='Allow multiple choice quiz for this program', verbose_name='Allow Multiple Choice Quiz'),
        ),
    ]