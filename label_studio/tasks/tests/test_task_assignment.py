# RBAC-feature
"""
Tests for task assignment functionality.

Tests cover:
- Task assignment permissions (only Manager/Admin/Owner can assign)
- Task unassignment permissions
- Task assignment helper methods
- Task permission checks based on assignment
- GET /api/tasks/assigned-to-me/ endpoint
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from projects.models import ProjectMember, RoleChoices
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory
from users.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory


class TestTaskAssignmentPermissions(TestCase):
    """Test task assignment/unassignment permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.admin = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.annotator1 = UserFactory(active_organization=self.organization)
        self.annotator2 = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.admin, role=RoleChoices.ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator1, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.annotator2, role=RoleChoices.ANNOTATOR)

        self.task = TaskFactory(project=self.project)

    def test_manager_can_assign_task(self):
        """Manager can assign tasks to annotators"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.task.is_assigned_to(self.annotator1)
        assert response.data['task_id'] == self.task.id
        assert self.annotator1.id in response.data['assigned_users']

    def test_admin_can_assign_task(self):
        """Admin can assign tasks to annotators"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.task.is_assigned_to(self.annotator1)

    def test_owner_can_assign_task(self):
        """Owner can assign tasks to annotators"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.task.is_assigned_to(self.annotator1)

    def test_annotator_cannot_assign_task(self):
        """Annotator cannot assign tasks"""
        self.client.force_authenticate(user=self.annotator1)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator2.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not self.task.is_assigned_to(self.annotator2)

    def test_assign_multiple_users_to_task(self):
        """Can assign multiple users to a single task"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id, self.annotator2.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert self.task.is_assigned_to(self.annotator1)
        assert self.task.is_assigned_to(self.annotator2)
        assert len(response.data['assigned_users']) == 2

    def test_cannot_assign_non_project_member(self):
        """Cannot assign users who are not project members"""
        non_member = UserFactory(active_organization=self.organization)

        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [non_member.id]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not self.task.is_assigned_to(non_member)

    def test_cannot_assign_invalid_user_id(self):
        """Cannot assign non-existent user"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-assign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [99999]}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTaskUnassignmentPermissions(TestCase):
    """Test task unassignment permission checks"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.manager = UserFactory(active_organization=self.organization)
        self.annotator1 = UserFactory(active_organization=self.organization)
        self.annotator2 = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.manager, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.annotator1, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.annotator2, role=RoleChoices.ANNOTATOR)

        self.task = TaskFactory(project=self.project)
        self.task.assign_to_users([self.annotator1, self.annotator2])

    def test_manager_can_unassign_task(self):
        """Manager can unassign users from tasks"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-unassign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id]}
        response = self.client.delete(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert not self.task.is_assigned_to(self.annotator1)
        assert self.task.is_assigned_to(self.annotator2)
        assert self.annotator1.id not in response.data['assigned_users']
        assert self.annotator2.id in response.data['assigned_users']

    def test_annotator_cannot_unassign_task(self):
        """Annotator cannot unassign users from tasks"""
        self.client.force_authenticate(user=self.annotator1)
        url = reverse('tasks:api:task-unassign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator2.id]}
        response = self.client.delete(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert self.task.is_assigned_to(self.annotator2)

    def test_unassign_multiple_users(self):
        """Can unassign multiple users at once"""
        self.client.force_authenticate(user=self.manager)
        url = reverse('tasks:api:task-unassign', kwargs={'pk': self.task.pk})
        data = {'user_ids': [self.annotator1.id, self.annotator2.id]}
        response = self.client.delete(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert not self.task.is_assigned_to(self.annotator1)
        assert not self.task.is_assigned_to(self.annotator2)
        assert len(response.data['assigned_users']) == 0


class TestTaskAssignmentHelperMethods(TestCase):
    """Test Task model helper methods for assignment"""

    def setUp(self):
        self.organization = OrganizationFactory()
        self.user1 = UserFactory(active_organization=self.organization)
        self.user2 = UserFactory(active_organization=self.organization)
        self.project = ProjectFactory(created_by=self.user1, organization=self.organization)
        self.task = TaskFactory(project=self.project)

    def test_is_assigned_to_returns_false_for_unassigned(self):
        """is_assigned_to returns False when user is not assigned"""
        assert not self.task.is_assigned_to(self.user1)

    def test_is_assigned_to_returns_true_for_assigned(self):
        """is_assigned_to returns True when user is assigned"""
        self.task.assign_to_users([self.user1])
        assert self.task.is_assigned_to(self.user1)

    def test_assign_to_users_adds_users(self):
        """assign_to_users adds users to assigned_to"""
        self.task.assign_to_users([self.user1, self.user2])
        assert self.task.assigned_to.count() == 2
        assert self.task.is_assigned_to(self.user1)
        assert self.task.is_assigned_to(self.user2)

    def test_assign_to_users_is_idempotent(self):
        """Assigning same user multiple times doesn't create duplicates"""
        self.task.assign_to_users([self.user1])
        self.task.assign_to_users([self.user1])
        assert self.task.assigned_to.count() == 1

    def test_unassign_from_users_removes_users(self):
        """unassign_from_users removes users from assigned_to"""
        self.task.assign_to_users([self.user1, self.user2])
        self.task.unassign_from_users([self.user1])
        assert not self.task.is_assigned_to(self.user1)
        assert self.task.is_assigned_to(self.user2)
        assert self.task.assigned_to.count() == 1


class TestTaskPermissionWithAssignment(TestCase):
    """Test Task.has_permission() with assignment checks"""

    def setUp(self):
        self.organization = OrganizationFactory()

        self.owner = UserFactory(active_organization=self.organization)
        self.manager = UserFactory(active_organization=self.organization)
        self.reviewer = UserFactory(active_organization=self.organization)
        self.annotator1 = UserFactory(active_organization=self.organization)
        self.annotator2 = UserFactory(active_organization=self.organization)

        self.project = ProjectFactory(created_by=self.owner, organization=self.organization)

        ProjectMember.objects.create(project=self.project, user=self.owner, role=RoleChoices.OWNER)
        ProjectMember.objects.create(project=self.project, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project, user=self.reviewer, role=RoleChoices.REVIEWER)
        ProjectMember.objects.create(project=self.project, user=self.annotator1, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project, user=self.annotator2, role=RoleChoices.ANNOTATOR)

        self.task = TaskFactory(project=self.project)

    def test_unassigned_task_accessible_to_all_members(self):
        """When task has no assignments, all project members can access it"""
        assert self.task.has_permission(self.owner)
        assert self.task.has_permission(self.manager)
        assert self.task.has_permission(self.reviewer)
        assert self.task.has_permission(self.annotator1)
        assert self.task.has_permission(self.annotator2)

    def test_assigned_task_accessible_to_assigned_annotator(self):
        """Assigned annotator can access their assigned task"""
        self.task.assign_to_users([self.annotator1])
        assert self.task.has_permission(self.annotator1)

    def test_assigned_task_not_accessible_to_unassigned_annotator(self):
        """Unassigned annotator cannot access task assigned to others"""
        self.task.assign_to_users([self.annotator1])
        assert not self.task.has_permission(self.annotator2)

    def test_assigned_task_accessible_to_manager_regardless_of_assignment(self):
        """Manager can access all tasks regardless of assignment"""
        self.task.assign_to_users([self.annotator1])
        assert self.task.has_permission(self.manager)

    def test_assigned_task_accessible_to_owner_regardless_of_assignment(self):
        """Owner can access all tasks regardless of assignment"""
        self.task.assign_to_users([self.annotator1])
        assert self.task.has_permission(self.owner)

    def test_assigned_task_accessible_to_reviewer_regardless_of_assignment(self):
        """Reviewer can access all tasks regardless of assignment"""
        self.task.assign_to_users([self.annotator1])
        assert self.task.has_permission(self.reviewer)

    def test_non_member_cannot_access_task(self):
        """Non-project member cannot access task"""
        non_member = UserFactory(active_organization=self.organization)
        assert not self.task.has_permission(non_member)


class TestAssignedToMeEndpoint(TestCase):
    """Test GET /api/tasks/assigned-to-me/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()

        self.manager = UserFactory(active_organization=self.organization)
        self.annotator1 = UserFactory(active_organization=self.organization)
        self.annotator2 = UserFactory(active_organization=self.organization)

        self.project1 = ProjectFactory(created_by=self.manager, organization=self.organization)
        self.project2 = ProjectFactory(created_by=self.manager, organization=self.organization)

        ProjectMember.objects.create(project=self.project1, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project1, user=self.annotator1, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project1, user=self.annotator2, role=RoleChoices.ANNOTATOR)
        ProjectMember.objects.create(project=self.project2, user=self.manager, role=RoleChoices.MANAGER)
        ProjectMember.objects.create(project=self.project2, user=self.annotator1, role=RoleChoices.ANNOTATOR)

        self.task1 = TaskFactory(project=self.project1)
        self.task2 = TaskFactory(project=self.project1)
        self.task3 = TaskFactory(project=self.project2)
        self.task4 = TaskFactory(project=self.project1)

        self.task1.assign_to_users([self.annotator1])
        self.task2.assign_to_users([self.annotator1, self.annotator2])
        self.task3.assign_to_users([self.annotator1])

    def test_annotator_sees_only_their_assigned_tasks(self):
        """Annotator sees only tasks assigned to them"""
        self.client.force_authenticate(user=self.annotator1)
        url = reverse('tasks:api:tasks-assigned-to-me')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        task_ids = [t['id'] for t in response.data]

        assert self.task1.id in task_ids
        assert self.task2.id in task_ids
        assert self.task3.id in task_ids
        assert self.task4.id not in task_ids
        assert len(task_ids) == 3

    def test_different_annotator_sees_different_tasks(self):
        """Different annotator sees different assigned tasks"""
        self.client.force_authenticate(user=self.annotator2)
        url = reverse('tasks:api:tasks-assigned-to-me')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        task_ids = [t['id'] for t in response.data]

        assert self.task1.id not in task_ids
        assert self.task2.id in task_ids
        assert self.task3.id not in task_ids
        assert len(task_ids) == 1

    def test_annotator_with_no_assignments_sees_empty_list(self):
        """Annotator with no assignments sees empty list"""
        annotator3 = UserFactory(active_organization=self.organization)
        ProjectMember.objects.create(project=self.project1, user=annotator3, role=RoleChoices.ANNOTATOR)

        self.client.force_authenticate(user=annotator3)
        url = reverse('tasks:api:tasks-assigned-to-me')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_filter_by_project(self):
        """Can filter assigned tasks by project"""
        self.client.force_authenticate(user=self.annotator1)
        url = reverse('tasks:api:tasks-assigned-to-me')
        response = self.client.get(url, {'project': self.project1.id})

        assert response.status_code == status.HTTP_200_OK
        task_ids = [t['id'] for t in response.data]

        assert self.task1.id in task_ids
        assert self.task2.id in task_ids
        assert self.task3.id not in task_ids
        assert len(task_ids) == 2
