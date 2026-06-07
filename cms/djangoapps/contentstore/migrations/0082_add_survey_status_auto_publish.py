# Generated migration for adding auto-publish status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0081_add_survey_voting_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='chalixsurveyform',
            name='status',
            field=models.CharField(
                choices=[
                    ('published', 'Published'),
                    ('draft', 'Draft'),
                    ('closed', 'Closed'),
                ],
                default='published',
                help_text='Survey is auto-published upon creation and becomes immediately available to learners',
                max_length=20,
                verbose_name='Status'
            ),
        ),
    ]
