# RBAC-feature
"""
API tests for project member role management endpoints.

Tests cover:
- Listing project members with roles
- Adding members with specific roles
- Updating member roles
- Removing members
- Getting current user's role
- Permission enforcement for all operations
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from projects.models import Project, ProjectMember, RoleChoices
from projects.tests.factories import ProjectFactory
from users.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory


class TestProjectMembersListAPI(TestCase):
    """Test GET /api/projects/{id}/members/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_owner_can_list_members(self):
        """Owner can list all project members"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4

    def test_admin_can_list_members(self):
        """Admin can list all project members"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4

    def test_manager_can_list_members(self):
        """Manager can list project members (has view_members permission)"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4

    def test_annotator_cannot_list_members(self):
        """Annotator cannot list members (lacks view_members permission)"""
        self.client.force_authenticate(user=self.annotator)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_member_cannot_list_members(self):
        """Non-member cannot list members"""
        self.client.force_authenticate(user=self.non_member)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_data_structure(self):
        """Test member data includes all required fields"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        member = response.data[0]
        assert 'id' in member
        assert 'user' in member
        assert 'role' in member
        assert 'role_display' in member
        assert 'enabled' in member
        assert 'created_at' in member


class TestProjectMembersAddAPI(TestCase):
    """Test POST /api/projects/{id}/members/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.new_user = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)

    def test_owner_can_add_member(self):
        """Owner can add new member with role"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': self.new_user.id, 'role': RoleChoices.ANNOTATOR}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['role'] == RoleChoices.ANNOTATOR
        assert ProjectMember.objects.filter(user=self.new_user, project=self.project).exists()

    def test_admin_can_add_member(self):
        """Admin can add new member"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': self.new_user.id, 'role': RoleChoices.REVIEWER}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['role'] == RoleChoices.REVIEWER

    def test_manager_cannot_add_member(self):
        """Manager cannot add members (lacks manage_members permission)"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': self.new_user.id, 'role': RoleChoices.ANNOTATOR}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_add_member_with_invalid_role(self):
        """Cannot add member with invalid role"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': self.new_user.id, 'role': 'invalid_role'}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_add_user_not_in_organization(self):
        """Cannot add user who is not in the organization"""
        user_outside_org = UserFactory()
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': user_outside_org.id, 'role': RoleChoices.ANNOTATOR}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_adding_existing_member_updates_role(self):
        """Adding existing member updates their role instead of creating duplicate"""
        existing_member = UserFactory(active_organization=self.organization)
        ProjectMember.objects.create(project=self.project, user=existing_member, role=RoleChoices.ANNOTATOR)

        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-list', kwargs={'pk': self.project.pk})
        data = {'user_id': existing_member.id, 'role': RoleChoices.REVIEWER}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        member = ProjectMember.objects.get(user=existing_member, project=self.project)
        assert member.role == RoleChoices.REVIEWER


class TestProjectMembersUpdateAPI(TestCase):
    """Test PATCH /api/projects/{id}/members/{member_id}/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        self.owner_membership = ProjectMember.objects.create(
            project=self.project, user=self.owner, role=RoleChoices.OWNER
        )
        self.admin_membership = ProjectMember.objects.create(
            project=self.project, user=self.admin, role=RoleChoices.ADMIN
        )
        self.manager_membership = ProjectMember.objects.create(
            project=self.project, user=self.manager, role=RoleChoices.MANAGER
        )
        self.annotator_membership = ProjectMember.objects.create(
            project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR
        )

    def test_owner_can_update_member_role(self):
        """Owner can update member roles"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        data = {'role': RoleChoices.REVIEWER}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        self.annotator_membership.refresh_from_db()
        assert self.annotator_membership.role == RoleChoices.REVIEWER

    def test_admin_can_update_member_role(self):
        """Admin can update member roles"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        data = {'role': RoleChoices.MANAGER}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        self.annotator_membership.refresh_from_db()
        assert self.annotator_membership.role == RoleChoices.MANAGER

    def test_manager_cannot_update_role(self):
        """Manager cannot update roles (lacks manage_members permission)"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        data = {'role': RoleChoices.REVIEWER}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change_owner_role(self):
        """Cannot change owner role (ownership transfer not implemented)"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.owner_membership.pk})
        data = {'role': RoleChoices.ADMIN}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'owner' in response.data['detail'].lower()

    def test_cannot_update_with_invalid_role(self):
        """Cannot update to invalid role"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        data = {'role': 'super_admin'}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProjectMembersDeleteAPI(TestCase):
    """Test DELETE /api/projects/{id}/members/{member_id}/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        self.owner_membership = ProjectMember.objects.create(
            project=self.project, user=self.owner, role=RoleChoices.OWNER
        )
        self.admin_membership = ProjectMember.objects.create(
            project=self.project, user=self.admin, role=RoleChoices.ADMIN
        )
        self.manager_membership = ProjectMember.objects.create(
            project=self.project, user=self.manager, role=RoleChoices.MANAGER
        )
        self.annotator_membership = ProjectMember.objects.create(
            project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR
        )

    def test_owner_can_remove_member(self):
        """Owner can remove project members"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectMember.objects.filter(pk=self.annotator_membership.pk).exists()

    def test_admin_can_remove_member(self):
        """Admin can remove project members"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_manager_cannot_remove_member(self):
        """Manager cannot remove members"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.annotator_membership.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_remove_last_owner(self):
        """Cannot remove the last owner"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': self.owner_membership.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'last owner' in response.data['detail'].lower()

    def test_can_remove_owner_if_multiple_exist(self):
        """Can remove owner if there are multiple owners"""
        second_owner = UserFactory(active_organization=self.organization)
        second_owner_membership = ProjectMember.objects.create(
            project=self.project, user=second_owner, role=RoleChoices.OWNER
        )

        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-detail', kwargs={'pk': self.project.pk, 'member_pk': second_owner_membership.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestCurrentUserRoleAPI(TestCase):
    """Test GET /api/projects/{id}/members/me/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory()

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_get_current_user_role(self):
        """Get current user's role in project"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-me', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == RoleChoices.OWNER
        assert 'permissions' in response.data

    def test_non_member_gets_403(self):
        """Non-member gets 403 when checking role"""
        self.client.force_authenticate(user=self.non_member)
        url = reverse('api:project-members-me', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_list_returned(self):
        """Test that permissions list is returned"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-members-me', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        permissions = response.data['permissions']
        assert isinstance(permissions, list)
        assert 'projects.delete' in permissions
        assert 'projects.change' in permissions
