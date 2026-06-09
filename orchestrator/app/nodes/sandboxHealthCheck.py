from __future__ import annotations

from ..models.contracts import AgentState
from ..services.sandbox import get_file_list, health_check
from ._shared import increment_retry, log, retry_count, retry_limit


async def sandboxHealthCheckNode(state: AgentState) -> AgentState:
    result = health_check(state.sandboxId)
    failures = result.get("failures", [])
    docker_only_failures = failures and all("container" in item or "node_modules" in item for item in failures)
    state.sandboxHealthy = bool(result.get("healthy")) or bool(result.get("sandboxPath") and docker_only_failures)
    state.fileTree = get_file_list(state.projectId)
    state.currentPhase = "dev_loop" if state.sandboxHealthy else "error"
    if state.sandboxHealthy:
        state.retryCounts.pop("sandboxSetup", None)
        log(state, "Sandbox health check passed" if result.get("healthy") else "Sandbox health check passed in local-only fallback mode")
    else:
        attempts = increment_retry(state, "sandboxSetup")
        max_attempts = retry_limit(state, "sandboxSetup", 2)
        log(state, f"Sandbox health check failed ({attempts}/{max_attempts}): " + "; ".join(result.get("failures", [])))
        if attempts >= max_attempts:
            state.error = f"Sandbox setup retry limit reached after {max_attempts} failed health check(s)."
            state.currentPhase = "failed"
            log(state, state.error)
    return state


def sandboxHealthRouter(state: AgentState) -> str:
    if not state.sandboxHealthy and retry_count(state, "sandboxSetup") >= retry_limit(state, "sandboxSetup", 2):
        return "presentToUser"
    return "__end__" if state.sandboxHealthy else "setupSandbox"
