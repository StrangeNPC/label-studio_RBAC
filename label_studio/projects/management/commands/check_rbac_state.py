"""
Management command to check RBAC state in the database.
This helps debug permission issues.
"""
from django.core.management.base import BaseCommand
from projects.models import Project, ProjectMember
from users.models import User


class Command(BaseCommand):
    help = 'Check RBAC state: projects, users, and memberships'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== RBAC State Check ===\n'))

        # List all users
        self.stdout.write(self.style.WARNING('Users:'))
        for user in User.objects.all():
            self.stdout.write(f'  ID: {user.id}, Email: {user.email}, Org: {user.active_organization_id}')

        # List all projects
        self.stdout.write(self.style.WARNING('\nProjects:'))
        for project in Project.objects.all():
            self.stdout.write(f'  ID: {project.id}, Title: {project.title}, Org: {project.organization_id}, Creator: {project.created_by_id}')

        # List all project members
        self.stdout.write(self.style.WARNING('\nProjectMembers:'))
        members = ProjectMember.objects.all()
        if members.exists():
            for member in members:
                self.stdout.write(f'  ID: {member.id}, User: {member.user_id} ({member.user.email}), Project: {member.project_id}, Role: {member.role}, Enabled: {member.enabled}')
        else:
            self.stdout.write(self.style.ERROR('  NO ProjectMember records found!'))

        self.stdout.write(self.style.SUCCESS('\n=== End of RBAC State Check ===\n'))
