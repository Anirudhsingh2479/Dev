from __future__ import annotations

import asyncio


_running_tasks: dict[str, asyncio.Task] = {}


def register_run(project_id: str, task: asyncio.Task) -> None:
    _running_tasks[project_id] = task


def unregister_run(project_id: str) -> None:
    _running_tasks.pop(project_id, None)


def cancel_run(project_id: str) -> bool:
    task = _running_tasks.get(project_id)
    if not task or task.done():
        return False
    task.cancel()
    return True


def is_running(project_id: str) -> bool:
    task = _running_tasks.get(project_id)
    return bool(task and not task.done())
