from rest_framework.permissions import BasePermission
import rules


class ProjectImportPermission(BasePermission):
    """
    Checks if the user has access to the project import API
    Default case is always true
    """

    def has_permission(self, request, view):
        return True


# =============================================================================
# RBAC-feature: Django-rules predicates for role-based access control
# =============================================================================

"""
Permission predicates for Label Studio RBAC system using django-rules.

This module defines role-based access control predicates for projects, tasks, and annotations.
Predicates are registered with django-rules and can be checked using user.has_perm().

Role Hierarchy:
- Owner: Full control over project
- Admin: Administrative access, can manage members and settings
- Manager: Task management, can assign tasks and review annotations
- Annotator: Data labeling, can create/edit own annotations
- Reviewer: Quality control, can review and approve annotations
- Viewer: Read-only access to tasks and annotations

Usage:
    user.has_perm('projects.view', project)
    user.has_perm('tasks.create', project)
    user.has_perm('annotations.delete', project)
"""

from projects.models import ProjectMember, RoleChoices


# RBAC-feature
@rules.predicate
def is_authenticated(user):
    """Check if user is authenticated."""
    return user and user.is_authenticated


# RBAC-feature
@rules.predicate
def is_superuser(user):
    """Check if user is a superuser (bypasses all permission checks)."""
    return user and user.is_superuser


# RBAC-feature
@rules.predicate
def is_project_member(user, project):
    """
    Check if user is an active member of the project.

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user is an enabled member or superuser
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.warning(f'[RBAC-DEBUG] is_project_member ENTRY: user={user.id if user else None}, project={project.id}')

    if not user or not user.is_authenticated:
        logger.warning(f'[RBAC-DEBUG] is_project_member FAIL: User not authenticated')
        return False

    if user.is_superuser:
        logger.warning(f'[RBAC-DEBUG] is_project_member PASS: User {user.id} is superuser')
        return True

    # Check organization membership first (THIS SHOULD NOT BE CALLED, Organization check is already done)
    # if not project.organization.has_permission(user):
    #     logger.warning(f'[RBAC-DEBUG] is_project_member FAIL: User {user.id} not in organization {project.organization.id}')
    #     return False

    # Check ProjectMember
    logger.warning(f'[RBAC-DEBUG] Querying ProjectMember for user={user.id}, project={project.id}')
    member_exists = ProjectMember.objects.filter(
        user=user,
        project=project,
        enabled=True
    ).exists()

    logger.warning(f'[RBAC-DEBUG] ProjectMember query result: {member_exists}')

    # Log all members for debugging
    if not member_exists:
        all_members = list(ProjectMember.objects.filter(project=project).values('id', 'user_id', 'role', 'enabled'))
        logger.error(f'[RBAC-DEBUG] ProjectMember NOT FOUND! All members for project {project.id}: {all_members}')

    return member_exists


# RBAC-feature
@rules.predicate
def is_owner(user, project):
    """
    Check if user is the project owner.

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user has owner role or is superuser
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        member = ProjectMember.objects.get(
            user=user,
            project=project,
            enabled=True
        )
        return member.role == RoleChoices.OWNER
    except ProjectMember.DoesNotExist:
        return False


# RBAC-feature
@rules.predicate
def is_admin_or_owner(user, project):
    """
    Check if user is an admin or owner.

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user has admin or owner role or is superuser
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        member = ProjectMember.objects.get(
            user=user,
            project=project,
            enabled=True
        )
        return member.role in [RoleChoices.OWNER, RoleChoices.ADMIN]
    except ProjectMember.DoesNotExist:
        return False


# RBAC-feature
@rules.predicate
def is_manager_or_above(user, project):
    """
    Check if user is a manager, admin, or owner.

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user has manager, admin, or owner role or is superuser
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        member = ProjectMember.objects.get(
            user=user,
            project=project,
            enabled=True
        )
        return member.role in [
            RoleChoices.OWNER,
            RoleChoices.ADMIN,
            RoleChoices.MANAGER
        ]
    except ProjectMember.DoesNotExist:
        return False


# RBAC-feature
@rules.predicate
def is_reviewer_or_above(user, project):
    """
    Check if user is a reviewer, manager, admin, or owner.

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user has reviewer role or above or is superuser
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        member = ProjectMember.objects.get(
            user=user,
            project=project,
            enabled=True
        )
        return member.role in [
            RoleChoices.OWNER,
            RoleChoices.ADMIN,
            RoleChoices.MANAGER,
            RoleChoices.REVIEWER
        ]
    except ProjectMember.DoesNotExist:
        return False


# RBAC-feature
@rules.predicate
def can_create_annotations(user, project):
    """
    Check if user can create annotations (all roles except viewer).

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user can create annotations or is superuser
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        member = ProjectMember.objects.get(
            user=user,
            project=project,
            enabled=True
        )
        return member.role in [
            RoleChoices.OWNER,
            RoleChoices.ADMIN,
            RoleChoices.MANAGER,
            RoleChoices.ANNOTATOR,
            RoleChoices.REVIEWER
        ]
    except ProjectMember.DoesNotExist:
        return False


# =============================================================================
# PROJECT PERMISSIONS
# =============================================================================

# RBAC-feature: Override default permissions with RBAC predicates
# Note: core/permissions.py registers these with rules.is_authenticated by default
# We use remove + add pattern to override with our role-based predicates

import logging
logger = logging.getLogger(__name__)

# RBAC-feature: Register projects.view with proper RBAC predicate
# No need to remove existing permission since core/permissions.py no longer registers defaults
logger.warning(f'[RBAC-DEBUG] permissions.py: Registering projects.view permission')
logger.warning(f'[RBAC-DEBUG] permissions.py: perm_exists before = {rules.perm_exists("projects.view")}')
rules.add_perm('projects.view', is_project_member)
logger.warning(f'[RBAC-DEBUG] permissions.py: perm_exists after = {rules.perm_exists("projects.view")}')

# RBAC-feature
rules.add_perm('projects.change', is_admin_or_owner)

# RBAC-feature
rules.add_perm('projects.delete', is_owner)

# RBAC-feature
rules.add_perm('projects.manage_members', is_admin_or_owner)

# RBAC-feature
rules.add_perm('projects.view_members', is_manager_or_above)

# RBAC-feature
rules.add_perm('projects.export_data', is_manager_or_above)


# =============================================================================
# TASK PERMISSIONS
# =============================================================================

# RBAC-feature: Allow all project members to perform all task operations
rules.add_perm('tasks.view', is_project_member)
rules.add_perm('tasks.create', is_project_member)
rules.add_perm('tasks.change', is_project_member)
rules.add_perm('tasks.delete', is_project_member)
rules.add_perm('tasks.assign', is_project_member)


# =============================================================================
# ANNOTATION PERMISSIONS
# =============================================================================

# RBAC-feature: Allow all project members to perform all annotation operations
rules.add_perm('annotations.create', is_project_member)
rules.add_perm('annotations.change', is_project_member)
rules.add_perm('annotations.delete', is_project_member)
rules.add_perm('annotations.review', is_project_member)
