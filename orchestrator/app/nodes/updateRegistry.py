from __future__ import annotations

from typing import Any

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ..services.sandbox import read_file
from ._shared import apply_token_delta, log, merge_file_registry, now_ms


REGISTRY_PROMPT = """You are analyzing JavaScript/JSX files to extract their public interface.

For each file, extract:
- Default export (if any): what it is and how to import it
- Named exports: list each with type and parameters
- The EXACT import statement other files should use

OUTPUT FORMAT (strict JSON):
{
  "files": [
    {
      "path": "backend/src/config/db.js",
      "defaultExport": null,
      "namedExports": ["pool", "connectDB"],
      "importStatement": "import { pool, connectDB } from '../config/db.js'",
      "interface": "pool: pg.Pool instance for queries. connectDB(): async, tests connection, returns void"
    }
  ]
}

RULES:
- importStatement must be a VALID ES module import that other files can copy-paste
- Use relative paths in importStatement (../models/User.js, not absolute)
- Be precise - if it's "export default class User", defaultExport is "User"
- If it's "export const pool = ...", that's a namedExport
- List ALL exports, not just the main one
- Mark every function as "async" or "sync" in the interface description
- If a function returns a Promise or uses await, it is async - the caller MUST use await"""


async def updateRegistryNode(state: AgentState) -> AgentState:
    file_contents: list[dict[str, str]] = []
    for file in (state.coderOutput or {}).get("files", []):
        if file.get("error") or not file.get("path"):
            continue
        content = read_file(state.sandboxId, file["path"])
        if content:
            file_contents.append({"path": file["path"], "content": content})

    if not file_contents:
        log(state, "Update Registry skipped: no file contents")
        return state

    user_prompt = "\n".join(f"--- {item['path']} ---\n{item['content']}\n" for item in file_contents)
    result = await safe_call_json_agent(
        agent_name="updateRegistry",
        system_prompt=REGISTRY_PROMPT,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "updateRegistry", result["tokens"])
    if not result["ok"]:
        state.error = f"updateRegistry failed: {result['error']}"
        log(state, state.error)
        return state

    entries: list[dict[str, Any]] = []
    for item in (result["parsed"] or {}).get("files", []):
        named = item.get("namedExports") or []
        default = item.get("defaultExport")
        entries.append({
            "path": item.get("path"),
            "defaultExport": default,
            "namedExports": named,
            "exports": [*named, *([default] if default else [])],
            "importStatement": item.get("importStatement", ""),
            "interface": item.get("interface", ""),
            "updatedAt": now_ms(),
        })
    state.fileRegistry = merge_file_registry(state.fileRegistry, entries)
    log(state, f"Update Registry indexed {len(entries)} file(s)")
    return state
