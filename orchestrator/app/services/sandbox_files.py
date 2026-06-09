from __future__ import annotations

import shutil
from typing import Any

from .sandbox_process import _docker_exec, _run, _shell, _stop_containers_for_sandbox_id, _write
from .sandbox_state import _active_preview_by_user, _sandbox_path, _sandboxes


def _info(sandbox_id: str) -> SandboxInfo | None:
    return _sandboxes.get(sandbox_id) or _sandboxes.get(str(sandbox_id))

def write_file(sandbox_id: str, relative_path: str, content: str) -> None:
    info = _info(sandbox_id)
    if not info:
        raise FileNotFoundError(f"Sandbox {sandbox_id} not found")
    _write(info.path / relative_path, content)

def read_file(sandbox_id: str, relative_path: str) -> str | None:
    info = _info(sandbox_id)
    if not info:
        raise FileNotFoundError(f"Sandbox {sandbox_id} not found")
    file_path = info.path / relative_path
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8")

def get_file_list(sandbox_id: str) -> list[str]:
    info = _info(sandbox_id)
    path = info.path if info else _sandbox_path(sandbox_id)
    if not path.exists():
        return []
    files: list[str] = []
    for entry in path.rglob("*"):
        if entry.is_file() and "node_modules" not in entry.parts and ".git" not in entry.parts:
            files.append(entry.relative_to(path).as_posix())
    return sorted(files)

def execute_command(sandbox_id: str, command: str, timeout: int = 30000) -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        raise FileNotFoundError(f"Sandbox {sandbox_id} not found")
    if info.backend_container_id and ("/app/backend" in command or "cd /app/backend" in command):
        return _docker_exec(info.backend_container_id, command, timeout)
    if info.frontend_container_id and ("/app/frontend" in command or "cd /app/frontend" in command):
        return _docker_exec(info.frontend_container_id, command, timeout)
    if info.backend_container_id:
        return _docker_exec(info.backend_container_id, command, timeout)
    result = _shell(command, cwd=info.path, timeout=timeout)
    return {"stdout": result.stdout or "", "stderr": result.stderr or "", "exitCode": result.returncode}

def run_in_sandbox(sandbox_id: str, command: str, timeout: int = 30000) -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        raise FileNotFoundError(f"Sandbox {sandbox_id} not found")
    result = _shell(command, cwd=info.path, timeout=timeout)
    return {"stdout": result.stdout or "", "stderr": result.stderr or "", "exitCode": result.returncode}

def health_check(sandbox_id: str) -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        return {"healthy": False, "failures": ["Sandbox not found"]}
    failures: list[str] = []
    if not info.backend_path.exists():
        failures.append("Backend directory missing")
    if not info.frontend_path.exists():
        failures.append("Frontend directory missing")
    if not (info.backend_path / "package.json").exists():
        failures.append("Backend package.json missing")
    if not (info.frontend_path / "package.json").exists():
        failures.append("Frontend package.json missing")
    if _run(["git", "status"], cwd=info.path).returncode != 0:
        failures.append("Git not initialized")
    if info.db_container_id:
        check = "pg_isready -U postgres" if info.db_type == "postgres" else "mongosh --eval 'db.runCommand({ping:1})' --quiet"
        if _docker_exec(info.db_container_id, check, 5000)["exitCode"] != 0:
            failures.append(f"{info.db_type} not responding")
    if info.backend_container_id:
        if _docker_exec(info.backend_container_id, "node --version", 5000)["exitCode"] != 0:
            failures.append("Backend container not responding")
        if _docker_exec(info.backend_container_id, "ls /app/backend/node_modules/.package-lock.json 2>/dev/null", 5000)["exitCode"] != 0:
            failures.append("Backend node_modules not installed")
    else:
        failures.append("No backend container")
    if info.frontend_container_id:
        if _docker_exec(info.frontend_container_id, "node --version", 5000)["exitCode"] != 0:
            failures.append("Frontend container not responding")
    else:
        failures.append("No frontend container")
    if info.db_container_id and info.db_type == "postgres":
        table_check = _docker_exec(
            info.db_container_id,
            "psql -U postgres -d appdb -c \"SELECT tablename FROM pg_tables WHERE schemaname='public'\" -t",
            5000,
        )
        if table_check["exitCode"] == 0 and table_check["stdout"].strip():
            tables = [table.strip() for table in table_check["stdout"].strip().split("\n") if table.strip()]
            if tables:
                print(f"   Tables found: {', '.join(tables)}")
    return {"healthy": len(failures) == 0, "failures": failures, "sandboxPath": str(info.path), "dockerEnabled": bool(info.backend_container_id)}

def get_sandbox_path(sandbox_id: str) -> str | None:
    info = _info(sandbox_id)
    return str(info.path) if info else None

def get_sandbox_info(sandbox_id: str) -> dict[str, Any] | None:
    info = _info(sandbox_id)
    if not info:
        return None
    return {
        "path": str(info.path),
        "dockerEnabled": bool(info.backend_container_id),
        "dbType": info.db_type,
        "dbContainer": (info.db_container_id or "")[:12] or None,
        "backendContainer": (info.backend_container_id or "")[:12] or None,
        "frontendContainer": (info.frontend_container_id or "")[:12] or None,
        "backendPort": int(info.backend_host_port) if info.backend_host_port else None,
        "frontendPort": int(info.frontend_host_port) if info.frontend_host_port else None,
        "backendUrl": f"http://localhost:{info.backend_host_port}" if info.backend_host_port else None,
        "frontendUrl": f"http://localhost:{info.frontend_host_port}" if info.frontend_host_port else None,
    }

def git_snapshot(sandbox_id: str, message: str = "agent snapshot") -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        return {"success": False, "error": f"Sandbox {sandbox_id} not found"}
    info.snapshot_count += 1
    tag = f"v0.{info.snapshot_count}.0"
    try:
        add_result = _run(["git", "add", "-A"], cwd=info.path)
        if add_result.returncode != 0:
            return {"success": False, "error": add_result.stderr or add_result.stdout}
        commit_result = _run(["git", "commit", "-m", message, "--allow-empty"], cwd=info.path)
        if commit_result.returncode != 0:
            return {"success": False, "error": commit_result.stderr or commit_result.stdout}
        tag_result = _run(["git", "tag", tag], cwd=info.path)
        if tag_result.returncode != 0:
            return {"success": False, "error": tag_result.stderr or tag_result.stdout}
        return {"success": True, "tag": tag, "message": message}
    except Exception as error:
        return {"success": False, "error": str(error)}

def snapshot(sandbox_id: str, message: str = "agent snapshot") -> dict[str, Any]:
    return git_snapshot(sandbox_id, message)

def rollback(sandbox_id: str, tag: str) -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        raise FileNotFoundError(f"Sandbox {sandbox_id} not found")
    result = _run(["git", "checkout", tag], cwd=info.path)
    if result.returncode == 0:
        return {"success": True, "rolledBackTo": tag}
    return {"success": False, "error": result.stderr or result.stdout}

def destroy_sandbox(sandbox_id: str) -> None:
    info = _info(sandbox_id)
    if not info:
        return
    stop_sandbox_containers(sandbox_id)
    shutil.rmtree(info.path, ignore_errors=True)
    for key, value in list(_sandboxes.items()):
        if value is info:
            _sandboxes.pop(key, None)

def stop_sandbox_containers(sandbox_id: str) -> dict[str, Any]:
    info = _info(sandbox_id)
    if not info:
        stopped = _stop_containers_for_sandbox_id(sandbox_id)
        return {"stopped": bool(stopped), "containers": stopped, "message": "Stopped by container name" if stopped else "Sandbox not found"}

    targets = [
        info.db_container_id or info.db_container_name,
        info.backend_container_id or info.backend_container_name,
        info.frontend_container_id or info.frontend_container_name,
    ]
    stopped: list[str] = []
    errors: list[str] = []

    for target in [item for item in targets if item]:
        result = _run(["docker", "rm", "-f", target], timeout=10000)
        if result.returncode == 0:
            stopped.append(target)
        else:
            detail = (result.stderr or result.stdout or "").strip()
            if "No such container" not in detail:
                errors.append(f"{target}: {detail}")

    info.db_container_id = None
    info.backend_container_id = None
    info.frontend_container_id = None
    for user_id, active_sandbox_id in list(_active_preview_by_user.items()):
        if active_sandbox_id == info.sandbox_id:
            _active_preview_by_user.pop(user_id, None)
    print("   Sandbox containers stopped")
    return {"stopped": bool(stopped), "containers": stopped, "errors": errors}
