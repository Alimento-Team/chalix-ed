from django.conf import settings
from django.db import migrations


def drop_unique_index_if_exists_0006(apps, schema_editor):
    """Drop any unique index on (user_id, course_id) so AlterUniqueTogether can run cleanly.

    This is defensive: some deployments already have an index on these columns with a
    different auto-generated name which causes MySQL to raise Duplicate key errors
    when Django attempts to create the constraint. We drop the existing unique
    index if it uses those columns and is unique.
    """
    connection = schema_editor.connection
    table_name = 'learning_analytics_learnerbehavior'
    cursor = connection.cursor()

    # Introspect existing constraints/indexes
    try:
        constraints = connection.introspection.get_constraints(cursor, table_name)
    except Exception:
        # If introspection fails for any reason, avoid blocking the migration
        return

    for name, info in constraints.items():
        if not info.get('unique'):
            continue
        cols = tuple(info.get('columns', []))
        # Match regardless of column order (some DBs may report order differently)
        if set(cols) == {"user_id", "course_id"}:
            try:
                sql = "DROP INDEX `{}` ON `{}`".format(name, table_name)
                schema_editor.execute(sql)
            except Exception:
                # Best-effort: ignore failures to drop and let the subsequent
                # AlterUniqueTogether handle/report errors.
                pass
            break


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_analytics', '0005_alter_learnerbehavior_unique_together'),
    ]

    operations = [
        migrations.RunPython(drop_unique_index_if_exists_0006, reverse_code=migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='learnerbehavior',
            unique_together={('user', 'course_id')},
        ),
    ]
