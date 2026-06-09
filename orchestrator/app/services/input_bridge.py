from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from ..models.contracts import StreamEvent
from .event_bus import append_event

_pending: dict[tuple[str, str], asyncio.Future[dict[str, Any]]] = {}
_history: dict[str, list[dict[str, Any]]] = defaultdict(list)


async def wait_for_input(project_id: str, input_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    key = (project_id, input_type)
    loop = asyncio.get_running_loop()
    future: asyncio.Future[dict[str, Any]] = loop.create_future()
    _pending[key] = future
    request = {"type": input_type, "payload": payload}
    _history[project_id].append({"direction": "request", **request})
    await append_event(
        project_id,
        StreamEvent(
            type="input.requested",
            node=input_type,
            message=f"Waiting for {input_type} response",
            state=request,
        ),
    )
    try:
        response = await future
        _history[project_id].append({"direction": "response", "type": input_type, "payload": response})
        return response
    finally:
        _pending.pop(key, None)


async def submit_input(project_id: str, input_type: str, response: dict[str, Any]) -> dict[str, Any]:
    key = (project_id, input_type)
    future = _pending.get(key)
    if not future or future.done():
        return {"accepted": False, "message": "No matching pending input request"}
    future.set_result(response)
    await append_event(
        project_id,
        StreamEvent(
            type="input.received",
            node=input_type,
            message=f"Received {input_type} response",
            state={"type": input_type},
        ),
    )
    return {"accepted": True}


def get_input_history(project_id: str) -> list[dict[str, Any]]:
    return list(_history.get(project_id, []))
