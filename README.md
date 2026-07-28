# AI Dev Team Three Layer

Three-layer rewrite of `AIDevFinal`.

This version maps the original JavaScript LangGraph project into the requested
3-layer model. The graph node names, main state fields, and routing shape match
the JS project: `pmAgent`, `architectStep1` through `architectStep5`,
`blueprintValidator`, `plannerAgent`, sandbox setup/health, the dev loop,
review/execution/debug routing, phase verification, deployment verification,
and `presentToUser`.

## Architecture

1. `frontend/` - React + Vite dashboard for requirements, file tree, terminal stream, and token/cost UI.
2. `gateway/` - Node.js + Express API gateway for login, project metadata, SSE/WebSocket streaming, and JSON relay to Python.
3. `orchestrator/` - Python + FastAPI + LangGraph AI engine using Pydantic v2, Gemini, Redis checkpointing, Docker sandbox metadata, and Git snapshots.

All layer-to-layer messages are JSON. The frontend never talks directly to the Python AI service.

## Quick Start

```bash


### Layer Contracts

- Frontend -> Gateway uses JSON HTTP requests only.
- Gateway -> Orchestrator uses JSON HTTP requests only.
- Streaming uses SSE/WebSocket frames whose payload is the same JSON event shape:
  `{ type, node, message, state }`.
- Public API payloads use snake_case fields such as `user_id`, `project_id`, and
  `token_budget_usd`.
- Agent state inside stream events keeps JS-compatible field names such as
  `projectId`, `userRequirement`, `fileTree`, and `tokenUsage`.

## Project Data

The gateway is prepared for PostgreSQL project/user metadata through `DATABASE_URL`.
Redis is used by the orchestrator for node checkpoints and SSE event replay.

## Gateway API

- `GET /api/health` checks the gateway and Python orchestrator.
- `POST /api/login` creates or updates lightweight user metadata.
- `GET /api/projects?user_id=demo-user` lists project metadata.
- `POST /api/projects` starts a new FastAPI/LangGraph run using JSON.
- `GET /api/projects/:projectId` returns stored project metadata.
- `GET /api/projects/:projectId/events` relays orchestrator SSE events.
- `WS /ws/projects/:projectId/events` relays the same event stream over WebSocket.
