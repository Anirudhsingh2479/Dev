from __future__ import annotations

from ..models.contracts import AgentState
from ..services.sandbox import create_sandbox, get_sandbox_info
from ._shared import log, now_ms


def getScaffoldRegistry(db_type: str) -> list[dict]:
    postgres = db_type != "mongo"
    return [
        {"path": "backend/src/config/db.js", "defaultExport": "mongoose" if not postgres else None, "namedExports": ["connectDB"] if not postgres else ["pool", "connectDB"], "exports": ["mongoose", "connectDB"] if not postgres else ["pool", "connectDB"], "importStatement": "import mongoose, { connectDB } from '../config/db.js'" if not postgres else "import { pool, connectDB } from '../config/db.js'", "interface": "Database connection helper.", "updatedAt": now_ms()},
        {"path": "backend/src/middleware/auth.js", "defaultExport": None, "namedExports": ["authenticateToken", "authorizeRole"], "exports": ["authenticateToken", "authorizeRole"], "importStatement": "import { authenticateToken, authorizeRole } from '../middleware/auth.js'", "interface": "JWT auth middleware and role guard.", "updatedAt": now_ms()},
        {"path": "backend/src/index.js", "defaultExport": "app", "namedExports": [], "exports": ["app"], "importStatement": "import app from '../index.js'", "interface": "Express app instance with health endpoint.", "updatedAt": now_ms()},
        {"path": "frontend/src/utils/api.js", "defaultExport": "api", "namedExports": [], "exports": ["api"], "importStatement": "import api from '../utils/api'", "interface": "Axios API client.", "updatedAt": now_ms()},
        {"path": "frontend/src/main.jsx", "defaultExport": None, "namedExports": [], "exports": [], "importStatement": "", "interface": "React entry point.", "updatedAt": now_ms()},
        {"path": "frontend/src/App.jsx", "defaultExport": "App", "namedExports": [], "exports": ["App"], "importStatement": "import App from '../App'", "interface": "Root React component.", "updatedAt": now_ms()},
    ]


async def setupSandboxNode(state: AgentState) -> AgentState:
    state.sandboxId = create_sandbox(
        state.projectId,
        state.userId,
        state.blueprint.get("folderStructure", ""),
        state.blueprint.get("dependencies", {}),
        state.blueprint.get("dbSchema", {}),
    )
    db_type = "mongo" if "mongo" in str(state.blueprint.get("dbSchema", {}).get("databaseType", "")).lower() else "postgres"
    state.fileRegistry = getScaffoldRegistry(db_type)
    state.currentPhase = "sandbox"
    log(state, f"Sandbox created with Docker scaffold: {state.sandboxId}; registry seeded with scaffold files")
    info = get_sandbox_info(state.sandboxId) or {}
    if info.get("frontendUrl"):
        state.previewFrontendUrl = info["frontendUrl"]
        state.previewFrontendPort = info.get("frontendPort")
        log(state, f"Frontend URL: {info['frontendUrl']}")
    if info.get("backendUrl"):
        state.previewBackendUrl = info["backendUrl"]
        state.previewBackendPort = info.get("backendPort")
        log(state, f"Backend URL: {info['backendUrl']}")
    return state
