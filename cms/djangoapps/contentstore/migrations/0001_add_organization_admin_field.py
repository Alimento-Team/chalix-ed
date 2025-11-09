# Generated migration for adding admin field to Organization model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Depend on the latest existing migration in this app to ensure proper ordering.
        ('contentstore', '0066_alter_finalevaluation_evaluation_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='admin',
            field=models.ForeignKey(
                blank=True,
                help_text='Admin user responsible for this organization',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='administered_organizations',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
