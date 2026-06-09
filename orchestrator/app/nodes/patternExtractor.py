from __future__ import annotations

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ..services.sandbox import get_file_list, read_file
from ._shared import apply_token_delta, log


PATTERN_PROMPT = """You are analyzing code files to extract exact coding patterns. Be VERY specific - include actual code snippets, not descriptions.

Extract these patterns:

OUTPUT FORMAT (strict JSON):
{
  "errorHandling": "try { ... } catch(err) { res.status(500).json({ success: false, message: err.message }) }",
  "responseFormat": "Success: { success: true, data: result } | Error: { success: false, message: string }",
  "authPattern": "Bearer token in Authorization header, extracted with req.headers.authorization?.split(' ')[1]",
  "importStyle": "ES modules, named: import { pool } from '../config/db.js', default: import User from '../models/User.js'",
  "envVarStyle": "Backend: process.env.DATABASE_URL, Frontend: import.meta.env.VITE_API_URL",
  "modelReturnStyle": "Models return clean data: const { rows } = await pool.query(...); return rows[0]",
  "middlewareOrder": "cors() -> express.json() -> routes -> errorHandler",
  "namingConvention": "camelCase vars, PascalCase components, snake_case DB fields, kebab-case API paths",
  "asyncPattern": "All DB/API functions are async, always called with await",
  "frontendApiPattern": "axios.get/post with baseURL from import.meta.env.VITE_API_URL, token in Authorization header"
}

RULES:
- Each value should be a SHORT code example or exact pattern, not a vague description
- If a pattern isn't established yet, use empty string ""
- Be precise enough that another developer can follow it exactly"""


async def patternExtractorNode(state: AgentState) -> AgentState:
    if not state.sandboxId:
        log(state, "Pattern Extractor skipped: no sandbox")
        return state
    code_files = [
        file for file in get_file_list(state.sandboxId)
        if file.endswith((".js", ".jsx")) and "node_modules" not in file
    ][:8]
    if not code_files:
        log(state, "Pattern Extractor skipped: no code files")
        return state
    code_content = ""
    for file_path in code_files:
        content = read_file(state.sandboxId, file_path)
        if content:
            code_content += f"\n--- {file_path} ---\n{chr(10).join(content.splitlines()[:40])}\n"

    result = await safe_call_json_agent(
        agent_name="patternExtractor",
        system_prompt=PATTERN_PROMPT,
        user_prompt=code_content,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "patternExtractor", result["tokens"])
    if not result["ok"]:
        state.error = f"patternExtractor failed: {result['error']}"
        log(state, state.error)
        return state

    state.projectPatterns.update(result["parsed"] or {})
    log(state, "Pattern Extractor updated project patterns")
    return state
