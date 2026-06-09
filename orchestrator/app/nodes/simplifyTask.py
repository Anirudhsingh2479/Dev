from __future__ import annotations

import json

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ._shared import apply_token_delta, clone, log, reset_retry, task_id


SIMPLIFY_PROMPT = """You are analyzing a coding task that failed multiple times and needs to be broken into smaller pieces.

Given the original task and the rejection reasons, create 2-3 simpler sub-tasks that together accomplish the same goal but are each simple enough to succeed individually.

OUTPUT FORMAT (strict JSON):
{
  "subTasks": [
    {
      "taskId": "original-taskId-a",
      "title": "Simpler task title",
      "description": "Focused description",
      "filesToCreate": ["file1.js"],
      "filesNeeded": [],
      "acceptanceCriteria": ["Simple criterion"],
      "canParallelize": false
    }
  ],
  "reason": "Why the original task was too complex"
}"""


async def simplifyTaskNode(state: AgentState) -> AgentState:
    current = state.currentTask or {}
    tid = task_id(current)
    user_prompt = f"FAILED TASK:\n{json.dumps(current, indent=2)}\n\nREJECTION HISTORY:\n{json.dumps(state.reviewResult.get('issues', []), indent=2)}"
    result = await safe_call_json_agent(
        agent_name="simplifyTask",
        system_prompt=SIMPLIFY_PROMPT,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "simplifyTask", result["tokens"])
    if not result["ok"]:
        state.error = f"simplifyTask failed: {result['error']}"
        log(state, state.error)
        return state

    sub_tasks = (result["parsed"] or {}).get("subTasks", [])
    updated_queue = clone(state.taskQueue)
    for phase in updated_queue.get("phases", []):
        tasks = phase.get("tasks", [])
        for index, task in enumerate(tasks):
            if task_id(task) == tid:
                tasks[index + 1:index + 1] = sub_tasks
                break

    state.taskQueue = updated_queue
    state.taskStatuses[tid] = "done"
    state.reviewResult = {"verdict": "", "issues": [], "reviewCycle": 0}
    reset_retry(state, "reviewRejections", current)
    reset_retry(state, "debugAttempts", current)
    state.currentTask = None
    log(state, f"Simplify Task split {tid} into {len(sub_tasks)} sub-task(s)")
    return state
