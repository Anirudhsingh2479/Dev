from __future__ import annotations

from ..models.contracts import AgentState
from ..services.sandbox import git_snapshot
from ._shared import log, reset_retry, task_id


async def snapshotManagerNode(state: AgentState) -> AgentState:
    tid = task_id(state.currentTask)
    task = state.currentTask
    if state.currentTask:
        state.taskStatuses[tid] = "done"
    snapshot = git_snapshot(state.projectId, f"Task {tid}: {(state.currentTask or {}).get('title', '')}")
    state.gitSnapshots.append(snapshot)
    state.reviewResult = {"verdict": "", "issues": [], "reviewCycle": 0}
    state.executionResult = {"result": "", "output": "", "errors": ""}
    state.debugState = {"tier": 1, "attempts": 0, "maxAttempts": 3, "rollbackAttempted": False}
    reset_retry(state, "reviewRejections", task)
    reset_retry(state, "debugAttempts", task)
    state.coderOutput = None
    state.contextPackage = None
    state.currentTask = None
    snapshot_label = snapshot.get("tag") if isinstance(snapshot, dict) and snapshot.get("success") else snapshot
    log(state, f"Snapshot saved for {tid}: {snapshot_label}")
    return state
