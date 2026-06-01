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
cp .env.example .env
GEMINI_API_KEY=AQ.Ab8RN6IyaVfFXRVd2OOHUNnL2lPTtFcncDXGpYHQWc2UX_T_sA
GEMINI_MODEL=gemini-2.5-flash
GEMINI_INPUT_COST_PER_1M=0.30
GEMINI_OUTPUT_COST_PER_1M=2.50

FRONTEND_PORT=5173
GATEWAY_PORT=3000
ORCHESTRATOR_PORT=8000

FRONTEND_URL=http://localhost:5173
GATEWAY_URL=http://localhost:3000
ORCHESTRATOR_URL=http://localhost:8000

DATABASE_URL=postgresql://aidev:aidev@postgres:5432/aidev
MONGO_URI=mongodb+srv://anirudhdixitsjknp_db_user:anirudh_2004@cluster0.lsdtwwj.mongodb.net/?appName=Cluster0
JWT_SECRET_KEY=dev-secret-change-in-production
REDIS_URL=redis://redis:6379/0
SANDBOX_ROOT=/workspace/sandboxes
HOST_SANDBOX_ROOT=/Users/anirudhdixit/Downloads/Lecture26 (1)/AIDevFinalThreeLayer/sandbox
TOKEN_BUDGET_USD=2.0
SANDBOX_FRONTEND_HOST_PORT=15173
SANDBOX_BACKEND_HOST_PORT=15000
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_SECURE=false
MAIL_USER=anirudhdixit0808@gmail.com
MAIL_PASS=zaeo sgiq lwwm vuxz

```

Then open:

- Frontend: http://localhost:5173
- Gateway API: http://localhost:3000/api/health
- Python orchestrator: http://localhost:8000/health

## Local Development

Run each layer separately:

```bash
cd orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd gateway
npm install
npm run dev
```

```bash
cd frontend
npm install
npm run dev
```

## JSON Flow

```text
React dashboard
  POST /api/login JSON
  GET /api/health JSON
  GET /api/projects JSON
  POST /api/projects JSON
  GET /api/projects/:projectId/events SSE with JSON data events
Node Express gateway
  stores user/project metadata in PostgreSQL
  POST /runs JSON
  GET /runs/:projectId/events SSE with JSON data events
Python FastAPI orchestrator
  LangGraph nodes with JS-compatible Pydantic state names
  Redis checkpoint after every node
  Git snapshot metadata after code steps
  Docker sandbox command contract
```

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
