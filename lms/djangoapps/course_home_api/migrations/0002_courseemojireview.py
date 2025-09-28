from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):

    dependencies = [
        ('course_home_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEmojiReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', models.CharField(max_length=255, db_index=True)),
                ('unit_usage_key', models.CharField(max_length=255, blank=True, null=True, db_index=True)),
                ('rating', models.CharField(max_length=10, choices=[('like', 'Like'), ('neutral', 'Neutral'), ('dislike', 'Dislike')])),
                ('comment', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emoji_reviews', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'course_key', 'unit_usage_key')},
            },
        ),
        migrations.AddIndex(
            model_name='courseemojireview',
            index=models.Index(fields=['course_key', 'unit_usage_key'], name='course_unit_idx'),
        ),
    ]
