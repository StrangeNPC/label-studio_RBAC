# RBAC-feature
"""
Unit tests for project permissions using django-rules.

Tests cover all permission predicates for the six roles:
- Owner
- Admin
- Manager
- Annotator
- Reviewer
- Viewer
"""

from django.test import TestCase
from projects.models import Project, ProjectMember, RoleChoices
from projects.tests.factories import ProjectFactory
from users.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory


class TestPermissionPredicates(TestCase):
    """Test basic permission predicates"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.reviewer = UserFactory(active_organization=self.organization)
        self.viewer = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()
        self.superuser = UserFactory(is_superuser=True)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.reviewer, role=RoleChoices.REVIEWER)
        ProjectMember.objects.create(project=self.project, user=self.viewer, role=RoleChoices.VIEWER)

    def test_is_project_member(self):
        """Test is_project_member predicate"""
        from projects.permissions import is_project_member

        assert is_project_member(self.owner, self.project)
        assert is_project_member(self.admin, self.project)
        assert is_project_member(self.manager, self.project)
        assert is_project_member(self.annotator, self.project)
        assert is_project_member(self.reviewer, self.project)
        assert is_project_member(self.viewer, self.project)
        assert not is_project_member(self.non_member, self.project)
        assert is_project_member(self.superuser, self.project)

    def test_is_owner(self):
        """Test is_owner predicate"""
        from projects.permissions import is_owner

        assert is_owner(self.owner, self.project)
        assert not is_owner(self.admin, self.project)
        assert not is_owner(self.manager, self.project)
        assert not is_owner(self.annotator, self.project)
        assert not is_owner(self.reviewer, self.project)
        assert not is_owner(self.viewer, self.project)
        assert not is_owner(self.non_member, self.project)
        assert is_owner(self.superuser, self.project)

    def test_is_admin_or_owner(self):
        """Test is_admin_or_owner predicate"""
        from projects.permissions import is_admin_or_owner

        assert is_admin_or_owner(self.owner, self.project)
        assert is_admin_or_owner(self.admin, self.project)
        assert not is_admin_or_owner(self.manager, self.project)
        assert not is_admin_or_owner(self.annotator, self.project)
        assert not is_admin_or_owner(self.reviewer, self.project)
        assert not is_admin_or_owner(self.viewer, self.project)
        assert not is_admin_or_owner(self.non_member, self.project)
        assert is_admin_or_owner(self.superuser, self.project)

    def test_is_manager_or_above(self):
        """Test is_manager_or_above predicate"""
        from projects.permissions import is_manager_or_above

        assert is_manager_or_above(self.owner, self.project)
        assert is_manager_or_above(self.admin, self.project)
        assert is_manager_or_above(self.manager, self.project)
        assert not is_manager_or_above(self.annotator, self.project)
        assert not is_manager_or_above(self.reviewer, self.project)
        assert not is_manager_or_above(self.viewer, self.project)
        assert not is_manager_or_above(self.non_member, self.project)
        assert is_manager_or_above(self.superuser, self.project)

    def test_disabled_member_has_no_access(self):
        """Test that disabled members have no permissions"""
        from projects.permissions import is_project_member

        disabled_user = UserFactory()
        ProjectMember.objects.create(
            project=self.project,
            user=disabled_user,
            role=RoleChoices.ADMIN,
            enabled=False
        )

        assert not is_project_member(disabled_user, self.project)


class TestProjectPermissions(TestCase):
    """Test project-level permissions"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.reviewer = UserFactory(active_organization=self.organization)
        self.viewer = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.reviewer, role=RoleChoices.REVIEWER)
        ProjectMember.objects.create(project=self.project, user=self.viewer, role=RoleChoices.VIEWER)

    def test_projects_view_permission(self):
        """Test projects.view permission - all members can view"""
        assert self.owner.has_perm('projects.view', self.project)
        assert self.admin.has_perm('projects.view', self.project)
        assert self.manager.has_perm('projects.view', self.project)
        assert self.annotator.has_perm('projects.view', self.project)
        assert self.reviewer.has_perm('projects.view', self.project)
        assert self.viewer.has_perm('projects.view', self.project)
        assert not self.non_member.has_perm('projects.view', self.project)

    def test_projects_change_permission(self):
        """Test projects.change permission - only owner and admin"""
        assert self.owner.has_perm('projects.change', self.project)
        assert self.admin.has_perm('projects.change', self.project)
        assert not self.manager.has_perm('projects.change', self.project)
        assert not self.annotator.has_perm('projects.change', self.project)
        assert not self.reviewer.has_perm('projects.change', self.project)
        assert not self.viewer.has_perm('projects.change', self.project)
        assert not self.non_member.has_perm('projects.change', self.project)

    def test_projects_delete_permission(self):
        """Test projects.delete permission - only owner"""
        assert self.owner.has_perm('projects.delete', self.project)
        assert not self.admin.has_perm('projects.delete', self.project)
        assert not self.manager.has_perm('projects.delete', self.project)
        assert not self.annotator.has_perm('projects.delete', self.project)
        assert not self.reviewer.has_perm('projects.delete', self.project)
        assert not self.viewer.has_perm('projects.delete', self.project)
        assert not self.non_member.has_perm('projects.delete', self.project)

    def test_projects_manage_members_permission(self):
        """Test projects.manage_members permission - owner and admin"""
        assert self.owner.has_perm('projects.manage_members', self.project)
        assert self.admin.has_perm('projects.manage_members', self.project)
        assert not self.manager.has_perm('projects.manage_members', self.project)
        assert not self.annotator.has_perm('projects.manage_members', self.project)
        assert not self.reviewer.has_perm('projects.manage_members', self.project)
        assert not self.viewer.has_perm('projects.manage_members', self.project)
        assert not self.non_member.has_perm('projects.manage_members', self.project)

    def test_projects_view_members_permission(self):
        """Test projects.view_members permission - owner, admin, manager"""
        assert self.owner.has_perm('projects.view_members', self.project)
        assert self.admin.has_perm('projects.view_members', self.project)
        assert self.manager.has_perm('projects.view_members', self.project)
        assert not self.annotator.has_perm('projects.view_members', self.project)
        assert not self.reviewer.has_perm('projects.view_members', self.project)
        assert not self.viewer.has_perm('projects.view_members', self.project)
        assert not self.non_member.has_perm('projects.view_members', self.project)

    def test_projects_export_data_permission(self):
        """Test projects.export_data permission - owner, admin, manager"""
        assert self.owner.has_perm('projects.export_data', self.project)
        assert self.admin.has_perm('projects.export_data', self.project)
        assert self.manager.has_perm('projects.export_data', self.project)
        assert not self.annotator.has_perm('projects.export_data', self.project)
        assert not self.reviewer.has_perm('projects.export_data', self.project)
        assert not self.viewer.has_perm('projects.export_data', self.project)
        assert not self.non_member.has_perm('projects.export_data', self.project)


class TestTaskPermissions(TestCase):
    """Test task-level permissions"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.reviewer = UserFactory(active_organization=self.organization)
        self.viewer = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.reviewer, role=RoleChoices.REVIEWER)
        ProjectMember.objects.create(project=self.project, user=self.viewer, role=RoleChoices.VIEWER)

    def test_tasks_view_permission(self):
        """Test tasks.view permission - all members can view"""
        assert self.owner.has_perm('tasks.view', self.project)
        assert self.admin.has_perm('tasks.view', self.project)
        assert self.manager.has_perm('tasks.view', self.project)
        assert self.annotator.has_perm('tasks.view', self.project)
        assert self.reviewer.has_perm('tasks.view', self.project)
        assert self.viewer.has_perm('tasks.view', self.project)
        assert not self.non_member.has_perm('tasks.view', self.project)

    def test_tasks_create_permission(self):
        """Test tasks.create permission - owner, admin, manager"""
        assert self.owner.has_perm('tasks.create', self.project)
        assert self.admin.has_perm('tasks.create', self.project)
        assert self.manager.has_perm('tasks.create', self.project)
        assert not self.annotator.has_perm('tasks.create', self.project)
        assert not self.reviewer.has_perm('tasks.create', self.project)
        assert not self.viewer.has_perm('tasks.create', self.project)
        assert not self.non_member.has_perm('tasks.create', self.project)

    def test_tasks_change_permission(self):
        """Test tasks.change permission - owner, admin, manager"""
        assert self.owner.has_perm('tasks.change', self.project)
        assert self.admin.has_perm('tasks.change', self.project)
        assert self.manager.has_perm('tasks.change', self.project)
        assert not self.annotator.has_perm('tasks.change', self.project)
        assert not self.reviewer.has_perm('tasks.change', self.project)
        assert not self.viewer.has_perm('tasks.change', self.project)
        assert not self.non_member.has_perm('tasks.change', self.project)

    def test_tasks_delete_permission(self):
        """Test tasks.delete permission - owner, admin, manager"""
        assert self.owner.has_perm('tasks.delete', self.project)
        assert self.admin.has_perm('tasks.delete', self.project)
        assert self.manager.has_perm('tasks.delete', self.project)
        assert not self.annotator.has_perm('tasks.delete', self.project)
        assert not self.reviewer.has_perm('tasks.delete', self.project)
        assert not self.viewer.has_perm('tasks.delete', self.project)
        assert not self.non_member.has_perm('tasks.delete', self.project)

    def test_tasks_assign_permission(self):
        """Test tasks.assign permission - owner, admin, manager"""
        assert self.owner.has_perm('tasks.assign', self.project)
        assert self.admin.has_perm('tasks.assign', self.project)
        assert self.manager.has_perm('tasks.assign', self.project)
        assert not self.annotator.has_perm('tasks.assign', self.project)
        assert not self.reviewer.has_perm('tasks.assign', self.project)
        assert not self.viewer.has_perm('tasks.assign', self.project)
        assert not self.non_member.has_perm('tasks.assign', self.project)


class TestAnnotationPermissions(TestCase):
    """Test annotation-level permissions"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.reviewer = UserFactory(active_organization=self.organization)
        self.viewer = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.reviewer, role=RoleChoices.REVIEWER)
        ProjectMember.objects.create(project=self.project, user=self.viewer, role=RoleChoices.VIEWER)

    def test_annotations_create_permission(self):
        """Test annotations.create permission - all except viewer"""
        assert self.owner.has_perm('annotations.create', self.project)
        assert self.admin.has_perm('annotations.create', self.project)
        assert self.manager.has_perm('annotations.create', self.project)
        assert self.annotator.has_perm('annotations.create', self.project)
        assert self.reviewer.has_perm('annotations.create', self.project)
        assert not self.viewer.has_perm('annotations.create', self.project)
        assert not self.non_member.has_perm('annotations.create', self.project)

    def test_annotations_change_permission(self):
        """Test annotations.change permission - all except viewer"""
        assert self.owner.has_perm('annotations.change', self.project)
        assert self.admin.has_perm('annotations.change', self.project)
        assert self.manager.has_perm('annotations.change', self.project)
        assert self.annotator.has_perm('annotations.change', self.project)
        assert self.reviewer.has_perm('annotations.change', self.project)
        assert not self.viewer.has_perm('annotations.change', self.project)
        assert not self.non_member.has_perm('annotations.change', self.project)

    def test_annotations_delete_permission(self):
        """Test annotations.delete permission - owner, admin, manager"""
        assert self.owner.has_perm('annotations.delete', self.project)
        assert self.admin.has_perm('annotations.delete', self.project)
        assert self.manager.has_perm('annotations.delete', self.project)
        assert not self.annotator.has_perm('annotations.delete', self.project)
        assert not self.reviewer.has_perm('annotations.delete', self.project)
        assert not self.viewer.has_perm('annotations.delete', self.project)
        assert not self.non_member.has_perm('annotations.delete', self.project)

    def test_annotations_review_permission(self):
        """Test annotations.review permission - owner, admin, manager, reviewer"""
        assert self.owner.has_perm('annotations.review', self.project)
        assert self.admin.has_perm('annotations.review', self.project)
        assert self.manager.has_perm('annotations.review', self.project)
        assert not self.annotator.has_perm('annotations.review', self.project)
        assert self.reviewer.has_perm('annotations.review', self.project)
        assert not self.viewer.has_perm('annotations.review', self.project)
        assert not self.non_member.has_perm('annotations.review', self.project)


class TestSuperuserPermissions(TestCase):
    """Test that superusers have all permissions"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.superuser = UserFactory(is_superuser=True)
        self.project = ProjectFactory(organization=self.organization)

    def test_superuser_has_all_project_permissions(self):
        """Superuser should have all project permissions"""
        assert self.superuser.has_perm('projects.view', self.project)
        assert self.superuser.has_perm('projects.change', self.project)
        assert self.superuser.has_perm('projects.delete', self.project)
        assert self.superuser.has_perm('projects.manage_members', self.project)
        assert self.superuser.has_perm('projects.view_members', self.project)
        assert self.superuser.has_perm('projects.export_data', self.project)

    def test_superuser_has_all_task_permissions(self):
        """Superuser should have all task permissions"""
        assert self.superuser.has_perm('tasks.view', self.project)
        assert self.superuser.has_perm('tasks.create', self.project)
        assert self.superuser.has_perm('tasks.change', self.project)
        assert self.superuser.has_perm('tasks.delete', self.project)
        assert self.superuser.has_perm('tasks.assign', self.project)

    def test_superuser_has_all_annotation_permissions(self):
        """Superuser should have all annotation permissions"""
        assert self.superuser.has_perm('annotations.create', self.project)
        assert self.superuser.has_perm('annotations.change', self.project)
        assert self.superuser.has_perm('annotations.delete', self.project)
        assert self.superuser.has_perm('annotations.review', self.project)


class TestProjectHasPermissionMethod(TestCase):
    """Test Project.has_permission() method integration with RBAC"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()
        self.superuser = UserFactory(is_superuser=True)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_has_permission_returns_true_for_members(self):
        """Test has_permission returns True for project members"""
        assert self.project.has_permission(self.owner) is True
        assert self.project.has_permission(self.admin) is True
        assert self.project.has_permission(self.annotator) is True

    def test_has_permission_returns_false_for_non_members(self):
        """Test has_permission returns False for non-members"""
        assert self.project.has_permission(self.non_member) is False

    def test_has_permission_returns_true_for_superuser(self):
        """Test has_permission returns True for superusers"""
        assert self.project.has_permission(self.superuser) is True

    def test_has_permission_returns_false_for_unauthenticated(self):
        """Test has_permission returns False for unauthenticated users"""
        from django.contrib.auth.models import AnonymousUser
        anonymous = AnonymousUser()
        assert self.project.has_permission(anonymous) is False

    def test_has_permission_maintains_activity_log_link(self):
        """Test has_permission maintains user.project link for activity log"""
        self.project.has_permission(self.owner)
        assert hasattr(self.owner, 'project')
        assert self.owner.project == self.project

    def test_has_permission_disabled_member(self):
        """Test has_permission returns False for disabled members"""
        disabled_user = UserFactory()
        ProjectMember.objects.create(
            project=self.project,
            user=disabled_user,
            role=RoleChoices.ADMIN,
            enabled=False
        )
        assert self.project.has_permission(disabled_user) is False

    def test_has_permission_checks_organization_membership(self):
        """Test has_permission checks organization membership first"""
        from organizations.models import OrganizationMember
        from django.utils import timezone

        user_not_in_org = UserFactory(active_organization=self.organization)
        ProjectMember.objects.create(
            project=self.project,
            user=user_not_in_org,
            role=RoleChoices.ADMIN
        )

        OrganizationMember.objects.filter(
            user=user_not_in_org,
            organization=self.organization
        ).update(deleted_at=timezone.now())

        assert self.project.has_permission(user_not_in_org) is False


class TestProjectHelperMethods(TestCase):
    """Test Project.has_perm() and check_permission() helper methods"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_has_perm_specific_permission(self):
        """Test has_perm checks specific permissions"""
        assert self.project.has_perm(self.owner, 'projects.change') is True
        assert self.project.has_perm(self.annotator, 'projects.change') is False

    def test_has_perm_non_member(self):
        """Test has_perm returns False for non-members"""
        assert self.project.has_perm(self.non_member, 'projects.view') is False

    def test_check_permission_raises_exception(self):
        """Test check_permission raises PermissionDenied"""
        from rest_framework.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            self.project.check_permission(self.non_member)

    def test_check_permission_no_exception(self):
        """Test check_permission returns False without raising when raise_exception=False"""
        result = self.project.check_permission(self.non_member, raise_exception=False)
        assert result is False

    def test_check_permission_with_specific_perm(self):
        """Test check_permission with specific permission"""
        from rest_framework.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            self.project.check_permission(self.annotator, 'projects.delete')

        result = self.project.check_permission(self.owner, 'projects.delete')
        assert result is True
