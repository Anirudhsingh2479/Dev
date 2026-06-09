import asyncio
import time
from collections import defaultdict
from ..models.contracts import StreamEvent

_events: dict[str, list[StreamEvent]] = defaultdict(list)
_signals: dict[str, asyncio.Event] = defaultdict(asyncio.Event)


async def append_event(project_id: str, event: StreamEvent) -> None:
    _events[project_id].append(event)
    _signals[project_id].set()
    _signals[project_id] = asyncio.Event()


async def stream_events(project_id: str):
    cursor = 0
    started = time.time()
    while True:
        while cursor < len(_events[project_id]):
            event = _events[project_id][cursor]
            cursor += 1
            yield event
            if event.type in {"run.completed", "run.failed", "run.cancelled"}:
                return
        if time.time() - started > 300:
            return
        try:
            await asyncio.wait_for(_signals[project_id].wait(), timeout=15)
        except asyncio.TimeoutError:
            yield StreamEvent(type="heartbeat", node="event_bus", message="still running")
