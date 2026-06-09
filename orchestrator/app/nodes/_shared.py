from __future__ import annotations

import json
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from ..models.contracts import AgentState


def log(state: AgentState, message: str) -> None:
    state.terminalOutput.append(message)


def task_id(task: dict[str, Any] | None) -> str:
    if not task:
        return "task"
    return task.get("taskId") or task.get("id") or "task"


def retry_key(name: str, task: dict[str, Any] | None = None) -> str:
    return f"{name}:{task_id(task)}" if task else name


def retry_count(state: AgentState, name: str, task: dict[str, Any] | None = None) -> int:
    return int((state.retryCounts or {}).get(retry_key(name, task), 0) or 0)


def retry_limit(state: AgentState, name: str, default: int) -> int:
    return int((state.retryLimits or {}).get(name, default) or default)


def increment_retry(state: AgentState, name: str, task: dict[str, Any] | None = None) -> int:
    key = retry_key(name, task)
    state.retryCounts[key] = int((state.retryCounts or {}).get(key, 0) or 0) + 1
    return state.retryCounts[key]


def reset_retry(state: AgentState, name: str, task: dict[str, Any] | None = None) -> None:
    state.retryCounts.pop(retry_key(name, task), None)


def snake_case(name: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).replace("-", "_")
    return re.sub(r"_+", "_", value).strip("_").lower()


def kebab_plural(name: str) -> str:
    value = snake_case(name).replace("_", "-")
    return value if value.endswith("s") else f"{value}s"


def table_name(name: str) -> str:
    value = snake_case(name)
    if value.endswith("y"):
        return f"{value[:-1]}ies"
    return value if value.endswith("s") else f"{value}s"


def camel_case(name: str) -> str:
    parts = re.split(r"[_\-\s]+", snake_case(name))
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def clone(value: Any) -> Any:
    return deepcopy(value)


def now_ms() -> int:
    return int(time.time() * 1000)


def merge_file_registry(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path = {entry.get("path"): entry for entry in existing if entry.get("path")}
    for entry in incoming:
        path = entry.get("path")
        if path:
            by_path[path] = {**by_path.get(path, {}), **entry}
    return list(by_path.values())


def apply_token_delta(state: AgentState, agent_name: str, tokens: dict[str, Any] | None) -> None:
    tokens = tokens or {}
    input_tokens = int(tokens.get("input", 0) or 0)
    output_tokens = int(tokens.get("output", 0) or 0)
    cost = float(tokens.get("cost", 0) or 0)
    state.tokenUsage.calls.append({
        "agent": agent_name,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "cost": cost,
        "source": tokens.get("source", "estimate"),
        "inputCostPer1M": tokens.get("inputCostPer1M"),
        "outputCostPer1M": tokens.get("outputCostPer1M"),
        "timestamp": now_ms(),
    })
    state.tokenUsage.totalInput += input_tokens
    state.tokenUsage.totalOutput += output_tokens
    state.tokenUsage.estimatedCost += cost


def read_jsonish(value: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(value)
    except Exception:
        return fallback


def import_statement_for(path: str, exports: list[str] | None = None, default_export: str | None = None) -> str:
    exports = exports or []
    stem = Path(path).stem
    if default_export:
        return f"import {default_export} from './{stem}.js'"
    if exports:
        return f"import {{ {', '.join(exports)} }} from './{stem}.js'"
    return ""
