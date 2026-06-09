from __future__ import annotations

from ..models.contracts import AgentState
from ._shared import log, task_id


async def selectNextTaskNode(state: AgentState) -> AgentState:
    phases = state.taskQueue.get("phases", [])
    if not phases:
        state.currentTask = None
        state.currentPhase = "done"
        log(state, "No phases in task queue")
        return state

    for phase in phases:
        tasks = phase.get("tasks", [])
        for task in tasks:
            tid = task_id(task)
            if state.taskStatuses.get(tid) in {None, "pending"}:
                state.currentTask = task
                state.currentPhaseIndex = phase.get("phaseNumber", 1) - 1
                state.taskStatuses[tid] = "in_progress"
                state.currentPhase = "dev_loop"
                log(state, f"Selected next task {tid}")
                return state

        all_done = bool(tasks) and all(state.taskStatuses.get(task_id(task)) == "done" for task in tasks)
        verified_key = f"phase-{phase.get('phaseNumber')}-verified"
        if all_done and state.taskStatuses.get(verified_key) != "done":
            state.currentTask = {"taskId": f"phase-{phase.get('phaseNumber')}-verify", "type": "phase_verification", "phase": phase}
            state.currentPhase = "phase_verification"
            log(state, f"Selected phase verification for phase {phase.get('phaseNumber')}")
            return state

    state.currentTask = None
    state.currentPhase = "done"
    log(state, "All tasks complete")
    return state


def selectNextTaskRouter(state: AgentState) -> str:
    if state.currentPhase == "done":
        return "presentToUser"
    if state.currentPhase == "phase_verification":
        return "phaseVerification"
    if state.currentTask:
        return "contextBuilder"
    return "presentToUser"
