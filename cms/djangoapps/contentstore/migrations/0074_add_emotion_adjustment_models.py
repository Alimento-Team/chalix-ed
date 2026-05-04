from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0073_create_default_bo_organization'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChalixStudentEmotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(db_index=True, max_length=128)),
                ('course_id', models.CharField(db_index=True, max_length=255)),
                ('course_name', models.CharField(blank=True, max_length=500)),
                ('topic_number', models.CharField(db_index=True, max_length=64)),
                ('topic_name', models.CharField(blank=True, max_length=500)),
                ('emotion', models.SmallIntegerField(choices=[(1, 'Yeu thich'), (0, 'Binh thuong'), (-1, 'Khong thich')])),
                ('source_batch', models.CharField(blank=True, default='', max_length=64)),
                ('imported_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Chalix Student Emotion',
                'verbose_name_plural': 'Chalix Student Emotions',
                'ordering': ['course_id', 'topic_number', 'student_id'],
            },
        ),
        migrations.CreateModel(
            name='ChalixTopicEmotionAggregate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(db_index=True, max_length=255)),
                ('course_name', models.CharField(blank=True, max_length=500)),
                ('topic_number', models.CharField(db_index=True, max_length=64)),
                ('topic_name', models.CharField(blank=True, max_length=500)),
                ('like_count', models.PositiveIntegerField(default=0)),
                ('neutral_count', models.PositiveIntegerField(default=0)),
                ('dislike_count', models.PositiveIntegerField(default=0)),
                ('score_sum', models.IntegerField(default=0)),
                ('adjust_required', models.BooleanField(db_index=True, default=False)),
                ('source_batch', models.CharField(blank=True, default='', max_length=64)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Chalix Topic Emotion Aggregate',
                'verbose_name_plural': 'Chalix Topic Emotion Aggregates',
                'ordering': ['course_id', 'topic_number'],
            },
        ),
        migrations.AddConstraint(
            model_name='chalixstudentemotion',
            constraint=models.UniqueConstraint(fields=('student_id', 'course_id', 'topic_number'), name='cstore_student_emotion_uniq'),
        ),
        migrations.AddConstraint(
            model_name='chalixtopicemotionaggregate',
            constraint=models.UniqueConstraint(fields=('course_id', 'topic_number'), name='cstore_topic_emotion_uniq'),
        ),
        migrations.AddIndex(
            model_name='chalixstudentemotion',
            index=models.Index(fields=['course_id', 'topic_number'], name='cstore_course_topic_emo_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixstudentemotion',
            index=models.Index(fields=['emotion'], name='contentstore_emotion_value_idx'),
        ),
        migrations.AddIndex(
            model_name='chalixtopicemotionaggregate',
            index=models.Index(fields=['course_id', 'adjust_required'], name='contentstore_course_adjust_idx'),
        ),
    ]
