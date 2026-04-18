from django.db import migrations


def ensure_learnerbehavior_activity_columns(apps, schema_editor):
    LearnerBehavior = apps.get_model('learning_analytics', 'LearnerBehavior')
    table_name = LearnerBehavior._meta.db_table
    connection = schema_editor.connection

    if table_name not in connection.introspection.table_names():
        return

    with connection.cursor() as cursor:
        existing_columns = {
            column.name for column in connection.introspection.get_table_description(cursor, table_name)
        }

    for field_name in ('videos_watched', 'problems_attempted', 'discussions_participated'):
        if field_name in existing_columns:
            continue

        schema_editor.add_field(LearnerBehavior, LearnerBehavior._meta.get_field(field_name))


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('learning_analytics', '0009_student_learning_process_snapshot'),
    ]

    operations = [
        migrations.RunPython(
            ensure_learnerbehavior_activity_columns,
            reverse_code=migrations.RunPython.noop,
        ),
    ]