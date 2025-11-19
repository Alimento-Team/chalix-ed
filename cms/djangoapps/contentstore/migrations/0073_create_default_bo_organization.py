# Generated migration to create default Bộ organization and assign to existing programs

from django.db import migrations


def create_default_bo_organization(apps, schema_editor):
    """
    Create a default 'Bộ' organization if it doesn't exist.
    Assign all programs without an organization to this default org.
    """
    ChalixOrganization = apps.get_model('contentstore', 'ChalixOrganization')
    LocalProgram = apps.get_model('contentstore', 'LocalProgram')
    
    # Create or get the default Bộ organization
    default_org, created = ChalixOrganization.objects.get_or_create(
        code='BO_DEFAULT',
        defaults={
            'name': 'bo_default',
            'display_name': 'Bộ (Mặc định)',
            'description': 'Tổ chức mặc định cho các chương trình học được tạo trước đây',
            'is_active': True,
        }
    )
    
    if created:
        print(f"Created default Bộ organization: {default_org.display_name}")
    else:
        print(f"Default Bộ organization already exists: {default_org.display_name}")
    
    # Assign all programs without an organization to the default org
    programs_without_org = LocalProgram.objects.filter(organization__isnull=True)
    count = programs_without_org.count()
    
    if count > 0:
        programs_without_org.update(organization=default_org)
        print(f"Assigned {count} existing programs to default Bộ organization")
    else:
        print("No programs without organization found")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration: Remove organization from programs that have the default org
    and optionally delete the default org.
    """
    ChalixOrganization = apps.get_model('contentstore', 'ChalixOrganization')
    LocalProgram = apps.get_model('contentstore', 'LocalProgram')
    
    try:
        default_org = ChalixOrganization.objects.get(code='BO_DEFAULT')
        # Set organization to NULL for programs that have the default org
        LocalProgram.objects.filter(organization=default_org).update(organization=None)
        print(f"Removed default organization from programs")
    except ChalixOrganization.DoesNotExist:
        print("Default Bộ organization does not exist")


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0072_add_organization_to_localprogram'),
    ]

    operations = [
        migrations.RunPython(
            create_default_bo_organization,
            reverse_code=reverse_migration
        ),
    ]
