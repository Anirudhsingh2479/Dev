from __future__ import annotations

import json

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ._shared import apply_token_delta, log


PLANNER_PROMPT = """You are the Planner Agent in an AI software development team.

ROLE: Senior tech lead who creates the build plan.

GOAL: Break the architecture blueprint into ordered coding tasks.

MANDATORY PHASE ORDER:
1. "setup" - Project scaffolding, DB connection file, environment config
2. "models" - Database models/schemas (one task per entity)
3. "middleware" - Auth middleware, error handler, validators
4. "backend" - API routes (one task per resource/entity)
5. "frontend" - React pages + components (one task per page)
6. "integration" - Wire frontend to backend, App.jsx routing, main entry points
7. "deployment" - Dockerfiles for backend + frontend, docker-compose.yml, final README

OUTPUT FORMAT (strict JSON):
{
  "phases": [
    {
      "phaseNumber": 1,
      "phaseName": "setup",
      "description": "What this phase accomplishes",
      "tasks": [
        {
          "taskId": "setup-1",
          "title": "Short task title",
          "description": "What exactly to build",
          "filesToCreate": ["backend/src/config/db.js"],
          "filesNeeded": [],
          "acceptanceCriteria": ["DB config exports pool and connectDB"],
          "canParallelize": false,
          "estimatedTokens": 500
        }
      ]
    }
  ],
  "totalTasks": 18,
  "estimatedTotalTokens": 10000
}

RULES:
- Each task creates 1-3 files max.
- "filesNeeded" = files this task imports from (must exist from prior tasks).
- "filesToCreate" = files this task writes.
- Phase 2 (models) tasks are parallelizable.
- Phase 4 (backend routes) tasks are parallelizable.
- Phase 5 (frontend pages) tasks are parallelizable.
- Give each task a unique taskId: "phaseName-N".
- Keep task count 15-25 for a typical CRUD app.

IMPORTANT - THESE FILES ALREADY EXIST (scaffolded automatically, do NOT create them):
- backend/src/config/db.js (DB connection pool)
- backend/src/middleware/auth.js (JWT auth middleware)
- backend/src/index.js (Express entry - routes are auto-wired after your route tasks complete)
- frontend/index.html, frontend/src/main.jsx, frontend/src/App.jsx (auto-assembled)
- frontend/src/index.css, frontend/tailwind.config.js, frontend/postcss.config.js, frontend/vite.config.js
- frontend/src/utils/api.js (axios instance with auth interceptor)
- .gitignore, all .env files

So your Phase 1 (setup) should ONLY create files that are project-SPECIFIC:
- Maybe a frontend AuthContext if auth is needed
- Maybe backend utility helpers specific to this app
- Do NOT recreate db.js, auth middleware, api.js, or config files.

Phase 6 (integration): Do NOT create backend/src/index.js or frontend/src/App.jsx - they are AUTO-ASSEMBLED from the route and page files you create in earlier phases. If you need an integration task, use it for wiring specific features (e.g. a shared layout component, or connecting auth flow).

Phase 7 (deployment): Include ONLY a README.md task. Docker files are auto-generated.

- File paths should NOT start with / (use relative: "backend/src/..." not "/backend/src/...")
- Backend models MUST use the file name format from the entity map: e.g., if entity.modelFile = "todoItem", the file is "backend/src/models/todoItem.js"
- Backend routes MUST match: e.g., if entity.routeFile = "todoItemRoutes", file is "backend/src/routes/todoItemRoutes.js"."""


async def plannerAgentNode(state: AgentState) -> AgentState:
    blueprint = state.blueprint
    summary = {
        "databaseType": (blueprint.get("dbSchema") or {}).get("databaseType"),
        "entities": [{
            "name": item.get("name"),
            "tableName": item.get("tableName"),
            "apiPath": item.get("apiPath"),
            "modelFile": item.get("modelFile"),
            "routeFile": item.get("routeFile"),
        } for item in blueprint.get("entities", [])],
        "tables": [{
            "name": item.get("name"),
            "fieldCount": len(item.get("fields", []) or []),
            "foreignKeys": [fk.get("references") for fk in item.get("foreignKeys", []) or []],
        } for item in (blueprint.get("dbSchema") or {}).get("tables", [])],
        "apiEndpoints": [{
            "method": item.get("method"),
            "path": item.get("path"),
            "relatedTable": item.get("relatedTable"),
            "requiresAuth": item.get("requiresAuth"),
        } for item in blueprint.get("apiEndpoints", [])],
        "frontendPages": [{
            "name": item.get("name"),
            "route": item.get("route"),
            "componentCount": len(item.get("components", []) or []),
        } for item in blueprint.get("frontendPages", [])],
        "folderStructure": blueprint.get("folderStructure"),
        "backendDeps": list((blueprint.get("dependencies", {}).get("backend", {}).get("dependencies", {}) or {}).keys()),
        "frontendDeps": list((blueprint.get("dependencies", {}).get("frontend", {}).get("dependencies", {}) or {}).keys()),
    }
    result = await safe_call_json_agent(
        agent_name="plannerAgent",
        system_prompt=PLANNER_PROMPT,
        user_prompt=f"App: {(state.clarifiedSpec or {}).get('appName')}\n\nBlueprint:\n{json.dumps(summary, indent=2)}\n\nSpec:\n{json.dumps(state.clarifiedSpec, indent=2)}",
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "plannerAgent", result["tokens"])
    if not result["ok"]:
        state.error = f"plannerAgent failed: {result['error']}"
        log(state, state.error)
        return state
    state.taskQueue = result["parsed"] or {"phases": []}
    state.currentPhaseIndex = 0
    state.currentTaskIndex = 0
    state.currentPhase = "sandbox"
    log(state, f"Planner produced {len(state.taskQueue.get('phases', []))} phase(s)")
    return state
