from typing import TYPE_CHECKING, Mapping, Optional

from core.redis import start_job_async_or_sync
from django.db.models import QuerySet
from django.utils.functional import cached_property
from projects.functions.utils import get_unique_ids_list

if TYPE_CHECKING:
    from users.models import User


class ProjectMixin:
    def rearrange_overlap_cohort(self):
        """
        Async start rearrange overlap depending on annotation count in tasks
        """
        start_job_async_or_sync(self._rearrange_overlap_cohort)

    def update_tasks_counters_and_is_labeled(self, tasks_queryset, from_scratch=True):
        """
        Async start updating tasks counters and than is_labeled
        :param tasks_queryset: Tasks to update queryset
        :param from_scratch: Skip calculated tasks
        """
        # get only id from queryset to decrease data size in job
        task_ids = get_unique_ids_list(tasks_queryset)
        start_job_async_or_sync(self._update_tasks_counters_and_is_labeled, task_ids, from_scratch=from_scratch)

    def update_tasks_counters_and_task_states(
        self,
        tasks_queryset,
        maximum_annotations_changed,
        overlap_cohort_percentage_changed,
        tasks_number_changed,
        from_scratch=True,
        recalculate_stats_counts: Optional[Mapping[str, int]] = None,
    ):
        """
        Async start updating tasks counters and than rearrange
        :param tasks_queryset: Tasks to update queryset
        :param maximum_annotations_changed: If maximum_annotations param changed
        :param overlap_cohort_percentage_changed: If cohort_percentage param changed
        :param tasks_number_changed: If tasks number changed in project
        :param from_scratch: Skip calculated tasks
        """
        # get only id from queryset to decrease data size in job
        task_ids = get_unique_ids_list(tasks_queryset)
        start_job_async_or_sync(
            self._update_tasks_counters_and_task_states,
            task_ids,
            maximum_annotations_changed,
            overlap_cohort_percentage_changed,
            tasks_number_changed,
            from_scratch=from_scratch,
            recalculate_stats_counts=recalculate_stats_counts,
        )

    def update_tasks_states(
        self, maximum_annotations_changed, overlap_cohort_percentage_changed, tasks_number_changed
    ):
        """
        Async start updating tasks states after settings change
        :param maximum_annotations_changed: If maximum_annotations param changed
        :param overlap_cohort_percentage_changed: If cohort_percentage param changed
        :param tasks_number_changed: If tasks number changed in project
        """
        start_job_async_or_sync(
            self._update_tasks_states,
            maximum_annotations_changed,
            overlap_cohort_percentage_changed,
            tasks_number_changed,
        )

    def has_permission(self, user):
        """
        Check if user has permission to access this project.

        This method implements role-based access control (RBAC) for projects.
        It checks:
        1. User authentication
        2. Superuser status (bypass)
        3. Organization membership
        4. Project membership via django-rules

        Args:
            user: User instance to check permissions for

        Returns:
            bool: True if user has access to the project, False otherwise
        """
        import logging
        import rules

        logger = logging.getLogger(__name__)
        user.project = self

        logger.warning(f'[RBAC-DEBUG] Project.has_permission ENTRY: user={user.id if user else None}, project={self.id}')

        if not user or not user.is_authenticated:
            logger.warning(f'[RBAC-DEBUG] FAIL: User not authenticated for project {self.id}')
            return False

        if user.is_superuser:
            logger.warning(f'[RBAC-DEBUG] PASS: User {user.id} is superuser for project {self.id}')
            return True

        logger.warning(f'[RBAC-DEBUG] Checking organization permission for user {user.id} in org {self.organization.id}')
        if not self.organization.has_permission(user):
            logger.warning(f'[RBAC-DEBUG] FAIL: User {user.id} not member of organization {self.organization.id}')
            return False

        logger.warning(f'[RBAC-DEBUG] Testing django-rules projects.view for user {user.id} project {self.id}')

        # CRITICAL FIX: Django wraps request.user in SimpleLazyObject for lazy evaluation
        # django-rules has issues with lazy objects - we must unwrap it first
        from django.utils.functional import SimpleLazyObject
        if isinstance(user, SimpleLazyObject):
            logger.warning(f'[RBAC-DEBUG] User is SimpleLazyObject, unwrapping...')
            # Access _wrapped to get the actual User instance
            user = user._wrapped if hasattr(user, '_wrapped') else user
            logger.warning(f'[RBAC-DEBUG] Unwrapped user type: {type(user)}')

        # Import the predicate directly and test it
        try:
            from projects.permissions import is_project_member
            logger.warning(f'[RBAC-DEBUG] Testing is_project_member predicate directly...')
            direct_result = is_project_member(user, self)
            logger.warning(f'[RBAC-DEBUG] is_project_member direct test result: {direct_result}')

            # If direct test passes, return True
            if direct_result:
                return True

            # If it fails, log why
            logger.error(f'[RBAC-DEBUG] is_project_member returned False for user={user.id} project={self.id}')
        except Exception as e:
            logger.error(f'[RBAC-DEBUG] Error calling is_project_member: {e}')
            import traceback
            logger.error(f'[RBAC-DEBUG] Traceback: {traceback.format_exc()}')

        # Fallback to rules.test_rule
        result = rules.test_rule('projects.view', user, self)
        logger.warning(f'[RBAC-DEBUG] Django-rules result: {result}')
        return result

    def has_perm(self, user, perm_name):
        """
        Check if user has specific permission on this project.

        Args:
            user: User instance to check permissions for
            perm_name: Permission name (e.g., 'projects.change', 'tasks.create')

        Returns:
            bool: True if user has the specified permission, False otherwise
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(f'[RBAC-DEBUG] has_perm ENTRY: user={user.id if user else None}, perm={perm_name}, project={self.id}')

        if not self.has_permission(user):
            logger.warning(f'[RBAC-DEBUG] has_perm FAIL: has_permission returned False')
            return False

        from projects.permissions import is_project_member, is_admin_or_owner, is_owner

        if perm_name in ['tasks.view', 'tasks.create', 'tasks.change', 'tasks.delete', 'tasks.assign',
                         'annotations.create', 'annotations.change', 'annotations.delete', 'annotations.review',
                         'projects.view']:
            result = is_project_member(user, self)
            logger.warning(f'[RBAC-DEBUG] has_perm using is_project_member for {perm_name}: {result}')
            return result
        elif perm_name in ['projects.change', 'projects.manage_members']:
            result = is_admin_or_owner(user, self)
            logger.warning(f'[RBAC-DEBUG] has_perm using is_admin_or_owner for {perm_name}: {result}')
            return result
        elif perm_name == 'projects.delete':
            result = is_owner(user, self)
            logger.warning(f'[RBAC-DEBUG] has_perm using is_owner for {perm_name}: {result}')
            return result

        logger.warning(f'[RBAC-DEBUG] has_perm PASS: default True for unknown perm {perm_name}')
        return True

    def check_permission(self, user, perm_name=None, raise_exception=True):
        """
        Check permission and optionally raise exception on failure.

        Args:
            user: User instance to check permissions for
            perm_name: Optional specific permission name
            raise_exception: If True, raise PermissionDenied on failure

        Returns:
            bool: True if permission granted

        Raises:
            PermissionDenied: If permission denied and raise_exception=True
        """
        from rest_framework.exceptions import PermissionDenied

        if perm_name:
            has_perm = self.has_perm(user, perm_name)
        else:
            has_perm = self.has_permission(user)

        if not has_perm and raise_exception:
            raise PermissionDenied("You don't have permission to access this project.")

        return has_perm

    def _can_use_overlap(self):
        """
        Returns if we can use overlap for is_labeled calculation
        :return:
        """
        return True

    @cached_property
    def all_members(self) -> QuerySet['User']:
        """
        Returns all users of project
        :return: QuerySet[User]
        """
        from users.models import User

        return User.objects.filter(id__in=self.organization.members.values_list('user__id'))
