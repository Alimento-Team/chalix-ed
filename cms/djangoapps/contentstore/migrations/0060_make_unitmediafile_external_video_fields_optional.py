# Generated migration for external video support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0059_merge_20251017_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unitmediafile',
            name='file_path',
            field=models.CharField(
                blank=True,
                help_text='Relative path to the stored file (empty for external videos)',
                max_length=500,
                verbose_name='File Path'
            ),
        ),
        migrations.AlterField(
            model_name='unitmediafile',
            name='upload_url',
            field=models.URLField(
                blank=True,
                help_text='Public URL for accessing the uploaded file (empty for external videos)',
                max_length=500,
                verbose_name='Upload URL'
            ),
        ),
    ]
