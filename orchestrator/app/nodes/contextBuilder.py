from __future__ import annotations

import json
import re
from typing import Any

from ..models.contracts import AgentState
from ..services.sandbox import get_file_list, read_file
from ._shared import clone, log


def _extract_basic_interface(content: str, file_path: str) -> dict[str, Any]:
    exports: list[str] = []
    for line in content.splitlines():
        named = re.search(r"export\s+(?:async\s+)?(?:function|const|let|class)\s+(\w+)", line)
        if named:
            exports.append(named.group(1))
        default = re.search(r"export\s+default\s+(?:function\s+)?(\w+)?", line)
        if default and default.group(1):
            exports.append(f"default:{default.group(1)}")
    default_name = next((item.split(":", 1)[1] for item in exports if item.startswith("default:")), None)
    named_exports = [item for item in exports if not item.startswith("default:")]
    if default_name and named_exports:
        import_statement = f"import {default_name}, {{ {', '.join(named_exports)} }} from '{file_path}'"
    elif default_name:
        import_statement = f"import {default_name} from '{file_path}'"
    elif named_exports:
        import_statement = f"import {{ {', '.join(named_exports)} }} from '{file_path}'"
    else:
        import_statement = ""
    return {
        "path": file_path,
        "exports": [*named_exports, *([default_name] if default_name else [])],
        "importStatement": import_statement,
        "interface": ", ".join(exports) or "unknown exports",
    }


async def contextBuilderNode(state: AgentState) -> AgentState:
    current_task = state.currentTask
    if not current_task:
        state.contextPackage = None
        log(state, "Context Builder skipped: no current task")
        return state

    blueprint = state.blueprint or {}
    registry = state.fileRegistry or []
    files_to_create = current_task.get("filesToCreate", []) or []
    context: dict[str, Any] = {
        "task": {
            "taskId": current_task.get("taskId"),
            "title": current_task.get("title"),
            "description": current_task.get("description"),
            "filesToCreate": files_to_create,
            "acceptanceCriteria": current_task.get("acceptanceCriteria", []) or [],
        },
        "patterns": clone(state.projectPatterns),
        "dependencyInterfaces": {},
        "dbSchema": None,
        "apiEndpoints": None,
        "templateFile": None,
        "namingMap": None,
        "appName": (state.clarifiedSpec or {}).get("appName", "app"),
        "authRequired": (state.clarifiedSpec or {}).get("authRequired", False),
    }

    auto_needed = set(current_task.get("filesNeeded", []) or [])
    is_backend_route = any("routes" in item or "controllers" in item for item in files_to_create)
    is_frontend_page = any("pages" in item or "components" in item for item in files_to_create)
    is_integration = any(item.endswith("index.js") or item.endswith("App.jsx") or item.endswith("server.js") for item in files_to_create)

    if is_backend_route:
        for entry in registry:
            path = entry.get("path", "")
            if any(part in path for part in ["models/", "middleware/", "config/"]):
                auto_needed.add(path)
    if is_frontend_page:
        for entry in registry:
            path = entry.get("path", "")
            if any(part in path for part in ["utils/api", "context/", "hooks/"]):
                auto_needed.add(path)
    if is_integration:
        is_backend = any("backend" in item for item in files_to_create)
        is_frontend = any("frontend" in item for item in files_to_create)
        for entry in registry:
            path = entry.get("path", "")
            if is_backend and path.startswith("backend/"):
                auto_needed.add(path)
            if is_frontend and path.startswith("frontend/"):
                auto_needed.add(path)

    for file_path in auto_needed:
        if file_path in files_to_create:
            continue
        entry = next((item for item in registry if item.get("path") == file_path), None)
        if not entry:
            directory = "/".join(file_path.split("/")[:-1])
            filename = re.sub(r"\.(js|jsx)$", "", file_path.split("/")[-1].lower())
            entry = next((
                item for item in registry
                if "/".join(item.get("path", "").split("/")[:-1]) == directory
                and (
                    re.sub(r"\.(js|jsx)$", "", item.get("path", "").split("/")[-1].lower()) in filename
                    or filename in re.sub(r"\.(js|jsx)$", "", item.get("path", "").split("/")[-1].lower())
                )
            ), None)
        if not entry and state.sandboxId:
            content = read_file(state.sandboxId, file_path)
            target_path = file_path
            if not content:
                all_files = get_file_list(state.sandboxId)
                directory = "/".join(file_path.split("/")[:-1])
                base_name = re.sub(r"\.(js|jsx)$", "", file_path.split("/")[-1].lower())
                match = next((
                    item for item in all_files
                    if "/".join(item.split("/")[:-1]) == directory
                    and (
                        re.sub(r"\.(js|jsx)$", "", item.split("/")[-1].lower()) in base_name
                        or base_name in re.sub(r"\.(js|jsx)$", "", item.split("/")[-1].lower())
                    )
                ), None)
                if match:
                    target_path = match
                    content = read_file(state.sandboxId, match)
            if content:
                entry = _extract_basic_interface(content, target_path)
        if entry:
            key = entry.get("path") or file_path
            context["dependencyInterfaces"][key] = {
                "importStatement": entry.get("importStatement"),
                "exports": entry.get("exports") or entry.get("namedExports") or [],
                "interface": entry.get("interface"),
            }

    if blueprint.get("entities"):
        context["namingMap"] = [{
            "entity": entity.get("name"),
            "tableName": entity.get("tableName"),
            "apiPath": entity.get("apiPath"),
            "modelFile": entity.get("modelFile"),
            "routeFile": entity.get("routeFile"),
        } for entity in blueprint.get("entities", [])]

    if any("backend" in item for item in files_to_create) and blueprint.get("dbSchema"):
        task_text = f"{current_task.get('title', '')} {current_task.get('description', '')}".lower()
        tables = blueprint.get("dbSchema", {}).get("tables", []) or []
        relevant = []
        for table in tables:
            table_name = str(table.get("name", "")).lower()
            entity_name = table_name.replace("_", "").removesuffix("s")
            if table_name in task_text or entity_name in task_text or table_name.replace("_", " ") in task_text:
                relevant.append(table)
        context["dbSchema"] = {
            "databaseType": blueprint.get("dbSchema", {}).get("databaseType"),
            "tables": relevant if relevant else tables,
        }

    if any("frontend" in item for item in files_to_create) and blueprint.get("apiEndpoints"):
        task_text = f"{current_task.get('title', '')} {current_task.get('description', '')}".lower()
        relevant = []
        for endpoint in blueprint.get("apiEndpoints", []) or []:
            parts = str(endpoint.get("path", "")).lower().split("/")
            if any(len(part) > 2 and part in task_text for part in parts):
                relevant.append(endpoint)
        auth = [item for item in blueprint.get("apiEndpoints", []) or [] if "/auth" in str(item.get("path", ""))]
        combined = [dict(item) for item in {json.dumps(item, sort_keys=True): item for item in [*auth, *relevant]}.values()]
        context["apiEndpoints"] = combined if combined else blueprint.get("apiEndpoints")

    if registry:
        target_file = files_to_create[0] if files_to_create else ""
        template_type = ""
        if "models" in target_file:
            template_type = "models"
        elif "routes" in target_file or "controllers" in target_file:
            template_type = "routes"
        elif "pages" in target_file:
            template_type = "pages"
        elif "components" in target_file:
            template_type = "components"
        if template_type:
            template_entry = next((item for item in registry if template_type in item.get("path", "") and item.get("path") not in files_to_create), None)
            if template_entry and state.sandboxId:
                content = read_file(state.sandboxId, template_entry.get("path", ""))
                if content:
                    context["templateFile"] = {"path": template_entry.get("path"), "content": content[:3000]}

    state.contextPackage = context
    log(state, f"Context package built for coder ({len(context['dependencyInterfaces'])} dependencies)")
    return state
