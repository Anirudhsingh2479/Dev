from __future__ import annotations

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ..services.sandbox import read_file
from ._shared import apply_token_delta, increment_retry, log, reset_retry, retry_count, retry_limit


REVIEWER_PROMPT = """You are the Reviewer Agent in an AI software development team.

ROLE: Senior code reviewer. Last gate before code runs.

GOAL: Review for correctness and consistency. Approve or reject with actionable feedback.

REVIEW CHECKLIST:
1. IMPORTS: Do imports use EXACT importStatements from dependencies? Are relative paths correct? Is .js extension included?
2. EXPORTS: Does the file export what the interface says? Named vs default correct?
3. ASYNC/AWAIT: Are async functions called with await? No missing awaits on DB queries or API calls?
4. ERROR RESPONSE FORMAT: Does it use { success: true/false, data/message }? Consistent across all endpoints?
5. AUTH PATTERN: Uses "Bearer " prefix? Extracts with split(' ')[1]? Sets req.user after verify?
6. REQUEST/RESPONSE FIELDS: Do field names match between frontend API calls and backend route handlers?
7. ENV VARIABLES: Uses process.env.DATABASE_URL (not DB_URL)? Frontend uses import.meta.env.VITE_API_URL (not process.env)?
8. MIDDLEWARE ORDER: cors -> json -> routes -> error handler?
9. MODEL RETURNS: Do models return clean data (not raw { rows })? Does caller handle null/undefined?
10. SECURITY: Parameterized queries? No hardcoded secrets? Proper password hashing?
11. COMPLETENESS: Does it meet acceptance criteria?

OUTPUT FORMAT (strict JSON):
{
  "verdict": "approved" | "rejected",
  "issues": ["Specific issue 1", "Specific issue 2"],
  "summary": "One-line summary"
}

RULES:
- If approved, issues should be empty or minor suggestions.
- If rejected, issues MUST be specific and actionable - include exact line/code to fix.
- Be practical. Don't reject for style preferences - only bugs, security, or missing functionality.
- If code is 90% correct with minor issues, APPROVE with suggestions.
- NEVER reject for missing features that are in a DIFFERENT task."""


async def reviewerAgentNode(state: AgentState) -> AgentState:
    current_cycle = state.reviewResult.get("reviewCycle", 0)
    files = (state.coderOutput or {}).get("files", [])
    if not state.currentTask or not files:
        if (state.coderOutput or {}).get("error"):
            state.reviewResult = {"verdict": "rejected", "issues": [state.coderOutput.get("notes", "Code generation failed")], "reviewCycle": current_cycle + 1}
            increment_retry(state, "reviewRejections", state.currentTask)
        else:
            state.reviewResult = {"verdict": "approved", "issues": [], "reviewCycle": 0}
            reset_retry(state, "reviewRejections", state.currentTask)
        return state

    code_content = ""
    for file in files:
        content = read_file(state.sandboxId, file.get("path", ""))
        if content:
            code_content += f"\n--- {file.get('path')} ---\n{content}\n"

    task = state.currentTask
    user_prompt = f"TASK: {task.get('title')}\nDESCRIPTION: {task.get('description', '')}\n\n"
    user_prompt += "ACCEPTANCE CRITERIA:\n" + "\n".join(f"  - {item}" for item in (task.get("acceptanceCriteria") or [])) + "\n\n"
    user_prompt += f"CODE TO REVIEW:\n{code_content}\n"
    patterns = (state.contextPackage or {}).get("patterns") or {}
    if any(patterns.values()):
        user_prompt += "\nPROJECT PATTERNS (check compliance):\n"
        for key, value in patterns.items():
            if value:
                user_prompt += f"  {key}: {value}\n"

    result = await safe_call_json_agent(
        agent_name="reviewerAgent",
        system_prompt=REVIEWER_PROMPT,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "reviewerAgent", result["tokens"])
    if not result["ok"]:
        state.error = f"reviewerAgent failed: {result['error']}"
        log(state, state.error)
        return state

    review = result["parsed"] or {}
    state.reviewResult = {
        "verdict": review.get("verdict", "approved"),
        "issues": review.get("issues", []),
        "reviewCycle": current_cycle + 1,
        "summary": review.get("summary", ""),
    }
    if state.reviewResult["verdict"] == "rejected":
        attempts = increment_retry(state, "reviewRejections", state.currentTask)
        log(state, f"Reviewer rejection count: {attempts}/{retry_limit(state, 'reviewRejections', 2)}")
    else:
        reset_retry(state, "reviewRejections", state.currentTask)
    log(state, f"Reviewer verdict: {state.reviewResult['verdict']}")
    return state


def reviewerRouter(state: AgentState) -> str:
    if state.reviewResult.get("verdict") == "approved":
        return "executorAgent"
    attempts = retry_count(state, "reviewRejections", state.currentTask)
    max_attempts = retry_limit(state, "reviewRejections", 2)
    if attempts >= max_attempts:
        log(state, f"Reviewer retry limit reached ({attempts}/{max_attempts}); simplifying task")
        return "simplifyTask"
    return "contextBuilder"
