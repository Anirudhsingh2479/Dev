from __future__ import annotations

from ..models.contracts import AgentState
from ..services.sandbox import start_sandbox_servers
from ._shared import log


async def presentToUserNode(state: AgentState) -> AgentState:
    if state.currentPhase == "failed" or state.error:
        log(state, f"Workflow stopped before completion: {state.error or 'retry limit reached'}")
        return state
    state.currentPhase = "done"
    if state.sandboxId:
        result = start_sandbox_servers(state.sandboxId)
        if result.get("frontendUrl"):
            state.previewFrontendUrl = result["frontendUrl"]
            state.previewFrontendPort = result.get("frontendPort")
            log(state, f"Open website: {result['frontendUrl']}")
        if result.get("backendUrl"):
            state.previewBackendUrl = result["backendUrl"]
            state.previewBackendPort = result.get("backendPort")
            log(state, f"Backend API: {result['backendUrl']}")
        if result.get("errors"):
            log(state, "Server start warnings: " + "; ".join(result["errors"]))
    log(state, "Present To User prepared final dashboard state")
    return state
