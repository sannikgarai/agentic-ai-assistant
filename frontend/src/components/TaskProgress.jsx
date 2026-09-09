
import React from "react";

function TaskProgress({
  tasks = [],
  currentTask = null,
  completed = false,
}) {
  if (!tasks || tasks.length === 0) {
    return null;
  }

  const getTaskStatus = (task, index) => {
    if (task.status) {
      return task.status;
    }

    if (completed) {
      return "completed";
    }

    if (currentTask === index || currentTask === task.id) {
      return "running";
    }

    if (index < currentTask) {
      return "completed";
    }

    return "pending";
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return "✓";

      case "running":
      case "in_progress":
        return "⟳";

      case "failed":
        return "✕";

      default:
        return "○";
    }
  };

  const completedCount = tasks.filter(
    (task, index) =>
      getTaskStatus(task, index) === "completed"
  ).length;

  const progress = Math.round(
    (completedCount / tasks.length) * 100
  );

  return (
    <div className="task-progress">

      <div className="task-progress-header">
        <div>
          <h3>Task Progress</h3>
          <span>
            {completedCount} of {tasks.length} completed
          </span>
        </div>

        <strong>{progress}%</strong>
      </div>

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="task-list">
        {tasks.map((task, index) => {
          const status = getTaskStatus(task, index);

          return (
            <div
              key={task.id || index}
              className={`task-item ${status}`}
            >
              <div className="task-status-icon">
                {getStatusIcon(status)}
              </div>

              <div className="task-details">
                <strong>
                  {task.title ||
                    task.name ||
                    `Task ${index + 1}`}
                </strong>

                {task.description && (
                  <p>{task.description}</p>
                )}

                {status === "running" && (
                  <small>Processing...</small>
                )}

                {status === "failed" && (
                  <small>Task failed</small>
                )}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}

export default TaskProgress;
