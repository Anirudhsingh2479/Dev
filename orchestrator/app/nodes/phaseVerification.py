from __future__ import annotations

from ..models.contracts import AgentState
from .assembleEntryPoints import assembleBackendEntry, assembleFrontendEntry
from ._shared import log


async def phaseVerificationNode(state: AgentState) -> AgentState:
    phase = (state.currentTask or {}).get("phase", {})
    missing = []
    for task in phase.get("tasks", []):
        for file_path in task.get("filesToCreate", []):
            if file_path not in state.fileTree:
                missing.append(file_path)
    key = f"phase-{phase.get('phaseNumber', 0)}-verified"
    state.taskStatuses[key] = "failed" if missing else "done"
    state.executionResult = {"result": "fail" if missing else "pass", "output": "Phase files verified", "errors": "\n".join(missing)}

    phase_name = str(phase.get("phaseName", "")).lower()
    if any(word in phase_name for word in ["backend", "route", "api"]):
        assembleBackendEntry(state.projectId, state.fileRegistry, state.blueprint)
        state.fileTree = sorted(set([*state.fileTree, "backend/src/index.js"]))
    if any(word in phase_name for word in ["frontend", "page", "ui"]):
        assembleFrontendEntry(state.projectId, state.fileRegistry, state.blueprint)
        state.fileTree = sorted(set([*state.fileTree, "frontend/src/App.jsx"]))
    if any(word in phase_name for word in ["integration", "deploy", "assembly"]):
        assembleBackendEntry(state.projectId, state.fileRegistry, state.blueprint)
        assembleFrontendEntry(state.projectId, state.fileRegistry, state.blueprint)
        state.fileTree = sorted(set([*state.fileTree, "backend/src/index.js", "frontend/src/App.jsx"]))

    log(state, f"Phase verification {'failed' if missing else 'passed'} for phase {phase.get('phaseNumber')}")
    return state


def phaseVerificationRouter(state: AgentState) -> str:
    return "patternExtractor"
