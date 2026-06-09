from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..models.contracts import AgentState
from ..services.sandbox import execute_command, get_file_list, get_sandbox_info, read_file
from ._shared import log


def _build_result(state: AgentState, passed: bool, outputs: list[str], errors: list[str]) -> AgentState:
    state.executionResult = {
        "result": "pass" if passed else "fail",
        "output": "\n".join(outputs),
        "errors": "\n".join(errors),
    }
    log(state, f"Executor result: {state.executionResult['result']}")
    return state


def _resolve_relative(file_dir: str, import_path: str) -> str:
    parts = [part for part in file_dir.split("/") if part]
    for part in import_path.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return PurePosixPath(*parts).as_posix() if parts else ""


async def executorAgentNode(state: AgentState) -> AgentState:
    if not state.currentTask or not state.sandboxId:
        return _build_result(state, True, ["Nothing to test"], [])

    info = get_sandbox_info(state.sandboxId) or {}
    is_docker = bool(info.get("dockerEnabled"))
    errors: list[str] = []
    outputs: list[str] = []
    files = (state.coderOutput or {}).get("files", [])
    registry = state.fileRegistry or []
    all_files = get_file_list(state.sandboxId)

    for file in files:
        content = read_file(state.sandboxId, file.get("path", ""))
        if not content:
            errors.append(f"File not found: {file.get('path')}")
        else:
            outputs.append(f"+ {file.get('path')} exists ({len(content.splitlines())} lines)")
    if errors:
        return _build_result(state, False, outputs, errors)

    for file in files:
        path = file.get("path", "")
        if not path.endswith((".js", ".jsx")):
            continue
        if path.endswith(".jsx"):
            content = read_file(state.sandboxId, path) or ""
            if "import" in content or "export" in content:
                outputs.append(f"+ {path} valid module structure")
            continue
        if is_docker:
            container = "frontend" if "frontend" in path else "backend"
            result = execute_command(state.sandboxId, f"cd /app/{container} && node --check /app/{path}", 10000)
            stderr = result.get("stderr", "")
            if result.get("exitCode") == 0:
                outputs.append(f"+ {path} syntax valid")
            elif "SyntaxError" in stderr:
                errors.append(f"Syntax error in {path}: {stderr[:300]}")
            else:
                outputs.append(f"~ {path} unresolved imports (will resolve after npm install)")
    if errors:
        return _build_result(state, False, outputs, errors)

    for file in files:
        path = file.get("path", "")
        content = read_file(state.sandboxId, path) or ""
        file_dir = "/".join(path.split("/")[:-1])
        for line in content.splitlines():
            match = re.search(r"import\s+.*\s+from\s+['\"]([.][^'\"]+)['\"]", line)
            if not match:
                continue
            import_path = match.group(1)
            resolved = _resolve_relative(file_dir, import_path)
            found_path = None
            for ext in ["", ".js", ".jsx", "/index.js", "/index.jsx"]:
                candidate = resolved + ext
                if candidate in all_files:
                    found_path = candidate
                    break
            if not found_path:
                errors.append(f"{path}: imports from \"{import_path}\" but resolved path \"{resolved}\" not found on disk")
                continue
            named_match = re.search(r"import\s+\{([^}]+)\}\s+from", line)
            if named_match:
                imported_names = [item.strip().split(" as ")[0].strip() for item in named_match.group(1).split(",")]
                reg_entry = next((item for item in registry if item.get("path") in [found_path, resolved]), None)
                if reg_entry and reg_entry.get("exports"):
                    for name in imported_names:
                        if name not in reg_entry.get("exports", []):
                            errors.append(f"{path}: imports \"{name}\" from {found_path} but that file doesn't export it. Available: [{', '.join(reg_entry.get('exports', []))}]")

    for file in files:
        path = file.get("path", "")
        content = read_file(state.sandboxId, path) or ""
        if "frontend" in path and "process.env" in content:
            errors.append(f"{path}: uses process.env - frontend must use import.meta.env")
        if "backend" in path and "import.meta.env" in content:
            errors.append(f"{path}: uses import.meta.env - backend must use process.env")

    if is_docker and not errors:
        if any("backend" in file.get("path", "") for file in files):
            result = execute_command(state.sandboxId, "cd /app/backend && npm install 2>&1", 60000)
            outputs.append("+ Backend npm install ok" if result.get("exitCode") == 0 else f"~ Backend npm: {(result.get('stderr') or result.get('stdout') or '')[:100]}")
        if any("frontend" in file.get("path", "") for file in files):
            result = execute_command(state.sandboxId, "cd /app/frontend && npm install 2>&1", 60000)
            outputs.append("+ Frontend npm install ok" if result.get("exitCode") == 0 else f"~ Frontend npm: {(result.get('stderr') or result.get('stdout') or '')[:100]}")

    return _build_result(state, len(errors) == 0, outputs, errors)


def executorRouter(state: AgentState) -> str:
    return "snapshotManager" if state.executionResult.get("result") == "pass" else "debuggerAgent"
