// RBAC-feature
import { useCallback, useContext, useEffect, useState } from "react";
import { useAPI } from "../providers/ApiProvider";
import { ProjectContext } from "../providers/ProjectProvider";

/**
 * Hook to get current user's permissions for a project based on their role.
 *
 * @returns {Object} Permission flags and role information
 * @property {boolean} canEdit - Can edit project settings (Owner, Admin)
 * @property {boolean} canDelete - Can delete project (Owner only)
 * @property {boolean} canManageMembers - Can manage project members (Owner, Admin)
 * @property {boolean} canAssignTasks - Can assign tasks to users (Owner, Admin, Manager)
 * @property {boolean} canManageTasks - Can manage tasks (Owner, Admin, Manager)
 * @property {boolean} canReview - Can review annotations (Owner, Admin, Manager, Reviewer)
 * @property {boolean} canAnnotate - Can create annotations (all roles except Viewer)
 * @property {boolean} isAnnotator - User has Annotator role
 * @property {boolean} isViewer - User has Viewer role (read-only)
 * @property {string|null} role - Current user's role
 * @property {boolean} loading - Whether role is still being fetched
 * @property {Function} refetch - Function to refetch user role
 */
export const useProjectPermissions = () => {
  const { project } = useContext(ProjectContext);
  const api = useAPI();
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRole = useCallback(async () => {
    if (!project?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await api.callApi("currentUserRole", {
        params: { pk: project.id },
      });

      if (response?.role) {
        setRole(response.role);
      }
    } catch (err) {
      console.error("Failed to fetch user role:", err);
      setError(err);
      // Default to most restrictive role on error
      setRole("viewer");
    } finally {
      setLoading(false);
    }
  }, [project?.id, api]);

  useEffect(() => {
    fetchRole();
  }, [fetchRole]);

  // Permission calculations based on role
  const canEdit = role && ["owner", "admin"].includes(role);
  const canDelete = role === "owner";
  const canManageMembers = role && ["owner", "admin"].includes(role);
  const canAssignTasks = role && ["owner", "admin", "manager"].includes(role);
  const canManageTasks = role && ["owner", "admin", "manager"].includes(role);
  const canReview = role && ["owner", "admin", "manager", "reviewer"].includes(role);
  const canAnnotate = role && role !== "viewer";
  const isAnnotator = role === "annotator";
  const isViewer = role === "viewer";

  return {
    role,
    loading,
    error,
    refetch: fetchRole,
    // Permission flags
    canEdit,
    canDelete,
    canManageMembers,
    canAssignTasks,
    canManageTasks,
    canReview,
    canAnnotate,
    isAnnotator,
    isViewer,
  };
};
