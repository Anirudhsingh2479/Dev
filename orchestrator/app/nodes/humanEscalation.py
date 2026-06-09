from __future__ import annotations

from ..models.contracts import AgentState
from ._shared import log, reset_retry, task_id
from ..services.input_bridge import wait_for_input


async def humanEscalationNode(state: AgentState) -> AgentState:
    tid = task_id(state.currentTask)
    response = await wait_for_input(
        state.projectId,
        "escalation",
        {
            "task": state.currentTask,
            "error": state.executionResult.get("errors", ""),
        },
    )
    choice = response.get("choice") or response.get("data", {}).get("choice") or "skip"
    guidance = response.get("guidance") or response.get("data", {}).get("guidance") or ""

    state.userFeedback.append({
        "type": "escalation",
        "taskId": tid,
        "message": state.executionResult.get("errors", ""),
        "choice": choice,
        "guidance": guidance,
    })

    if choice == "simplify":
        log(state, f"Human escalation requested simplification for {tid}")
        return state

    if choice == "guide":
        state.reviewResult = {
            "verdict": "rejected",
            "issues": [f"HUMAN GUIDANCE: {guidance}"],
            "reviewCycle": 0,
        }
        state.debugState = {"tier": 1, "attempts": 0, "maxAttempts": 3, "rollbackAttempted": False}
        reset_retry(state, "debugAttempts", state.currentTask)
        reset_retry(state, "reviewRejections", state.currentTask)
        log(state, f"Human escalation guidance recorded for {tid}")
        return state

    state.taskStatuses[tid] = "done"
    state.currentTask = None
    state.reviewResult = {"verdict": "", "issues": [], "reviewCycle": 0}
    state.debugState = {"tier": 1, "attempts": 0, "maxAttempts": 3, "rollbackAttempted": False}
    reset_retry(state, "debugAttempts", state.currentTask)
    reset_retry(state, "reviewRejections", state.currentTask)
    log(state, f"Human escalation skipped {tid}")
    return state


def humanEscalationRouter(state: AgentState) -> str:
    tid = task_id(state.currentTask)
    if not state.currentTask or state.taskStatuses.get(tid) == "done":
        return "selectNextTask"
    if any(str(issue).startswith("HUMAN GUIDANCE") for issue in state.reviewResult.get("issues", [])):
        return "contextBuilder"
    return "simplifyTask"
