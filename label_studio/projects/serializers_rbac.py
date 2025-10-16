# RBAC-feature
"""
Serializers for RBAC (Role-Based Access Control) features.

This module provides serializers for managing project member roles and permissions.
"""

from rest_framework import serializers
from projects.models import ProjectMember, RoleChoices
from users.serializers import UserSimpleSerializer
from organizations.models import OrganizationMember


class ProjectMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectMember with role information.

    Used for listing and creating project members with roles.
    """

    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'user_id', 'role', 'role_display', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'enabled']

    def validate_role(self, value):
        """
        Validate that role is a valid choice.
        """
        if value not in RoleChoices.values:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(RoleChoices.values)}"
            )
        return value

    def validate_user_id(self, value):
        """
        Validate that user exists and is in the organization.
        """
        from users.models import User

        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        project = self.context.get('project')
        if not project:
            raise serializers.ValidationError("Project context is required.")

        is_org_member = OrganizationMember.objects.filter(
            user=user,
            organization=project.organization,
            deleted_at__isnull=True
        ).exists()

        if not is_org_member:
            raise serializers.ValidationError(
                "User must be a member of the project's organization."
            )

        return value

    def create(self, validated_data):
        """
        Create or update ProjectMember.

        If member already exists, update their role instead of creating duplicate.
        """
        from users.models import User

        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        project = self.context.get('project')

        member, created = ProjectMember.objects.update_or_create(
            user=user,
            project=project,
            defaults={'role': validated_data.get('role', RoleChoices.ANNOTATOR)}
        )

        return member


class ProjectMemberRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project member roles.

    Validates role changes and prevents invalid operations like changing owner role.
    """

    class Meta:
        model = ProjectMember
        fields = ['role']

    def validate_role(self, value):
        """
        Validate role change.

        - Cannot change owner role (ownership transfer not implemented)
        - Must be valid role choice
        """
        if value not in RoleChoices.values:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(RoleChoices.values)}"
            )

        instance = self.instance
        if instance and instance.role == RoleChoices.OWNER:
            raise serializers.ValidationError(
                "Cannot change the role of an owner. Ownership transfer is not yet implemented."
            )

        return value


class CurrentUserRoleSerializer(serializers.Serializer):
    """
    Serializer for current user's role and permissions in a project.

    Returns the user's role and a list of permissions they have.
    """

    user_id = serializers.IntegerField()
    role = serializers.CharField()
    role_display = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())

    def to_representation(self, instance):
        """
        Build representation with role and permissions.

        Args:
            instance: ProjectMember instance

        Returns:
            dict with role, role_display, and permissions list
        """
        import rules

        project = instance.project
        user = instance.user

        all_permissions = [
            'projects.view',
            'projects.change',
            'projects.delete',
            'projects.manage_members',
            'projects.view_members',
            'projects.export_data',
            'tasks.view',
            'tasks.create',
            'tasks.change',
            'tasks.delete',
            'tasks.assign',
            'annotations.create',
            'annotations.change',
            'annotations.delete',
            'annotations.review',
        ]

        user_permissions = [
            perm for perm in all_permissions
            if rules.test_rule(perm, user, project)
        ]

        return {
            'user_id': user.id,
            'role': instance.role,
            'role_display': instance.get_role_display(),
            'permissions': user_permissions
        }
