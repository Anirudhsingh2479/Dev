from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .sandbox_process import _docker_exec, _run_required, _run_with_input
from .sandbox_state import PROJECT_DB_URI


def _external_project_db_enabled(db_type: str) -> bool:
    return db_type == "postgres" and bool(PROJECT_DB_URI)

def _project_schema_name(sandbox_id: str) -> str:
    suffix = re.sub(r"[^a-zA-Z0-9_]", "_", sandbox_id).strip("_")
    return f"project_{suffix}".lower()

def _project_db_url(sandbox_id: str, db_type: str, db_container_name: str) -> str:
    if db_type == "mongo":
        return f"mongodb://{db_container_name}:27017/appdb"
    if not PROJECT_DB_URI:
        return f"postgresql://postgres:postgres@{db_container_name}:5432/appdb"

    parsed = urlparse(PROJECT_DB_URI)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")
    query["options"] = f"-c search_path={_project_schema_name(sandbox_id)},public"
    return urlunparse(parsed._replace(query=urlencode(query)))

def _project_db_env_args() -> list[str]:
    parsed = urlparse(PROJECT_DB_URI)
    if not parsed.hostname or not parsed.username:
        raise RuntimeError("PROJECT_DB_URI is invalid or missing host/user")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    return [
        "-e", f"PGHOST={parsed.hostname}",
        "-e", f"PGPORT={parsed.port or 5432}",
        "-e", f"PGDATABASE={parsed.path.lstrip('/')}",
        "-e", f"PGUSER={parsed.username}",
        "-e", f"PGPASSWORD={parsed.password or ''}",
        "-e", f"PGSSLMODE={query.get('sslmode', 'require')}",
    ]

def _external_project_psql(sql: str, timeout: int = 30000, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        "docker", "run", "--rm", "-i",
        "--dns", "1.1.1.1", "--dns", "8.8.8.8",
        *_project_db_env_args(), "postgres:16-alpine",
        "psql", *(args or []), "-v", "ON_ERROR_STOP=1",
    ]
    last_result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, 5):
        result = _run_with_input(command, sql, timeout=timeout)
        if result.returncode == 0:
            return result
        last_result = result
        detail = (result.stderr or result.stdout or "").lower()
        if "could not translate host name" not in detail and "temporary failure" not in detail:
            return result
        print(f"   External project DB DNS failed; retrying psql attempt {attempt}/4...")
        time.sleep(min(attempt * 2, 8))
    return last_result or _run_with_input(command, sql, timeout=timeout)

def _external_project_table_count(schema: str) -> int | None:
    sql = (
        "SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE';"
    )
    result = _external_project_psql(sql, timeout=15000, args=["-tA"])
    if result.returncode != 0:
        print(f"   Could not inspect external project DB tables: {(result.stderr or result.stdout).strip()[:200]}")
        return None
    try:
        return int((result.stdout or "").strip().splitlines()[-1])
    except (IndexError, ValueError):
        return None

def _initialize_external_project_db(sandbox_id: str, backend_path: Path, db_schema: dict[str, Any] | None = None) -> None:
    schema = _project_schema_name(sandbox_id)
    create_schema = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    result = _external_project_psql(create_schema, timeout=30000)
    if result.returncode != 0:
        raise RuntimeError(f"Project database schema creation failed: {(result.stderr or result.stdout).strip()}")

    table_count = _external_project_table_count(schema)
    if table_count is None:
        print("   Skipping external project DB initialization because table state could not be verified")
        return
    if table_count > 0:
        print(f"   External project DB schema {schema} already has {table_count} table(s); skipping initialization")
        return

    init_sql = backend_path / "src" / "db" / "init.sql"
    sql_parts = [f"SET search_path TO {schema}, public;"]
    generated_sql = _generate_create_table_sql(db_schema)
    if generated_sql:
        sql_parts.append(generated_sql)
    if init_sql.exists():
        sql_parts.append(init_sql.read_text(encoding="utf-8"))
    if len(sql_parts) == 1:
        print(f"   External project DB schema {schema} created without table SQL")
        return

    print(f"   Initializing external project DB schema {schema}...")
    result = _external_project_psql("\n\n".join(sql_parts), timeout=60000)
    if result.returncode != 0:
        raise RuntimeError(f"External project database initialization failed: {(result.stderr or result.stdout).strip()}")
    print(f"   External project DB schema {schema} initialized")

def _postgres_table_count(container_id: str) -> int | None:
    result = _docker_exec(
        container_id,
        (
            "psql -U postgres -d appdb -tAc "
            "\"SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE';\""
        ),
        10000,
    )
    if result["exitCode"] != 0:
        print(f"   Could not inspect PostgreSQL tables: {(result['stderr'] or result['stdout']).strip()[:200]}")
        return None
    try:
        return int(result["stdout"].strip() or "0")
    except ValueError:
        return None

def _initialize_postgres_from_project_sql(container_id: str, backend_path: Path) -> None:
    init_sql = backend_path / "src" / "db" / "init.sql"
    if not init_sql.exists():
        return

    table_count = _postgres_table_count(container_id)
    if table_count is None:
        print("   Skipping project init.sql because table state could not be verified")
        return
    if table_count > 0:
        print(f"   PostgreSQL already has {table_count} table(s); skipping project init.sql")
        return

    print("   Applying project database init.sql...")
    _run_required(["docker", "cp", str(init_sql), f"{container_id}:/tmp/aidev-init.sql"], timeout=10000)
    result = _docker_exec(container_id, "psql -U postgres -d appdb -v ON_ERROR_STOP=1 -f /tmp/aidev-init.sql", 30000)
    if result["exitCode"] != 0:
        detail = (result["stderr"] or result["stdout"]).strip()
        raise RuntimeError(f"Project database init.sql failed: {detail}")
    print("   Project database initialized")

def _generate_create_table_sql(db_schema: dict[str, Any] | None) -> str | None:
    if not db_schema or not db_schema.get("tables"):
        return None
    statements: list[str] = []
    for table in db_schema.get("tables", []):
        fields = []
        for field in table.get("fields", []):
            constraints = " ".join(field.get("constraints", []) or [])
            fields.append(f"  {field.get('name')} {field.get('type', 'TEXT')} {constraints}".rstrip())
        if fields:
            statements.append(f"CREATE TABLE IF NOT EXISTS {table.get('name')} (\n{',\n'.join(fields)}\n);")
    for table in db_schema.get("tables", []):
        for fk in table.get("foreignKeys", []) or []:
            statements.append(
                f"ALTER TABLE {table.get('name')} ADD CONSTRAINT IF NOT EXISTS "
                f"fk_{table.get('name')}_{fk.get('field')} FOREIGN KEY ({fk.get('field')}) "
                f"REFERENCES {fk.get('references')} ON DELETE {fk.get('onDelete', 'CASCADE')};"
            )
        for idx in table.get("indexes", []) or []:
            idx_name = f"idx_{table.get('name')}_{str(idx).replace(',', '_')}"
            statements.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table.get('name')} ({idx});")
    return "\n".join(statements) if statements else None
