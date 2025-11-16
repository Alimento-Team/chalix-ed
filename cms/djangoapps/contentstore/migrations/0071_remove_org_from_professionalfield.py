# Generated migration for removing org field from ProfessionalField
# Professional fields are now global, not organization-specific

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0070_merge_20251116_0358'),
    ]

    operations = [
        # Remove unique_together constraint that includes org
        migrations.AlterUniqueTogether(
            name='professionalfield',
            unique_together=set(),
        ),
        # Remove org field
        migrations.RemoveField(
            model_name='professionalfield',
            name='org',
        ),
        # Add unique constraint on name alone
        migrations.AlterField(
            model_name='professionalfield',
            name='name',
            field=models.CharField(
                help_text='The name of the professional field (e.g., \'Y tế\', \'Giáo dục\')',
                max_length=200,
                unique=True,
                verbose_name='Professional Field Name'
            ),
        ),
        # Update ordering in Meta
        migrations.AlterModelOptions(
            name='professionalfield',
            options={
                'verbose_name': 'Professional Field',
                'verbose_name_plural': 'Professional Fields',
                'ordering': ['sort_order', 'name'],
            },
        ),
    ]
