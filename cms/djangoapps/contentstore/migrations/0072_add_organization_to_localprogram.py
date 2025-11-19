# Generated migration to add organization field to LocalProgram

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0071_remove_org_from_professionalfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='localprogram',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                help_text='Organization that owns this program (for visibility control)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='local_programs',
                to='contentstore.chalixorganization'
            ),
        ),
        migrations.AlterField(
            model_name='localprogram',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_local_programs',
                to='auth.user'
            ),
        ),
    ]
