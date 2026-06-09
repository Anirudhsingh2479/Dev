from __future__ import annotations

import json
from typing import Any

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ..services.sandbox import get_file_list, read_file, write_file
from ._shared import apply_token_delta, log, task_id


BACKEND_PROMPT = """You are a senior backend developer. Write ONE file.

OUTPUT FORMAT (strict JSON - single file only):
{
  "path": "backend/src/models/todoItem.js",
  "content": "// Full file content here",
  "notes": "Brief explanation"
}

RULES:
- ES module syntax ONLY (import/export, never require)
- Express: use Router(), router.get/post/put/delete
- DB: ALWAYS parameterized queries ($1, $2). NEVER string concatenation.
- Models: return clean data (not raw {rows}). Mark async functions.
- Response format EVERYWHERE: { success: true/false, data: ... } or { success: false, message: "..." }
  200: { success: true, data: result }
  201: { success: true, data: newItem }
  400: { success: false, message: "Invalid input" }
  401: { success: false, message: "Unauthorized" }
  404: { success: false, message: "Not found" }
  500: { success: false, message: error.message }
- Auth: JWT Bearer token. req.headers.authorization?.split(' ')[1]. req.user = decoded.
- Env vars: process.env.DATABASE_URL, process.env.JWT_SECRET, process.env.PORT
- .js extension in ALL imports (required for ES modules)
- Write COMPLETE files. No TODO, no placeholders.
- Keep code concise: 60-120 lines target. No excessive comments."""


FRONTEND_PROMPT = """You are a senior React developer. Write ONE file.

OUTPUT FORMAT (strict JSON - single file only):
{
  "path": "frontend/src/pages/DashboardPage.jsx",
  "content": "// Full file content here",
  "notes": "Brief explanation"
}

RULES:
- Functional components with hooks (useState, useEffect, useContext)
- Use Tailwind CSS - NO inline styles, NO CSS modules
- Import api utility: import api from '../utils/api' (already configured with auth)
- Navigation: import { useNavigate, Link } from 'react-router-dom'
- ALWAYS include loading state and error state
- Forms: controlled inputs, onSubmit with e.preventDefault()
- NEVER use process.env (use import.meta.env for Vite)

DESIGN SYSTEM - DARK MODE (follow strictly):
- Background: bg-gray-950. Cards: bg-gray-900/80 border border-gray-800/60 rounded-2xl p-6
- Text: text-white (titles), text-gray-300 (body), text-gray-500 (meta)
- Accent: emerald. Buttons: bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg px-4 py-2.5
- Inputs: bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 focus:ring-2 focus:ring-emerald-500/40
- Tables: header text-xs text-gray-500 uppercase. Rows: hover:bg-gray-800/30
- Loading: animate-pulse skeleton. Empty: centered text-gray-500 message.
- Nav bar: h-16 bg-gray-900/80 border-b border-gray-800 sticky top-0 z-50
- Icons: Use Unicode symbols (+ x <- ->), NO emoji
- Write COMPLETE files. No TODO. Keep concise: 60-120 lines."""


SCAFFOLD_FILES = {
    "backend/src/index.js",
    "backend/src/config/db.js",
    "backend/src/middleware/auth.js",
    "frontend/index.html",
    "frontend/src/main.jsx",
    "frontend/src/App.jsx",
    "frontend/src/index.css",
    "frontend/src/utils/api.js",
    "frontend/tailwind.config.js",
    "frontend/postcss.config.js",
    "frontend/vite.config.js",
}


def _shared_context(context: dict[str, Any], existing_files: list[str]) -> str:
    text = ""
    if context.get("namingMap"):
        text += "NAMING MAP:\n"
        for item in context["namingMap"]:
            text += f"  {item.get('entity')} -> table: {item.get('tableName')}, api: {item.get('apiPath')}, model: {item.get('modelFile')}, route: {item.get('routeFile')}\n"
        text += "\n"
    deps = context.get("dependencyInterfaces") or {}
    if deps:
        text += "EXISTING FILES YOU CAN IMPORT FROM:\n"
        for dep_path, info in deps.items():
            text += f"  {dep_path}: {info.get('importStatement') or ''}\n"
            if info.get("interface"):
                text += f"    -> {info.get('interface')}\n"
        text += "\n"
    if context.get("dbSchema"):
        text += f"DATABASE: {context['dbSchema'].get('databaseType')}\nTABLES: {json.dumps(context['dbSchema'].get('tables'), indent=2)}\n\n"
    if context.get("apiEndpoints"):
        text += f"API ENDPOINTS:\n{json.dumps(context['apiEndpoints'], indent=2)}\n\n"
    scaffold_on_disk = [item for item in existing_files if item in SCAFFOLD_FILES]
    if scaffold_on_disk:
        text += "ALREADY EXISTS (do NOT recreate, just import from them):\n"
        for item in scaffold_on_disk:
            text += f"  - {item}\n"
        text += "\n"
    if context.get("templateFile"):
        template = context["templateFile"]
        text += f"STYLE TEMPLATE (match this pattern):\n--- {template.get('path')} ---\n{template.get('content')}\n\n"
    return text


async def coderAgentNode(state: AgentState) -> AgentState:
    current_task = state.currentTask or {}
    context = state.contextPackage or {}
    if not current_task or not context:
        state.coderOutput = None
        log(state, "Coder Agent skipped: no task/context")
        return state

    files_to_create = context.get("task", {}).get("filesToCreate", []) or []
    is_retry = state.reviewResult.get("verdict") == "rejected" and bool(state.reviewResult.get("issues"))
    existing_files = get_file_list(state.sandboxId)
    shared_context = _shared_context(context, existing_files)

    retry_context = ""
    if is_retry:
        retry_context += "\n=== RETRY - FIX THESE ISSUES ===\n"
        for issue in state.reviewResult.get("issues", []):
            retry_context += f"  - {issue}\n"
        if state.executionResult.get("errors"):
            retry_context += f"\nEXECUTOR ERROR:\n{state.executionResult.get('errors', '')[:400]}\n"

    written_files: list[dict[str, Any]] = []
    total_tokens = {"input": 0, "output": 0, "cost": 0.0}
    for file_path in files_to_create:
        if file_path in SCAFFOLD_FILES:
            log(state, f"Coder Agent skipped scaffold file: {file_path}")
            continue

        system_prompt = BACKEND_PROMPT if "backend" in file_path else FRONTEND_PROMPT
        file_prompt = f"FILE TO WRITE: {file_path}\nTASK: {current_task.get('title')}\nDESCRIPTION: {current_task.get('description', '')}\n\n"
        criteria = context.get("task", {}).get("acceptanceCriteria") or []
        if criteria:
            file_prompt += "ACCEPTANCE CRITERIA:\n" + "\n".join(f"  - {item}" for item in criteria) + "\n\n"
        file_prompt += shared_context
        if is_retry:
            file_prompt += retry_context
            current_content = read_file(state.sandboxId, file_path)
            if current_content:
                file_prompt += f"\nCURRENT FILE ON DISK (fix it, don't rewrite from scratch):\n--- {file_path} ---\n{current_content}\n"
        file_prompt += f"\nAPP: {context.get('appName')}\nOUTPUT: Return JSON with path, content, notes. The \"path\" MUST be exactly \"{file_path}\".\n"

        result = await safe_call_json_agent(
            agent_name="coderAgent",
            system_prompt=system_prompt,
            user_prompt=file_prompt,
            current_cost=state.tokenUsage.estimatedCost + total_tokens["cost"],
            token_budget=state.tokenBudget,
        )
        total_tokens["input"] += result["tokens"]["input"]
        total_tokens["output"] += result["tokens"]["output"]
        total_tokens["cost"] += result["tokens"]["cost"]
        if not result["ok"]:
            written_files.append({"path": file_path, "lines": 0, "error": result["error"]})
            continue

        file_data = result["parsed"] or {}
        if isinstance(file_data.get("files"), list):
            file_data = file_data["files"][0] if file_data["files"] else {}
        content = file_data.get("content") or ""
        if not content:
            written_files.append({"path": file_path, "lines": 0, "error": "Empty content"})
            continue
        write_path = file_path
        if write_path in SCAFFOLD_FILES and not is_retry:
            continue
        try:
            write_file(state.sandboxId, write_path, content)
            written_files.append({"path": write_path, "lines": len(content.splitlines())})
            log(state, f"Coder Agent wrote {write_path}")
        except Exception as error:
            written_files.append({"path": write_path, "lines": 0, "error": str(error)})

    success_count = len([item for item in written_files if not item.get("error")])
    state.fileTree = get_file_list(state.sandboxId)
    state.coderOutput = {
        "files": written_files,
        "notes": "All files failed to generate" if success_count == 0 and files_to_create else f"{success_count} files written",
        "error": success_count == 0 and bool(files_to_create),
    }
    apply_token_delta(state, "coderAgent", total_tokens)
    log(state, f"Coder Agent done for {task_id(current_task)}: {success_count} written")
    return state
