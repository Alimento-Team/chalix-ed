# Generated migration to add short_description field to LocalProgram

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0046_add_template_fields_to_localcourse'),
    ]

    operations = [
        migrations.AddField(
            model_name='localprogram',
            name='short_description',
            field=models.TextField(blank=True, help_text='Short description of the program'),
        ),
    ]