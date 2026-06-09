from __future__ import annotations

import re

from ..models.contracts import AgentState
from ._shared import log, retry_limit, snake_case


async def blueprintValidatorNode(state: AgentState) -> AgentState:
    blueprint = state.blueprint
    db_schema = blueprint.get("dbSchema", {})
    api_endpoints = blueprint.get("apiEndpoints", [])
    frontend_pages = blueprint.get("frontendPages", [])
    entities = blueprint.get("entities", [])
    current_cycles = state.blueprintValidation.get("validationCycles", 0)
    max_cycles = retry_limit(state, "blueprintRepairs", 2)
    issues = []

    tables = db_schema.get("tables", [])
    table_names = set()
    for table in tables:
        name = str(table.get("name", "")).lower()
        table_names.add(name)
        table_names.add(re.sub(r"s$", "", name))
        table_names.add(name.replace("_", ""))
        table_names.add(re.sub(r"s$", "", name.replace("_", "")))

    for entity in entities:
        plain = str(entity.get("name", "")).lower()
        snake = snake_case(entity.get("name", ""))
        candidates = {plain, f"{plain}s", snake, f"{snake}s", re.sub(r"y$", "ie", snake) + "s"}
        if table_names and not candidates.intersection(table_names):
            issues.append({
                "type": "missing_table",
                "severity": "error",
                "fixTarget": "architectStep2",
                "message": f"Entity \"{entity.get('name')}\" has no matching DB table.",
            })

    exact_table_names = {str(table.get("name", "")).lower() for table in tables}

    for table in tables:
        for fk in table.get("foreignKeys", []):
            match = re.match(r"^(\w+)\(", str(fk.get("references", "")))
            if match and match.group(1).lower() not in exact_table_names:
                issues.append({
                    "type": "invalid_foreign_key",
                    "severity": "error",
                    "fixTarget": "architectStep2",
                    "message": f"Table \"{table.get('name')}\" references missing table \"{match.group(1)}\".",
                })

    for endpoint in api_endpoints:
        related = str(endpoint.get("relatedTable", ""))
        for related_table in [part.strip().lower() for part in related.split(",") if part.strip()]:
            if related_table not in exact_table_names:
                issues.append({
                    "type": "orphan_endpoint",
                    "severity": "error",
                    "fixTarget": "architectStep3",
                    "message": f"API \"{endpoint.get('method')} {endpoint.get('path')}\" references table \"{related_table}\" which does not exist.",
                })

    api_paths = {str(endpoint.get("path", "")).lower() for endpoint in api_endpoints}
    for page in frontend_pages:
        for component in page.get("components", []):
            for api_call in component.get("apiCalls", []):
                normalized = re.sub(r"/:\w+", "/:param", str(api_call).lower())
                exists = any(re.sub(r"/:\w+", "/:param", path) == normalized for path in api_paths)
                if not exists:
                    issues.append({
                        "type": "missing_api",
                        "severity": "warning",
                        "fixTarget": "architectStep3",
                        "message": f"Page \"{page.get('name')}\" calls \"{api_call}\" but no matching API endpoint exists.",
                    })

    auth_paths = {str(endpoint.get("path", "")).lower() for endpoint in api_endpoints if endpoint.get("requiresAuth")}
    for page in frontend_pages:
        for component in page.get("components", []):
            calls_auth_api = any(str(call).lower() in auth_paths for call in component.get("apiCalls", []))
            if calls_auth_api and not page.get("requiresAuth"):
                issues.append({
                    "type": "auth_mismatch",
                    "severity": "warning",
                    "fixTarget": "architectStep4",
                    "message": f"Page \"{page.get('name')}\" calls an auth-required API but page.requiresAuth is false.",
                })

    referenced_tables = set()
    for endpoint in api_endpoints:
        related = str(endpoint.get("relatedTable", ""))
        for related_table in [part.strip().lower() for part in related.split(",") if part.strip()]:
            referenced_tables.add(related_table)

    for table in tables:
        name = str(table.get("name", "")).lower()
        is_junction = "_" in name and not any(field in name for field in ["created_at", "updated_at"])
        if name and name not in referenced_tables and not is_junction:
            issues.append({
                "type": "orphan_table",
                "severity": "warning",
                "fixTarget": "architectStep3",
                "message": f"Table \"{table.get('name')}\" exists but no API endpoint references it. Either add endpoints or remove the table.",
            })

    errors = [issue for issue in issues if issue.get("severity") == "error"]
    force_proceed = bool(issues) and current_cycles >= max_cycles
    state.blueprintValidation = {
        "isValid": len(issues) == 0 or force_proceed,
        "issues": issues,
        "validationCycles": current_cycles + 1,
    }
    if len(issues) == 0 or force_proceed:
        state.currentPhase = "planner"
    if force_proceed:
        log(state, f"Blueprint repair retry limit reached ({max_cycles}); proceeding with warnings")
    log(state, f"Blueprint validator found {len(errors)} errors and {len(issues) - len(errors)} warnings")
    return state


def blueprintValidatorRouter(state: AgentState) -> str:
    validation = state.blueprintValidation
    if validation.get("isValid"):
        return "__end__"
    first_error = next((issue for issue in validation.get("issues", []) if issue.get("severity") == "error"), None)
    if first_error:
        return first_error.get("fixTarget", "architectStep3")
    target_counts: dict[str, int] = {}
    for issue in validation.get("issues", []):
        target = issue.get("fixTarget", "architectStep3")
        target_counts[target] = target_counts.get(target, 0) + 1
    return max(target_counts.items(), key=lambda item: item[1])[0] if target_counts else "__end__"
