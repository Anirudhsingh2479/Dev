from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


NETWORK_NAME = "aidev-network"
DOCKER_RUN_TIMEOUT_MS = int(os.getenv("DOCKER_RUN_TIMEOUT_MS", "300000"))
NPM_INSTALL_TIMEOUT_MS = int(os.getenv("NPM_INSTALL_TIMEOUT_MS", "300000"))
SANDBOX_FRONTEND_HOST_PORT = os.getenv("SANDBOX_FRONTEND_HOST_PORT", "15173")
SANDBOX_BACKEND_HOST_PORT = os.getenv("SANDBOX_BACKEND_HOST_PORT", "15000")
SANDBOX_PREVIEW_PORT_POOL_SIZE = int(os.getenv("SANDBOX_PREVIEW_PORT_POOL_SIZE", "100"))
PROJECT_DB_URI = os.getenv("PROJECT_DB_URI", "").strip()
_sandboxes: dict[str, "SandboxInfo"] = {}
_active_preview_by_user: dict[str, str] = {}


@dataclass
class SandboxInfo:
    sandbox_id: str
    path: Path
    backend_path: Path
    frontend_path: Path
    db_type: str
    db_container_id: str | None = None
    backend_container_id: str | None = None
    frontend_container_id: str | None = None
    db_container_name: str = ""
    backend_container_name: str = ""
    frontend_container_name: str = ""
    backend_host_port: str | None = None
    frontend_host_port: str | None = None
    user_id: str = "demo-user"
    created_at: float = 0
    snapshot_count: int = 0

def _sandbox_root() -> Path:
    return Path(os.getenv("SANDBOX_ROOT") or os.getenv("SANDBOX_DIR") or "/tmp/aidev-sandboxes")

def _sandbox_path(sandbox_id: str) -> Path:
    return _sandbox_root() / sandbox_id

def _docker_mount_path(sandbox_id: str) -> Path:
    host_root = os.getenv("HOST_SANDBOX_ROOT")
    if host_root:
        return Path(host_root) / sandbox_id
    return _sandbox_path(sandbox_id)
