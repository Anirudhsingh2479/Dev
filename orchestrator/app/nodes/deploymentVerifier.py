from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

from ..models.contracts import AgentState
from ..services.sandbox import get_file_list, read_file, run_in_sandbox, write_file
from ._shared import log, retry_limit

BACKEND_PORT = 15000
FRONTEND_PORT = 15173
DB_PORT = 15432


def _detect_backend_entry(state: AgentState) -> str:
    candidates = ["src/index.js", "src/server.js", "src/app.js", "index.js", "server.js", "app.js"]
    files = set(get_file_list(state.sandboxId) or state.fileTree)
    for candidate in candidates:
        if f"backend/{candidate}" in files:
            return candidate

    package_json = read_file(state.sandboxId, "backend/package.json")
    if package_json:
        try:
            pkg = json.loads(package_json)
            if pkg.get("main"):
                return str(pkg["main"])
            start_script = (pkg.get("scripts") or {}).get("start", "")
            match = re.search(r"node\s+(.+)", start_script)
            if match:
                return match.group(1).strip()
        except json.JSONDecodeError:
            pass

    return "src/index.js"


def _detect_db_type(state: AgentState) -> str:
    package_json = read_file(state.sandboxId, "backend/package.json")
    if package_json:
        try:
            deps = (json.loads(package_json).get("dependencies") or {})
            if deps.get("mongoose") or deps.get("mongodb"):
                return "mongo"
        except json.JSONDecodeError:
            pass
    return "postgres"


def _generate_deployment_files(state: AgentState) -> dict[str, str]:
    entry_point = _detect_backend_entry(state)
    db_type = _detect_db_type(state)
    db_image = "mongo:7" if db_type == "mongo" else "postgres:16-alpine"
    db_port = "27017" if db_type == "mongo" else "5432"
    db_env = "MONGO_INITDB_DATABASE: appdb" if db_type == "mongo" else "\n      ".join([
        "POSTGRES_USER: postgres",
        "POSTGRES_PASSWORD: postgres",
        "POSTGRES_DB: appdb",
    ])
    db_url = "mongodb://db:27017/appdb" if db_type == "mongo" else "postgresql://postgres:postgres@db:5432/appdb"
    db_health_check = 'mongosh --eval "db.runCommand({ping:1})" --quiet' if db_type == "mongo" else "pg_isready -U postgres"
    volume_path = "/data/db" if db_type == "mongo" else "/var/lib/postgresql/data"

    write_file(state.sandboxId, "backend/Dockerfile", f"""FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 5000
CMD ["node", "{entry_point}"]
""")

    write_file(state.sandboxId, "frontend/Dockerfile", """FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
""")

    write_file(state.sandboxId, "frontend/nginx.conf", """server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  location /api/ {
      proxy_pass http://backend:5000/api/;
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
  }

  location / {
      try_files $uri $uri/ /index.html;
  }
}
""")

    write_file(state.sandboxId, "docker-compose.yml", f"""version: "3.8"

services:
  db:
    image: {db_image}
    restart: unless-stopped
    ports:
      - "{DB_PORT}:{db_port}"
    environment:
      {db_env}
    volumes:
      - db_data:{volume_path}
    healthcheck:
      test: ["CMD-SHELL", "{db_health_check}"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    restart: unless-stopped
    ports:
      - "{BACKEND_PORT}:5000"
    environment:
      DATABASE_URL: {db_url}
      JWT_SECRET: dev-secret-change-in-production
      PORT: "5000"
      NODE_ENV: production
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "{FRONTEND_PORT}:80"
    depends_on:
      - backend

volumes:
  db_data:
""")

    if read_file(state.sandboxId, "backend/.env") is None:
        write_file(state.sandboxId, "backend/.env", "\n".join([
            f"DATABASE_URL={db_url}",
            "JWT_SECRET=dev-secret-change-in-production",
            "PORT=5000",
            "NODE_ENV=production",
        ]) + "\n")

    if read_file(state.sandboxId, "frontend/.env") is None:
        write_file(state.sandboxId, "frontend/.env", "VITE_API_URL=/api\n")

    if read_file(state.sandboxId, "frontend/vite.config.js") is None:
        write_file(state.sandboxId, "frontend/vite.config.js", """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
});
""")

    return {"entryPoint": entry_point, "dbType": db_type}


def _compose(state: AgentState, command: str, timeout: int) -> dict[str, Any]:
    result = run_in_sandbox(state.sandboxId, f"docker-compose {command} 2>&1", timeout)
    if result["exitCode"] != 0 and "not found" in (result["stdout"] + result["stderr"]).lower():
        result = run_in_sandbox(state.sandboxId, f"docker compose {command} 2>&1", timeout)
    return result


def _test_endpoint(url: str, timeout: int = 10000) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout / 1000) as response:
            return {"success": 200 <= response.status < 500, "status": response.status, "body": response.read(4096).decode("utf-8", "ignore")}
    except urllib.error.HTTPError as error:
        return {"success": 200 <= error.code < 500, "status": error.code, "body": error.read(4096).decode("utf-8", "ignore")}
    except Exception as error:
        return {"success": False, "status": 0, "body": str(error)}


def _last_lines(text: str, count: int = 20) -> str:
    return "\n".join((text or "").splitlines()[-count:])


def _build_verify_result(state: AgentState, passed: bool, outputs: list[str], errors: list[str], attempts: int) -> AgentState:
    state.deploymentAttempts = attempts
    state.executionResult = {
        "result": "pass" if passed else "fail",
        "output": "\n".join(outputs),
        "errors": "\n".join(errors),
    }
    state.deploymentConfig = {
        "platform": "docker-compose",
        "files": ["docker-compose.yml", "backend/Dockerfile", "frontend/Dockerfile", "frontend/nginx.conf"],
        "instructions": [
            "cd sandboxes/<sandbox-id>",
            "docker-compose up --build",
            f"Frontend: http://localhost:{FRONTEND_PORT}",
            f"Backend API: http://localhost:{BACKEND_PORT}/api",
        ],
    }
    state.fileTree = get_file_list(state.sandboxId)
    return state


async def deploymentVerifierNode(state: AgentState) -> AgentState:
    attempts = state.deploymentAttempts or 0
    max_attempts = retry_limit(state, "deploymentRepairs", 2)
    if attempts >= max_attempts:
        state.deploymentAttempts = attempts
        state.executionResult = {
            "result": "pass",
            "output": f"Skipped after {max_attempts} deployment attempt(s). Code is complete, docker-compose may need manual fixes.",
            "errors": "",
        }
        log(state, f"Deployment Verifier skipped after max attempts ({max_attempts})")
        return state

    outputs: list[str] = []
    errors: list[str] = []
    try:
        detected = _generate_deployment_files(state)
        outputs.append(f"Generated Dockerfiles (entry: {detected['entryPoint']}, db: {detected['dbType']})")

        build_result = _compose(state, "build --no-cache", 300000)
        if build_result["exitCode"] != 0:
            errors.append(f"Docker build failed:\n{_last_lines(build_result['stdout'] + build_result['stderr'])}")
            return _build_verify_result(state, False, outputs, errors, attempts + 1)
        outputs.append("Docker build successful")

        _compose(state, "down", 15000)
        up_result = _compose(state, "up -d", 60000)
        if up_result["exitCode"] != 0:
            errors.append(f"docker-compose up failed:\n{(up_result['stdout'] + up_result['stderr'])[-500:]}")
            return _build_verify_result(state, False, outputs, errors, attempts + 1)
        outputs.append("Services started")

        time.sleep(20)
        ps_result = _compose(state, "ps", 10000)
        if ps_result["stdout"]:
            outputs.append(ps_result["stdout"].strip())

        backend_ok = False
        for test_path in ["/api/health", "/api", "/health", "/"]:
            result = _test_endpoint(f"http://localhost:{BACKEND_PORT}{test_path}", 5000)
            if result["success"]:
                outputs.append(f"Backend responds at {test_path}: {result['status']}")
                backend_ok = True
                break
        if not backend_ok:
            logs = _compose(state, "logs --tail=30 backend", 10000)
            errors.append(f"Backend not responding. Logs:\n{logs['stdout'][-300:]}")

        frontend_test = _test_endpoint(f"http://localhost:{FRONTEND_PORT}", 10000)
        if frontend_test["success"]:
            outputs.append(f"Frontend responds: {frontend_test['status']}")
        else:
            logs = _compose(state, "logs --tail=30 frontend", 10000)
            errors.append(f"Frontend not responding. Logs:\n{logs['stdout'][-300:]}")

        if detected["dbType"] == "postgres":
            db_test = _compose(state, "exec -T db pg_isready -U postgres", 10000)
        else:
            db_test = _compose(state, "exec -T db mongosh --eval 'db.runCommand({ping:1})' --quiet", 10000)
        outputs.append("Database accepting connections" if db_test["exitCode"] == 0 else "Database check inconclusive")

        passed = len(errors) == 0
        if not passed:
            _compose(state, "down", 15000)

        log(state, "Deployment Verifier completed")
        return _build_verify_result(state, passed, outputs, errors, attempts + 1)
    except Exception as error:
        try:
            _compose(state, "down", 15000)
        except Exception:
            pass
        errors.append(f"Verification error: {error}")
        log(state, "Deployment Verifier failed")
        return _build_verify_result(state, False, outputs, errors, attempts + 1)


def deploymentVerifierRouter(state: AgentState) -> str:
    if state.executionResult.get("result") == "pass":
        return "presentToUser"
    if state.deploymentAttempts >= retry_limit(state, "deploymentRepairs", 2):
        return "presentToUser"
    return "debuggerAgent"
