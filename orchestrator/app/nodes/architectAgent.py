from __future__ import annotations

import json
from typing import Any

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ._shared import apply_token_delta, log


NAMING_RULES = """
STRICT NAMING CONVENTION (you MUST follow this):
- Table names: snake_case + plural (e.g., "users", "todo_items", "categories")
- DB field names: snake_case (e.g., "created_at", "password_hash", "user_id")
- API paths: kebab-case + plural (e.g., "/api/users", "/api/todo-items")
- relatedTable field: ALWAYS a single table name, NEVER comma-separated
- Foreign key format: "table_name(field)" (e.g., "users(id)")
"""

STEP1_PROMPT = f"""You are the Architect Agent in an AI software development team.

ROLE: Senior software architect.
GOAL: Identify ALL entities and their relationships, AND generate a standard naming map.

{NAMING_RULES}

OUTPUT FORMAT (strict JSON):
{{
  "entities": [
    {{
      "name": "TodoItem",
      "tableName": "todo_items",
      "apiPath": "/api/todo-items",
      "modelFile": "todoItem",
      "routeFile": "todoItemRoutes",
      "description": "A task or todo entry",
      "relationships": [
        {{ "target": "User", "type": "many-to-one", "foreignKey": "user_id", "description": "Each todo belongs to a user" }}
      ]
    }}
  ]
}}

RULES:
- Always include a "User" entity if auth is required.
- Generate tableName, apiPath, modelFile, routeFile for EVERY entity.
- tableName must be snake_case plural.
- apiPath must be kebab-case plural with /api/ prefix.
- modelFile and routeFile must be camelCase (no extension)."""

STEP2_PROMPT = f"""You are the Architect Agent designing the database schema.

{NAMING_RULES}

CRITICAL: Use the EXACT table names from the entity naming map provided. Do NOT rename tables.

OUTPUT FORMAT (strict JSON):
{{
  "databaseType": "PostgreSQL" | "MongoDB",
  "databaseReason": "Why this DB (1 line)",
  "tables": [
    {{
      "name": "todo_items",
      "description": "Stores todo entries",
      "fields": [
        {{ "name": "id", "type": "UUID DEFAULT gen_random_uuid()", "constraints": ["PRIMARY KEY"], "description": "Unique ID" }},
        {{ "name": "title", "type": "VARCHAR(255)", "constraints": ["NOT NULL"], "description": "Todo title" }},
        {{ "name": "user_id", "type": "UUID", "constraints": ["NOT NULL"], "description": "Owner" }},
        {{ "name": "created_at", "type": "TIMESTAMP", "constraints": ["DEFAULT NOW()"], "description": "Created time" }},
        {{ "name": "updated_at", "type": "TIMESTAMP", "constraints": ["DEFAULT NOW()"], "description": "Updated time" }}
      ],
      "foreignKeys": [
        {{ "field": "user_id", "references": "users(id)", "onDelete": "CASCADE" }}
      ],
      "indexes": ["user_id"]
    }}
  ]
}}

RULES:
- Every table MUST have "id" (UUID with gen_random_uuid()), "created_at", "updated_at".
- Use snake_case for ALL table and field names.
- Be SPECIFIC with types - VARCHAR(255), not just "string".
- If auth: users table needs password_hash (NEVER plain passwords).
- Add indexes on foreign keys."""

STEP3_PROMPT = f"""You are the Architect Agent designing REST API endpoints.

{NAMING_RULES}

CRITICAL:
- Use the EXACT apiPath from the entity naming map.
- "relatedTable" must be a SINGLE table name, never comma-separated.

OUTPUT FORMAT (strict JSON):
{{
  "apiEndpoints": [
    {{
      "method": "GET",
      "path": "/api/todo-items",
      "description": "Get all todos for current user",
      "requiresAuth": true,
      "roleAccess": ["user"],
      "requestBody": {{}},
      "responseBody": {{ "todos": "array of todo objects" }},
      "relatedTable": "todo_items"
    }}
  ]
}}

RULES:
- REST conventions: GET=read, POST=create, PUT/PATCH=update, DELETE=delete.
- Include auth endpoints if needed: POST /api/auth/register, POST /api/auth/login.
- Every entity: GET all, GET by id, POST, PUT/PATCH, DELETE.
- Pagination on GET-all (page, limit query params).
- relatedTable = the PRIMARY table this endpoint queries. ONE table only."""

STEP4_PROMPT = """You are the Architect Agent designing frontend pages.

TECH: React (Vite), React Router, useState + useContext, Tailwind CSS.

OUTPUT FORMAT (strict JSON):
{
  "frontendPages": [
    {
      "name": "DashboardPage",
      "route": "/dashboard",
      "description": "Main page showing todos with add/edit/delete",
      "requiresAuth": true,
      "components": [
        { "name": "TodoList", "description": "Displays todos in a list/grid", "apiCalls": ["/api/todo-items"] }
      ]
    }
  ]
}

RULES:
- Include auth pages if needed: LoginPage, RegisterPage.
- Include a layout/navbar component.
- Every data page must reference which API it calls.
- Use the EXACT API paths from the endpoints provided.
- Descriptive routes: /dashboard, /login, not /page1."""

STEP5_PROMPT = """You are the Architect Agent generating project structure and dependencies.

TECH: Express.js backend + React (Vite) frontend, monorepo: /backend and /frontend.

OUTPUT FORMAT (strict JSON):
{
  "folderStructure": "tree-format string showing every folder and file",
  "dependencies": {
    "backend": {
      "name": "backend",
      "dependencies": { "express": "^4.18.2", "cors": "^2.8.5", "dotenv": "^16.4.7", "pg": "^8.11.0", "bcryptjs": "^2.4.3", "jsonwebtoken": "^9.0.2", "uuid": "^9.0.0" },
      "devDependencies": { "nodemon": "^3.0.0" }
    },
    "frontend": {
      "name": "frontend",
      "dependencies": { "react": "^18.2.0", "react-dom": "^18.2.0", "react-router-dom": "^6.20.0", "axios": "^1.6.0" },
      "devDependencies": { "vite": "^5.0.0", "@vitejs/plugin-react": "^4.2.0", "tailwindcss": "^3.4.0", "postcss": "^8.4.0", "autoprefixer": "^10.4.0" }
    }
  }
}

RULES:
- Backend: src/models/, src/routes/, src/middleware/, src/config/, src/utils/
- Frontend: src/pages/, src/components/, src/hooks/, src/context/, src/utils/
- EXACT version numbers.
- Backend MUST include: express, cors, dotenv, bcryptjs, jsonwebtoken, pg (or mongoose), uuid.
- Frontend MUST include: react, react-dom, react-router-dom, axios, tailwindcss, vite."""


async def _architect_call(state: AgentState, agent_name: str, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    result = await safe_call_json_agent(
        agent_name=agent_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, agent_name, result["tokens"])
    if not result["ok"]:
        state.error = f"{agent_name} failed: {result['error']}"
        log(state, state.error)
        return None
    return result["parsed"]


async def architectStep1Node(state: AgentState) -> AgentState:
    parsed = await _architect_call(state, "architectStep1", STEP1_PROMPT, f"Project Specification:\n{json.dumps(state.clarifiedSpec, indent=2)}")
    if parsed is None:
        return state
    entities = parsed.get("entities") if isinstance(parsed, dict) else parsed
    state.blueprint["entities"] = entities or []
    log(state, f"Architect step 1 identified {len(state.blueprint['entities'])} entities")
    return state


async def architectStep2Node(state: AgentState) -> AgentState:
    entity_names = [{"name": item.get("name"), "tableName": item.get("tableName")} for item in state.blueprint.get("entities", [])]
    fix_context = f"\n\nPREVIOUS VALIDATION ISSUES TO FIX:\n{json.dumps(state.blueprintValidation.get('issues', []), indent=2)}" if state.blueprintValidation.get("issues") else ""
    prompt = f"Entity Naming Map (use these EXACT table names):\n{json.dumps(entity_names, indent=2)}\n\nFull Entities:\n{json.dumps(state.blueprint.get('entities'), indent=2)}\n\nSpec:\n{json.dumps(state.clarifiedSpec, indent=2)}{fix_context}"
    parsed = await _architect_call(state, "architectStep2", STEP2_PROMPT, prompt)
    if parsed is not None:
        state.blueprint["dbSchema"] = parsed
        log(state, "Architect step 2 designed database schema")
    return state


async def architectStep3Node(state: AgentState) -> AgentState:
    entity_map = [{"name": item.get("name"), "tableName": item.get("tableName"), "apiPath": item.get("apiPath")} for item in state.blueprint.get("entities", [])]
    fix_context = f"\n\nPREVIOUS VALIDATION ISSUES TO FIX:\n{json.dumps(state.blueprintValidation.get('issues', []), indent=2)}" if state.blueprintValidation.get("issues") else ""
    prompt = f"Entity Naming Map:\n{json.dumps(entity_map, indent=2)}\n\nDB Schema:\n{json.dumps(state.blueprint.get('dbSchema'), indent=2)}\n\nSpec:\n{json.dumps(state.clarifiedSpec, indent=2)}{fix_context}"
    parsed = await _architect_call(state, "architectStep3", STEP3_PROMPT, prompt)
    if parsed is not None:
        endpoints = parsed.get("apiEndpoints") if isinstance(parsed, dict) else parsed
        state.blueprint["apiEndpoints"] = endpoints if isinstance(endpoints, list) else []
        log(state, f"Architect step 3 designed {len(state.blueprint['apiEndpoints'])} API endpoints")
    return state


async def architectStep4Node(state: AgentState) -> AgentState:
    fix_context = f"\n\nPREVIOUS VALIDATION ISSUES TO FIX:\n{json.dumps(state.blueprintValidation.get('issues', []), indent=2)}" if state.blueprintValidation.get("issues") else ""
    prompt = f"API Endpoints:\n{json.dumps(state.blueprint.get('apiEndpoints'), indent=2)}\n\nSpec:\n{json.dumps(state.clarifiedSpec, indent=2)}{fix_context}"
    parsed = await _architect_call(state, "architectStep4", STEP4_PROMPT, prompt)
    if parsed is not None:
        pages = parsed.get("frontendPages") if isinstance(parsed, dict) else parsed
        state.blueprint["frontendPages"] = pages if isinstance(pages, list) else []
        log(state, f"Architect step 4 designed {len(state.blueprint['frontendPages'])} pages")
    return state


async def architectStep5Node(state: AgentState) -> AgentState:
    db_schema = state.blueprint.get("dbSchema", {})
    api_endpoints = state.blueprint.get("apiEndpoints", [])
    frontend_pages = state.blueprint.get("frontendPages", [])
    prompt = f"DB: {db_schema.get('databaseType')} ({len(db_schema.get('tables', []) or [])} tables)\nAPIs: {len(api_endpoints)} endpoints\nPages: {len(frontend_pages)} pages\n\nSpec:\n{json.dumps(state.clarifiedSpec, indent=2)}"
    parsed = await _architect_call(state, "architectStep5", STEP5_PROMPT, prompt)
    if parsed is not None:
        state.blueprint["folderStructure"] = parsed.get("folderStructure", "")
        state.blueprint["dependencies"] = parsed.get("dependencies", {})
        log(state, "Architect step 5 produced folder structure and dependencies")
    return state
