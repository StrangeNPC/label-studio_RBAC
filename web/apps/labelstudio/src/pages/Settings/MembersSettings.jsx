// RBAC-feature
import { useCallback, useContext, useEffect, useState } from "react";
import { Button, Userpic, useToast } from "@humansignal/ui";
import { Spinner } from "../../components";
import { ProjectContext } from "../../providers/ProjectProvider";
import { useAPI } from "../../providers/ApiProvider";
import { Block, Elem } from "../../utils/bem";
import { RoleSelector } from "./RoleSelector";
import "./members-settings.scss";

const ROLE_LABELS = {
  owner: "Owner",
  admin: "Admin",
  manager: "Manager",
  reviewer: "Reviewer",
  annotator: "Annotator",
  viewer: "Viewer",
};

const ROLE_DESCRIPTIONS = {
  owner: "Full access to all project features including deletion",
  admin: "Full access except project deletion and owner transfer",
  manager: "Can manage tasks, assignments, and view all annotations",
  reviewer: "Can review and approve annotations",
  annotator: "Can create and edit own annotations",
  viewer: "Read-only access to project",
};

export const MembersSettings = () => {
  const { project } = useContext(ProjectContext);
  const api = useAPI();
  const toast = useToast();
  const [members, setMembers] = useState(null);
  const [currentUserRole, setCurrentUserRole] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMembers = useCallback(async () => {
    if (!project?.id) return;

    try {
      setLoading(true);
      const response = await api.callApi("projectMembers", {
        params: { pk: project.id },
      });

      if (response) {
        setMembers(response);
      }
    } catch (error) {
      console.error("Failed to fetch project members:", error);
    } finally {
      setLoading(false);
    }
  }, [project?.id, api]);

  const fetchCurrentUserRole = useCallback(async () => {
    if (!project?.id) return;

    try {
      const response = await api.callApi("currentUserRole", {
        params: { pk: project.id },
      });

      if (response?.role) {
        setCurrentUserRole(response.role);
        setCurrentUserId(response.user_id);
      }
    } catch (error) {
      console.error("Failed to fetch current user role:", error);
    }
  }, [project?.id, api]);

  useEffect(() => {
    fetchMembers();
    fetchCurrentUserRole();
  }, [fetchMembers, fetchCurrentUserRole]);

  const handleRoleChange = useCallback(
    async (memberId, newRole) => {
      try {
        await api.callApi("updateProjectMember", {
          params: {
            pk: project.id,
            memberPk: memberId,
          },
          body: {
            role: newRole,
          },
        });

        toast.show({ message: "Role updated successfully" });
        // Refresh members list
        await fetchMembers();
      } catch (error) {
        console.error("Failed to update member role:", error);
        toast.show({ message: `Failed to update role: ${error.message}`, type: "error" });
      }
    },
    [project?.id, api, fetchMembers, toast]
  );

  const handleRemoveMember = useCallback(
    async (memberId) => {
      const confirmed = window.confirm("Are you sure you want to remove this member?");

      if (!confirmed) return;

      try {
        await api.callApi("deleteProjectMember", {
          params: {
            pk: project.id,
            memberPk: memberId,
          },
        });

        toast.show({ message: "Member removed successfully" });
        // Refresh members list
        await fetchMembers();
      } catch (error) {
        console.error("Failed to remove member:", error);
        toast.show({ message: `Failed to remove member: ${error.message}`, type: "error" });
      }
    },
    [project?.id, api, fetchMembers, toast]
  );

  const canManageMembers = currentUserRole && ["owner", "admin"].includes(currentUserRole);

  if (loading) {
    return (
      <Block name="members-settings">
        <Elem name="loading">
          <Spinner size={36} />
        </Elem>
      </Block>
    );
  }

  return (
    <Block name="members-settings">
      <Elem name="wrapper">
        <h1>Members</h1>
        <Elem name="description">
          Manage project members and their roles. Only Owners and Admins can modify member roles.
        </Elem>

        <Elem name="members-table">
          <Elem name="table-header">
            <Elem name="column" mix="avatar" />
            <Elem name="column" mix="name">
              Name
            </Elem>
            <Elem name="column" mix="email">
              Email
            </Elem>
            <Elem name="column" mix="role">
              Role
            </Elem>
            {canManageMembers && (
              <Elem name="column" mix="actions">
                Actions
              </Elem>
            )}
          </Elem>

          <Elem name="table-body">
            {members && members.length > 0 ? (
              members.map((member) => {
                const isOwner = member.role === "owner";
                const isCurrentUser = member.user.id === currentUserId;
                const ownerCount = members.filter((m) => m.role === "owner").length;
                const isLastOwner = isOwner && ownerCount === 1;

                return (
                  <Elem key={member.id} name="member-row">
                    <Elem name="field" mix="avatar">
                      <Userpic user={member.user} style={{ width: 32, height: 32 }} />
                    </Elem>
                    <Elem name="field" mix="name">
                      {member.user.first_name} {member.user.last_name}
                      {isCurrentUser && <Elem name="badge" mix="you">You</Elem>}
                    </Elem>
                    <Elem name="field" mix="email">
                      {member.user.email}
                    </Elem>
                    <Elem name="field" mix="role">
                      <RoleSelector
                        currentRole={member.role}
                        onChange={(newRole) => handleRoleChange(member.id, newRole)}
                        disabled={!canManageMembers || isLastOwner}
                        roleLabels={ROLE_LABELS}
                        roleDescriptions={ROLE_DESCRIPTIONS}
                      />
                    </Elem>
                    {canManageMembers && (
                      <Elem name="field" mix="actions">
                        <Button
                          size="small"
                          look="danger"
                          onClick={() => handleRemoveMember(member.id)}
                          disabled={isLastOwner}
                          title={isLastOwner ? "Cannot remove the last owner" : "Remove member"}
                        >
                          Remove
                        </Button>
                      </Elem>
                    )}
                  </Elem>
                );
              })
            ) : (
              <Elem name="empty">No members found</Elem>
            )}
          </Elem>
        </Elem>
      </Elem>
    </Block>
  );
};

MembersSettings.menuItem = "Members";
MembersSettings.path = "/members";
MembersSettings.exact = true;
