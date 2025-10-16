# Task Assignment API - Integration Guide

## Overview

This directory contains a **demonstration page** showing how to integrate task assignment functionality into Label Studio. The task assignment API allows Managers, Admins, and Owners to assign specific tasks to annotators.

## API Endpoints

The following endpoints are available for task assignment:

### 1. Assign Task to Users

**POST** `/api/tasks/:taskId/assign`

Assigns a task to one or more users.

**Request Body:**
```json
{
  "user_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "id": 123,
  "assigned_to": [1, 2, 3],
  "message": "Task assigned successfully"
}
```

**Example Usage:**
```javascript
await api.callApi("assignTask", {
  params: { taskId: 123 },
  body: { user_ids: [1, 2, 3] },
});
```

---

### 2. Unassign Task from Users

**DELETE** `/api/tasks/:taskId/unassign`

Removes user assignments from a task.

**Request Body:**
```json
{
  "user_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "id": 123,
  "assigned_to": [],
  "message": "Task unassigned successfully"
}
```

**Example Usage:**
```javascript
await api.callApi("unassignTask", {
  params: { taskId: 123 },
  body: { user_ids: [1, 2, 3] },
});
```

---

### 3. Get Tasks Assigned to Current User

**GET** `/api/tasks/assigned-to-me?project=:projectId`

Returns all tasks assigned to the currently authenticated user in a specific project.

**Query Parameters:**
- `project` (required): Project ID

**Response:**
```json
[
  {
    "id": 123,
    "data": { "text": "Example task data" },
    "assigned_to": [1],
    "project": 5,
    "created_at": "2025-01-16T10:00:00Z"
  },
  ...
]
```

**Example Usage:**
```javascript
const response = await api.callApi("tasksAssignedToMe", {
  params: { project: 5 },
});

console.log(`You have ${response.length} tasks assigned`);
```

---

## Integration into Data Manager

To integrate task assignment into the Data Manager, follow these steps:

### Step 1: Add Assignment Column

Add an "Assigned To" column to the task list:

```javascript
// In DataManager columns configuration
{
  id: "assigned_to",
  title: "Assigned To",
  type: "Array",
  render: (task) => {
    const assignedUsers = task.assigned_to?.map(userId => {
      const user = members.find(m => m.user.id === userId);
      return user ? `${user.user.first_name} ${user.user.last_name}` : `User ${userId}`;
    }).join(", ");

    return assignedUsers || "Unassigned";
  }
}
```

### Step 2: Add Bulk Assignment Action

Add a bulk action to assign multiple tasks at once:

```javascript
// In DataManager bulk actions
{
  id: "assign-tasks",
  label: "Assign to User",
  icon: "user-plus",
  action: async (selectedTasks) => {
    const userIds = await showUserSelectionDialog();

    await Promise.all(
      selectedTasks.map(task =>
        api.callApi("assignTask", {
          params: { taskId: task.id },
          body: { user_ids: userIds },
        })
      )
    );

    showNotification("Tasks assigned successfully");
    refreshTaskList();
  },
  permission: "canAssignTasks", // Only Managers+
}
```

### Step 3: Add "My Tasks" Filter

Add a filter to show only tasks assigned to the current user:

```javascript
// In DataManager filters
{
  id: "assigned-to-me",
  label: "Assigned to Me",
  type: "boolean",
  default: false,
  apply: async (enabled) => {
    if (!enabled) return null;

    const myTasks = await api.callApi("tasksAssignedToMe", {
      params: { project: projectId },
    });

    return {
      task_ids: myTasks.map(t => t.id),
    };
  },
  visible: isAnnotator, // Show for annotators
}
```

### Step 4: Add Assignment Context Menu

Add right-click menu option to assign individual tasks:

```javascript
// In DataManager task context menu
{
  id: "assign",
  label: "Assign to...",
  icon: "user-plus",
  action: async (task) => {
    const userIds = await showUserSelectionDialog();

    await api.callApi("assignTask", {
      params: { taskId: task.id },
      body: { user_ids: userIds },
    });

    showNotification("Task assigned successfully");
    refreshTask(task.id);
  },
  permission: "canAssignTasks",
}
```

---

## Permission Requirements

Task assignment requires specific permissions:

| Action | Required Role | Permission Flag |
|--------|---------------|-----------------|
| Assign tasks | Manager, Admin, Owner | `canAssignTasks` |
| Unassign tasks | Manager, Admin, Owner | `canAssignTasks` |
| View assigned tasks | All (own tasks only) | N/A |
| View all assignments | Manager, Admin, Owner | `canManageTasks` |

Use the `useProjectPermissions` hook to check permissions:

```javascript
import { useProjectPermissions } from "../../hooks/useProjectPermissions";

const { canAssignTasks, isAnnotator } = useProjectPermissions();

// Show assignment UI only to authorized users
{canAssignTasks && <AssignmentButton />}

// Show "My Tasks" filter to annotators
{isAnnotator && <MyTasksFilter />}
```

---

## Demo Page

The `TaskAssignment.jsx` file in this directory provides a working demonstration of all three API endpoints. To test it:

1. **Add the page to Settings** (optional, for testing):
   ```javascript
   // In Settings/index.jsx
   import { TaskAssignment } from "../TaskAssignment/TaskAssignment";

   menuItems={[
     // ... other items
     TaskAssignment, // Demo page
   ]}
   ```

2. **Navigate to the demo page** in project settings

3. **Test the functionality**:
   - Select a task from the dropdown
   - Click on users to select them
   - Click "Assign Task" to assign
   - Click "Unassign All" to remove assignments
   - Click "View My Assigned Tasks" to see your tasks

---

## Backend Implementation

The backend implementation for task assignment is located in:

- **Model**: `label_studio/tasks/models.py` - Task model with `assigned_to` ManyToManyField
- **Serializers**: `label_studio/tasks/serializers.py` - TaskSerializer with assignment fields
- **Views**: `label_studio/tasks/api.py` - TaskViewSet with assignment endpoints
- **Permissions**: `label_studio/projects/permissions.py` - Role-based permission checks

### Database Schema

```sql
-- Task assignment table (many-to-many)
CREATE TABLE task_assignments (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    user_id INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP,
    assigned_by_id INTEGER REFERENCES users(id),
    UNIQUE(task_id, user_id)
);

-- Index for fast lookups
CREATE INDEX idx_task_assignments_user ON task_assignments(user_id);
CREATE INDEX idx_task_assignments_task ON task_assignments(task_id);
```

---

## Error Handling

Handle common errors when working with task assignment:

```javascript
try {
  await api.callApi("assignTask", {
    params: { taskId: 123 },
    body: { user_ids: [1, 2, 3] },
  });
} catch (error) {
  if (error.status === 403) {
    showError("You don't have permission to assign tasks");
  } else if (error.status === 404) {
    showError("Task not found");
  } else if (error.status === 400) {
    showError("Invalid user IDs provided");
  } else {
    showError("Failed to assign task. Please try again.");
  }
}
```

---

## Testing Checklist

- [ ] Manager can assign tasks to annotators
- [ ] Admin can assign tasks to annotators
- [ ] Owner can assign tasks to annotators
- [ ] Annotators cannot assign tasks (403 error)
- [ ] Viewers cannot assign tasks (403 error)
- [ ] Assigned tasks appear in "My Tasks" filter for annotators
- [ ] Bulk assignment works for multiple tasks
- [ ] Unassignment removes task from user's assigned list
- [ ] Task assignment persists after page refresh
- [ ] Assignment changes are reflected in real-time

---

## Future Enhancements

Potential improvements for task assignment:

1. **Email Notifications** - Notify users when tasks are assigned to them
2. **Task Deadlines** - Set due dates for assigned tasks
3. **Assignment History** - Track who assigned tasks and when
4. **Auto-Assignment** - Automatically distribute tasks based on workload
5. **Task Priority** - Prioritize certain assignments
6. **Batch Import** - Import task assignments from CSV
7. **Assignment Analytics** - Track assignment completion rates
8. **Reassignment** - Easily reassign tasks from one user to another

---

## Related Files

- `ApiConfig.js` - API endpoint definitions
- `useProjectPermissions.js` - Permission checking hook
- `TaskAssignment.jsx` - Demo page implementation
- `task-assignment.scss` - Demo page styles
- `TICKET-011-add-task-assignment-ui.md` - Original ticket specification

---

## Support

For questions or issues with task assignment:

1. Check the backend API logs for errors
2. Verify user roles and permissions
3. Test with the demo page first
4. Review the RBAC implementation tickets (TICKET-001 through TICKET-011)
5. Consult the Label Studio documentation on RBAC

---

**Last Updated**: 2025-01-16
**Feature Status**: Demo Implementation Complete
**Production Ready**: Requires Data Manager integration
