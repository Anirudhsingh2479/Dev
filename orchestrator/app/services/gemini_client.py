from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate


def _mock_agent_response(agent_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_name == "pmAgent":
        return {
            "appName": "Generated App",
            "features": ["Strict JSON contracts", "Layered workflow", "Sandbox snapshots"],
            "users": ["user", "admin"],
            "pages": ["Login", "Dashboard"],
            "entities": ["User", "Project", "Task"],
            "databaseRecommendation": "PostgreSQL",
            "source": "mock-langgraph-agent",
        }
    return {"source": "mock-langgraph-agent", "payload": payload}


def _repair_truncated_json(text: str) -> str:
    cleaned = text.strip()
    in_string = False
    escaped = False
    for char in cleaned:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
    if in_string:
        if cleaned.endswith("\\"):
            cleaned += "\\"
        cleaned += '"'

    stack: list[str] = []
    in_string = False
    escaped = False
    for char in cleaned:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in ("}", "]") and stack:
            stack.pop()
    while stack:
        cleaned += stack.pop()
    return cleaned


def _extract_json(raw_text: str) -> Any:
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json|JSON|js)?\s*\n?", "", clean)
        clean = re.sub(r"\n?\s*```\s*$", "", clean)

    starts = [idx for idx in [clean.find("{"), clean.find("[")] if idx != -1]
    if starts:
        clean = clean[min(starts):]
    end_idx = max(clean.rfind("}"), clean.rfind("]"))
    if end_idx != -1 and end_idx < len(clean) - 1:
        clean = clean[:end_idx + 1]

    try:
        return json.loads(clean)
    except Exception:
        repaired = _repair_truncated_json(clean)
        try:
            return json.loads(repaired)
        except Exception:
            if '"files"' in clean:
                match = re.search(r'"files"\s*:\s*\[', clean)
                if match:
                    array_start = clean.find("[", match.start())
                    depth = 0
                    last_complete = array_start
                    for index, char in enumerate(clean[array_start:], start=array_start):
                        if char == "{":
                            depth += 1
                        elif char == "}":
                            depth -= 1
                            if depth == 0:
                                last_complete = index + 1
                    partial_files = clean[array_start:last_complete]
                    return json.loads(f'{{"files": {partial_files}], "notes": "Response was truncated - partial files extracted"}}')
            raise


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                chunks.append(str(item.get("text") or ""))
        return "".join(chunks)
    return str(content or "")


def _usage_value(metadata: dict[str, Any], *names: str) -> int:
    for name in names:
        value = metadata.get(name)
        if value is not None:
            return int(value or 0)
    return 0


def _token_counts(full_prompt: str, raw_text: str, response: Any | None = None) -> dict[str, Any]:
    usage = getattr(response, "usage_metadata", None) or {}
    response_metadata = getattr(response, "response_metadata", None) or {}
    if not usage:
        usage = response_metadata.get("usage_metadata") or response_metadata.get("token_usage") or {}

    input_tokens = _usage_value(usage, "input_tokens", "prompt_token_count", "prompt_tokens")
    output_tokens = _usage_value(usage, "output_tokens", "candidates_token_count", "completion_tokens")

    if not input_tokens:
        input_tokens = max(1, len(full_prompt) // 4)
    if not output_tokens:
        output_tokens = max(1, len(raw_text) // 4)

    input_price = float(os.getenv("GEMINI_INPUT_COST_PER_1M", "0.30"))
    output_price = float(os.getenv("GEMINI_OUTPUT_COST_PER_1M", "2.50"))
    cost = (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price
    return {
        "input": input_tokens,
        "output": output_tokens,
        "cost": cost,
        "source": "provider" if usage else "estimate",
        "inputCostPer1M": input_price,
        "outputCostPer1M": output_price,
    }


async def call_json_agent(
    *,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    current_cost: float = 0,
    token_budget: float = 2.0,
    model: str | None = None,
) -> dict[str, Any]:
    if current_cost >= token_budget:
        raise RuntimeError(f"TOKEN_BUDGET_EXCEEDED: ${current_cost:.4f} >= budget ${token_budget}")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        parsed = _mock_agent_response(agent_name, {"prompt": user_prompt})
        return {"parsed": parsed, "raw": json.dumps(parsed), "tokens": _token_counts(system_prompt + user_prompt, json.dumps(parsed))}

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        parsed = _mock_agent_response(agent_name, {"prompt": user_prompt, "warning": "Install langchain-google-genai for live Gemini calls."})
        return {"parsed": parsed, "raw": json.dumps(parsed), "tokens": _token_counts(system_prompt + user_prompt, json.dumps(parsed))}

    full_prompt = (
        f"{system_prompt}\n\n---\n\nINPUT:\n{user_prompt}\n\n---\n\n"
        "IMPORTANT: Respond with ONLY valid JSON. No markdown, no backticks, no explanation outside JSON."
    )
    prompt = ChatPromptTemplate.from_messages([("human", "{prompt}")])
    llm = ChatGoogleGenerativeAI(
        model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        temperature=0.2,
        max_output_tokens=65536,
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = await llm.ainvoke(prompt.format_messages(prompt=full_prompt))
            raw = _text_from_content(response.content)
            parsed = _extract_json(raw or "")
            return {"parsed": parsed, "raw": raw or "", "tokens": _token_counts(full_prompt, raw or "", response)}
        except Exception as error:
            last_error = error
            if attempt == 3:
                raise RuntimeError(f"JSON_PARSE_FAILED after 3 attempts: {error}") from error
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(str(last_error))


async def safe_call_json_agent(**options: Any) -> dict[str, Any]:
    try:
        result = await call_json_agent(**options)
        return {"ok": True, **result}
    except Exception as error:
        if "TOKEN_BUDGET_EXCEEDED" in str(error):
            raise
        return {"ok": False, "error": str(error), "parsed": None, "raw": "", "tokens": {"input": 0, "output": 0, "cost": 0}}


async def invoke_json_agent(agent_name: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = await call_json_agent(agent_name=agent_name, system_prompt=system_prompt, user_prompt=json.dumps(payload, indent=2))
    return result["parsed"]
