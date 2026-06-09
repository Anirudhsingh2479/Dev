from __future__ import annotations

import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

from .sandbox_state import (
    NETWORK_NAME,
    SANDBOX_BACKEND_HOST_PORT,
    SANDBOX_FRONTEND_HOST_PORT,
    SANDBOX_PREVIEW_PORT_POOL_SIZE,
    _active_preview_by_user,
    _sandboxes,
)


def _run(command: list[str], cwd: Path | None = None, timeout: int = 30000) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, timeout=timeout / 1000, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(command, 127, "", str(error))

def _run_with_input(command: list[str], stdin: str, timeout: int = 30000) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, input=stdin, timeout=timeout / 1000, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(command, 127, "", str(error))

def _run_required(command: list[str], cwd: Path | None = None, timeout: int = 30000) -> subprocess.CompletedProcess[str]:
    result = _run(command, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Command failed ({' '.join(command)}): {detail}")
    return result

def _shell(command: str, cwd: Path | None = None, timeout: int = 30000) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, timeout=timeout / 1000, capture_output=True, shell=True, check=False)

def _docker_available() -> bool:
    return _run(["docker", "info"], timeout=5000).returncode == 0

def _requires_docker() -> bool:
    return os.getenv("REQUIRE_DOCKER", "true").lower() in {"1", "true", "yes"}

def _docker_exec(container_id: str, command: str, timeout: int = 30000) -> dict[str, Any]:
    result = _run(["docker", "exec", container_id, "sh", "-c", command], timeout=timeout)
    return {"stdout": result.stdout or "", "stderr": result.stderr or "", "exitCode": result.returncode}

def _published_port(container_id: str, container_port: int) -> str | None:
    result = _run(["docker", "port", container_id, str(container_port)], timeout=5000)
    if result.returncode != 0:
        return None
    line = (result.stdout or "").strip().splitlines()[0] if result.stdout else ""
    return line.rsplit(":", 1)[-1] if ":" in line else None

def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def _docker_port_is_published(port: int) -> bool:
    result = _run(["docker", "ps", "--format", "{{.Ports}}"], timeout=5000)
    if result.returncode != 0:
        return False
    return f":{port}->" in (result.stdout or "")

def _host_port_available(port: int) -> bool:
    return _port_is_free(port) and not _docker_port_is_published(port)

def _allocate_preview_ports(preferred_backend_port: str | int | None = None, preferred_frontend_port: str | int | None = None) -> tuple[str, str]:
    if preferred_backend_port and preferred_frontend_port:
        backend = int(preferred_backend_port)
        frontend = int(preferred_frontend_port)
        if _host_port_available(backend) and _host_port_available(frontend):
            return str(backend), str(frontend)

    backend_base = int(SANDBOX_BACKEND_HOST_PORT)
    frontend_base = int(SANDBOX_FRONTEND_HOST_PORT)
    for offset in range(SANDBOX_PREVIEW_PORT_POOL_SIZE):
        backend = backend_base + offset
        frontend = frontend_base + offset
        if _host_port_available(backend) and _host_port_available(frontend):
            return str(backend), str(frontend)
    raise RuntimeError(
        f"No free preview port pair found in backend range {backend_base}-{backend_base + SANDBOX_PREVIEW_PORT_POOL_SIZE - 1} "
        f"and frontend range {frontend_base}-{frontend_base + SANDBOX_PREVIEW_PORT_POOL_SIZE - 1}"
    )

def _remove_container(name_or_id: str, timeout: int = 10000) -> bool:
    result = _run(["docker", "rm", "-f", name_or_id], timeout=timeout)
    return result.returncode == 0

def _stop_containers_for_sandbox_id(sandbox_id: str) -> list[str]:
    stopped: list[str] = []
    for name in [
        f"aidev-db-{sandbox_id}",
        f"aidev-backend-{sandbox_id}",
        f"aidev-frontend-{sandbox_id}",
    ]:
        if _remove_container(name):
            stopped.append(name)
    return stopped

def stop_active_preview_containers() -> dict[str, Any]:
    result = _run(["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"], timeout=10000)
    if result.returncode != 0:
        return {"stopped": False, "containers": [], "errors": [(result.stderr or result.stdout or "").strip()]}

    sandbox_ids: set[str] = set()
    for line in (result.stdout or "").splitlines():
        if f":{SANDBOX_FRONTEND_HOST_PORT}->" not in line and f":{SANDBOX_BACKEND_HOST_PORT}->" not in line:
            continue
        match = re.search(r"(sandbox-\d+)", line)
        if match:
            sandbox_ids.add(match.group(1))

    stopped: list[str] = []
    for sandbox_id in sandbox_ids:
        stopped.extend(_stop_containers_for_sandbox_id(sandbox_id))
        info = _sandboxes.get(sandbox_id)
        if info:
            info.db_container_id = None
            info.backend_container_id = None
            info.frontend_container_id = None

    return {"stopped": bool(stopped), "containers": stopped, "activeSandboxIds": sorted(sandbox_ids)}

def stop_active_preview_for_user(user_id: str, except_sandbox_id: str | None = None) -> dict[str, Any]:
    active_sandbox_id = _active_preview_by_user.get(user_id)
    if not active_sandbox_id or active_sandbox_id == except_sandbox_id:
        return {"stopped": False, "containers": [], "activeSandboxId": active_sandbox_id}
    stopped = _stop_containers_for_sandbox_id(active_sandbox_id)
    info = _sandboxes.get(active_sandbox_id)
    if info:
        info.db_container_id = None
        info.backend_container_id = None
        info.frontend_container_id = None
    _active_preview_by_user.pop(user_id, None)
    return {"stopped": bool(stopped), "containers": stopped, "activeSandboxId": active_sandbox_id}

def _ensure_network() -> None:
    if _run(["docker", "network", "inspect", NETWORK_NAME], timeout=5000).returncode != 0:
        _run_required(["docker", "network", "create", NETWORK_NAME], timeout=30000)

def _wait_for_container(container_id: str, check_cmd: str, max_attempts: int = 20) -> bool:
    for _ in range(max_attempts):
        if _docker_exec(container_id, check_cmd, timeout=5000)["exitCode"] == 0:
            return True
        time.sleep(1)
    return False

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
