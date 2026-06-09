from __future__ import annotations

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ..services.sandbox import get_file_list, read_file, rollback
from ._shared import apply_token_delta, increment_retry, log, reset_retry, retry_limit, task_id


DEBUGGER_PROMPT = """You are the Debugger Agent in an AI software development team.

ROLE: Expert debugger who reads error messages and identifies root causes.

GOAL: Analyze the error and provide a SPECIFIC fix that the Coder can implement.

OUTPUT FORMAT (strict JSON):
{
  "rootCause": "What exactly is wrong (1-2 lines)",
  "fix": "Specific code change needed",
  "affectedFiles": ["file1.js", "file2.js"],
  "confidence": "high | medium | low"
}

RULES:
- Be SPECIFIC. Not "fix the import" but "change line 5 from 'import X from Y' to 'import { X } from Y'"
- If the error is a missing dependency, say which package to install
- If the error is in a different file than expected, identify which file
- Read the error message carefully - the line number and file path tell you exactly where to look"""


async def debuggerAgentNode(state: AgentState) -> AgentState:
    debug_state = state.debugState or {"tier": 1, "attempts": 0, "maxAttempts": 3, "rollbackAttempted": False}
    max_debug_attempts = retry_limit(state, "debugAttempts", 3)
    debug_attempts = increment_retry(state, "debugAttempts", state.currentTask)
    if debug_attempts >= max_debug_attempts and not debug_state.get("rollbackAttempted"):
        done_tasks = [task_id for task_id, status in (state.taskStatuses or {}).items() if status == "done"]
        if done_tasks:
            last_good_tag = f"v0.{len(done_tasks)}.0"
            rb_result = rollback(state.sandboxId, last_good_tag)
            if rb_result.get("success"):
                reset_retry(state, "debugAttempts", state.currentTask)
                state.debugState = {**debug_state, "rollbackAttempted": True, "tier": 1, "attempts": 0}
                state.reviewResult = {"verdict": "", "issues": [], "reviewCycle": 0}
                state.executionResult = {"result": "", "output": "", "errors": ""}
                log(state, f"Debugger retry limit reached ({max_debug_attempts}); rolled back to {last_good_tag}")
                return state
        state.debugState = {**debug_state, "rollbackAttempted": True, "tier": 3}
        log(state, f"Debugger retry limit reached ({max_debug_attempts}); escalating to human")
        return state

    if debug_state.get("tier", 1) >= 3 or (debug_state.get("tier") == 2 and debug_state.get("attempts", 0) >= 2):
        state.debugState = {**debug_state, "tier": 3}
        log(state, "Debugger exhausted all tiers; escalating to human")
        return state

    errors = state.executionResult.get("errors") or "Unknown error"
    failing_files = (state.currentTask or {}).get("filesToCreate", []) or []
    context_files = ""
    for file_path in failing_files:
        content = read_file(state.sandboxId, file_path)
        if content:
            context_files += f"\n--- {file_path} ---\n{content}\n"
    if debug_state.get("tier", 1) >= 2:
        related = [
            file for file in get_file_list(state.sandboxId)
            if file.endswith((".js", ".jsx")) and "node_modules" not in file and file not in failing_files
        ][:10]
        for file_path in related:
            content = read_file(state.sandboxId, file_path)
            if content:
                context_files += f"\n--- {file_path} (context) ---\n{chr(10).join(content.splitlines()[:50])}\n"

    user_prompt = f"ERROR:\n{errors}\n\nTASK: {(state.currentTask or {}).get('title')}\nFILES TO FIX: {', '.join(failing_files)}\n\nCODE:\n{context_files}"
    result = await safe_call_json_agent(
        agent_name="debuggerAgent",
        system_prompt=DEBUGGER_PROMPT,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "debuggerAgent", result["tokens"])
    if not result["ok"]:
        state.error = f"debuggerAgent failed: {result['error']}"
        log(state, state.error)
        return state

    debug = result["parsed"] or {}
    new_attempts = debug_state.get("attempts", 0) + 1
    should_promote = new_attempts >= max_debug_attempts or debug.get("confidence") == "low"
    new_tier = debug_state.get("tier", 1) + 1 if should_promote else debug_state.get("tier", 1)
    state.debugState = {
        "tier": new_tier,
        "attempts": 0 if should_promote else new_attempts,
        "maxAttempts": max_debug_attempts,
        "rollbackAttempted": debug_state.get("rollbackAttempted", False),
    }
    state.reviewResult = {
        "verdict": "rejected",
        "issues": [debug.get("rootCause", ""), debug.get("fix", "")],
        "reviewCycle": 0,
    }
    log(state, f"Debugger root cause: {debug.get('rootCause', '')}")
    return state


def debuggerRouter(state: AgentState) -> str:
    return "humanEscalation" if state.debugState.get("tier", 1) >= 3 else "contextBuilder"
