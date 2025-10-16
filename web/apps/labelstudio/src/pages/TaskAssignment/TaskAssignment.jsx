// RBAC-feature
/**
 * Task Assignment Demo Page
 *
 * This is a demonstration page showing how to use the task assignment API.
 * It provides a simple interface to:
 * - View tasks
 * - Assign tasks to users
 * - Unassign tasks from users
 * - View tasks assigned to the current user
 *
 * For production, these features should be integrated into the Data Manager.
 */

import { useCallback, useContext, useEffect, useState } from "react";
import { Button, Userpic, Typography, useToast } from "@humansignal/ui";
import { Spinner } from "../../components";
import { ProjectContext } from "../../providers/ProjectProvider";
import { useAPI } from "../../providers/ApiProvider";
import { useProjectPermissions } from "../../hooks/useProjectPermissions";
import { Block, Elem } from "../../utils/bem";
import "./task-assignment.scss";

export const TaskAssignment = () => {
  const { project } = useContext(ProjectContext);
  const api = useAPI();
  const toast = useToast();
  const { canAssignTasks, isAnnotator } = useProjectPermissions();

  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState([]);

  // Fetch project members
  const fetchMembers = useCallback(async () => {
    if (!project?.id) return;

    try {
      const response = await api.callApi("projectMembers", {
        params: { pk: project.id },
      });

      if (response) {
        setMembers(response);
      }
    } catch (error) {
      console.error("Failed to fetch members:", error);
    }
  }, [project?.id, api]);

  // Fetch tasks (mock - in real implementation, use Data Manager API)
  const fetchTasks = useCallback(async () => {
    if (!project?.id) return;

    try {
      setLoading(true);

      // For demo purposes, we'll show a message about API integration
      // In production, you would fetch tasks from the Data Manager API

      setTasks([
        {
          id: 1,
          data: { text: "Example Task 1" },
          assigned_to: [],
        },
        {
          id: 2,
          data: { text: "Example Task 2" },
          assigned_to: [1],
        },
      ]);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  }, [project?.id]);

  useEffect(() => {
    fetchMembers();
    fetchTasks();
  }, [fetchMembers, fetchTasks]);

  // Assign task to users
  const handleAssign = useCallback(async () => {
    if (!selectedTask || selectedUsers.length === 0) return;

    try {
      await api.callApi("assignTask", {
        params: { taskId: selectedTask.id },
        body: { user_ids: selectedUsers },
      });

      toast.show({ message: `Task ${selectedTask.id} assigned successfully!` });

      // Refresh tasks
      await fetchTasks();

      // Clear selection
      setSelectedTask(null);
      setSelectedUsers([]);
    } catch (error) {
      console.error("Failed to assign task:", error);
      toast.show({ message: `Failed to assign task: ${error.message}`, type: "error" });
    }
  }, [selectedTask, selectedUsers, api, fetchTasks, toast]);

  // Unassign task from users
  const handleUnassign = useCallback(
    async (taskId, userIds) => {
      try {
        await api.callApi("unassignTask", {
          params: { taskId },
          body: { user_ids: userIds },
        });

        toast.show({ message: `Task ${taskId} unassigned successfully!` });

        // Refresh tasks
        await fetchTasks();
      } catch (error) {
        console.error("Failed to unassign task:", error);
        toast.show({ message: `Failed to unassign task: ${error.message}`, type: "error" });
      }
    },
    [api, fetchTasks, toast]
  );

  // View tasks assigned to current user
  const handleViewMyTasks = useCallback(async () => {
    try {
      const response = await api.callApi("tasksAssignedToMe", {
        params: { project: project.id },
      });

      console.log("Tasks assigned to me:", response);
      toast.show({ message: `You have ${response?.length || 0} tasks assigned. Check console for details.` });
    } catch (error) {
      console.error("Failed to fetch assigned tasks:", error);
      toast.show({ message: `Failed to fetch assigned tasks: ${error.message}`, type: "error" });
    }
  }, [api, project?.id, toast]);

  if (loading) {
    return (
      <Block name="task-assignment">
        <Elem name="loading">
          <Spinner size={36} />
        </Elem>
      </Block>
    );
  }

  return (
    <Block name="task-assignment">
      <Elem name="wrapper">
        <Typography variant="headline" size="large" className="mb-base">
          Task Assignment Demo
        </Typography>

        <Elem name="info-box">
          <Typography variant="body" size="medium">
            <strong>Note:</strong> This is a demonstration page showing the task assignment API.
            <br />
            API Endpoints Available:
          </Typography>
          <ul>
            <li>
              <code>POST /api/tasks/:taskId/assign/</code> - Assign users to a task
            </li>
            <li>
              <code>DELETE /api/tasks/:taskId/unassign/</code> - Remove user assignments
            </li>
            <li>
              <code>GET /api/tasks/assigned-to-me/</code> - Get tasks assigned to current user
            </li>
          </ul>
        </Elem>

        {isAnnotator && (
          <Elem name="section">
            <Typography variant="title" size="large" className="mb-tight">
              My Assigned Tasks
            </Typography>
            <Button onClick={handleViewMyTasks} className="mb-base">
              View My Assigned Tasks
            </Button>
            <Typography variant="body" size="small" className="text-neutral-content-subtler">
              Click to fetch tasks assigned to you. Results will appear in the browser console.
            </Typography>
          </Elem>
        )}

        {canAssignTasks && (
          <>
            <Elem name="section">
              <Typography variant="title" size="large" className="mb-tight">
                Assign Tasks
              </Typography>

              <Elem name="assignment-form">
                <Elem name="form-group">
                  <label>Select Task:</label>
                  <select
                    value={selectedTask?.id || ""}
                    onChange={(e) => {
                      const task = tasks.find((t) => t.id === Number(e.target.value));
                      setSelectedTask(task);
                    }}
                  >
                    <option value="">-- Select a task --</option>
                    {tasks.map((task) => (
                      <option key={task.id} value={task.id}>
                        Task {task.id}: {task.data?.text || "No description"}
                      </option>
                    ))}
                  </select>
                </Elem>

                <Elem name="form-group">
                  <label>Select Users to Assign:</label>
                  <Elem name="user-list">
                    {members.map((member) => (
                      <Elem
                        key={member.id}
                        name="user-item"
                        mod={{ selected: selectedUsers.includes(member.user.id) }}
                        onClick={() => {
                          setSelectedUsers((prev) =>
                            prev.includes(member.user.id)
                              ? prev.filter((id) => id !== member.user.id)
                              : [...prev, member.user.id]
                          );
                        }}
                      >
                        <Userpic user={member.user} style={{ width: 24, height: 24 }} />
                        <span>
                          {member.user.first_name} {member.user.last_name}
                        </span>
                        <Elem name="role-badge">{member.role}</Elem>
                      </Elem>
                    ))}
                  </Elem>
                </Elem>

                <Button
                  onClick={handleAssign}
                  disabled={!selectedTask || selectedUsers.length === 0}
                  className="mt-base"
                >
                  Assign Task
                </Button>
              </Elem>
            </Elem>

            <Elem name="section">
              <Typography variant="title" size="large" className="mb-tight">
                Current Task Assignments (Demo Data)
              </Typography>

              <Elem name="task-list">
                {tasks.map((task) => (
                  <Elem key={task.id} name="task-item">
                    <Elem name="task-info">
                      <strong>Task {task.id}:</strong> {task.data?.text || "No description"}
                    </Elem>
                    <Elem name="task-assignments">
                      {task.assigned_to && task.assigned_to.length > 0 ? (
                        <>
                          <span>Assigned to: </span>
                          {task.assigned_to.map((userId) => {
                            const member = members.find((m) => m.user.id === userId);
                            return member ? (
                              <Elem key={userId} name="assignment-badge">
                                <Userpic user={member.user} style={{ width: 20, height: 20 }} />
                                {member.user.first_name} {member.user.last_name}
                              </Elem>
                            ) : null;
                          })}
                          <Button
                            size="small"
                            look="outlined"
                            onClick={() => handleUnassign(task.id, task.assigned_to)}
                          >
                            Unassign All
                          </Button>
                        </>
                      ) : (
                        <span className="text-neutral-content-subtler">Not assigned</span>
                      )}
                    </Elem>
                  </Elem>
                ))}
              </Elem>
            </Elem>
          </>
        )}

        {!canAssignTasks && !isAnnotator && (
          <Elem name="no-permission">
            <Typography variant="body" size="medium">
              You do not have permission to assign tasks or view assigned tasks.
            </Typography>
          </Elem>
        )}
      </Elem>
    </Block>
  );
};
