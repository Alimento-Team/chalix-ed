from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_home_api', '0006_topicquizattempt_topicquizanswer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicquizattempt',
            name='unit_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text='Unit usage key this attempt belongs to',
                max_length=512,
            ),
        ),
        migrations.AddIndex(
            model_name='topicquizattempt',
            index=models.Index(fields=['unit_id', 'learner'], name='course_home_unit_id_learner_idx'),
        ),
    ]
