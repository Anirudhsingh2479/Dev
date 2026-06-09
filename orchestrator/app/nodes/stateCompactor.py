from __future__ import annotations

from ..models.contracts import AgentState
from ._shared import clone, log, task_id


async def stateCompactorNode(state: AgentState) -> AgentState:
    compacted = clone(state.taskQueue)
    for phase in compacted.get("phases", []):
        compacted_tasks = []
        for task in phase.get("tasks", []):
            if state.taskStatuses.get(task_id(task)) == "done":
                compacted_tasks.append({
                    "taskId": task_id(task),
                    "title": task.get("title"),
                    "filesToCreate": task.get("filesToCreate", []),
                    "canParallelize": task.get("canParallelize", False),
                })
            else:
                compacted_tasks.append(task)
        phase["tasks"] = compacted_tasks
    state.taskQueue = compacted
    state.terminalOutput = state.terminalOutput[-100:]
    log(state, "State Compactor trimmed completed task details")
    return state
