"""
Django migration to add external URL support to UnitMediaFile model
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # The original dependency referenced a migration that doesn't exist in this tree.
        # Point this migration to a real existing prior migration so Django can build
        # a correct migration graph. Adjust if your migration history differs.
        ('contentstore', '0011_enable_markdown_editor_flag_by_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='unitmediafile',
            name='external_url',
            field=models.URLField(
                blank=True,
                help_text='URL for external video sources like YouTube or Google Drive',
                max_length=1000,
                null=True,
                verbose_name='External Video URL'
            ),
        ),
        migrations.AddField(
            model_name='unitmediafile',
            name='video_source_type',
            field=models.CharField(
                blank=True,
                help_text='Type of video source: youtube, google_drive, upload, etc.',
                max_length=50,
                null=True,
                verbose_name='Video Source Type'
            ),
        ),
        migrations.AddField(
            model_name='unitmediafile',
            name='client_video_id',
            field=models.CharField(
                blank=True,
                help_text='Unique identifier for the video on the client side',
                max_length=255,
                null=True,
                verbose_name='Client Video ID'
            ),
        ),
        migrations.AddField(
            model_name='unitmediafile',
            name='upload_status',
            field=models.CharField(
                default='pending',
                help_text='Status of the upload: pending, ready, failed, etc.',
                max_length=50,
                verbose_name='Upload Status'
            ),
        ),
        migrations.AddField(
            model_name='unitmediafile',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who created this media record',
                null=True,
                on_delete=models.SET_NULL,
                related_name='created_unit_media',
                to='auth.User',
                verbose_name='Created By'
            ),
        ),
    ]