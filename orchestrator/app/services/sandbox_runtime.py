from __future__ import annotations

import json
import time
from typing import Any

from .sandbox_database import (
    _external_project_db_enabled,
    _generate_create_table_sql,
    _initialize_external_project_db,
    _initialize_postgres_from_project_sql,
    _project_db_url,
)
from .sandbox_files import _info, get_sandbox_info, stop_sandbox_containers
from .sandbox_process import (
    _allocate_preview_ports,
    _docker_available,
    _docker_exec,
    _ensure_network,
    _published_port,
    _requires_docker,
    _run,
    _run_required,
    _wait_for_container,
    _write,
    stop_active_preview_for_user,
)
from .sandbox_scaffold import _scaffold
from .sandbox_state import (
    DOCKER_RUN_TIMEOUT_MS,
    NETWORK_NAME,
    NPM_INSTALL_TIMEOUT_MS,
    SandboxInfo,
    _active_preview_by_user,
    _docker_mount_path,
    _sandbox_path,
    _sandboxes,
)


def create_sandbox(
    project_id: str,
    user_id: str = "demo-user",
    folder_structure: str | None = None,
    dependencies: dict[str, Any] | None = None,
    db_schema: dict[str, Any] | None = None,
) -> str:
    sandbox_id = f"sandbox-{int(time.time() * 1000)}"
    sandbox_path = _sandbox_path(sandbox_id)
    docker_mount_path = _docker_mount_path(sandbox_id)
    print(f"   Creating sandbox: {sandbox_path}")
    print(f"   Docker mount path: {docker_mount_path}")
    print(f"   Docker: {'ENABLED' if _docker_available() else 'DISABLED'}")
    sandbox_path.mkdir(parents=True, exist_ok=True)

    if folder_structure:
        for line in folder_structure.splitlines():
            cleaned = line.replace("├──", "").replace("└──", "").replace("│", "").strip().rstrip("/")
            if cleaned and "." not in cleaned and len(cleaned) < 100:
                (sandbox_path / cleaned).mkdir(parents=True, exist_ok=True)

    db_type = "mongo" if (dependencies or {}).get("backend", {}).get("dependencies", {}).get("mongoose") else "postgres"
    db_container_name = f"aidev-db-{sandbox_id}"
    backend_container_name = f"aidev-backend-{sandbox_id}"
    frontend_container_name = f"aidev-frontend-{sandbox_id}"
    volume_name = f"aidev-dbdata-{sandbox_id}"
    db_url = _project_db_url(sandbox_id, db_type, db_container_name)
    _scaffold(sandbox_path, dependencies, db_type, db_url)
    print("   Scaffold: backend skeleton, frontend boilerplate, configs created")

    try:
        _run(["git", "init"], cwd=sandbox_path)
        _run(["git", "config", "user.email", "aidev@example.local"], cwd=sandbox_path)
        _run(["git", "config", "user.name", "AI Dev Team"], cwd=sandbox_path)
        _run(["git", "add", "-A"], cwd=sandbox_path)
        _run(["git", "commit", "-m", "Initial scaffold", "--allow-empty"], cwd=sandbox_path)
        _run(["git", "tag", "v0.0.0"], cwd=sandbox_path)
        print("   Git initialized")
    except Exception as error:
        print(f"   Git init failed: {error}")

    info = SandboxInfo(
        sandbox_id=sandbox_id,
        path=sandbox_path,
        backend_path=sandbox_path / "backend",
        frontend_path=sandbox_path / "frontend",
        db_type=db_type,
        db_container_name=db_container_name,
        backend_container_name=backend_container_name,
        frontend_container_name=frontend_container_name,
        user_id=user_id,
        created_at=time.time(),
    )
    _sandboxes[sandbox_id] = info
    _sandboxes[project_id] = info

    docker_available = _docker_available()
    if not docker_available and _requires_docker():
        raise RuntimeError(
            "Docker is required but unavailable inside the orchestrator container. "
            "Start Docker Desktop, rebuild with docker compose up --build, and make sure /var/run/docker.sock is mounted."
        )

    if docker_available:
        try:
            cleanup = stop_active_preview_for_user(user_id)
            if cleanup.get("containers"):
                print(f"   Stopped user's active preview containers before new sandbox: {', '.join(cleanup['containers'])}")
            _ensure_network()
            backend_host_port, frontend_host_port = _allocate_preview_ports()
            info.backend_host_port = backend_host_port
            info.frontend_host_port = frontend_host_port
            _write(info.frontend_path / ".env", f"VITE_API_URL=http://localhost:{backend_host_port}/api\n")
            if _external_project_db_enabled(db_type):
                print("   Using external project PostgreSQL database")
                _initialize_external_project_db(sandbox_id, info.backend_path, db_schema)
            elif db_type == "mongo":
                print("   Starting MongoDB container...")
                db = _run_required(["docker", "run", "-d", "--name", db_container_name, "--network", NETWORK_NAME, "-v", f"{volume_name}:/data/db", "-e", "MONGO_INITDB_DATABASE=appdb", "mongo:7"], timeout=DOCKER_RUN_TIMEOUT_MS)
                info.db_container_id = db.stdout.strip()
                print(f"   MongoDB container: {info.db_container_id[:12]}")
                print("   Waiting for MongoDB to be ready...")
                _wait_for_container(info.db_container_id, "mongosh --eval 'db.runCommand({ping:1})' --quiet", 30)
            else:
                print("   Starting PostgreSQL container...")
                db = _run_required(["docker", "run", "-d", "--name", db_container_name, "--network", NETWORK_NAME, "-v", f"{volume_name}:/var/lib/postgresql/data", "-e", "POSTGRES_USER=postgres", "-e", "POSTGRES_PASSWORD=postgres", "-e", "POSTGRES_DB=appdb", "postgres:16-alpine"], timeout=DOCKER_RUN_TIMEOUT_MS)
                info.db_container_id = db.stdout.strip()
                print(f"   PostgreSQL container: {info.db_container_id[:12]}")
                print("   Waiting for PostgreSQL to be ready...")
                _wait_for_container(info.db_container_id, "pg_isready -U postgres", 30)
                sql = _generate_create_table_sql(db_schema)
                if sql and info.db_container_id:
                    print("   Creating database tables...")
                    _docker_exec(info.db_container_id, f"psql -U postgres -d appdb -c '{sql.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'", 15000)
                if info.db_container_id:
                    _initialize_postgres_from_project_sql(info.db_container_id, info.backend_path)

            print("   Starting Backend container...")
            backend = _run_required(["docker", "run", "-d", "--name", backend_container_name, "--network", NETWORK_NAME, "-p", f"127.0.0.1:{backend_host_port}:5000", "-v", f"{docker_mount_path}:/app", "-w", "/app", "-e", f"DATABASE_URL={db_url}", "-e", "JWT_SECRET=dev-secret-change-in-production", "-e", "PORT=5000", "-e", "NODE_ENV=development", "node:20-slim", "tail", "-f", "/dev/null"], timeout=DOCKER_RUN_TIMEOUT_MS)
            info.backend_container_id = backend.stdout.strip()
            info.backend_host_port = _published_port(info.backend_container_id, 5000) or backend_host_port
            print(f"   Backend container: {info.backend_container_id[:12]}")
            if info.backend_host_port:
                print(f"   Backend URL: http://localhost:{info.backend_host_port}")
            print("   Installing backend dependencies...")
            _docker_exec(info.backend_container_id, "cd /app/backend && npm install 2>&1", NPM_INSTALL_TIMEOUT_MS)
            print("   Backend dependencies installed")

            print("   Starting Frontend container...")
            browser_api_url = f"http://localhost:{info.backend_host_port}/api" if info.backend_host_port else f"http://{backend_container_name}:5000/api"
            frontend = _run_required(["docker", "run", "-d", "--name", frontend_container_name, "--network", NETWORK_NAME, "-p", f"127.0.0.1:{frontend_host_port}:5173", "-v", f"{docker_mount_path}:/app", "-w", "/app", "-e", f"VITE_API_URL={browser_api_url}", "-e", f"VITE_API_PROXY_TARGET=http://{backend_container_name}:5000", "node:20-slim", "tail", "-f", "/dev/null"], timeout=DOCKER_RUN_TIMEOUT_MS)
            info.frontend_container_id = frontend.stdout.strip()
            info.frontend_host_port = _published_port(info.frontend_container_id, 5173) or frontend_host_port
            print(f"   Frontend container: {info.frontend_container_id[:12]}")
            if info.frontend_host_port:
                print(f"   Frontend URL: http://localhost:{info.frontend_host_port}")
            print("   Installing frontend dependencies...")
            _docker_exec(info.frontend_container_id, "cd /app/frontend && npm install 2>&1", NPM_INSTALL_TIMEOUT_MS)
            print("   Frontend dependencies installed")
            _active_preview_by_user[user_id] = sandbox_id
        except Exception as error:
            stop_sandbox_containers(sandbox_id)
            if _requires_docker():
                raise RuntimeError(f"Docker sandbox setup failed: {error}") from error

    return sandbox_id

def reconnect_sandbox(
    sandbox_id: str,
    user_id: str = "demo-user",
    preferred_backend_port: str | int | None = None,
    preferred_frontend_port: str | int | None = None,
) -> bool:
    sandbox_path = _sandbox_path(sandbox_id)
    docker_mount_path = _docker_mount_path(sandbox_id)

    print(f"\n   Reconnecting sandbox: {sandbox_id}")

    if not sandbox_path.exists():
        print(f"   Sandbox folder not found: {sandbox_path}")
        return False

    print(f"   Found sandbox at: {sandbox_path}")
    print(f"   Docker mount path: {docker_mount_path}")

    backend_path = sandbox_path / "backend"
    frontend_path = sandbox_path / "frontend"

    db_type = "postgres"
    try:
        package_path = backend_path / "package.json"
        if package_path.exists():
            package_json = json.loads(package_path.read_text(encoding="utf-8"))
            if package_json.get("dependencies", {}).get("mongoose"):
                db_type = "mongo"
    except Exception:
        pass

    db_container_name = f"aidev-db-{sandbox_id}"
    backend_container_name = f"aidev-backend-{sandbox_id}"
    frontend_container_name = f"aidev-frontend-{sandbox_id}"
    db_url = _project_db_url(sandbox_id, db_type, db_container_name)

    if not _docker_available():
        print("   Docker not available")
        return False

    for name in [db_container_name, backend_container_name, frontend_container_name]:
        _run(["docker", "rm", "-f", name], timeout=5000)

    try:
        _ensure_network()
        backend_host_port, frontend_host_port = _allocate_preview_ports(preferred_backend_port, preferred_frontend_port)

        print(f"   Starting {'MongoDB' if db_type == 'mongo' else 'PostgreSQL'}...")
        volume_name = f"aidev-dbdata-{sandbox_id}"
        db_container_id = None
        if _external_project_db_enabled(db_type):
            print("   Using external project PostgreSQL database")
            _initialize_external_project_db(sandbox_id, backend_path)
        elif db_type == "mongo":
            db = _run_required([
                "docker", "run", "-d", "--name", db_container_name, "--network", NETWORK_NAME,
                "-v", f"{volume_name}:/data/db", "-e", "MONGO_INITDB_DATABASE=appdb", "mongo:7",
            ], timeout=DOCKER_RUN_TIMEOUT_MS)
            db_container_id = db.stdout.strip()
            print("   Waiting for MongoDB...")
            _wait_for_container(db_container_id, "mongosh --eval 'db.runCommand({ping:1})' --quiet", 30)
        else:
            db = _run_required([
                "docker", "run", "-d", "--name", db_container_name, "--network", NETWORK_NAME,
                "-v", f"{volume_name}:/var/lib/postgresql/data", "-e", "POSTGRES_USER=postgres",
                "-e", "POSTGRES_PASSWORD=postgres", "-e", "POSTGRES_DB=appdb", "postgres:16-alpine",
            ], timeout=DOCKER_RUN_TIMEOUT_MS)
            db_container_id = db.stdout.strip()
            print("   Waiting for PostgreSQL...")
            _wait_for_container(db_container_id, "pg_isready -U postgres", 30)
            _initialize_postgres_from_project_sql(db_container_id, backend_path)
        print("   Database ready")

        print("   Starting Backend container...")
        backend = _run_required([
            "docker", "run", "-d", "--name", backend_container_name, "--network", NETWORK_NAME,
            "-p", f"127.0.0.1:{backend_host_port}:5000", "-v", f"{docker_mount_path}:/app", "-w", "/app", "-e", f"DATABASE_URL={db_url}",
            "-e", "JWT_SECRET=dev-secret-change-in-production", "-e", "PORT=5000",
            "-e", "NODE_ENV=development", "node:20-slim", "tail", "-f", "/dev/null",
        ], timeout=DOCKER_RUN_TIMEOUT_MS)
        backend_container_id = backend.stdout.strip()
        backend_host_port = _published_port(backend_container_id, 5000) or backend_host_port
        _write(frontend_path / ".env", f"VITE_API_URL=http://localhost:{backend_host_port}/api\n")
        print("   Installing backend dependencies...")
        _docker_exec(backend_container_id, "cd /app/backend && npm install 2>&1", NPM_INSTALL_TIMEOUT_MS)
        print("   Backend ready")

        print("   Starting Frontend container...")
        browser_api_url = f"http://localhost:{backend_host_port}/api" if backend_host_port else f"http://{backend_container_name}:5000/api"
        frontend = _run_required([
            "docker", "run", "-d", "--name", frontend_container_name, "--network", NETWORK_NAME,
            "-p", f"127.0.0.1:{frontend_host_port}:5173", "-v", f"{docker_mount_path}:/app", "-w", "/app",
            "-e", f"VITE_API_URL={browser_api_url}",
            "-e", f"VITE_API_PROXY_TARGET=http://{backend_container_name}:5000",
            "node:20-slim", "tail", "-f", "/dev/null",
        ], timeout=DOCKER_RUN_TIMEOUT_MS)
        frontend_container_id = frontend.stdout.strip()
        frontend_host_port = _published_port(frontend_container_id, 5173) or frontend_host_port
        print("   Installing frontend dependencies...")
        _docker_exec(frontend_container_id, "cd /app/frontend && npm install 2>&1", NPM_INSTALL_TIMEOUT_MS)
        print("   Frontend ready")

        _sandboxes[sandbox_id] = SandboxInfo(
            sandbox_id=sandbox_id,
            path=sandbox_path,
            backend_path=backend_path,
            frontend_path=frontend_path,
            db_type=db_type,
            db_container_id=db_container_id,
            backend_container_id=backend_container_id,
            frontend_container_id=frontend_container_id,
            db_container_name=db_container_name,
            backend_container_name=backend_container_name,
            frontend_container_name=frontend_container_name,
            backend_host_port=backend_host_port,
            frontend_host_port=frontend_host_port,
            user_id=user_id,
            created_at=time.time(),
            snapshot_count=0,
        )
        _active_preview_by_user[user_id] = sandbox_id

        print("   Sandbox reconnected! All containers running.\n")
        return True
    except Exception as error:
        print(f"   Reconnect failed: {error}")
        return False
