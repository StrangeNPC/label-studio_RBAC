# RBAC-feature
"""
API tests for project permission enforcement.

Tests cover:
- Project list filtering by membership
- Permission checks on project operations (view, update, delete)
- 403 errors for unauthorized access
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from projects.models import Project, ProjectMember, RoleChoices
from projects.tests.factories import ProjectFactory
from users.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory


class TestProjectListFiltering(TestCase):
    """Test GET /api/projects/ filters by membership"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        # Create users
        self.user1 = UserFactory(active_organization=self.organization)
        self.user2 = UserFactory(active_organization=self.organization)

        # Create projects
        self.project1 = ProjectFactory(created_by=self.user1, organization=self.organization)
        self.project2 = ProjectFactory(created_by=self.user1, organization=self.organization)
        self.project3 = ProjectFactory(created_by=self.user2, organization=self.organization)

        # Add memberships
        ProjectMember.objects.create(project=self.project1, user=self.user1, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project2, user=self.user1, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project2, user=self.user2, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project3, user=self.user2, role=RoleChoices.OWNER)

    def test_user_sees_only_their_projects(self):
        """User1 should only see projects they're a member of"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p['id'] for p in response.data['results']]

        # user1 is member of project1 and project2
        assert self.project1.id in project_ids
        assert self.project2.id in project_ids
        assert self.project3.id not in project_ids

    def test_user2_sees_different_projects(self):
        """User2 should see different set of projects"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('api:project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p['id'] for p in response.data['results']]

        # user2 is member of project2 and project3
        assert self.project1.id not in project_ids
        assert self.project2.id in project_ids
        assert self.project3.id in project_ids

    def test_user_with_no_projects_sees_empty_list(self):
        """User with no project memberships sees empty list"""
        user_no_projects = UserFactory(active_organization=self.organization)
        self.client.force_authenticate(user=user_no_projects)
        url = reverse('api:project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


class TestProjectCountsFiltering(TestCase):
    """Test GET /api/projects/counts/ filters by membership"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.user1 = UserFactory(active_organization=self.organization)
        self.user2 = UserFactory(active_organization=self.organization)

        self.project1 = ProjectFactory(created_by=self.user1, organization=self.organization)
        self.project2 = ProjectFactory(created_by=self.user2, organization=self.organization)

        ProjectMember.objects.create(project=self.project1, user=self.user1, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project2, user=self.user2, role=RoleChoices.OWNER)

    def test_counts_filtered_by_membership(self):
        """Project counts should only show user's projects"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:project-counts-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p['id'] for p in response.data['results']]

        assert self.project1.id in project_ids
        assert self.project2.id not in project_ids


class TestProjectViewPermissions(TestCase):
    """Test GET /api/projects/{id}/ permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.viewer = UserFactory(active_organization=self.organization)
        self.non_member = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.viewer, role=RoleChoices.VIEWER)

    def test_owner_can_view_project(self):
        """Owner can view project details"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.project.id

    def test_viewer_can_view_project(self):
        """Viewer can view project details"""
        self.client.force_authenticate(user=self.viewer)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.project.id

    def test_non_member_cannot_view_project(self):
        """Non-member cannot view project"""
        self.client.force_authenticate(user=self.non_member)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        # Should get 404 because queryset filtering excludes it
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectUpdatePermissions(TestCase):
    """Test PATCH /api/projects/{id}/ permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_owner_can_update_project(self):
        """Owner can update project"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        self.project.refresh_from_db()
        assert self.project.title == 'Updated Title'

    def test_admin_can_update_project(self):
        """Admin can update project"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {'title': 'Admin Updated'}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_manager_cannot_update_project(self):
        """Manager cannot update project settings (only Owner/Admin can)"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {'title': 'Manager Updated'}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_annotator_cannot_update_project(self):
        """Annotator cannot update project"""
        self.client.force_authenticate(user=self.annotator)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {'title': 'Should Fail'}
        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectDeletePermissions(TestCase):
    """Test DELETE /api/projects/{id}/ permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)

    def test_owner_can_delete_project(self):
        """Owner can delete project"""
        project = ProjectFactory(created_by=self.owner, organization=self.organization)
        ProjectMember.objects.create(project=project, user=self.owner, role=RoleChoices.OWNER)

        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(pk=project.pk).exists()

    def test_admin_can_delete_project(self):
        """Admin can delete project"""
        project = ProjectFactory(created_by=self.owner, organization=self.organization)
        ProjectMember.objects.create(project=project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=project, user=self.admin, role=RoleChoices.ADMIN)

        self.client.force_authenticate(user=self.admin)
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_manager_cannot_delete_project(self):
        """Manager cannot delete project"""
        project = ProjectFactory(created_by=self.owner, organization=self.organization)
        ProjectMember.objects.create(project=project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=project, user=self.manager, role=RoleChoices.MANAGER)

        self.client.force_authenticate(user=self.manager)
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Project.objects.filter(pk=project.pk).exists()


class TestProjectPUTPermissions(TestCase):
    """Test PUT /api/projects/{id}/ permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.annotator = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.annotator, role=RoleChoices.ANNOTATOR)

    def test_owner_can_put_project(self):
        """Owner can fully update project via PUT"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {
            'title': 'PUT Updated',
            'description': 'Full update',
            'label_config': '<View></View>'
        }
        response = self.client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_annotator_cannot_put_project(self):
        """Annotator cannot update project via PUT"""
        self.client.force_authenticate(user=self.annotator)
        url = reverse('api:project-detail', kwargs={'pk': self.project.pk})
        data = {
            'title': 'Should Fail',
            'description': 'Should not work',
            'label_config': '<View></View>'
        }
        response = self.client.put(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCrossOrganizationAccess(TestCase):
    """Test that users from different organizations cannot access each other's projects"""

    def setUp(self):
        self.client = APIClient()

        self.org1 = OrganizationFactory()
        self.org2 = OrganizationFactory()

        self.user_org1 = UserFactory(active_organization=self.org1)
        self.user_org2 = UserFactory(active_organization=self.org2)

        self.project_org1 = ProjectFactory(created_by=self.user_org1, organization=self.org1)
        self.project_org2 = ProjectFactory(created_by=self.user_org2, organization=self.org2)

        ProjectMember.objects.create(project=self.project_org1, user=self.user_org1, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project_org2, user=self.user_org2, role=RoleChoices.OWNER)

    def test_user_cannot_see_other_org_projects_in_list(self):
        """User from org1 cannot see org2 projects in list"""
        self.client.force_authenticate(user=self.user_org1)
        url = reverse('api:project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p['id'] for p in response.data['results']]

        assert self.project_org1.id in project_ids
        assert self.project_org2.id not in project_ids

    def test_user_cannot_access_other_org_project_directly(self):
        """User from org1 cannot access org2 project by ID"""
        self.client.force_authenticate(user=self.user_org1)
        url = reverse('api:project-detail', kwargs={'pk': self.project_org2.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
