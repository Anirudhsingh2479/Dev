import asyncio
import json
import uuid
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .models.contracts import HumanInputSubmitRequest, RunCreateRequest, RunCreateResponse, StreamEvent
from .graph.workflow import run_workflow
from .services.event_bus import append_event, stream_events
from .services.input_bridge import get_input_history, submit_input
from .services.run_manager import cancel_run, register_run, unregister_run
from .services.sandbox import restart_sandbox_preview, stop_sandbox_containers

app = FastAPI(title="AI Dev Team Orchestrator", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "layer": "python-fastapi-langgraph-orchestrator"}


@app.post("/runs", response_model=RunCreateResponse)
async def create_run(payload: RunCreateRequest) -> RunCreateResponse:
    project_id = f"project-{uuid.uuid4().hex[:12]}"
    await append_event(project_id, StreamEvent(type="run.created", node="api", message="Run accepted by orchestrator"))
    task = asyncio.create_task(run_workflow(project_id, payload))
    register_run(project_id, task)
    task.add_done_callback(lambda _task: unregister_run(project_id))
    return RunCreateResponse(project_id=project_id, status="running")


@app.get("/runs/{project_id}/events")
async def events(project_id: str) -> StreamingResponse:
    async def generate():
      async for event in stream_events(project_id):
          yield f"data: {json.dumps(event.model_dump())}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/runs/{project_id}/cancel")
async def cancel(project_id: str) -> dict:
    cancelled = cancel_run(project_id)
    sandbox_cleanup = stop_sandbox_containers(project_id)
    if not cancelled:
        await append_event(project_id, StreamEvent(type="run.cancelled", node="api", message="No active workflow task found"))
    return {"cancelled": cancelled, "sandbox_cleanup": sandbox_cleanup}


@app.post("/runs/{project_id}/preview/stop")
async def stop_preview(project_id: str, payload: dict | None = None) -> dict:
    sandbox_id = (payload or {}).get("sandbox_id") or project_id
    return stop_sandbox_containers(sandbox_id)


@app.post("/runs/{project_id}/preview/restart")
async def restart_preview(project_id: str, payload: dict | None = None) -> dict:
    data = payload or {}
    sandbox_id = data.get("sandbox_id") or project_id
    return restart_sandbox_preview(
        project_id,
        sandbox_id,
        data.get("user_id") or "demo-user",
        data.get("backend_port"),
        data.get("frontend_port"),
    )


@app.post("/runs/{project_id}/input")
async def input_response(project_id: str, payload: HumanInputSubmitRequest) -> dict:
    response = payload.model_dump(exclude_none=True)
    if payload.data:
        response.update(payload.data)
    return await submit_input(project_id, payload.type, response)


@app.get("/runs/{project_id}/input")
async def input_history(project_id: str) -> dict:
    return {"inputs": get_input_history(project_id)}
