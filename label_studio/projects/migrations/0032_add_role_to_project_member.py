# RBAC-feature
# Generated manually for TICKET-001: Add role field to ProjectMember model
from django.db import migrations, models


def assign_default_roles(apps, schema_editor):
    """
    Assign default roles to existing ProjectMember records.
    - Project creators (project.created_by) get 'owner' role
    - All other members get 'annotator' role (already set by default)
    """
    ProjectMember = apps.get_model('projects', 'ProjectMember')
    Project = apps.get_model('projects', 'Project')

    for project in Project.objects.select_related('created_by').all():
        if project.created_by:
            ProjectMember.objects.filter(
                project=project,
                user=project.created_by
            ).update(role='owner')


def reverse_assign_roles(apps, schema_editor):
    """
    Reverse migration - no action needed as we're removing the role field
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0031_alter_project_show_ground_truth_first'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmember',
            name='role',
            field=models.CharField(
                choices=[
                    ('owner', 'Owner'),
                    ('admin', 'Admin'),
                    ('manager', 'Manager'),
                    ('annotator', 'Annotator'),
                    ('reviewer', 'Reviewer'),
                    ('viewer', 'Viewer')
                ],
                db_index=True,
                default='annotator',
                help_text='User role in the project',
                max_length=20,
                verbose_name='role'
            ),
        ),
        migrations.RunPython(assign_default_roles, reverse_assign_roles),
    ]
