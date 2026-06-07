# Generated migration for adding survey voting configuration options

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0080_add_survey_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='chalixsurveyform',
            name='allow_multiple_votes',
            field=models.BooleanField(
                default=False,
                help_text='If False, each respondent can only vote once. If True, respondents can select multiple choices.',
                verbose_name='Allow Multiple Votes'
            ),
        ),
        migrations.AddField(
            model_name='chalixsurveyform',
            name='allow_add_choice',
            field=models.BooleanField(
                default=False,
                help_text='If True, respondents can add custom choices (Khác option) in addition to predefined ones.',
                verbose_name='Allow Add Choice'
            ),
        ),
    ]
