# AI Dev Team Three Layer

AI Dev Team Three Layer is a full-stack AI software-development platform. A user enters a product requirement in the React dashboard, the Node.js gateway creates and tracks the project run, and the Python LangGraph orchestrator plans, codes, reviews, tests, debugs, previews, and packages the generated application inside an isolated sandbox.

This repository is a three-layer rewrite of `AIDevFinal`. It keeps the original LangGraph workflow shape and node names, including `pmAgent`, `architectStep1` through `architectStep5`, `blueprintValidator`, `plannerAgent`, sandbox setup and health checks, the developer loop, reviewer, executor, debugger, phase verification, deployment verification, and `presentToUser`.

This README is intentionally self-contained for GitHub. The full contents of the local `study/` markdown files and every Mermaid `.mmd` diagram have been copied into this file, so the repository can still explain itself even if the `study/` folder is not pushed.

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Three-Layer Architecture](#three-layer-architecture)
- [Repository Structure](#repository-structure)
- [End-to-End Runtime Flow](#end-to-end-runtime-flow)
- [Core Workflow Nodes](#core-workflow-nodes)
- [Data and Storage](#data-and-storage)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [API Contracts](#api-contracts)
- [Testing](#testing)
- [Complete Inline Study Notes](#complete-inline-study-notes)
- [Complete Inline Mermaid Diagram Appendix](#complete-inline-mermaid-diagram-appendix)

## What This Project Does

The platform turns a natural-language software idea into a generated application. It collects requirements, clarifies missing information, designs an architecture, creates a task plan, writes code, runs commands in a sandbox, reviews failures, applies fixes, verifies phases, and streams progress back to the browser.

The important idea is separation of responsibility:

- The frontend owns the user experience, project screen, file tree, terminal stream, preview actions, and token/cost display.
- The gateway owns authentication, project metadata, API boundaries, SSE/WebSocket relay, download packaging, and communication with the orchestrator.
- The orchestrator owns AI reasoning, LangGraph state transitions, Gemini calls, sandbox lifecycle, code generation, review, execution, debugging, snapshots, and final handoff.

## Three-Layer Architecture

1. `frontend/` is a React + Vite dashboard for authentication, requirements, project status, generated files, terminal output, previews, downloads, and user input prompts.
2. `gateway/` is a Node.js + Express API gateway for login, OTP mail, user/project metadata, PostgreSQL/MongoDB access, orchestrator JSON relay, SSE/WebSocket event streaming, and generated project ZIP creation.
3. `orchestrator/` is a Python + FastAPI + LangGraph AI engine using Pydantic v2 contracts, Gemini, Redis checkpointing, Docker sandbox metadata, sandbox runtime services, and Git snapshots.

All layer-to-layer messages are JSON. The frontend does not call the Python AI service directly. The gateway is the public backend boundary, and the orchestrator remains an internal AI/workflow service.

```mermaid
flowchart LR
  User[User] --> Frontend[React + Vite Dashboard]
  Frontend --> Gateway[Node.js + Express Gateway]
  Gateway --> Orchestrator[Python FastAPI + LangGraph Orchestrator]
  Gateway --> Mongo[(MongoDB Auth + OTP)]
  Gateway --> Postgres[(Postgres Project Metadata)]
  Gateway --> Redis[(Redis Token Blocklist)]
  Orchestrator --> RedisCheckpoints[(Redis Checkpoints)]
  Orchestrator --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated React + Express App]
```

## Repository Structure

```text
AIDevFinalThreeLayer/
  frontend/                  React + Vite client
  gateway/                   Node.js + Express API gateway
  orchestrator/              FastAPI + LangGraph AI engine
  infra/                     Database schema and infrastructure files
  sandbox/                   Host-mounted generated app workspaces
  tests/                     Orchestrator and gateway tests
  docs/                      Additional PDF/Markdown architecture documents
  docker-compose.yml         Local multi-service runtime
  docker-compose.aws.yml     AWS-oriented compose configuration
  README.md                  Self-contained GitHub project README
```

## End-to-End Runtime Flow

```text
React dashboard
  POST /api/login
  GET /api/health
  GET /api/projects
  POST /api/projects
  GET /api/projects/:projectId/events
  WS  /ws/projects/:projectId/events

Node Express gateway
  stores user and project metadata
  validates public API input
  starts orchestrator runs with JSON
  relays orchestrator events to the browser
  packages generated app files for download

Python FastAPI orchestrator
  executes LangGraph workflow nodes
  checkpoints state in Redis
  manages sandbox metadata and runtime commands
  generates, reviews, executes, debugs, and verifies code
  streams JSON events back through the gateway
```

## Core Workflow Nodes

The orchestrator graph follows the original JavaScript-compatible naming model while using Python services and Pydantic contracts.

- `pmAgent` clarifies the user requirement and prepares product intent.
- `architectStep1` to `architectStep5` produce architecture, data model, API plan, UI plan, and implementation blueprint.
- `blueprintValidator` validates architecture consistency before coding.
- `plannerAgent` turns the blueprint into phases and implementation tasks.
- `setupSandbox` and `sandboxHealthCheck` prepare the isolated project workspace.
- `selectNextTask`, `coderAgent`, `reviewerAgent`, `executorAgent`, and `debuggerAgent` form the main code-build-fix loop.
- `phaseVerification` checks phase completion before moving on.
- `deploymentVerifier` checks the generated app can be presented and previewed.
- `snapshotManager`, `updateRegistry`, `stateCompactor`, and `presentToUser` preserve useful state and prepare the final result.
- `humanInput`, `humanEscalation`, and `simplifyTask` handle cases where the graph needs user input or must reduce task complexity.

## Data and Storage

The project uses different stores for different kinds of data:

- PostgreSQL stores platform user/project metadata for the gateway.
- MongoDB supports OTP/auth-related user data where configured.
- Redis stores orchestrator checkpoints and event replay state.
- The host `sandbox/` directory stores generated project workspaces.
- Git snapshots preserve generated code state after important workflow steps.
- Optional generated application databases can be configured through `PROJECT_DB_URI`.

## Quick Start

### Docker Compose

```bash
cp .env.example .env
# Edit .env and replace all placeholder values before starting services.
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Gateway health: `http://localhost:3000/api/health`
- Orchestrator health: `http://localhost:8000/health`

### Important Before GitHub Push

Do not commit real API keys, database URLs, mail passwords, private keys, or generated `.env` files. Keep `.env` ignored, and make sure `.env.example` contains placeholders only.

## Environment Variables

Use placeholder values like this in committed examples:

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_INPUT_COST_PER_1M=0.30
GEMINI_OUTPUT_COST_PER_1M=2.50

FRONTEND_PORT=5173
GATEWAY_PORT=3000
ORCHESTRATOR_PORT=8000

FRONTEND_URL=http://localhost:5173
GATEWAY_URL=http://localhost:3000
VITE_GATEWAY_URL=http://localhost:3000
ORCHESTRATOR_URL=http://orchestrator:8000

PUBLIC_PROTOCOL=http
PUBLIC_HOST=localhost
PREVIEW_PUBLIC_PROTOCOL=http
PREVIEW_PUBLIC_HOST=localhost

DATABASE_URL=postgresql://aidev:aidev@postgres:5432/aidev
POSTGRES_USER=aidev
POSTGRES_PASSWORD=aidev
POSTGRES_DB=aidev
POSTGRES_PORT=5432
PROJECT_DB_URI=postgresql://project_user:project_password@project-host.example.com:5432/postgres?sslmode=require
MONGO_URI=your_mongodb_connection_string
JWT_SECRET_KEY=change_this_secret
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

SANDBOX_ROOT=/workspace/sandboxes
HOST_SANDBOX_ROOT=/absolute/path/to/AIDevFinalThreeLayer/sandbox
SANDBOX_FRONTEND_HOST_PORT=15173
SANDBOX_BACKEND_HOST_PORT=15000
SANDBOX_PREVIEW_BIND_HOST=127.0.0.1
SANDBOX_PREVIEW_TTL_SECONDS=300

TOKEN_BUDGET_USD=2.0
REQUIRE_DOCKER=true
DOCKER_RUN_TIMEOUT_MS=300000
NPM_INSTALL_TIMEOUT_MS=300000

MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_SECURE=false
MAIL_USER=your_email@example.com
MAIL_PASS=your_mail_app_password
```

## Local Development

Run each layer separately when you do not want the full Docker Compose stack.

### Orchestrator

```bash
cd orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Gateway

```bash
cd gateway
npm install
npm run dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Contracts

Public gateway endpoints:

- `GET /api/health` checks the gateway and Python orchestrator.
- `POST /api/login` creates or updates lightweight user metadata.
- `GET /api/projects?user_id=demo-user` lists project metadata.
- `POST /api/projects` starts a new FastAPI/LangGraph run using JSON.
- `GET /api/projects/:projectId` returns stored project metadata.
- `GET /api/projects/:projectId/events` relays orchestrator SSE events.
- `WS /ws/projects/:projectId/events` relays the same event stream over WebSocket.

Layer contracts:

- Frontend to gateway uses JSON HTTP requests and browser event streams.
- Gateway to orchestrator uses JSON HTTP requests.
- Streaming uses SSE/WebSocket frames whose payload follows the shared event shape: `{ type, node, message, state }`.
- Public API payloads use snake_case fields such as `user_id`, `project_id`, and `token_budget_usd`.
- Agent state inside stream events keeps JavaScript-compatible field names such as `projectId`, `userRequirement`, `fileTree`, and `tokenUsage`.

## Testing

```bash
npm run test:orchestrator
npm run test:gateway
npm run test:all:mock
```

The orchestrator test command is designed for the Docker container because that environment already has Python, Pydantic, LangGraph, and orchestrator dependencies installed. If Python dependencies are installed locally, you can also run:

```bash
npm run test:orchestrator:local
```

Test coverage includes the graph skeleton, blueprint validation, retry limits, task selection, phase verification, and generated-code ZIP filtering.

## Complete Inline Study Notes

Everything below was copied from the local `study/` folder. File links that would break without `study/` were converted to plain text references.

| Original Study File | Included Section |
| --- | --- |
| `01_three_layer_architecture.md` | [Question 1: Why Did We Use Three-Layer Architecture?](#inline-01-three-layer-architecture) |
| `02_project_architecture.md` | [Question 2: Explain The Project Architecture In Detail](#inline-02-project-architecture) |
| `03_high_level_project_overview.md` | [Question 3: High-Level Project Overview For Beginners](#inline-03-high-level-project-overview) |
| `04_workflow_nodes_deep_dive.md` | [Question 4: What Does Each Workflow Node Do, Why Was It Added, And What Happens If It Is Removed?](#inline-04-workflow-nodes-deep-dive) |
| `05_project_call_flow_and_sandbox_lifecycle.md` | [Question 5: How Does Each Part Call The Other, And How Is The Sandbox/Docker Lifecycle Managed?](#inline-05-project-call-flow-and-sandbox-lifecycle) |
| `06_solid_hld_lld_models_erd_uml.md` | [Question 6: SOLID Principles, HLD, LLD, Models, ER Diagrams, And UML Diagrams](#inline-06-solid-hld-lld-models-erd-uml) |
| `07_gateway_deep_dive.md` | [Question 7: Gateway Deep Dive, File By File](#inline-07-gateway-deep-dive) |
| `08_orchestrator_deep_dive.md` | [Question 8: Orchestrator Deep Dive, File By File](#inline-08-orchestrator-deep-dive) |
| `09_frontend_deep_dive.md` | [Question 9: Frontend Deep Dive, File By File](#inline-09-frontend-deep-dive) |
| `10_generated_app_and_sandbox_output.md` | [Question 10: Generated App And Sandbox Output](#inline-10-generated-app-and-sandbox-output) |
| `11_interview_master_qa.md` | [Question 11: Interview Master Q&A](#inline-11-interview-master-qa) |
| `12_security_and_production_hardening.md` | [Question 12: Security And Production Hardening](#inline-12-security-and-production-hardening) |
| `13_failure_scenarios_and_debugging.md` | [Failure Scenarios and Debugging Guide](#inline-13-failure-scenarios-and-debugging) |
| `14_database_and_storage_deep_dive.md` | [Database and Storage Deep Dive](#inline-14-database-and-storage-deep-dive) |
| `15_demo_script.md` | [Demo Script](#inline-15-demo-script) |
| `16_one_page_cheatsheet.md` | [One Page Cheatsheet](#inline-16-one-page-cheatsheet) |
| `README.md` | [Original Study README / Index](#inline-readme) |

<details id="inline-01-three-layer-architecture">
<summary>01_three_layer_architecture.md - Question 1: Why Did We Use Three-Layer Architecture?</summary>

### Question 1: Why Did We Use Three-Layer Architecture?

#### Short Answer

We used a three-layer architecture because this project has three very different types of work:

1. The frontend handles the user experience.
2. The gateway handles product/backend concerns such as login, sessions, project ownership, project history, event relay, cancel, preview, and download APIs.
3. The orchestrator handles the agentic workflow: LangGraph, Gemini calls, state transitions, Docker sandboxing, code generation, review, execution, debugging, and deployment verification.

Technically, React could call FastAPI directly. Python could act as both the user-facing backend and the AI orchestrator. But in this project, that would mix normal web-app responsibilities with long-running agent runtime responsibilities. The gateway keeps that boundary clean.

The most interview-friendly line is:

> We used three layers so the browser talks only to a secure application gateway, while the Python service stays focused on long-running AI orchestration. The gateway owns authentication, project ownership, metadata, streaming relay, and preview controls; the orchestrator owns LangGraph, agents, checkpoints, and Docker sandbox execution.

#### Best Logical Interview Reason

The strongest reason is this:

> We separated the gateway from the orchestrator because user-facing requests and agentic execution have very different failure modes, security needs, and scaling behavior.

That is the key interview logic.

A normal backend request is usually short-lived:

- user logs in
- user creates a project
- user lists past projects
- user downloads a zip
- user opens or stops a preview

These are product/API operations. They need authentication, authorization, cookies, user ownership checks, database records, and stable responses.

But an agentic orchestrator run is long-lived and risky:

- it may run for minutes
- it calls an LLM many times
- it stores intermediate state
- it asks for human input
- it writes files
- it runs shell commands inside a sandbox
- it starts containers
- it may fail, retry, debug, or pause

Those two worlds should not be tightly coupled.

If the same FastAPI service handled both login/product APIs and the entire AI build workflow, then one long-running or failing agent run could affect the public dashboard backend. Also, the public backend would become much harder to secure because it would expose endpoints close to sandbox execution, preview control, and workflow cancellation.

So the gateway acts like a controlled door:

```mermaid
flowchart LR
  Browser[Browser / React UI] --> Gateway[Gateway: auth, ownership, product API]
  Gateway --> Orchestrator[Orchestrator: internal AI runtime]
  Orchestrator --> Sandbox[Sandbox: generated code and containers]
```

This means the browser does not directly talk to the service that runs the AI agents and sandbox. The browser only talks to the gateway, and the gateway decides what is allowed.

In interview words:

> We did not split the layers just for style. We split them because the frontend needs a stable product API, while the orchestrator is a long-running internal execution engine. Keeping a gateway in between protects the orchestrator, centralizes auth and project ownership, and lets the AI workflow evolve independently from the dashboard.

#### Simple Interview Answer You Can Say

If someone asks, "Why not directly call FastAPI from React?", you can say:

> We could have done that for a small prototype, but our FastAPI service is not just a CRUD backend. It runs the agentic workflow: LangGraph nodes, LLM calls, Redis checkpoints, Docker sandbox execution, debugging, and preview management. Exposing that directly to the browser would mix public API concerns with internal execution concerns. So we added a Node gateway as the public backend. It handles auth, sessions, project ownership, project history, event relay, cancel, preview, and download. FastAPI stays focused on orchestration. That gives us better security, cleaner separation, easier debugging, and independent scaling.

#### Even Shorter Answer

> Direct React to FastAPI would reduce one service, but it would make FastAPI responsible for everything: authentication, project metadata, streaming, permissions, orchestration, LLM calls, sandboxing, and Docker preview control. We used the gateway so the public web backend and the private AI runtime remain separate.

#### My Recommendation For This Project

For this project, I would keep the three-layer architecture.

If this were a very small demo where the user enters a prompt and FastAPI returns one response, then direct React to FastAPI would be fine. In that case, adding a separate gateway might be unnecessary complexity.

But this project is not that simple. It is closer to a platform:

- users log in
- users create projects
- projects run for a long time
- progress streams back live
- the system may ask for human input
- generated files are written into a sandbox
- commands run inside Docker
- preview containers are started and stopped
- completed projects can be downloaded
- project history must be stored

Because of that, I would not expose the orchestrator directly to the frontend.

The better design is:

```mermaid
flowchart LR
  React[React UI] --> Gateway[Gateway / Public Backend]
  Gateway --> FastAPI[FastAPI / Internal Orchestrator]
```

The gateway is the public product backend. The FastAPI service is the internal AI engine.

That distinction is valuable.

My personal view:

> Direct React to FastAPI would look simpler in the beginning, but the three-layer architecture is better for this project because it keeps the dangerous, long-running, tool-executing AI workflow behind a controlled backend layer.

So I would not choose direct frontend to FastAPI here unless the goal was only a quick proof of concept.

For an interview, you can say:

> I considered direct React to FastAPI, but I decided the gateway was worth it because our FastAPI service is not a simple API server. It is an execution engine that manages agents, LLM calls, Docker sandboxes, checkpoints, and generated app previews. Keeping it behind a gateway gives us a cleaner security boundary, centralized auth, better project ownership handling, and more flexibility to scale or change the orchestrator later.

#### The Core Engineering Principle

The decision is based on separation by responsibility, not separation by programming language.

The question is not:

> Can Python do both?

Yes, Python can do both.

The better question is:

> Should the same service own both public user traffic and long-running AI execution?

For this project, the answer is no.

Why?

- Public user traffic needs predictable, secure, fast API responses.
- Agentic execution needs long-running stateful processing, retries, tool execution, and sandbox control.
- Combining them increases blast radius: if orchestration breaks, the dashboard backend is affected too.
- Splitting them gives clearer ownership: gateway owns users/projects; orchestrator owns agents/sandbox.

That is the real architecture reason.

#### Current Architecture

```mermaid
flowchart LR
  User[User] --> Frontend[React + Vite Dashboard]
  Frontend --> Gateway[Node.js + Express Gateway]
  Gateway --> Orchestrator[Python FastAPI + LangGraph Orchestrator]
  Gateway --> Mongo[(MongoDB Auth + OTP)]
  Gateway --> Postgres[(Postgres Project Metadata)]
  Gateway --> Redis[(Redis Token Blocklist)]
  Orchestrator --> RedisCheckpoints[(Redis Checkpoints)]
  Orchestrator --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated React + Express App]
```

In the actual codebase:

- Frontend starts project runs, displays event streams, submits human answers, cancels runs, restarts previews, and downloads generated code.
- Gateway protects `/api/projects` routes, checks the logged-in user, stores project metadata, forwards commands to FastAPI, and relays event streams.
- Orchestrator exposes `/runs`, `/runs/{project_id}/events`, `/runs/{project_id}/input`, `/runs/{project_id}/cancel`, and preview endpoints, but it does not own full dashboard authentication.

#### Why Not Direct React To FastAPI?

Direct React to FastAPI would look simpler:

```mermaid
flowchart LR
  User[User] --> Frontend[React Dashboard]
  Frontend --> FastAPI[FastAPI Backend + Orchestrator]
  FastAPI --> AuthDB[(Auth DB)]
  FastAPI --> ProjectDB[(Project DB)]
  FastAPI --> Redis[(Redis)]
  FastAPI --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated App]
```

This is possible. But then FastAPI must become two things at once:

1. A normal application backend.
2. A long-running AI workflow engine.

That means FastAPI would need to handle:

- Signup, login, OTP, password hashing, cookies, JWT verification, logout, and Redis token blocklisting.
- User/project ownership checks.
- Project listing and project history.
- One-active-build-per-user policy.
- Cancel and preview permissions.
- Event stream relay and metadata updates.
- Downloading generated code safely.
- LangGraph node execution.
- Gemini JSON calls and token/cost tracking.
- Human-in-the-loop waiting.
- Redis checkpoints.
- Docker sandbox lifecycle.
- Generated app preview containers.

That is a lot of unrelated responsibility in one service. It would work for a small prototype, but it becomes harder to explain, test, secure, and scale.

#### The Main Reason: Separation Of Concerns

The gateway exists because browser-facing product logic and AI orchestration logic are different.

```mermaid
flowchart TB
  subgraph Frontend["Layer 1: Frontend"]
    F1[Forms and buttons]
    F2[Pipeline UI]
    F3[Terminal stream]
    F4[Human input panel]
  end

  subgraph Gateway["Layer 2: Gateway"]
    G1[Auth and cookies]
    G2[Project ownership]
    G3[Project metadata]
    G4[SSE and WebSocket relay]
    G5[Cancel, preview, download APIs]
  end

  subgraph Orchestrator["Layer 3: Orchestrator"]
    O1[LangGraph workflow]
    O2[AgentState]
    O3[Gemini calls]
    O4[Docker sandbox]
    O5[Review, execute, debug loop]
  end

  Frontend --> Gateway
  Gateway --> Orchestrator
```

The frontend should not know about internal agent implementation. It should only know that it can start a project, listen for events, answer questions, cancel, preview, and download.

The gateway should not generate code. It should decide whether the user is allowed to perform an action, store project state, and pass valid commands to the orchestrator.

The orchestrator should not become a dashboard-auth backend. It should focus on the complex agent runtime.

#### Reason 1: Security Boundary

The orchestrator has powerful capabilities. It can:

- Start long-running workflows.
- Call Gemini.
- Write generated source files.
- Run commands in a sandbox.
- Start and stop Docker containers.
- Initialize databases.
- Generate deployment files.

If React talked directly to FastAPI, then the browser would be closer to this powerful internal service. FastAPI would need strict authentication and authorization on every endpoint.

In the current architecture, the browser talks to the gateway first. The gateway checks the user session before forwarding project commands. This gives us a cleaner security boundary:

```mermaid
sequenceDiagram
  participant Browser as React Browser
  participant Gateway as Node Gateway
  participant Orchestrator as FastAPI Orchestrator

  Browser->>Gateway: POST /api/projects with cookie
  Gateway->>Gateway: Verify JWT cookie and user
  Gateway->>Gateway: Check active project policy
  Gateway->>Orchestrator: POST /runs with JSON
  Orchestrator-->>Gateway: project_id and running status
  Gateway-->>Browser: Project created
```

This is safer because React does not directly reach the AI runtime. The gateway is the public-facing gate.

#### Reason 2: Authentication Already Belongs In The Gateway

This project has dashboard auth implemented in the Node gateway:

- MongoDB stores dashboard users and OTP records.
- JWT cookies hold the login session.
- Redis stores logged-out token blocklist entries.
- Nodemailer sends OTP and welcome emails.

If React talked directly to FastAPI, we would have three choices, all with tradeoffs:

1. Rewrite all auth in Python/FastAPI.
2. Keep auth in Node but still let React call FastAPI, which creates split security rules.
3. Duplicate auth checks in both Node and Python.

The current design avoids that. The frontend calls only the gateway. The gateway is the identity layer. The orchestrator receives trusted internal requests from the gateway.

#### Reason 3: Project Ownership And Metadata

The dashboard is not just a live terminal. It has project history:

- `project_id`
- `user_id`
- requirement
- status
- last event type
- last event node
- last message
- last state JSON
- sandbox id
- preview ports and URLs
- preview running flag

That is product state, not agent state.

The orchestrator state is about the build workflow. The gateway state is about the user's dashboard experience. Keeping these separate is useful:

- The orchestrator can focus on producing state events.
- The gateway can persist the latest useful state for the dashboard.
- The frontend can refresh and still list previous projects.

If React consumed FastAPI directly, FastAPI would also need to persist and query all dashboard project metadata.

#### Reason 4: Streaming Events Are Cleaner Through A Gateway

The orchestrator emits events like:

- `run.created`
- `node.started`
- `node.completed`
- `input.requested`
- `input.received`
- `run.completed`
- `run.failed`
- `run.cancelled`
- `heartbeat`

The gateway consumes the FastAPI event stream, updates project metadata, and forwards events to the browser.

```mermaid
sequenceDiagram
  participant Node as LangGraph Node
  participant Bus as event_bus
  participant FastAPI as FastAPI SSE
  participant Gateway as Gateway SSE
  participant React as React Dashboard

  Node->>Bus: append node.completed event
  Bus->>FastAPI: stream event
  FastAPI->>Gateway: SSE data JSON
  Gateway->>Gateway: update project last_state
  Gateway->>React: SSE data JSON
  React->>React: update pipeline, file tree, terminal, tokens
```

This gives us two benefits:

1. The browser gets real-time updates.
2. The gateway also records the latest state for project history.

Without the gateway, React could still display the stream, but the persistence logic would need to move into FastAPI.

#### Reason 5: One Active Build And Preview Control

This platform creates generated apps in Docker. That means it must control ports and containers carefully.

The gateway enforces product-level rules such as:

- A user cannot launch another project while one is already running or queued.
- Starting a new project can stop old active previews.
- Preview stop/restart requests update project metadata.
- Download code is only allowed when a sandbox exists.

These are dashboard/application policies. They are not LangGraph node logic.

If everything lived in FastAPI, the orchestrator would need to carry those product rules too. That makes the orchestrator less clean.

#### Reason 6: The Orchestrator Is Already Complex

The Python orchestrator already has heavy responsibilities:

- Builds a LangGraph `StateGraph`.
- Maintains Pydantic `AgentState`.
- Calls Gemini through a safe JSON wrapper.
- Tracks token usage and cost.
- Emits stream events.
- Waits for human input.
- Saves Redis checkpoints.
- Creates sandbox folders.
- Starts Docker containers.
- Writes code files.
- Reviews generated code.
- Executes checks.
- Debugs failures.
- Creates Git snapshots.
- Verifies Docker Compose deployment.

Adding login, OTP, cookies, project listing, and browser API policy into the same service would make it harder to reason about. Keeping the orchestrator focused makes the system easier to maintain.

#### Why Node.js For Gateway Instead Of Python?

Python could be used for the gateway. There is no rule that the middle layer must be Node.

But Node.js made sense here because:

- The frontend is JavaScript/React, so Express fits naturally for browser-facing APIs.
- The auth style is MERN-like: MongoDB, Mongoose models, JWT, bcryptjs, Nodemailer.
- The gateway is mostly I/O work: HTTP routing, database calls, cookies, SSE/WebSocket relay.
- Python is reserved for the AI-heavy part: LangGraph, Pydantic, async workflow, and agent execution.

So this is not "Node is better than Python." It is "Node is better placed for this project's web gateway because the existing auth and dashboard backend are already JavaScript-style."

#### What Would Happen If We Removed The Gateway?

If we removed the Node gateway, the architecture would become:

```mermaid
flowchart LR
  React[React Dashboard] --> FastAPI[FastAPI App Backend + AI Orchestrator]
  FastAPI --> Mongo[(Auth + OTP)]
  FastAPI --> Postgres[(Project Metadata)]
  FastAPI --> Redis[(Sessions + Checkpoints)]
  FastAPI --> Docker[Docker Sandbox]
```

This would reduce one service, but FastAPI would need to absorb almost everything:

- `/api/auth/sendotp`
- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/logout`
- `/api/auth/check`
- `/api/projects`
- `/api/projects/:id/events`
- `/api/projects/:id/input`
- `/api/projects/:id/cancel`
- `/api/projects/:id/preview/stop`
- `/api/projects/:id/preview/restart`
- `/api/projects/:id/download`
- project ownership checks
- cookie/JWT handling
- Redis logout blocklist
- Mongo user models
- Postgres project metadata
- event persistence
- orchestration
- sandboxing

That design is simpler in the deployment diagram but more complicated inside one codebase.

#### Tradeoff Table

| Option | Benefit | Problem |
| --- | --- | --- |
| React -> FastAPI only | Fewer services and simpler local prototype | FastAPI becomes auth server, app backend, event relay, metadata store, and AI runtime |
| React -> Gateway -> FastAPI | Cleaner responsibility split, safer boundary, easier project ownership and history | One extra service to run and debug |
| Python gateway + Python orchestrator | Same language everywhere | Still mixes web backend and orchestrator unless split into two Python services |
| Node gateway + Python orchestrator | Fits current auth/dashboard code and keeps Python focused on agents | Requires Node and Python runtime knowledge |

#### Final Deep Answer

We used three layers because this is not a simple CRUD backend. It is a platform that lets authenticated users launch long-running AI software-building workflows, stream progress, answer human-in-the-loop questions, cancel runs, manage generated Docker previews, and download generated code.

If React called FastAPI directly, FastAPI would need to own both the public web backend and the private agent runtime. That would combine user/session security, project ownership, metadata storage, event relay, and preview policy with LangGraph, Gemini, sandbox execution, checkpointing, debugging, and deployment verification.

The gateway prevents that mixing. It is the controlled public API. It knows who the user is, which projects belong to them, whether another project is active, and how to expose events and previews safely. The orchestrator stays as the internal AI engine. It accepts structured JSON commands, runs the graph, emits JSON events, and controls the sandbox.

So the real reason is not just "three layers is cleaner." The deeper reason is that each layer protects the others from responsibility overload:

- React stays a dashboard, not an AI runtime client.
- Node/Express stays the product backend and security boundary.
- FastAPI/LangGraph stays the agentic engine.

That makes the project easier to explain, debug, secure, test, and extend.


The best reason to say in an interview is:
We separated the gateway from the orchestrator because user-facing requests and agentic execution have very different failure modes, security needs, and scaling behavior.

In simple terms:
React → FastAPI directly is possible, but then FastAPI becomes responsible for everything:
login/auth
project ownership
project history
event streaming
cancel/download/preview APIs
LangGraph orchestration
LLM calls
Redis checkpoints
Docker sandbox execution
debugging and deployment verification
That makes one backend too overloaded.
The cleaner interview answer is:
FastAPI in our system is not just a backend. It is an internal AI runtime. It runs long workflows, calls LLMs, writes files, executes code in Docker, handles retries, and manages checkpoints. So we kept a Node gateway in front of it. The gateway handles public web concerns like auth, user sessions, project ownership, metadata, streaming relay, cancel, preview, and download. This keeps the orchestrator protected and focused only on agent execution.

That sounds logical because it explains the real engineering reason: not “three layers because architecture pattern,” but “three layers because public API traffic and long-running AI execution should not be mixed.”

</details>

<details id="inline-02-project-architecture">
<summary>02_project_architecture.md - Question 2: Explain The Project Architecture In Detail</summary>

### Question 2: Explain The Project Architecture In Detail

#### Short Interview Answer

This project is an AI software-builder platform. The user enters a requirement in a React dashboard, the request goes to a Node/Express gateway, and the gateway triggers a Python FastAPI/LangGraph orchestrator run. The orchestrator breaks the requirement into architecture, planning, coding, review, execution, debugging, sandbox preview, and final presentation steps.

The architecture has three main layers:

1. **Frontend:** React + Vite dashboard for login, project launch, live pipeline view, terminal stream, file tree, human input, preview, cancel, and download.
2. **Gateway:** Node.js + Express public backend for authentication, cookies, project ownership, project metadata, event relay, preview control, cancellation, and zip download.
3. **Orchestrator:** Python + FastAPI + LangGraph internal AI engine for PM clarification, architecture generation, task planning, code generation, review, execution, debugging, checkpointing, sandbox control, and deployment verification.

The important idea is:

> The frontend does not directly run AI workflows. It talks to the gateway. The gateway validates the user and forwards safe structured requests to the orchestrator. The orchestrator runs the internal agent workflow and streams progress back as events.

#### Overall Architecture Diagram

```mermaid
flowchart LR
  User[User] --> Browser[React + Vite Frontend]

  Browser -->|HTTP JSON + cookies| Gateway[Node.js Express Gateway]
  Browser -->|SSE events| Gateway

  Gateway -->|Auth records + OTP| Mongo[(MongoDB)]
  Gateway -->|Project metadata| Postgres[(Postgres)]
  Gateway -->|JWT logout blocklist| RedisGateway[(Redis)]

  Gateway -->|POST /runs| Orchestrator[Python FastAPI Orchestrator]
  Gateway -->|GET /runs/:id/events| Orchestrator
  Gateway -->|cancel/input/preview commands| Orchestrator

  Orchestrator -->|LangGraph state| Graph[LangGraph Workflow]
  Graph --> Gemini[Gemini LLM]
  Graph --> Checkpoints[(Redis Checkpoints)]
  Graph --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated Full-Stack App]
  Sandbox --> Git[Git Snapshots]
```

#### Layer 1: Frontend Architecture

The frontend lives in `frontend/`.

Its job is not to generate code. Its job is to give the user a clean dashboard for controlling and observing the build.

Main responsibilities:

- Show login/signup screen.
- Check whether the user is authenticated.
- Let the user enter a project requirement.
- Start a new project build.
- Block launching another project while one is already running.
- Listen to server-sent events from the gateway.
- Show pipeline node progress.
- Show terminal-style event output.
- Show generated file tree.
- Show token/cost usage.
- Show human input forms when the orchestrator asks questions.
- Let the user cancel the build.
- Let the user open, stop, or restart the preview.
- Let the user download generated code.

Important frontend files:

| File                                     | Purpose                                                                                       |
| ---------------------------------------- | --------------------------------------------------------------------------------------------- |
| `frontend/src/App.jsx`                   | Main app state, project launch, SSE subscription, human input, cancel, preview, download flow |
| `frontend/src/components/AuthScreen.jsx` | Login/signup/OTP user interface                                                               |
| `frontend/src/components/Dashboard.jsx`  | Main project dashboard UI                                                                     |
| `frontend/src/api/gateway.js`            | Gateway URL helpers, JSON fetch helper, stream event normalization                            |
| `frontend/src/styles.css`                | Dashboard styling                                                                             |

The frontend communicates with the gateway using JSON APIs and cookies. For live updates it opens an `EventSource` connection to:

```text
GET /api/projects/:projectId/events
```

The frontend then receives events such as:

```text
run.created
node.started
node.completed
input.requested
input.received
run.completed
run.failed
run.cancelled
heartbeat
```

Those events update the visual pipeline, latest state, terminal output, file tree, preview information, and pending human input.

#### Layer 2: Gateway Architecture

The gateway lives in `gateway/`.

It is the public backend for the product. The browser talks to this layer, not directly to the Python orchestrator.

Main responsibilities:

- Accept browser requests.
- Handle CORS and cookies.
- Authenticate users.
- Register and log in users.
- Send and verify OTP.
- Store dashboard user records.
- Store project metadata.
- Check whether a project belongs to the current user.
- Start orchestrator runs.
- Relay orchestrator events to the browser.
- Update project metadata from stream events.
- Enforce one-active-build style policy.
- Stop old previews when a new project starts.
- Cancel running projects.
- Submit human input back to the orchestrator.
- Stop/restart generated app previews.
- Create downloadable zip files from sandbox output.

Important gateway files:

| File                                         | Purpose                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------------ |
| `gateway/src/index.js`                       | Express app setup, CORS, cookies, auth routes, project routes, WebSocket event relay |
| `gateway/src/routes/auth.js`                 | OTP, signup, login, logout, session check                                            |
| `gateway/src/routes/projects.js`             | Project start/list/get/events/input/cancel/preview/download routes                   |
| `gateway/src/middleware/auth.js`             | Requires valid authenticated user                                                    |
| `gateway/src/services/orchestratorClient.js` | Calls FastAPI orchestrator APIs                                                      |
| `gateway/src/services/projectStore.js`       | Stores project metadata in Postgres, with memory fallback behavior                   |
| `gateway/src/services/projectZip.js`         | Safely zips generated sandbox code                                                   |
| `gateway/src/config/mongo.js`                | Mongo connection for auth/OTP                                                        |
| `gateway/src/config/redis.js`                | Redis connection for token blocklist                                                 |

The gateway exposes APIs like:

| API                                             | Meaning                                |
| ----------------------------------------------- | -------------------------------------- |
| `GET /api/health`                               | Checks gateway and orchestrator health |
| `POST /api/auth/sendotp`                        | Sends OTP                              |
| `POST /api/auth/register`                       | Creates account                        |
| `POST /api/auth/login`                          | Logs user in                           |
| `POST /api/auth/logout`                         | Logs user out                          |
| `GET /api/auth/check`                           | Checks current session                 |
| `GET /api/projects`                             | Lists the user's projects              |
| `POST /api/projects`                            | Starts a new project run               |
| `GET /api/projects/:projectId`                  | Gets one project's metadata            |
| `GET /api/projects/:projectId/events`           | Streams live run events                |
| `POST /api/projects/:projectId/input`           | Sends human answer/escalation guidance |
| `POST /api/projects/:projectId/cancel`          | Cancels a run                          |
| `POST /api/projects/:projectId/preview/stop`    | Stops preview containers               |
| `POST /api/projects/:projectId/preview/restart` | Restarts preview containers            |
| `GET /api/projects/:projectId/download`         | Downloads generated project zip        |

The gateway is important because it turns the orchestrator into an internal service. The user-facing product logic stays in one place.

#### Layer 3: Orchestrator Architecture

The orchestrator lives in `orchestrator/`.

It is the internal AI execution engine. Its job is to take one user requirement and turn it into a generated full-stack project.

Main responsibilities:

- Accept a run request from the gateway.
- Create a `project_id`.
- Start an async LangGraph workflow.
- Emit stream events while nodes run.
- Maintain an `AgentState`.
- Ask clarification questions when needed.
- Generate architecture blueprint.
- Validate the blueprint.
- Plan implementation tasks.
- Create and check the sandbox.
- Build code task by task.
- Review generated code.
- Execute checks.
- Debug failures.
- Ask for human escalation if needed.
- Save snapshots.
- Verify deployment/preview.
- Return final project state.

Important orchestrator files:

| File                                            | Purpose                                                         |
| ----------------------------------------------- | --------------------------------------------------------------- |
| `orchestrator/app/main.py`                      | FastAPI endpoints: health, runs, events, cancel, input, preview |
| `orchestrator/app/models/contracts.py`          | Pydantic request/response/event/state models                    |
| `orchestrator/app/graph/workflow.py`            | LangGraph node registration and routing                         |
| `orchestrator/app/services/event_bus.py`        | In-memory event bus and SSE streaming                           |
| `orchestrator/app/services/input_bridge.py`     | Human input wait/submit bridge                                  |
| `orchestrator/app/services/run_manager.py`      | Tracks and cancels active asyncio tasks                         |
| `orchestrator/app/services/redis_checkpoint.py` | Saves state checkpoints after each node                         |
| `orchestrator/app/services/gemini_client.py`    | Gemini JSON wrapper, retries, token/cost tracking               |
| `orchestrator/app/services/sandbox.py`          | Sandbox lifecycle and preview control                            |
| `orchestrator/app/nodes/*`                      | Individual agent/workflow nodes                                 |

The orchestrator exposes internal APIs:

| API                                     | Meaning                             |
| --------------------------------------- | ----------------------------------- |
| `GET /health`                           | Orchestrator health                 |
| `POST /runs`                            | Start a LangGraph workflow          |
| `GET /runs/:projectId/events`           | Stream workflow events              |
| `POST /runs/:projectId/input`           | Submit human input                  |
| `GET /runs/:projectId/input`            | Read input history                  |
| `POST /runs/:projectId/cancel`          | Cancel workflow and cleanup sandbox |
| `POST /runs/:projectId/preview/stop`    | Stop sandbox preview                |
| `POST /runs/:projectId/preview/restart` | Restart sandbox preview             |

#### Main Runtime Flow

When a user starts a project, the flow is:

```mermaid
sequenceDiagram
  participant U as User
  participant F as React Frontend
  participant G as Node Gateway
  participant O as FastAPI Orchestrator
  participant LG as LangGraph
  participant S as Sandbox
  participant DB as Databases

  U->>F: Enter requirement and click build
  F->>G: POST /api/projects
  G->>G: Verify JWT cookie and user
  G->>DB: Check active project and save metadata
  G->>O: POST /runs
  O->>LG: Start async workflow
  O-->>G: project_id + running
  G-->>F: Project created
  F->>G: GET /api/projects/:id/events
  G->>O: GET /runs/:id/events
  LG->>S: Create files, run commands, start preview
  LG-->>O: Emit node events
  O-->>G: SSE events
  G->>DB: Update last_state and metadata
  G-->>F: SSE events
  F->>F: Update pipeline, terminal, file tree, preview
```

#### LangGraph Workflow

The orchestrator workflow is the brain of the project.

High-level phases:

1. **PM phase:** Understand the requirement and ask clarification questions if needed.
2. **Architecture phase:** Create entities, database schema, API endpoints, frontend pages, folder structure, and dependencies.
3. **Validation phase:** Check whether the blueprint is internally consistent.
4. **Planning phase:** Break the build into ordered implementation tasks.
5. **Sandbox phase:** Create the generated app workspace and verify the sandbox is healthy.
6. **Development loop:** Select task, build context, code, update registry, review, execute, debug if needed, snapshot.
7. **Phase verification:** Check each phase before moving forward.
8. **Deployment verification:** Verify final app/preview readiness.
9. **Presentation phase:** Return final state to the user.

```mermaid
flowchart TD
  Start([Start]) --> PM[pmAgent]
  PM -->|needs clarification| HumanInput[humanInput]
  HumanInput --> PM
  PM -->|spec ready| A1[architectStep1]
  A1 --> A2[architectStep2]
  A2 --> A3[architectStep3]
  A3 --> A4[architectStep4]
  A4 --> A5[architectStep5]
  A5 --> Validator[blueprintValidator]
  Validator -->|repair needed| A2
  Validator -->|valid| Planner[plannerAgent]
  Planner --> Setup[setupSandbox]
  Setup --> Health[sandboxHealthCheck]
  Health -->|retry setup| Setup
  Health -->|healthy| Select[selectNextTask]
  Select -->|task exists| Context[contextBuilder]
  Context --> Coder[coderAgent]
  Coder --> Registry[updateRegistry]
  Registry --> Reviewer[reviewerAgent]
  Reviewer -->|approved| Executor[executorAgent]
  Reviewer -->|needs changes| Context
  Reviewer -->|too complex| Simplify[simplifyTask]
  Simplify --> Select
  Executor -->|passed| Snapshot[snapshotManager]
  Snapshot --> Select
  Executor -->|failed| Debugger[debuggerAgent]
  Debugger -->|retry| Context
  Debugger -->|needs human| Escalation[humanEscalation]
  Escalation --> Select
  Escalation --> Context
  Select -->|phase done| PhaseVerify[phaseVerification]
  PhaseVerify --> Patterns[patternExtractor]
  Patterns --> Compact[stateCompactor]
  Compact --> Select
  Select -->|all tasks done| Deploy[deploymentVerifier]
  Deploy -->|repair| Debugger
  Deploy -->|ready| Present[presentToUser]
  Present --> End([End])
```

#### AgentState: The Central Contract

The orchestrator passes one shared state object through the graph: `AgentState`.

This state is important because each node reads and writes part of the same build memory.

Important fields:

| Field                 | Meaning                                                                    |
| --------------------- | -------------------------------------------------------------------------- |
| `projectId`           | Unique run/project id                                                      |
| `userId`              | User who launched the project                                              |
| `userRequirement`     | Original requirement                                                       |
| `pmStatus`            | PM clarification/spec status                                               |
| `pmQuestions`         | Clarification questions                                                    |
| `clarifiedSpec`       | Structured understood requirement                                          |
| `blueprint`           | Architecture plan: entities, DB schema, APIs, frontend pages, dependencies |
| `blueprintValidation` | Validation result and issues                                               |
| `taskQueue`           | Ordered implementation plan                                                |
| `currentTask`         | Task currently being implemented                                           |
| `fileRegistry`        | Known files and their purpose                                              |
| `projectPatterns`     | Learned coding conventions                                                 |
| `sandboxId`           | Generated project workspace id                                             |
| `fileTree`            | Generated files visible to frontend                                        |
| `previewFrontendPort` | Frontend preview port                                                      |
| `previewBackendPort`  | Backend preview port                                                       |
| `contextPackage`      | Context prepared for coder                                                 |
| `coderOutput`         | Files/changes proposed by coder                                            |
| `reviewResult`        | Reviewer verdict/issues                                                    |
| `executionResult`     | Command result/output/errors                                               |
| `debugState`          | Debug attempt state                                                        |
| `tokenUsage`          | LLM token and cost tracking                                                |
| `terminalOutput`      | Logs shown in frontend terminal                                            |
| `gitSnapshots`        | Snapshots after code steps                                                 |
| `currentPhase`        | Current high-level workflow phase                                          |
| `error`               | Failure message if workflow fails                                          |

The frontend sees this state inside stream events and uses it to update the UI.

#### Data Storage Architecture

This project uses different storage systems for different kinds of data.

```mermaid
flowchart TB
  Gateway[Node Gateway]
  Orchestrator[Python Orchestrator]

  Gateway --> Mongo[(MongoDB)]
  Gateway --> Postgres[(Postgres)]
  Gateway --> RedisAuth[(Redis Auth Blocklist)]

  Orchestrator --> RedisCheckpoint[(Redis Checkpoints)]
  Orchestrator --> SandboxFS[Sandbox Filesystem]
  Orchestrator --> Docker[Docker Containers]
  Orchestrator --> Git[Git Snapshots]

  Mongo --> M1[Users and OTP records]
  Postgres --> P1[Project metadata and latest state]
  RedisAuth --> R1[Logged-out JWT blocklist]
  RedisCheckpoint --> R2[Node-by-node AgentState snapshots]
  SandboxFS --> S1[Generated source code]
  Docker --> D1[Generated app runtime]
  Git --> G1[Recovery snapshots]
```

Storage split:

| Storage            | Owned by     | Stores                                       |
| ------------------ | ------------ | -------------------------------------------- |
| MongoDB            | Gateway      | User auth records and OTP records            |
| Postgres           | Gateway      | Project metadata, latest state, preview info |
| Redis              | Gateway      | Logout/token blocklist                       |
| Redis checkpoints  | Orchestrator | Agent state after graph nodes                |
| Sandbox filesystem | Orchestrator | Generated project files                      |
| Docker             | Orchestrator | Running generated app containers             |
| Git snapshots      | Orchestrator | Recoverable snapshots after code changes     |

#### Event Streaming Architecture

The project is interactive because events stream continuously while the workflow runs.

Event flow:

```mermaid
sequenceDiagram
  participant Node as LangGraph Node
  participant Bus as Orchestrator Event Bus
  participant FastAPI as FastAPI SSE Endpoint
  participant Gateway as Gateway Event Relay
  participant Store as Project Store
  participant React as React Dashboard

  Node->>Bus: append StreamEvent
  Bus->>FastAPI: stream JSON event
  FastAPI-->>Gateway: SSE data
  Gateway->>Store: update last_event and last_state
  Gateway-->>React: SSE data
  React->>React: update UI
```

Each event has this shape:

```json
{
  "type": "node.completed",
  "node": "coderAgent",
  "message": "coderAgent completed",
  "state": {}
}
```

This design lets the frontend show live progress without constantly polling.

#### Human-In-The-Loop Architecture

Some workflows need user input. For example:

- PM agent may ask clarification questions.
- Debugger may escalate when the system cannot fix something automatically.

The flow is:

1. A node decides input is needed.
2. Orchestrator emits `input.requested`.
3. Frontend displays a human input panel.
4. User submits an answer.
5. Frontend sends answer to gateway.
6. Gateway forwards answer to orchestrator.
7. Orchestrator resumes the waiting workflow.
8. Orchestrator emits `input.received`.

This is important because the workflow is not just fire-and-forget. It can pause, ask for help, and continue.

#### Sandbox Architecture

The sandbox is where generated code lives and runs.

The orchestrator uses the sandbox for:

- creating generated project folders
- writing backend files
- writing frontend files
- installing/running dependencies
- executing validation commands
- starting preview containers
- exposing frontend/backend preview URLs
- creating downloadable project output

Conceptually:

```text
orchestrator
  -> sandbox/sandbox-<id>/
      -> backend/
      -> frontend/
      -> docker-compose.yml
      -> generated files
```

The sandbox is separated from the main project because generated code can be messy, incomplete, or failing while the AI is building it. The sandbox gives the agent a controlled workspace.

#### Why This Architecture Works Well

This architecture works because each layer has a clear job:

| Layer        | Main Question It Answers                                                  |
| ------------ | ------------------------------------------------------------------------- |
| Frontend     | What should the user see and control?                                     |
| Gateway      | Is this user allowed to do this, and how do we store/relay product state? |
| Orchestrator | How do we turn the requirement into working code?                         |
| Sandbox      | Where can generated code safely be created and executed?                  |

The main benefit is that complexity is contained.

- UI complexity stays in React.
- Product/API/security complexity stays in the gateway.
- AI workflow complexity stays in the orchestrator.
- Generated-code execution complexity stays in the sandbox.

#### Interview-Ready Explanation

If an interviewer asks, "Explain your architecture," you can say:

> My project is an AI full-stack app builder. The user enters a requirement in a React dashboard. The React frontend calls a Node/Express gateway, which acts as the public backend. The gateway handles authentication, cookies, project ownership, project metadata, active-project policy, event relay, preview control, cancellation, and code download. It then calls a Python FastAPI orchestrator service. The orchestrator is the internal AI engine. It uses LangGraph to run multiple nodes such as PM, architect, planner, coder, reviewer, executor, debugger, deployment verifier, and presenter. It maintains a shared Pydantic AgentState, checkpoints state to Redis, calls Gemini for structured JSON outputs, writes generated files into a Docker sandbox, runs checks, starts preview containers, and streams events back through the gateway to the frontend.
>
> The reason for this architecture is separation of concerns. The frontend is only the UI, the gateway is the secure product backend, and the orchestrator is the long-running agent runtime. This makes the system easier to secure, debug, explain, and extend.

#### Deep Interview Follow-Up Answer

If they ask, "What happens internally after a user submits a prompt?", answer like this:

> First, the frontend sends the requirement to the gateway through `POST /api/projects`. The gateway verifies the user's session, checks whether they already have a running project, stops old previews if needed, and forwards the requirement to the orchestrator through `POST /runs`. The orchestrator creates a project id, starts an async LangGraph workflow, and immediately returns a running status. Then the frontend opens an SSE stream through the gateway. As each LangGraph node runs, the orchestrator emits events such as `node.started` and `node.completed`. The gateway relays those events to the frontend and also stores the latest state in Postgres. The frontend uses those events to update the pipeline, terminal, file tree, token usage, and preview state.
>
> Inside LangGraph, the PM agent clarifies the requirement, architect nodes create the blueprint, the validator checks consistency, the planner creates tasks, the sandbox is prepared, then the system loops through context building, coding, registry update, review, execution, debugging, and snapshotting. After all tasks are done, deployment verification checks the final app and `presentToUser` returns the completed result.

#### One-Line Summary

> This project uses React as the dashboard, Node/Express as the secure product gateway, and FastAPI/LangGraph as the internal agentic build engine that generates and verifies code inside a Docker sandbox.

</details>

<details id="inline-03-high-level-project-overview">
<summary>03_high_level_project_overview.md - Question 3: High-Level Project Overview For Beginners</summary>

### Question 3: High-Level Project Overview For Beginners

#### One-Line Summary

This project is an **AI app builder**.

The user types what kind of app they want, and the system uses AI agents to plan, generate, review, run, debug, preview, and package that app.

#### What This Project Is

At a high level, this project is like a small automated software development team inside a web application.

Instead of one user manually writing every file, the user gives a requirement like:

```text
Build a todo app with login, categories, and due dates.
```

Then the system tries to build that app step by step.

It does not simply ask an LLM one question and paste one answer. It runs a workflow with multiple roles:

- PM agent understands the requirement.
- Architect agents design the system.
- Validator checks if the design makes sense.
- Planner breaks the work into tasks.
- Coder writes files.
- Reviewer checks the code.
- Executor runs commands.
- Debugger fixes failures.
- Deployment verifier checks if the app is ready.
- Presenter returns the final result to the user.

So the project is not just a chatbot. It is an **agentic software generation platform**.

#### Simple Mental Model

Think of the project like this:

```text
User says: "Build me an app"
        ↓
Dashboard sends the request
        ↓
Backend validates the user and creates a project
        ↓
AI orchestrator runs a software-building workflow
        ↓
Generated app is created inside a sandbox
        ↓
User watches progress, previews the app, and downloads the code
```

#### High-Level Diagram

```mermaid
flowchart LR
  User[User] --> UI[React Dashboard]
  UI --> Gateway[Node Gateway]
  Gateway --> AI[Python AI Orchestrator]
  AI --> Agents[AI Agent Workflow]
  Agents --> Sandbox[Generated App Sandbox]
  Sandbox --> Preview[Live Preview + Downloadable Code]
  Preview --> User
```

#### What Problem Does This Project Solve?

Normally, if someone wants to build an app, they need to:

1. Understand the requirement.
2. Design the database.
3. Design API endpoints.
4. Design frontend screens.
5. Create the folder structure.
6. Write backend code.
7. Write frontend code.
8. Run the app.
9. Fix errors.
10. Package or deploy it.

This project tries to automate that process using AI agents.

The goal is:

> A user should be able to describe an app in natural language and watch the system generate a working full-stack project.

#### What The User Sees

From the user's point of view, the app feels like a dashboard.

The user can:

- sign up or log in
- type a project requirement
- start a build
- see the workflow pipeline running
- watch terminal-like progress logs
- see generated files
- answer clarification questions
- cancel a project
- open the generated app preview
- stop or restart the preview
- download the generated source code

The user does not directly see all the backend complexity. They mostly see progress and results.

#### What Happens Behind The Scenes

Behind the scenes, the project has three major systems:

1. **Frontend**
2. **Gateway**
3. **Orchestrator**

##### 1. Frontend

The frontend is the React dashboard.

Its job is to show the user interface.

It lets the user:

- log in
- submit requirements
- watch progress
- answer questions
- open preview
- download final code

The frontend is basically the "control room" for the user.

##### 2. Gateway

The gateway is the public backend.

Its job is to manage normal web-app responsibilities:

- authentication
- cookies/session
- user identity
- project ownership
- project history
- event relay
- preview controls
- cancellation
- downloads

The gateway is like the receptionist/security desk. It checks who the user is and decides what request is allowed.

##### 3. Orchestrator

The orchestrator is the AI engine.

Its job is to actually build the generated app.

It runs the agent workflow:

- understand requirement
- create blueprint
- validate blueprint
- create tasks
- write code
- review code
- run code
- debug errors
- verify deployment

The orchestrator is like the engineering team.

#### What Is The Sandbox?

The sandbox is a separate workspace where the AI-generated app is created.

This is important because generated code may be incomplete or broken while it is being built.

The sandbox keeps generated code separate from the main project.

Inside the sandbox, the system can create things like:

```text
sandbox/sandbox-<id>/
  backend/
  frontend/
  docker-compose.yml
  generated files
```

The sandbox is where the generated app can be run, tested, previewed, and zipped for download.

#### What Makes This Project Interesting?

The interesting part is that this is not a single prompt-to-code call.

It is a structured workflow.

The system tries to behave more like a real development process:

```text
Requirement
  → clarification
  → architecture
  → validation
  → planning
  → coding
  → review
  → execution
  → debugging
  → deployment verification
  → final presentation
```

That is why the project has many nodes in the orchestrator.

Each node has one responsibility, just like each person in a development team would have a different role.

#### Very Simple Interview Explanation

If you know nothing and need to explain it simply, say:

> My project is an AI-powered full-stack app builder. A user enters an app idea in a React dashboard. The request goes through a Node gateway that handles authentication and project management. Then a Python FastAPI orchestrator runs a LangGraph workflow with different AI agents like PM, architect, planner, coder, reviewer, executor, and debugger. These agents generate code inside a Docker sandbox, stream progress back to the dashboard, and finally let the user preview or download the generated app.

#### Even Simpler Version

> It is like an automated AI development team. The user gives a requirement, and the system plans the app, writes the code, runs it, fixes issues, and shows the result.

#### What You Should Understand Before Going Deeper

Before going deeper, keep only this picture in your mind:

```text
React Dashboard
  = user interface

Node Gateway
  = secure product backend

FastAPI Orchestrator
  = AI workflow engine

Docker Sandbox
  = place where generated apps are built and run
```

If you understand this, the next level becomes much easier.

#### Next Level To Study

The next level is to understand:

1. What exactly happens when the user clicks "Build".
2. How the frontend, gateway, and orchestrator talk to each other.
3. How the LangGraph nodes work one by one.
4. How events stream back to the dashboard.
5. How generated code is written into the sandbox.

</details>

<details id="inline-04-workflow-nodes-deep-dive">
<summary>04_workflow_nodes_deep_dive.md - Question 4: What Does Each Workflow Node Do, Why Was It Added, And What Happens If It Is Removed?</summary>

### Question 4: What Does Each Workflow Node Do, Why Was It Added, And What Happens If It Is Removed?

#### Short Interview Answer

The orchestrator is built as a LangGraph workflow. Each node represents one responsibility in an automated software development process.

Instead of asking the LLM to generate a full project in one shot, the workflow breaks the work into stages:

```text
Requirement
  -> PM clarification
  -> Architecture design
  -> Blueprint validation
  -> Task planning
  -> Sandbox setup
  -> Task-by-task coding
  -> Registry update
  -> Review
  -> Execution
  -> Debugging / simplification / human escalation
  -> Phase verification
  -> Pattern extraction
  -> State compaction
  -> Deployment verification
  -> Final presentation
```

The core reason for having many nodes is:

> Each node reduces one type of risk. PM reduces requirement risk, architect reduces design risk, validator reduces consistency risk, planner reduces task-size risk, reviewer reduces code-quality risk, executor reduces runtime risk, debugger reduces failure risk, and deployment verifier reduces final-delivery risk.

#### Full Workflow Diagram

```mermaid
flowchart TD
  Start([Start]) --> PM[pmAgent]
  PM -->|needs clarification| HumanInput[humanInput]
  HumanInput --> PM
  PM -->|spec ready| A1[architectStep1]
  A1 --> A2[architectStep2]
  A2 --> A3[architectStep3]
  A3 --> A4[architectStep4]
  A4 --> A5[architectStep5]
  A5 --> Validator[blueprintValidator]
  Validator -->|repair schema| A2
  Validator -->|repair APIs| A3
  Validator -->|repair pages| A4
  Validator -->|valid| Planner[plannerAgent]
  Planner --> Setup[setupSandbox]
  Setup --> Health[sandboxHealthCheck]
  Health -->|retry setup| Setup
  Health -->|healthy| Select[selectNextTask]
  Select -->|task exists| Context[contextBuilder]
  Context --> Coder[coderAgent]
  Coder --> Registry[updateRegistry]
  Registry --> Reviewer[reviewerAgent]
  Reviewer -->|approved| Executor[executorAgent]
  Reviewer -->|rejected| Context
  Reviewer -->|too many rejections| Simplify[simplifyTask]
  Simplify --> Select
  Executor -->|pass| Snapshot[snapshotManager]
  Snapshot --> Select
  Executor -->|fail| Debugger[debuggerAgent]
  Debugger -->|retry| Context
  Debugger -->|cannot fix| Escalation[humanEscalation]
  Escalation -->|guide| Context
  Escalation -->|simplify| Simplify
  Escalation -->|skip| Select
  Select -->|phase complete| PhaseVerify[phaseVerification]
  PhaseVerify --> Pattern[patternExtractor]
  Pattern --> Compact[stateCompactor]
  Compact --> Select
  Select -->|all tasks done| Deploy[deploymentVerifier]
  Deploy -->|repair| Debugger
  Deploy -->|ready or max attempts| Present[presentToUser]
  Present --> End([End])
```

#### Important Background: Every Node Is Wrapped

In `workflow.py`, every node is wrapped by `_run_node`.

That wrapper does three important things:

1. Emits `node.started`.
2. Runs the actual node function.
3. Saves a Redis checkpoint and emits `node.completed`.

Why this was added:

- The frontend can show live progress.
- The gateway can store the latest project state.
- The system can inspect what happened after each node.
- Debugging is easier because each state transition is visible.

What happens if this wrapper is removed:

- The frontend would not know which node is running.
- There would be no node-by-node state checkpoints.
- Debugging failures would be much harder.
- The whole run would feel like a black box.

#### Node 1: `pmAgent`

##### What this node does

`pmAgent` is the product manager node. It reads the user's raw requirement and converts it into a clearer project specification.

It can return two outcomes:

1. `needs_clarification`
2. `spec_ready`

If the requirement is vague, it asks a small number of business-logic questions. Example:

```text
Should users have roles?
Should todo items be private per user?
Should due dates support reminders?
```

If the requirement is clear enough, it creates `clarifiedSpec`, including:

- app name
- description
- user roles
- auth requirement
- features
- sub-features
- database recommendation
- pages
- assumptions

It also tracks `pmConversation`, `pmQuestions`, and `pmStatus`.

The node has a retry limit for clarification. If it asks too many times, it stops asking and proceeds with reasonable defaults.

##### Why this node was added

This node exists because users usually give incomplete requirements.

For example, if the user says:

```text
Build a finance app.
```

That could mean:

- expense tracker
- stock portfolio tracker
- budgeting app
- invoice manager
- personal banking dashboard

The PM node reduces ambiguity before the system starts designing code.

##### What happens if this node is removed

If `pmAgent` is removed, the architect receives a raw vague prompt.

That causes:

- wrong assumptions
- missing features
- wrong database design
- wrong pages
- wrong user roles
- more downstream debugging

Interview answer:

> I added the PM node because building from a vague prompt is risky. It converts natural language into a structured spec before architecture starts. Without it, the system may generate technically valid code for the wrong product.

#### Node 2: `humanInput`

##### What this node does

`humanInput` pauses the workflow when the PM agent needs clarification.

It sends an `input.requested` event to the frontend. The dashboard shows the questions to the user. When the user answers, the frontend sends the answer back through the gateway, and the orchestrator resumes.

It appends the user's answer into `pmConversation` and sends control back to `pmAgent`.

##### Why this node was added

This node adds human-in-the-loop behavior.

The system should not always guess important business rules. Sometimes the correct thing is to ask the user.

##### What happens if this node is removed

If this node is removed:

- the workflow cannot pause for clarification
- PM questions have nowhere to go
- the system must either guess everything or fail
- the final generated app may not match what the user wanted

Interview answer:

> I added `humanInput` so the AI workflow can pause and ask the user when the requirement is ambiguous. Without this node, the system becomes a one-way generator and loses user correction.

#### Node 3: `architectStep1`

##### What this node does

`architectStep1` identifies the main entities and relationships in the app.

It creates a naming map for each entity:

- entity name
- table name
- API path
- model file name
- route file name
- relationships

Example:

```text
TodoItem
  tableName: todo_items
  apiPath: /api/todo-items
  modelFile: todoItem
  routeFile: todoItemRoutes
```

##### Why this node was added

This node establishes naming consistency early.

Generated projects often fail because the LLM names the same concept differently in different places:

- `Todo`
- `TodoItem`
- `todos`
- `todo_items`
- `/api/tasks`
- `/api/todos`

The naming map gives later nodes a single source of truth.

##### What happens if this node is removed

Without this node:

- database tables may not match API endpoints
- models may not match route imports
- frontend may call the wrong path
- planner may create inconsistent tasks

Interview answer:

> `architectStep1` creates the entity and naming foundation. Without it, later nodes may use inconsistent names for the same resource, which creates integration bugs.

#### Node 4: `architectStep2`

##### What this node does

`architectStep2` designs the database schema.

It uses the entity map from step 1 and creates:

- database type
- tables
- fields
- field types
- constraints
- foreign keys
- indexes

It also receives previous validation issues if the blueprint validator found schema problems.

##### Why this node was added

The database is the foundation of a full-stack app. Backend models, controllers, API responses, and frontend forms depend on it.

Separating DB design into its own node makes the schema more deliberate.

##### What happens if this node is removed

Without this node:

- code may be generated without a clear data model
- fields may be invented differently in each file
- foreign keys may be missing or wrong
- backend APIs may not know what data they are storing

Interview answer:

> I added a separate database architecture node because the DB schema is the backbone of the generated app. If the schema is weak, every backend and frontend task becomes unstable.

#### Node 5: `architectStep3`

##### What this node does

`architectStep3` designs the REST API endpoints.

It maps business features and database tables into endpoints such as:

```text
GET /api/todo-items
POST /api/todo-items
PUT /api/todo-items/:id
DELETE /api/todo-items/:id
```

Each endpoint can include:

- method
- path
- purpose
- related table
- auth requirement
- request body
- response shape

##### Why this node was added

This node creates the contract between frontend and backend.

The frontend needs to know which APIs exist. The backend needs to know which routes/controllers/models to create.

##### What happens if this node is removed

Without this node:

- frontend pages may call non-existing endpoints
- backend routes may not cover required features
- auth requirements may be unclear
- integration becomes guesswork

Interview answer:

> `architectStep3` defines the API contract. Without it, the frontend and backend can easily drift apart.

#### Node 6: `architectStep4`

##### What this node does

`architectStep4` designs the frontend pages and components.

It creates:

- page names
- frontend routes
- page descriptions
- auth requirements
- components
- API calls used by each component

Example:

```text
DashboardPage
  route: /dashboard
  components: TodoList, TodoForm
  apiCalls: /api/todo-items
```

##### Why this node was added

This node makes sure the frontend is designed from the user experience, not just from database tables.

It connects UI screens to the API contract.

##### What happens if this node is removed

Without this node:

- the project may have backend APIs but no useful UI
- frontend pages may be missing
- routes may be random
- API calls may not match the backend

Interview answer:

> I added `architectStep4` so the system plans the user interface before coding. It prevents the generated app from becoming backend-only or having pages that do not match the APIs.

#### Node 7: `architectStep5`

##### What this node does

`architectStep5` creates the folder structure and dependency plan.

It decides things like:

- backend folders
- frontend folders
- backend dependencies
- frontend dependencies
- dev dependencies

Example backend dependencies:

- express
- cors
- dotenv
- pg or mongoose
- bcryptjs
- jsonwebtoken
- uuid

Example frontend dependencies:

- react
- react-dom
- react-router-dom
- axios
- vite
- tailwindcss

##### Why this node was added

The coder needs a predictable project structure and package plan.

If dependencies are not planned, generated files may import packages that are not installed.

##### What happens if this node is removed

Without this node:

- missing dependencies become common
- folder paths may be inconsistent
- generated files may be placed in random locations
- deployment may fail because package files are incomplete

Interview answer:

> `architectStep5` turns the design into a concrete filesystem and dependency plan. Without it, code generation would have no stable project skeleton.

#### Node 8: `blueprintValidator`

##### What this node does

`blueprintValidator` checks whether the architecture blueprint is internally consistent.

It validates:

- every entity has a matching DB table
- foreign keys reference existing tables
- API endpoints reference valid tables
- frontend API calls match real API endpoints
- auth-required APIs are not used by pages marked public
- tables are not orphaned without APIs

If it finds serious issues, it routes back to the correct architect step:

- schema issue -> `architectStep2`
- API issue -> `architectStep3`
- frontend page issue -> `architectStep4`

It also has a repair retry limit so the workflow does not loop forever.

##### Why this node was added

This is a design QA gate.

LLMs can produce architecture that looks good in English but has hidden contradictions.

Example:

```text
Entity: TodoItem
DB table: tasks
API relatedTable: todos
Frontend calls: /api/todo-items
```

Each part looks reasonable alone, but together they are inconsistent.

##### What happens if this node is removed

Without this node:

- bad architecture reaches the planner
- planner creates tasks from inconsistent design
- coder generates files that do not connect
- errors appear much later during execution or deployment

Interview answer:

> `blueprintValidator` catches architecture-level mistakes before coding starts. It is cheaper to fix a bad blueprint than to debug many generated files later.

#### Node 9: `plannerAgent`

##### What this node does

`plannerAgent` converts the validated blueprint into a task queue.

It creates phases in a fixed order:

1. setup
2. models
3. middleware
4. backend
5. frontend
6. integration
7. deployment

Each task includes:

- task id
- title
- description
- files to create
- files needed
- acceptance criteria
- parallelization hint
- estimated tokens

##### Why this node was added

This node turns architecture into an executable plan.

The LLM should not be asked to generate a full app in one giant response. That usually causes missing files, broken imports, and incomplete logic.

##### What happens if this node is removed

Without this node:

- there is no ordered build process
- coder does not know what to build next
- dependencies may be created after files that import them
- tasks become too large for reliable generation

Interview answer:

> `plannerAgent` breaks the project into small ordered tasks. Without it, code generation becomes a giant uncontrolled prompt and reliability drops.

#### Node 10: `setupSandbox`

##### What this node does

`setupSandbox` creates the isolated generated-project workspace.

It:

- creates the sandbox folder
- scaffolds backend/frontend structure
- prepares Docker metadata
- creates basic config files
- seeds the file registry with known scaffold files
- records preview frontend/backend URLs and ports if available

It also adds scaffold files to `fileRegistry`, such as:

- `backend/src/config/db.js`
- `backend/src/middleware/auth.js`
- `backend/src/index.js`
- `frontend/src/utils/api.js`
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`

##### Why this node was added

Generated code should not be written into the main project.

The sandbox gives the AI a controlled place to create, run, break, debug, and package generated apps.

##### What happens if this node is removed

Without this node:

- generated files have nowhere safe to go
- the AI could overwrite the main project
- Docker preview cannot be managed cleanly
- code execution becomes unsafe and disorganized

Interview answer:

> `setupSandbox` creates an isolated workspace for generated code. Without it, we cannot safely run, test, preview, or package the app.

#### Node 11: `sandboxHealthCheck`

##### What this node does

`sandboxHealthCheck` verifies that the sandbox is usable.

It checks:

- sandbox path exists
- scaffold files exist
- Docker/container readiness where available
- local fallback mode if Docker is limited

It updates:

- `sandboxHealthy`
- `fileTree`
- `currentPhase`

If the sandbox is unhealthy, it retries setup until the retry limit is reached. After the retry limit, it marks the workflow as failed.

##### Why this node was added

Before writing code, the system must know the workspace exists and is usable.

This is like checking that your development environment is ready before coding.

##### What happens if this node is removed

Without this node:

- the coder may write into a broken or missing directory
- later nodes fail with confusing file errors
- sandbox setup problems are discovered too late

Interview answer:

> `sandboxHealthCheck` is an environment gate. It prevents the workflow from coding into a broken workspace.

#### Node 12: `selectNextTask`

##### What this node does

`selectNextTask` is the scheduler.

It looks at `taskQueue` and `taskStatuses`, then selects the next pending task.

It also detects when a phase is complete and creates a special phase verification task.

Possible outcomes:

- if a normal task exists -> go to `contextBuilder`
- if phase is complete -> go to `phaseVerification`
- if all tasks are done -> go to `deploymentVerifier`

##### Why this node was added

The workflow needs a central controller for task progress.

The planner creates the list, but `selectNextTask` decides what should run now.

##### What happens if this node is removed

Without this node:

- the system has no task scheduler
- it cannot track completed vs pending tasks
- phase verification may never run
- the workflow cannot know when to deploy

Interview answer:

> `selectNextTask` acts like the task manager. It keeps the build moving task by task and knows when a phase or whole project is complete.

#### Node 13: `contextBuilder`

##### What this node does

`contextBuilder` prepares the information the coder needs for the current task.

It builds `contextPackage`, including:

- current task details
- acceptance criteria
- files to create
- project patterns
- dependency interfaces
- naming map
- relevant DB schema
- relevant API endpoints
- template file examples
- app name
- auth requirement

It automatically includes useful dependency context:

- model/controller/config/middleware files for backend tasks
- controllers for route tasks
- API utility/context/hooks for frontend tasks
- all relevant files for integration tasks

It can also read files from the sandbox and infer exports/imports if registry data is missing.

##### Why this node was added

LLMs make mistakes when they lack context.

For example, a coder may import:

```js
import User from '../models/User'
```

when the actual file exports:

```js
export async function findUserByEmail(...)
```

`contextBuilder` reduces that risk by giving exact dependency interfaces and naming rules.

##### What happens if this node is removed

Without this node:

- coder guesses imports
- coder guesses field names
- coder guesses API paths
- generated files do not connect well
- review/execution failures increase

Interview answer:

> `contextBuilder` gives the coder only the relevant context for the current task. Without it, every coding step becomes a blind generation step.

#### Node 14: `coderAgent`

##### What this node does

`coderAgent` writes the actual generated files.

It uses different prompts for:

- backend files
- frontend files

Backend rules include:

- ES modules only
- parameterized SQL
- layered backend structure
- routes are thin
- controllers contain request handlers
- models contain DB functions
- consistent response format
- JWT bearer auth pattern

Frontend rules include:

- React functional components
- hooks
- controlled forms
- loading/error states
- Tailwind dark design system
- Vite env style
- API utility usage

It writes one file at a time into the sandbox.

On retry, it includes:

- reviewer issues
- executor errors
- current file content

It updates:

- `coderOutput`
- `fileTree`
- token usage
- terminal logs

##### Why this node was added

This is the actual code generation step.

It is separated from planning, reviewing, and execution so that each responsibility remains clear.

##### What happens if this node is removed

Without this node:

- no generated source files are created
- the workflow remains only a planning system

Interview answer:

> `coderAgent` is the implementation node. It writes code into the sandbox using the current task and context. It is separate from reviewer and executor so generated code is checked before being accepted.

#### Node 15: `updateRegistry`

##### What this node does

`updateRegistry` reads the files written by the coder and extracts their public interface.

It records:

- file path
- default export
- named exports
- import statement
- interface description
- updated timestamp

This information is merged into `fileRegistry`.

##### Why this node was added

Future tasks need to know how to import files created by earlier tasks.

Example:

If a model exports:

```js
export async function createTodo(...)
```

then a controller should import:

```js
import { createTodo } from '../models/todoItem.js'
```

The registry makes this possible.

##### What happens if this node is removed

Without this node:

- future coder tasks guess imports
- named/default export mismatches become common
- frontend/backend integration breaks
- contextBuilder has less useful dependency information

Interview answer:

> `updateRegistry` creates memory of generated files. Without it, each coding step forgets what previous files exported.

#### Node 16: `reviewerAgent`

##### What this node does

`reviewerAgent` reviews the generated code before execution.

It checks:

- imports
- exports
- async/await
- error response format
- auth pattern
- request/response fields
- env variable usage
- middleware order
- model return style
- security
- backend layering
- acceptance criteria

It also has deterministic checks for common backend layering violations, such as:

- route files importing models directly
- route files containing SQL queries
- route files using bcrypt/JWT logic directly
- controllers creating routers
- models using `req` or `res`
- importing native `bcrypt` when package uses `bcryptjs`

Routing:

- approved -> `executorAgent`
- rejected -> `contextBuilder`
- too many rejections -> `simplifyTask`

##### Why this node was added

This is a quality gate before running code.

Some mistakes are easier to catch by reading code than by executing it.

##### What happens if this node is removed

Without this node:

- bad code goes directly to execution
- style/layering/security mistakes may survive
- executor becomes overloaded
- debugging becomes slower because every issue becomes a runtime issue

Interview answer:

> `reviewerAgent` is the code quality gate. It catches logical, structural, and security issues before execution. Without it, we rely only on runtime failures, which is too late for many design mistakes.

#### Node 17: `executorAgent`

##### What this node does

`executorAgent` performs objective checks on the generated files.

It verifies:

- files were actually written
- JavaScript syntax is valid
- relative imports resolve to real files
- named imports exist in the registry
- frontend does not use `process.env`
- backend does not use `import.meta.env`
- npm install can run for affected backend/frontend areas

It stores:

- pass/fail result
- command output
- errors

Routing:

- pass -> `snapshotManager`
- fail -> `debuggerAgent`

##### Why this node was added

LLM review is useful, but execution gives objective proof.

This node answers:

```text
Does the file exist?
Does it parse?
Do imports resolve?
Can dependencies install?
```

##### What happens if this node is removed

Without this node:

- syntax errors may not be caught
- missing imports may not be caught
- env mistakes may not be caught
- the project may look complete but fail when run

Interview answer:

> `executorAgent` gives objective validation. Reviewer checks code semantically, but executor checks whether it actually exists, parses, imports correctly, and can run basic install checks.

#### Node 18: `snapshotManager`

##### What this node does

`snapshotManager` runs after a task passes execution.

It:

- marks the task as done
- creates a Git snapshot
- resets review state
- resets execution state
- resets debug state
- clears current task
- clears temporary coder/context data

##### Why this node was added

The workflow needs stable checkpoints after successful tasks.

If a future task breaks the app, the debugger can roll back to a known-good snapshot.

##### What happens if this node is removed

Without this node:

- no reliable recovery point exists
- task statuses may not be marked done
- debugger rollback becomes difficult
- stale errors/context can pollute future tasks

Interview answer:

> `snapshotManager` saves progress after each successful task. It gives the system recovery points and keeps state clean for the next task.

#### Node 19: `debuggerAgent`

##### What this node does

`debuggerAgent` runs when execution or deployment fails.

It:

- reads the error message
- reads failing files
- optionally reads related files
- asks the LLM for root cause and fix
- writes the fix as review feedback
- sends the workflow back to `contextBuilder`

It has tiers and retry limits.

If retries are exhausted, it tries to roll back to the last good Git snapshot. If rollback is not enough, it escalates to human input.

##### Why this node was added

Generated code will fail sometimes. The project needs an automatic repair loop.

The debugger turns raw errors into actionable instructions for the coder.

##### What happens if this node is removed

Without this node:

- any execution failure stops the workflow
- coder gets no root-cause guidance
- repeated failures are harder to recover from
- human intervention is needed much earlier

Interview answer:

> `debuggerAgent` makes the workflow self-healing. It translates execution errors into specific fixes and retries the task instead of failing immediately.

#### Node 20: `simplifyTask`

##### What this node does

`simplifyTask` runs when a task keeps getting rejected or is too complex.

It asks the LLM to split one failed task into 2-3 smaller sub-tasks.

Then it inserts those sub-tasks into the task queue after the original task.

##### Why this node was added

LLMs perform better on smaller tasks.

If a task says:

```text
Build the entire dashboard with auth, CRUD, filtering, and analytics.
```

that may be too large. It is better to split it into:

```text
Build auth context.
Build dashboard layout.
Build CRUD list.
Build filter controls.
```

##### What happens if this node is removed

Without this node:

- hard tasks keep failing
- reviewer/coder loops may repeat
- the system has no way to reduce complexity

Interview answer:

> `simplifyTask` is a recovery strategy for oversized tasks. Without it, the workflow may keep retrying a task that is too large for reliable generation.

#### Node 21: `humanEscalation`

##### What this node does

`humanEscalation` runs when automated debugging reaches its limit.

It asks the user what to do.

The user can choose:

- guide: provide advice and retry
- simplify: split the task
- skip: mark the task done and continue

It records the decision in `userFeedback`.

##### Why this node was added

Some issues require human judgment.

For example:

- the requirement is unclear
- the generated feature is too hard
- the user prefers skipping a feature
- the user knows the correct business logic

##### What happens if this node is removed

Without this node:

- the workflow may fail permanently after debug retries
- the user cannot guide the system
- the system cannot ask whether to simplify or skip

Interview answer:

> `humanEscalation` is the escape hatch. It prevents the workflow from getting stuck when automatic debugging cannot confidently fix the issue.

#### Node 22: `phaseVerification`

##### What this node does

`phaseVerification` runs after all tasks in a phase are done.

It checks whether each file expected by that phase exists in `fileTree`.

It marks:

- `phase-N-verified = done`
- or `phase-N-verified = failed`

It also assembles entrypoints at phase boundaries:

- backend phase -> assemble `backend/src/index.js`
- frontend phase -> assemble `frontend/src/App.jsx`
- integration/deploy phase -> assemble both

##### Why this node was added

Completing individual tasks is not enough. The workflow also needs phase-level checks.

A backend phase is only useful if the backend entrypoint imports and mounts the routes. A frontend phase is only useful if pages are connected to routes.

##### What happens if this node is removed

Without this node:

- missing files may go unnoticed
- generated pages/routes may exist but not be reachable
- phase completion becomes unreliable

Interview answer:

> `phaseVerification` checks that a whole phase is complete, not just one task. It also wires backend and frontend entrypoints so generated files become reachable.

#### Supporting Helper: `assembleEntryPoints`

##### What this helper does

This is not directly added as a LangGraph node, but `phaseVerification` uses it.

It assembles:

- backend route imports and `app.use(...)` mounts in `backend/src/index.js`
- frontend page imports and `<Route />` entries in `frontend/src/App.jsx`

##### Why this helper was added

The coder creates route/page files task by task. But those files must be connected to the app entrypoint.

This helper handles that wiring deterministically.

##### What happens if this helper is removed

Without it:

- routes may exist but never be mounted
- pages may exist but never be reachable
- the final app may build but appear empty or broken

Interview answer:

> `assembleEntryPoints` ensures generated files are actually wired into the app. Without it, files can exist on disk but not be reachable at runtime.

#### Node 23: `patternExtractor`

##### What this node does

`patternExtractor` reads existing generated code files and extracts project coding patterns.

It updates `projectPatterns`, including:

- error handling style
- response format
- auth pattern
- import style
- env variable style
- model return style
- middleware order
- naming convention
- async pattern
- frontend API pattern

##### Why this node was added

Generated code should become more consistent over time.

Once the project has a style, later files should follow it.

##### What happens if this node is removed

Without this node:

- each new file may use a different style
- response formats may vary
- imports may become inconsistent
- later tasks do not learn from earlier code

Interview answer:

> `patternExtractor` helps the workflow learn the style of the generated project. Without it, every new file may look like it came from a different developer.

#### Node 24: `stateCompactor`

##### What this node does

`stateCompactor` reduces the size of the workflow state.

It:

- replaces completed task details with compact summaries
- keeps only the last 100 terminal output lines
- preserves unfinished task details

##### Why this node was added

Agent workflows can accumulate large state.

If the state becomes too large:

- LLM prompts become expensive
- context becomes noisy
- performance gets worse
- token budget can be wasted

##### What happens if this node is removed

Without this node:

- state keeps growing
- later prompts may become too large
- cost increases
- useful context gets buried under old details

Interview answer:

> `stateCompactor` controls context size. It keeps important state while trimming completed details, which helps token cost and workflow stability.

#### Node 25: `deploymentVerifier`

##### What this node does

`deploymentVerifier` checks whether the generated app can be packaged and run.

It:

- detects backend entrypoint
- detects database type
- generates backend Dockerfile
- generates frontend Dockerfile
- generates nginx config
- generates `docker-compose.yml`
- creates env files if missing
- builds Docker services
- starts services
- checks backend endpoint
- checks frontend endpoint
- checks database readiness

If deployment verification fails, it routes to `debuggerAgent` unless max deployment repair attempts are reached.

##### Why this node was added

A generated project is not truly complete just because files exist.

The final test is:

```text
Can it build and run as an app?
```

##### What happens if this node is removed

Without this node:

- the system may claim success even if Docker build fails
- frontend may not load
- backend may not start
- database may not connect
- final delivery is less trustworthy

Interview answer:

> `deploymentVerifier` is the final proof step. It checks whether the generated project can actually be built and served, not just written to disk.

#### Node 26: `presentToUser`

##### What this node does

`presentToUser` prepares the final result for the dashboard.

If the workflow failed, it logs the failure reason.

If the workflow succeeded, it:

- marks `currentPhase` as `done`
- starts sandbox servers
- records preview frontend URL
- records preview backend URL
- logs final access information

##### Why this node was added

The user needs a clean final state.

This node turns internal workflow output into something the dashboard can show:

- preview link
- backend API link
- final logs
- completed status

##### What happens if this node is removed

Without this node:

- the workflow may finish but not expose preview links
- the dashboard may not know the final state
- the user experience feels incomplete

Interview answer:

> `presentToUser` is the handoff node. It converts the internal workflow result into a final dashboard-ready result for the user.

#### Why So Many Nodes Instead Of One Big Agent?

The interviewer may ask this.

The answer:

> One big agent would be simpler to code but harder to control. This project uses many nodes because each node owns one responsibility and one failure mode. That makes the workflow easier to debug, retry, test, and explain.

One big agent would have to:

- clarify requirements
- design DB
- design APIs
- design UI
- create tasks
- write all files
- review itself
- run checks
- debug errors
- deploy

That is too much for one prompt.

With nodes:

- PM mistakes are caught before architecture.
- Architecture mistakes are caught before planning.
- Planning mistakes are isolated before coding.
- Code mistakes are caught by reviewer/executor.
- Runtime mistakes go to debugger.
- Repeated failures go to simplification or human escalation.
- Final app readiness is checked by deployment verifier.

#### Best Interview Summary

If the interviewer asks, "Why did you add these nodes?", say:

> I designed the workflow like an automated development team. Each node represents a real software engineering role or checkpoint. The PM clarifies the requirement, architect nodes design the system, validator checks consistency, planner creates small tasks, coder writes code, registry records interfaces, reviewer checks quality, executor runs objective checks, debugger fixes failures, snapshot manager saves good states, phase verifier checks phase completion, pattern extractor keeps style consistent, state compactor controls context growth, deployment verifier proves the app can run, and presenter returns the result to the user.
>
> The reason for this design is reliability. A single LLM call can generate code, but it is hard to trust. This workflow adds planning, validation, review, execution, retries, rollback, and human escalation so the generated project is more controlled and explainable.

</details>

<details id="inline-05-project-call-flow-and-sandbox-lifecycle">
<summary>05_project_call_flow_and_sandbox_lifecycle.md - Question 5: How Does Each Part Call The Other, And How Is The Sandbox/Docker Lifecycle Managed?</summary>

### Question 5: How Does Each Part Call The Other, And How Is The Sandbox/Docker Lifecycle Managed?

#### Short Interview Answer

The project works as a chain of calls:

```text
React frontend
  -> Node/Express gateway
  -> Python FastAPI orchestrator
  -> LangGraph workflow
  -> workflow nodes
  -> sandbox service
  -> Docker containers and sandbox files
```

The frontend never directly calls the orchestrator. It calls the gateway. The gateway validates the user, stores project metadata, and then calls FastAPI using HTTP JSON. FastAPI creates an async task for the LangGraph workflow. LangGraph runs node by node. Nodes call services such as Gemini, Redis checkpointing, event bus, and sandbox utilities. The sandbox utilities create folders, write files, start Docker containers, install dependencies, run checks, stop/restart containers, and expose preview URLs.

#### Big Picture Call Chain

```mermaid
sequenceDiagram
  participant U as User
  participant F as React Frontend
  participant G as Node Gateway
  participant O as FastAPI Orchestrator
  participant LG as LangGraph
  participant N as Workflow Nodes
  participant S as Sandbox Service
  participant D as Docker
  participant DB as Project Store

  U->>F: Click Build
  F->>G: POST /api/projects
  G->>G: Authenticate user and check active project
  G->>O: POST /runs
  O->>O: Create project_id
  O->>LG: asyncio.create_task(run_workflow)
  LG->>N: Execute graph nodes
  N->>S: create_sandbox / write_file / execute_command
  S->>D: docker run / docker exec / docker rm
  O-->>G: Return project_id + running
  G->>DB: Save project metadata
  G-->>F: Return project created
```

#### 1. How The Frontend Calls The Gateway

The frontend is in `frontend/`.

The common helper is:

```js
gatewayJson(path, options)
```

It is defined in `frontend/src/api/gateway.js`.

It builds requests like:

```text
http://localhost:3000 + /api/projects
```

It also sends cookies with:

```js
credentials: "include"
```

That matters because the gateway uses cookie-based auth.

##### Important frontend calls

| User action | Frontend call | Gateway endpoint |
| --- | --- | --- |
| Check login | `gatewayJson("/api/auth/check")` | `GET /api/auth/check` |
| Load project list | `gatewayJson("/api/projects")` | `GET /api/projects` |
| Start build | `gatewayJson("/api/projects", { method: "POST" })` | `POST /api/projects` |
| Stream events | `new EventSource(...)` | `GET /api/projects/:id/events` |
| Submit human input | `gatewayJson("/api/projects/:id/input")` | `POST /api/projects/:id/input` |
| Cancel project | `gatewayJson("/api/projects/:id/cancel")` | `POST /api/projects/:id/cancel` |
| Stop preview | `gatewayJson("/api/projects/:id/preview/stop")` | `POST /api/projects/:id/preview/stop` |
| Restart preview | `gatewayJson("/api/projects/:id/preview/restart")` | `POST /api/projects/:id/preview/restart` |
| Download code | `window.open("/api/projects/:id/download")` | `GET /api/projects/:id/download` |

##### What happens when user clicks Build

In `frontend/src/App.jsx`, `startProject()` sends:

```js
POST /api/projects
{
  requirement: requirement.trim(),
  user_id: user.user_id,
  token_budget_usd: 2.0
}
```

The frontend then waits for the gateway to return:

```json
{
  "project_id": "...",
  "status": "running",
  "project": {}
}
```

After that, the frontend opens an event stream.

#### 2. How The Gateway Receives The Frontend Request

The gateway is in `gateway/`.

The main server is `gateway/src/index.js`.

It sets up:

- Express
- CORS
- JSON parsing
- cookies
- auth routes
- project routes
- WebSocket event relay

Important route mounting:

```js
app.use("/api/auth", authRouter);
app.use("/api/projects", requireAuth, projectsRouter);
```

That means project APIs are protected by `requireAuth`.

#### 3. How The Gateway Calls The Orchestrator

The gateway calls the orchestrator through `gateway/src/services/orchestratorClient.js`.

The orchestrator base URL comes from:

```js
process.env.ORCHESTRATOR_URL || "http://localhost:8000"
```

##### Gateway-to-orchestrator API map

| Gateway function | FastAPI endpoint called | Purpose |
| --- | --- | --- |
| `getOrchestratorHealth()` | `GET /health` | Check Python orchestrator health |
| `createProjectRun(payload)` | `POST /runs` | Start a new LangGraph run |
| `streamProjectEvents(projectId, onEvent)` | `GET /runs/:projectId/events` | Read orchestrator SSE events |
| `cancelProjectRun(projectId)` | `POST /runs/:projectId/cancel` | Cancel async workflow and stop sandbox containers |
| `submitProjectInput(projectId, payload)` | `POST /runs/:projectId/input` | Send human clarification/escalation answer |
| `stopProjectPreview(projectId, sandboxId)` | `POST /runs/:projectId/preview/stop` | Stop preview containers |
| `restartProjectPreview(projectId, sandboxId, options)` | `POST /runs/:projectId/preview/restart` | Recreate/restart preview containers |

##### Project creation flow inside gateway

When frontend calls:

```text
POST /api/projects
```

the gateway route in `gateway/src/routes/projects.js` does this:

1. Validates that `requirement` exists.
2. Builds payload:

   ```js
   {
     requirement,
     user_id,
     token_budget_usd
   }
   ```

3. Checks whether the user already has a running or queued project.
4. Stops old active previews for that user.
5. Calls FastAPI:

   ```js
   createProjectRun(payload)
   ```

6. Saves project metadata in project store.
7. Returns project info to the frontend.

#### 4. How FastAPI Starts The Orchestrator Run

The orchestrator is in `orchestrator/`.

The main FastAPI file is:

```text
orchestrator/app/main.py
```

The important endpoint is:

```python
@app.post("/runs")
async def create_run(payload: RunCreateRequest)
```

It does:

1. Creates a project id:

   ```python
   project_id = f"project-{uuid.uuid4().hex[:12]}"
   ```

2. Emits a `run.created` event.

3. Starts the workflow in the background:

   ```python
   task = asyncio.create_task(run_workflow(project_id, payload))
   ```

4. Registers the task:

   ```python
   register_run(project_id, task)
   ```

5. Returns immediately:

   ```json
   {
     "project_id": "...",
     "status": "running"
   }
   ```

This is important because the HTTP request does not wait until the whole AI build finishes. It returns quickly, and progress comes through events.

#### 5. How FastAPI Calls LangGraph

FastAPI does not manually call every node.

It calls:

```python
run_workflow(project_id, payload)
```

Inside `orchestrator/app/graph/workflow.py`, `run_workflow()` does:

```python
graph = build_graph()
state = AgentState(...)
final_state = await graph.ainvoke(state, {"recursion_limit": 500})
```

So the chain is:

```text
FastAPI /runs
  -> asyncio.create_task(run_workflow)
  -> build_graph()
  -> StateGraph(AgentState)
  -> graph.add_node(...)
  -> graph.add_edge(...)
  -> graph.compile()
  -> graph.ainvoke(initial_state)
```

LangGraph then decides which node to run next based on normal edges and conditional routers.

#### 6. How LangGraph Calls Nodes

In `build_graph()`, every node is registered like this:

```python
graph.add_node("pmAgent", _node("pmAgent", pmAgentNode))
```

The `_node(...)` helper wraps the actual node function.

The wrapper:

1. Converts dict state into `AgentState` if needed.
2. Emits `node.started`.
3. Calls the node function.
4. Saves Redis checkpoint.
5. Emits `node.completed`.
6. Returns the updated state.

That means each node does not need to manually stream its own start/end event. The graph wrapper handles that consistently.

#### 7. How Events Flow Back To The Browser

Events are created inside the orchestrator event bus.

##### Event append

Nodes and FastAPI call:

```python
append_event(project_id, StreamEvent(...))
```

The event bus stores events in memory and wakes any stream listeners.

##### FastAPI stream

FastAPI exposes:

```text
GET /runs/:projectId/events
```

It returns:

```python
StreamingResponse(..., media_type="text/event-stream")
```

Each event is sent as:

```text
data: {"type": "...", "node": "...", "message": "...", "state": {...}}
```

##### Gateway relay

The frontend does not call this FastAPI stream directly.

The frontend calls:

```text
GET /api/projects/:projectId/events
```

The gateway then calls:

```text
GET /runs/:projectId/events
```

For every event, the gateway:

1. Parses the SSE chunk.
2. Calls `updateProjectFromEvent(projectId, event)`.
3. Writes the same event to the browser SSE stream.

```mermaid
sequenceDiagram
  participant Node as LangGraph Node
  participant Bus as Event Bus
  participant API as FastAPI SSE
  participant Gateway as Node Gateway
  participant Store as Project Store
  participant UI as React EventSource

  Node->>Bus: append_event(projectId, StreamEvent)
  Bus-->>API: stream_events(projectId)
  API-->>Gateway: data: JSON event
  Gateway->>Store: updateProjectFromEvent
  Gateway-->>UI: data: JSON event
  UI->>UI: update pipeline, terminal, fileTree, preview
```

#### 8. How Human Input Flows

Some nodes call:

```python
wait_for_input(project_id, input_type, payload)
```

This happens in:

- `humanInput`
- `humanEscalation`

The input bridge:

1. Creates an async Future.
2. Stores it in `_pending[(project_id, input_type)]`.
3. Emits `input.requested`.
4. Waits until frontend sends a response.

The frontend sees `input.requested` and shows a form.

Then frontend sends:

```text
POST /api/projects/:projectId/input
```

Gateway forwards it to:

```text
POST /runs/:projectId/input
```

FastAPI calls:

```python
submit_input(project_id, payload.type, response)
```

That resolves the pending Future, and the paused node continues.

#### 9. How Cancel Works

Frontend calls:

```text
POST /api/projects/:projectId/cancel
```

Gateway calls:

```text
POST /runs/:projectId/cancel
```

FastAPI does two things:

1. Cancels the async LangGraph task:

   ```python
   cancel_run(project_id)
   ```

2. Stops sandbox containers:

   ```python
   stop_sandbox_containers(project_id)
   ```

The run manager stores active tasks in:

```python
_running_tasks: dict[str, asyncio.Task]
```

When cancelled, the graph catches `asyncio.CancelledError`, marks the state as cancelled, and emits:

```text
run.cancelled
```

Important distinction:

> Cancel stops the active workflow task and stops containers. It does not necessarily delete the sandbox folder from disk.

#### 10. How The Sandbox Is Created

The sandbox is created by the `setupSandbox` node.

The node calls:

```python
create_sandbox(
  state.projectId,
  state.userId,
  state.blueprint.get("folderStructure", ""),
  state.blueprint.get("dependencies", {}),
  state.blueprint.get("dbSchema", {}),
)
```

The implementation is in:

```text
orchestrator/app/services/sandbox_runtime.py
```

##### Sandbox creation step by step

`create_sandbox()` does:

1. Creates a sandbox id:

   ```python
   sandbox_id = f"sandbox-{int(time.time() * 1000)}"
   ```

2. Computes sandbox path:

   ```text
   SANDBOX_ROOT / sandbox-<timestamp>
   ```

3. Computes Docker mount path:

   ```text
   HOST_SANDBOX_ROOT / sandbox-<timestamp>
   ```

   This matters because Docker needs a host path it can mount.

4. Creates the sandbox folder.

5. Creates folder structure from the blueprint if provided.

6. Detects DB type:

   - if backend dependencies include `mongoose` -> MongoDB
   - otherwise -> PostgreSQL

7. Builds Docker/container names:

   ```text
   aidev-db-sandbox-...
   aidev-backend-sandbox-...
   aidev-frontend-sandbox-...
   aidev-dbdata-sandbox-...
   ```

8. Calls `_scaffold(...)` to generate base files.

9. Initializes Git:

   ```text
   git init
   git config user.email
   git config user.name
   git add -A
   git commit -m "Initial scaffold"
   git tag v0.0.0
   ```

10. Saves sandbox info in memory:

   ```python
   _sandboxes[sandbox_id] = info
   _sandboxes[project_id] = info
   ```

11. If Docker is available:

   - stops existing active preview for the user
   - ensures Docker network exists
   - allocates backend/frontend host ports
   - starts DB container
   - starts backend container
   - installs backend dependencies
   - starts frontend container
   - installs frontend dependencies
   - records active preview for user
   - schedules auto-stop

#### 11. What Files The Sandbox Scaffolds

The scaffold is created in:

```text
orchestrator/app/services/sandbox_scaffold.py
```

It creates:

```text
sandbox/sandbox-<id>/
  backend/
    package.json
    .env
    src/
      index.js
      config/db.js
      middleware/auth.js
      models/
      routes/
      utils/
  frontend/
    package.json
    .env
    index.html
    src/
      main.jsx
      App.jsx
      index.css
      pages/
      components/
      hooks/
      context/
      utils/api.js
    vite.config.js
    tailwind.config.js
    postcss.config.js
  .gitignore
```

The scaffold gives the coder a ready project skeleton.

#### 12. How Docker Containers Are Set Up

The orchestrator container has Docker access because `docker-compose.yml` mounts:

```yaml
/var/run/docker.sock:/var/run/docker.sock
```

That means the orchestrator can call Docker commands from inside the orchestrator service.

The main Docker network is:

```text
aidev-network
```

It is created if missing:

```python
docker network create aidev-network
```

##### DB container

If MongoDB:

```text
docker run -d
  --name aidev-db-<sandbox_id>
  --network aidev-network
  -v aidev-dbdata-<sandbox_id>:/data/db
  -e MONGO_INITDB_DATABASE=appdb
  mongo:7
```

If PostgreSQL:

```text
docker run -d
  --name aidev-db-<sandbox_id>
  --network aidev-network
  -v aidev-dbdata-<sandbox_id>:/var/lib/postgresql/data
  -e POSTGRES_USER=postgres
  -e POSTGRES_PASSWORD=postgres
  -e POSTGRES_DB=appdb
  postgres:16-alpine
```

Then it waits for DB readiness:

- PostgreSQL: `pg_isready -U postgres`
- MongoDB: `mongosh --eval 'db.runCommand({ping:1})' --quiet`

If the blueprint has table schema, PostgreSQL tables can be created from generated SQL.

##### Backend container

The backend container uses `node:20-slim`.

It is started with:

```text
docker run -d
  --name aidev-backend-<sandbox_id>
  --network aidev-network
  -p 127.0.0.1:<backend_host_port>:5000
  -v <sandbox_mount_path>:/app
  -w /app
  -e DATABASE_URL=...
  -e JWT_SECRET=...
  -e PORT=5000
  -e NODE_ENV=development
  node:20-slim
  tail -f /dev/null
```

Notice that the container initially runs:

```text
tail -f /dev/null
```

That keeps the container alive. Later, the system uses `docker exec` to install dependencies and start the actual server.

Then it runs:

```text
cd /app/backend && npm install
```

##### Frontend container

The frontend container also uses `node:20-slim`.

It is started with:

```text
docker run -d
  --name aidev-frontend-<sandbox_id>
  --network aidev-network
  -p 127.0.0.1:<frontend_host_port>:5173
  -v <sandbox_mount_path>:/app
  -w /app
  -e VITE_API_URL=http://localhost:<backend_host_port>/api
  -e VITE_API_PROXY_TARGET=http://aidev-backend-<sandbox_id>:5000
  node:20-slim
  tail -f /dev/null
```

Then it runs:

```text
cd /app/frontend && npm install
```

#### 13. How Preview Ports Are Allocated

Port settings come from `sandbox_state.py`:

```text
SANDBOX_BACKEND_HOST_PORT=15000
SANDBOX_FRONTEND_HOST_PORT=15173
SANDBOX_PREVIEW_PORT_POOL_SIZE=100
SANDBOX_PREVIEW_BIND_HOST=127.0.0.1
SANDBOX_PREVIEW_TTL_SECONDS=300
```

The allocator checks pairs:

```text
backend: 15000, frontend: 15173
backend: 15001, frontend: 15174
backend: 15002, frontend: 15175
...
```

It checks:

- whether the host port is free
- whether Docker already published the port

Then it assigns the first available pair.

#### 14. How The Generated App Servers Are Started

Containers are created during sandbox setup, but the actual dev servers are started by:

```python
start_sandbox_servers(sandbox_id)
```

This happens in `presentToUser`, and also during preview restart.

For backend, it runs inside the backend container:

```text
cd /app/backend && nohup npm start > /tmp/aidev-backend.log 2>&1 &
```

For frontend, it runs inside the frontend container:

```text
cd /app/frontend && nohup npm run dev -- --host 0.0.0.0 --port 5173 --strictPort > /tmp/aidev-frontend.log 2>&1 &
```

It first checks whether the service is already responding. If not, it kills old processes and starts again.

Then it returns:

```json
{
  "started": true,
  "frontendUrl": "http://localhost:15173",
  "backendUrl": "http://localhost:15000"
}
```

#### 15. How Files Are Written And Commands Are Run

Workflow nodes call sandbox helpers:

| Helper | What it does |
| --- | --- |
| `write_file(sandbox_id, path, content)` | Writes generated source file into sandbox folder |
| `read_file(sandbox_id, path)` | Reads a file from sandbox |
| `get_file_list(sandbox_id)` | Lists sandbox files, excluding `.git` and `node_modules` |
| `execute_command(sandbox_id, command)` | Runs command in backend/frontend container when possible |
| `run_in_sandbox(sandbox_id, command)` | Runs shell command in sandbox folder |
| `git_snapshot(sandbox_id, message)` | Commits and tags current sandbox state |
| `rollback(sandbox_id, tag)` | Checks out a previous Git tag |

Important detail:

- `execute_command()` prefers Docker containers if they exist.
- `run_in_sandbox()` runs in the sandbox folder on the host/container filesystem.

#### 16. How Preview Stop Works

Frontend calls:

```text
POST /api/projects/:projectId/preview/stop
```

Gateway calls:

```text
POST /runs/:projectId/preview/stop
```

FastAPI calls:

```python
stop_sandbox_containers(sandbox_id)
```

That function:

1. Finds the sandbox info.
2. Targets DB, backend, and frontend containers.
3. Runs:

   ```text
   docker rm -f <container>
   ```

4. Clears container ids in memory.
5. Removes the active preview mapping for that user.
6. Returns the stopped container list.

Important:

> Preview stop removes containers, but it does not delete the generated sandbox folder.

That is good because the user may restart preview later or download the code.

#### 17. How Preview Restart Works

Frontend calls:

```text
POST /api/projects/:projectId/preview/restart
```

Gateway calls:

```text
POST /runs/:projectId/preview/restart
```

FastAPI calls:

```python
restart_sandbox_preview(project_id, sandbox_id, user_id, backend_port, frontend_port)
```

That function:

1. Stops active preview for the user.
2. Stops existing containers for this sandbox.
3. Clears old container ids.
4. Calls `reconnect_sandbox(...)`.
5. Recreates DB/backend/frontend containers.
6. Reinstalls backend/frontend dependencies.
7. Updates `_sandboxes`.
8. Marks this sandbox as active for the user.
9. Schedules auto-stop.
10. Calls `start_sandbox_servers(...)`.

So restart means:

```text
stop old containers
  -> recreate containers from existing sandbox files
  -> install dependencies
  -> start backend/frontend dev servers
  -> return preview URLs
```

It does not regenerate the app code. It reuses the existing sandbox files.

#### 18. How Auto-Stop Works

After sandbox creation or reconnect, the system calls:

```python
schedule_preview_auto_stop(sandbox_id)
```

Default TTL:

```text
SANDBOX_PREVIEW_TTL_SECONDS=300
```

That means after about 5 minutes, a background thread:

1. Checks whether the preview is still the same active preview.
2. Removes containers for that sandbox.
3. Clears DB/backend/frontend container ids.
4. Clears active preview mapping.

Important:

> Auto-stop stops containers. It does not delete generated files.

This prevents old previews from using ports and CPU forever.

#### 19. How Sandbox Delete Works

There is a function:

```python
destroy_sandbox(sandbox_id)
```

It does:

1. Calls `stop_sandbox_containers(sandbox_id)`.
2. Deletes the sandbox folder:

   ```python
   shutil.rmtree(info.path, ignore_errors=True)
   ```

3. Removes sandbox entries from the in-memory `_sandboxes` map.

Important distinction:

> The code has a delete/destroy function, but the current gateway project routes expose stop/restart/cancel/download, not a direct public "delete sandbox" endpoint.

Also important:

> The code removes containers and sandbox files, but I do not see explicit removal of the named Docker DB volume `aidev-dbdata-<sandbox_id>`. Since containers are removed with `docker rm -f` and not explicitly `docker volume rm`, DB volumes may remain unless Docker cleanup/prune is done separately.

This is a good honest interview point if asked about cleanup limitations.

#### 20. How Download Works

Frontend opens:

```text
GET /api/projects/:projectId/download
```

Gateway:

1. Gets project metadata.
2. Checks project ownership.
3. Extracts `sandbox_id`.
4. Calls:

   ```js
   createProjectZipBuffer(sandboxId)
   ```

5. Returns a zip file.

The zip code:

- only accepts sandbox ids matching `sandbox-\d+`
- resolves path under sandbox root
- excludes `.git`, `node_modules`, `dist`, `build`, `.env`, logs, etc.

Important:

> Download is handled by the gateway, not the orchestrator, because the gateway owns user authorization and project ownership.

#### 21. How Project Metadata Is Updated

The gateway stores project metadata using `projectStore.js`.

It stores:

- project id
- user id
- requirement
- status
- last event type
- last event node
- last message
- last state
- sandbox id
- preview ports
- preview URLs
- preview running flag

When events stream through the gateway, the gateway calls:

```js
updateProjectFromEvent(projectId, event)
```

That means the dashboard can refresh and still show the latest known state.

#### 22. Full Sandbox Lifecycle Diagram

```mermaid
flowchart TD
  A[setupSandbox node] --> B[create_sandbox]
  B --> C[Create sandbox folder]
  C --> D[Scaffold backend/frontend files]
  D --> E[Initialize Git and v0.0.0 tag]
  E --> F{Docker available?}
  F -->|No| G[Local-only sandbox fallback or error if Docker required]
  F -->|Yes| H[Stop user's old active preview]
  H --> I[Ensure aidev-network]
  I --> J[Allocate backend/frontend host ports]
  J --> K[Start DB container]
  K --> L[Start backend container]
  L --> M[npm install backend]
  M --> N[Start frontend container]
  N --> O[npm install frontend]
  O --> P[Save SandboxInfo and active preview mapping]
  P --> Q[Schedule auto-stop]
  Q --> R[Coder writes files into sandbox]
  R --> S[presentToUser/start_sandbox_servers]
  S --> T[Run npm start backend and npm run dev frontend]
  T --> U[Preview URLs returned]

  U --> V[preview stop/cancel/auto-stop]
  V --> W[docker rm -f DB/backend/frontend containers]
  W --> X[Sandbox files remain]

  U --> Y[destroy_sandbox if called internally]
  Y --> Z[Stop containers + delete sandbox folder]
```

#### 23. Best Interview Explanation

If an interviewer asks, "How is everything calling everything?", say:

> The frontend talks only to the Node gateway. For normal actions it uses JSON HTTP calls, and for live progress it opens an EventSource stream. The gateway validates the user, stores project metadata, and calls the Python orchestrator through HTTP endpoints like `/runs`, `/runs/:id/events`, `/input`, `/cancel`, and preview stop/restart. The FastAPI orchestrator starts the LangGraph workflow as an async task using `asyncio.create_task(run_workflow(...))`, so the request returns quickly while the workflow continues in the background. Inside `run_workflow`, we build and compile a LangGraph `StateGraph`, initialize `AgentState`, and call `graph.ainvoke`. LangGraph then runs nodes according to edges and routers. Each node updates the shared state and may call services like Gemini, Redis checkpoints, event bus, or sandbox utilities.
>
> The sandbox is created by the `setupSandbox` node. It creates an isolated folder, scaffolds backend and frontend files, initializes Git, allocates ports, creates Docker containers for DB/backend/frontend, installs dependencies, and records preview URLs. The generated code is written into that sandbox. When the app is ready, `presentToUser` starts backend and frontend servers inside the containers and returns preview URLs. Stop/cancel removes the containers using `docker rm -f`, restart recreates containers from the existing sandbox files, and destroy removes both containers and the sandbox folder if that internal function is called.

#### One-Line Summary

> The gateway calls the orchestrator over HTTP, the orchestrator calls LangGraph with `graph.ainvoke`, LangGraph calls nodes, nodes call sandbox services, and sandbox services control Docker containers and generated files.

</details>

<details id="inline-06-solid-hld-lld-models-erd-uml">
<summary>06_solid_hld_lld_models_erd_uml.md - Question 6: SOLID Principles, HLD, LLD, Models, ER Diagrams, And UML Diagrams</summary>

### Question 6: SOLID Principles, HLD, LLD, Models, ER Diagrams, And UML Diagrams

#### Short Interview Answer

This project follows SOLID mostly through separation of responsibilities across layers and modules.

At high level:

- React owns UI.
- Node Gateway owns auth, project APIs, project metadata, event relay, and download.
- FastAPI Orchestrator owns long-running AI workflow execution.
- LangGraph nodes each own one workflow step.
- Sandbox services own generated code files, Docker containers, ports, previews, snapshots, and cleanup.

The design is not "perfect textbook SOLID", because this is a practical prototype. But the architecture uses SOLID ideas strongly:

- **Single Responsibility:** each layer/module/node has a clear job.
- **Open/Closed:** new workflow nodes or services can be added without rewriting the whole app.
- **Liskov Substitution:** common contracts like `AgentState`, `StreamEvent`, and service functions let components depend on expected behavior.
- **Interface Segregation:** modules expose small focused APIs instead of one giant service.
- **Dependency Inversion:** higher-level routes/nodes call service abstractions instead of directly mixing DB, Docker, LLM, and HTTP logic everywhere.

The most interview-friendly line:

> We applied SOLID mainly by splitting the system around responsibilities: gateway for product/backend concerns, orchestrator for AI workflow concerns, nodes for individual workflow responsibilities, and sandbox services for Docker/file execution concerns. This keeps the system understandable, testable, and easier to extend.

#### High-Level Design

High-level design answers:

> What are the main components, and how do they interact?

This project has four major runtime areas:

1. **React frontend**
2. **Node/Express gateway**
3. **Python FastAPI/LangGraph orchestrator**
4. **Docker sandbox runtime**

Supporting stores:

- MongoDB for dashboard auth users and OTPs.
- PostgreSQL for user/project metadata.
- Redis for token blocklist and workflow checkpoints.
- Filesystem/Git for generated app files and snapshots.

```mermaid
flowchart LR
  User[User] --> Frontend[React Dashboard]

  Frontend -->|JSON + cookies| Gateway[Node Express Gateway]
  Frontend -->|SSE EventSource| Gateway

  Gateway --> AuthDB[(MongoDB Auth Users + OTPs)]
  Gateway --> ProjectDB[(PostgreSQL Users + Projects)]
  Gateway --> RedisAuth[(Redis Token Blocklist)]
  Gateway -->|HTTP JSON/SSE| Orchestrator[FastAPI Orchestrator]

  Orchestrator --> Graph[LangGraph Workflow]
  Graph --> Nodes[Workflow Nodes]
  Nodes --> Gemini[Gemini LLM]
  Nodes --> RedisCheckpoints[(Redis Checkpoints)]
  Nodes --> Sandbox[Sandbox Services]
  Sandbox --> Docker[Docker DB + Backend + Frontend Containers]
  Sandbox --> Files[Generated Files + Git Snapshots]
```

#### HLD Responsibilities

| Component | Responsibility |
| --- | --- |
| React frontend | User interaction, auth screens, project launch, event rendering, file tree, token usage, preview controls |
| Node gateway | Public API, auth boundary, project ownership, metadata persistence, event relay, cancel/input/preview/download APIs |
| FastAPI orchestrator | Internal AI workflow API, async run management, event stream, human input bridge, cancellation |
| LangGraph workflow | Controls node order, conditional routing, retry loops, and state transitions |
| Workflow nodes | PM, architect, validator, planner, coder, reviewer, executor, debugger, verifier, presenter |
| Sandbox services | Create generated project workspace, scaffold files, run Docker containers, write files, execute commands, stop/restart preview |
| MongoDB | Stores dashboard auth users and OTPs |
| PostgreSQL | Stores project metadata and lightweight user mirror |
| Redis | Stores JWT logout blocklist and workflow checkpoints |
| Docker | Runs generated app DB/backend/frontend safely away from the main app |

#### Low-Level Design

Low-level design answers:

> Which modules/classes/functions implement the system?

```mermaid
flowchart TB
  subgraph Frontend["frontend/src"]
    App[App.jsx]
    Api[gateway.js]
    AuthUI[AuthScreen.jsx]
    Dashboard[Dashboard.jsx]
  end

  subgraph Gateway["gateway/src"]
    Index[index.js]
    AuthRoutes[routes/auth.js]
    ProjectRoutes[routes/projects.js]
    AuthMiddleware[middleware/auth.js]
    UserModel[models/userModel.js]
    OtpModel[models/otpModel.js]
    ProjectStore[services/projectStore.js]
    OrchestratorClient[services/orchestratorClient.js]
    Zip[services/projectZip.js]
  end

  subgraph Orchestrator["orchestrator/app"]
    Main[main.py]
    Contracts[models/contracts.py]
    Workflow[graph/workflow.py]
    Nodes[nodes/*.py]
    EventBus[services/event_bus.py]
    InputBridge[services/input_bridge.py]
    RunManager[services/run_manager.py]
    Gemini[services/gemini_client.py]
    RedisCheckpoint[services/redis_checkpoint.py]
    Sandbox[services/sandbox_*.py]
  end

  App --> Api
  Api --> ProjectRoutes
  Api --> AuthRoutes
  Index --> AuthRoutes
  Index --> ProjectRoutes
  ProjectRoutes --> OrchestratorClient
  ProjectRoutes --> ProjectStore
  AuthRoutes --> UserModel
  AuthRoutes --> OtpModel
  AuthRoutes --> ProjectStore
  AuthMiddleware --> UserModel
  OrchestratorClient --> Main
  Main --> Workflow
  Workflow --> Nodes
  Workflow --> EventBus
  Workflow --> RedisCheckpoint
  Nodes --> Gemini
  Nodes --> Sandbox
  Nodes --> InputBridge
  Main --> RunManager
```

#### SOLID Principles In This Project

#### 1. Single Responsibility Principle

Principle:

> A module should have one main reason to change.

##### How this project uses it

The project separates responsibilities in several places.

##### Layer-level SRP

| Layer | One main responsibility |
| --- | --- |
| Frontend | Show and control user experience |
| Gateway | Secure public backend and project metadata |
| Orchestrator | Run AI workflow |
| Sandbox | Isolate generated code execution |

##### Gateway SRP examples

| File | Responsibility |
| --- | --- |
| `routes/auth.js` | Auth endpoints: OTP, register, login, logout, check |
| `routes/projects.js` | Project endpoints: list, create, events, input, cancel, preview, download |
| `services/orchestratorClient.js` | HTTP/SSE calls to FastAPI |
| `services/projectStore.js` | Project/user metadata persistence |
| `services/projectZip.js` | Create safe downloadable zip |
| `middleware/auth.js` | Verify JWT cookie and attach authenticated user |
| `models/userModel.js` | Mongoose user schema |
| `models/otpModel.js` | Mongoose OTP schema |

##### Orchestrator SRP examples

| File/module | Responsibility |
| --- | --- |
| `main.py` | FastAPI endpoints |
| `workflow.py` | LangGraph node registration/routing |
| `contracts.py` | Pydantic data contracts |
| `event_bus.py` | Event storage and SSE stream source |
| `input_bridge.py` | Human-in-the-loop pending input |
| `run_manager.py` | Track/cancel active asyncio tasks |
| `redis_checkpoint.py` | Save checkpoints |
| `gemini_client.py` | Safe LLM JSON calls and token tracking |
| `sandbox_runtime.py` | Create/reconnect sandbox containers |
| `sandbox_files.py` | Read/write/list files, snapshots, rollback, stop containers |
| `sandbox_process.py` | Low-level Docker/subprocess/port helpers |
| `sandbox_preview.py` | Start/restart preview servers |
| `sandbox_scaffold.py` | Generate starter backend/frontend files |

##### Node-level SRP

Each LangGraph node does one kind of work:

- `pmAgent` clarifies requirement.
- `architectStep1` identifies entities.
- `architectStep2` designs DB.
- `architectStep3` designs APIs.
- `architectStep4` designs frontend pages.
- `architectStep5` designs folders/dependencies.
- `blueprintValidator` validates architecture.
- `plannerAgent` creates tasks.
- `coderAgent` writes files.
- `reviewerAgent` reviews files.
- `executorAgent` runs checks.
- `debuggerAgent` diagnoses failures.
- `deploymentVerifier` verifies final runtime.

##### Why this matters

If authentication changes, we mainly touch auth routes/models/middleware.

If sandbox behavior changes, we mainly touch sandbox services.

If the workflow changes, we mainly touch LangGraph nodes/routing.

##### What if SRP was not followed?

If one file handled auth, projects, LangGraph, Docker, Gemini, and downloads, every change would risk breaking unrelated behavior.

Interview answer:

> We use SRP by giving each layer and module one job. For example, the gateway project route does not know LangGraph internals; it calls `orchestratorClient`. The orchestrator nodes do not know HTTP cookie auth; they work on `AgentState`. This separation reduces coupling and makes debugging easier.

#### 2. Open/Closed Principle

Principle:

> Software should be open for extension but closed for modification.

##### How this project uses it

The best example is the LangGraph workflow.

To add a new workflow step, we can:

1. Create a new node file.
2. Register it in `workflow.py`.
3. Add edges/router rules.

We do not need to rewrite every existing node.

Examples:

- Add a `securityScannerNode` after `reviewerAgent`.
- Add a `testGeneratorNode` before `executorAgent`.
- Add a `cloudDeployNode` after `deploymentVerifier`.

Gateway also shows OCP through service wrappers.

For example:

- `orchestratorClient.js` wraps FastAPI calls.
- If the orchestrator URL or protocol changes, route handlers do not need major changes.

Sandbox modules also show OCP:

- `sandbox.py` exports a stable facade.
- Lower-level implementation is split into runtime/files/process/preview/scaffold/database modules.

##### What if OCP was not followed?

Every new feature would require editing large, central files.

Example:

If all orchestration logic was one giant function, adding a new validation step would require risky changes across the whole function.

Interview answer:

> The graph design supports OCP because we can add a new node or service without rewriting the entire workflow. Existing nodes stay mostly unchanged while the graph is extended through new edges and routers.

#### 3. Liskov Substitution Principle

Principle:

> A component should be replaceable by another implementation that follows the same expected contract.

This principle is more obvious in strongly typed OOP systems, but this project still uses contract-based substitution.

##### How this project uses it

Examples:

1. Every LangGraph node receives and returns `AgentState`.
2. Every stream event follows `StreamEvent`.
3. Gateway/orchestrator HTTP payloads follow request/response contracts.
4. Sandbox functions return predictable dictionaries like `{ started, errors, frontendUrl }`.
5. `projectStore.js` can use Postgres or memory fallback while exposing the same functions.

##### Practical substitution examples

| Current implementation | Possible substitute | Why it works |
| --- | --- | --- |
| Gemini client | Different LLM provider | If it returns structured JSON and token info |
| Postgres project store | Memory fallback or another DB | If `saveProjectMetadata`, `listProjects`, `getProjectMetadata` behave the same |
| Docker sandbox | Different container runtime | If sandbox service API remains stable |
| SSE stream | WebSocket stream | If event payload shape stays `StreamEvent` |

##### What if LSP-style contracts were not followed?

If each node returned a different state shape, the graph would break.

If events had inconsistent formats, the frontend could not reliably render progress.

Interview answer:

> We use contract-based substitution. Nodes can be changed internally as long as they accept and return `AgentState`. The frontend can render any event as long as it follows `StreamEvent`. This makes parts replaceable without breaking the full chain.

#### 4. Interface Segregation Principle

Principle:

> Clients should not depend on interfaces they do not use.

##### How this project uses it

The project exposes focused functions instead of one giant utility.

Examples:

| Client | Focused dependency |
| --- | --- |
| Gateway project routes | `createProjectRun`, `streamProjectEvents`, `cancelProjectRun`, `submitProjectInput`, preview helpers |
| Auth routes | `User`, `OTP`, `sendMail`, `saveUser`, Redis blocklist |
| Coder node | `write_file`, `get_file_list`, Gemini client |
| Executor node | `execute_command`, `read_file`, `get_file_list` |
| Present node | `start_sandbox_servers` |
| Deployment verifier | `write_file`, `run_in_sandbox`, endpoint checks |

The frontend also has a small gateway API helper instead of knowing all fetch details everywhere.

##### What if ISP was not followed?

Every route/node would import one massive service object.

That would make each module depend on unrelated features. For example, the reviewer should not need to know how OTP email sending works. The project zip service should not know how Gemini calls are made.

Interview answer:

> We follow ISP by giving modules small, purpose-specific dependencies. A route or node imports only the service functions it needs.

#### 5. Dependency Inversion Principle

Principle:

> High-level logic should depend on abstractions/contracts, not low-level details.

##### How this project uses it

The gateway project route does not directly build FastAPI URLs everywhere. It calls:

```js
createProjectRun(payload)
streamProjectEvents(projectId, onEvent)
cancelProjectRun(projectId)
```

Those are service-level abstractions from `orchestratorClient.js`.

The LangGraph workflow does not directly call Docker commands. Nodes call sandbox service functions like:

```python
create_sandbox(...)
write_file(...)
execute_command(...)
start_sandbox_servers(...)
```

The nodes do not need to know whether those are implemented through Docker, local shell, or another runtime.

##### What if DIP was not followed?

If every node directly ran Docker commands, then changing Docker behavior would require editing many nodes.

If every gateway route directly used raw `fetch` to the orchestrator, then changing orchestrator URL/error parsing/SSE parsing would require editing many routes.

Interview answer:

> The high-level workflow depends on service functions, not raw Docker/subprocess details. Gateway routes depend on `orchestratorClient`, not direct scattered FastAPI calls. That is dependency inversion in a practical service-based style.

#### SOLID Responsibility Map

```mermaid
flowchart TB
  SOLID[SOLID in this project]

  SOLID --> SRP[Single Responsibility]
  SRP --> SRP1[Frontend UI only]
  SRP --> SRP2[Gateway auth/projects/events]
  SRP --> SRP3[Orchestrator AI workflow]
  SRP --> SRP4[Sandbox Docker/files]
  SRP --> SRP5[One node = one workflow role]

  SOLID --> OCP[Open/Closed]
  OCP --> OCP1[Add new LangGraph node]
  OCP --> OCP2[Swap/extend service implementation]
  OCP --> OCP3[Add new gateway route using service layer]

  SOLID --> LSP[Liskov Substitution]
  LSP --> LSP1[Nodes preserve AgentState contract]
  LSP --> LSP2[Events preserve StreamEvent shape]
  LSP --> LSP3[Project store functions can use DB or memory]

  SOLID --> ISP[Interface Segregation]
  ISP --> ISP1[Small service functions]
  ISP --> ISP2[Focused route modules]
  ISP --> ISP3[Focused sandbox modules]

  SOLID --> DIP[Dependency Inversion]
  DIP --> DIP1[Routes call orchestratorClient]
  DIP --> DIP2[Nodes call sandbox facade]
  DIP --> DIP3[Workflow calls node functions through contracts]
```

#### Data Models And Entities

This project has two categories of models:

1. **Platform models:** fixed models used by this app itself.
2. **Generated app models:** dynamic models created for each user prompt.

#### Platform Entity 1: `DashboardUser`

Defined in:

```text
gateway/src/models/userModel.js
```

Storage:

```text
MongoDB / Mongoose
```

Purpose:

> Stores real dashboard login users.

Fields:

| Field | Type | Rules |
| --- | --- | --- |
| `_id` | ObjectId | Mongo-generated primary id |
| `userName` | String | required, unique, trim, 3-30 chars, letters/numbers/underscore |
| `firstName` | String | required, trim, 3-30 chars |
| `lastName` | String | optional, trim, max 30 chars |
| `profilePhoto` | String | optional |
| `emailId` | String | required, unique, lowercase, immutable, validated email |
| `role` | String | enum `user`, default `user` |
| `password` | String | required hashed password |
| `createdAt` | Date | automatic timestamp |
| `updatedAt` | Date | automatic timestamp |

Why this model exists:

- It owns dashboard authentication identity.
- It stores hashed password and profile info.
- It is used by register/login/auth-check flows.

Interview note:

> The Mongo user model is the real authentication model. The Postgres user table is only a lightweight mirror for project ownership and listing.

#### Platform Entity 2: `DashboardOTP`

Defined in:

```text
gateway/src/models/otpModel.js
```

Storage:

```text
MongoDB / Mongoose
```

Purpose:

> Stores short-lived OTP records during registration.

Fields:

| Field | Type | Rules |
| --- | --- | --- |
| `_id` | ObjectId | Mongo-generated |
| `emailId` | String | required, trim, lowercase |
| `otp` | String | required |
| `createdAt` | Date | default now, expires after 5 minutes |

Important design point:

Mongo TTL index is created through:

```js
expires: 5 * 60
```

That means OTP records automatically expire after 5 minutes.

Why this model exists:

- Registration needs email verification.
- OTP should be temporary.
- TTL cleanup avoids keeping old OTPs forever.

#### Platform Entity 3: Postgres `users`

Defined in:

```text
gateway/src/services/projectStore.js
```

Storage:

```text
PostgreSQL
```

Purpose:

> Lightweight user mirror for project ownership and project listing.

Fields:

| Column | Type | Constraint |
| --- | --- | --- |
| `user_id` | text | primary key |
| `email` | text | not null, unique |
| `display_name` | text | nullable |
| `created_at` | timestamptz | default now |
| `updated_at` | timestamptz | default now |

Why both Mongo user and Postgres user?

Mongo stores full auth user data. Postgres stores lightweight dashboard/project identity.

This lets the project metadata layer avoid depending directly on Mongo auth documents for every project query.

#### Platform Entity 4: Postgres `projects`

Defined in:

```text
gateway/src/services/projectStore.js
```

Storage:

```text
PostgreSQL
```

Purpose:

> Stores project metadata, status, latest workflow state, sandbox id, and preview information.

Fields:

| Column | Type | Meaning |
| --- | --- | --- |
| `project_id` | text | primary key from orchestrator |
| `user_id` | text | owner id |
| `requirement` | text | original user prompt |
| `status` | text | running, queued, completed, failed, cancelled |
| `last_event_type` | text | latest event type |
| `last_event_node` | text | latest workflow node |
| `last_message` | text | latest event message |
| `last_state` | jsonb | latest `AgentState` snapshot |
| `sandbox_id` | text | generated sandbox id |
| `preview_frontend_port` | integer | frontend preview port |
| `preview_backend_port` | integer | backend preview port |
| `preview_frontend_url` | text | frontend preview URL |
| `preview_backend_url` | text | backend preview URL |
| `preview_running` | boolean | whether preview is active |
| `created_at` | timestamptz | creation time |
| `updated_at` | timestamptz | last update time |

Important design point:

The code treats `user_id` as the logical owner. The table creation shown in code does not define an explicit foreign key constraint, but design-wise:

```text
users 1 ---> many projects
```

Why this model exists:

- The dashboard needs project history.
- The frontend needs to refresh and still know project status.
- Event streaming updates latest state continuously.
- Download/preview actions need sandbox metadata.

#### Platform Entity 5: Redis Token Blocklist

Defined through:

```text
gateway/src/routes/auth.js
gateway/src/middleware/auth.js
gateway/src/config/redis.js
```

Storage:

```text
Redis
```

Shape:

```text
key: token:<jwt>
value: blocked
expiry: token expiry time
```

Purpose:

> Supports logout for JWT cookies.

JWTs are normally stateless. If a user logs out, the server needs a way to reject that token before its natural expiry. Redis blocklist solves that.

#### Platform Entity 6: `RunCreateRequest`

Defined in:

```text
orchestrator/app/models/contracts.py
```

Purpose:

> Request body for starting a new orchestrator run.

Fields:

| Field | Type | Rule |
| --- | --- | --- |
| `requirement` | string | min length 3 |
| `user_id` | string | default `demo-user` |
| `token_budget_usd` | float | default 2.0, greater than 0 |

#### Platform Entity 7: `RunCreateResponse`

Purpose:

> Response returned immediately after FastAPI accepts a run.

Fields:

| Field | Type |
| --- | --- |
| `project_id` | string |
| `status` | `running` or `queued` |

#### Platform Entity 8: `HumanInputSubmitRequest`

Purpose:

> Payload for answering PM clarification or human escalation.

Fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `type` | `pm_clarification` or `escalation` | input category |
| `answers` | any | PM clarification answers |
| `choice` | `guide`, `skip`, or `simplify` | escalation decision |
| `guidance` | string | human guidance text |
| `data` | dict | additional payload |

#### Platform Entity 9: `TokenUsage`

Purpose:

> Tracks LLM usage and estimated/provider cost.

Fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `calls` | list of dict | per-agent token/cost records |
| `totalInput` | int | total input tokens |
| `totalOutput` | int | total output tokens |
| `estimatedCost` | float | total estimated/provider cost |

#### Platform Entity 10: `AgentState`

Purpose:

> Central workflow state passed through every LangGraph node.

This is the most important orchestrator model.

Major sections:

| Section | Fields |
| --- | --- |
| Identity | `projectId`, `userId`, `userRequirement` |
| PM | `pmStatus`, `pmQuestions`, `pmConversation`, `clarifiedSpec` |
| Architecture | `blueprint`, `blueprintValidation` |
| Planning | `taskQueue`, `currentPhaseIndex`, `currentTaskIndex`, `currentTask`, `taskStatuses` |
| Registry/patterns | `fileRegistry`, `projectPatterns` |
| Sandbox | `sandboxId`, `sandboxHealthy`, `fileTree`, preview ports/URLs |
| Dev loop | `contextPackage`, `coderOutput`, `reviewResult`, `executionResult`, `debugState`, `retryCounts`, `retryLimits` |
| Feedback/deploy | `userFeedback`, `deploymentConfig`, `deploymentAttempts` |
| Token/control | `tokenUsage`, `tokenBudget`, `currentPhase`, `error`, `terminalOutput`, `gitSnapshots` |

Why this model exists:

- LangGraph needs one shared state contract.
- Frontend needs one consistent event state shape.
- Redis checkpointing needs serializable state.
- Nodes can communicate through state without direct coupling.

Interview answer:

> `AgentState` is the backbone of the orchestrator. Every node reads from it, updates a small part of it, and passes it forward.

#### Platform Entity 11: `StreamEvent`

Purpose:

> Standard event object streamed from orchestrator to gateway to frontend.

Fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `type` | string | event type like `node.started`, `node.completed`, `run.completed` |
| `node` | string/null | source node |
| `message` | string | human-readable message |
| `state` | dict/null | optional AgentState snapshot or input payload |

Why this model exists:

- Standardizes live progress updates.
- Lets gateway persist latest state.
- Lets frontend render events consistently.

#### Platform Entity 12: Redis Checkpoint

Defined in:

```text
orchestrator/app/services/redis_checkpoint.py
```

Storage:

```text
Redis
```

Shape:

```text
checkpoint:<project_id>:<node_name> -> serialized AgentState JSON
checkpoints:<project_id> -> list of checkpoint keys
```

Purpose:

> Saves state after every node so the workflow is inspectable and recoverable at node boundaries.

#### Platform Entity 13: `SandboxInfo`

Defined in:

```text
orchestrator/app/services/sandbox_state.py
```

Purpose:

> In-memory runtime record for a sandbox and its containers.

Fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `sandbox_id` | string | sandbox identifier |
| `path` | Path | sandbox root path |
| `backend_path` | Path | generated backend path |
| `frontend_path` | Path | generated frontend path |
| `db_type` | string | postgres or mongo |
| `db_container_id` | string/null | DB container id |
| `backend_container_id` | string/null | backend container id |
| `frontend_container_id` | string/null | frontend container id |
| `db_container_name` | string | DB container name |
| `backend_container_name` | string | backend container name |
| `frontend_container_name` | string | frontend container name |
| `backend_host_port` | string/null | host port for backend |
| `frontend_host_port` | string/null | host port for frontend |
| `user_id` | string | owner |
| `created_at` | float | creation timestamp |
| `snapshot_count` | int | number of Git snapshots |
| `preview_expires_at` | float | auto-stop expiry |

Why this model exists:

- The orchestrator needs to know which containers belong to which sandbox.
- Stop/restart/preview operations depend on these ids and ports.

#### Generated App Models

Generated app models are dynamic. They depend on the user's prompt.

For example:

```text
Build a notes app with login
```

may generate:

- `User`
- `Note`

But:

```text
Build a simple counter page
```

may generate no backend entities at all.

The generated app model information is stored inside `AgentState.blueprint`:

| Blueprint field | Meaning |
| --- | --- |
| `entities` | business entities and relationships |
| `dbSchema` | database type, tables, fields, foreign keys, indexes |
| `apiEndpoints` | REST API contract |
| `frontendPages` | pages, routes, components, API calls |
| `folderStructure` | planned file tree |
| `dependencies` | backend/frontend package dependencies |

So the generated app ERD is not fixed. It is created per project by architect nodes.

#### Platform ER Diagram

```mermaid
erDiagram
  DASHBOARD_USER {
    ObjectId _id PK
    string userName UK
    string firstName
    string lastName
    string profilePhoto
    string emailId UK
    string role
    string password_hash
    datetime createdAt
    datetime updatedAt
  }

  DASHBOARD_OTP {
    ObjectId _id PK
    string emailId
    string otp
    datetime createdAt_TTL_5min
  }

  PROJECT_USER {
    text user_id PK
    text email UK
    text display_name
    timestamptz created_at
    timestamptz updated_at
  }

  PROJECT {
    text project_id PK
    text user_id
    text requirement
    text status
    text last_event_type
    text last_event_node
    text last_message
    jsonb last_state
    text sandbox_id
    int preview_frontend_port
    int preview_backend_port
    text preview_frontend_url
    text preview_backend_url
    boolean preview_running
    timestamptz created_at
    timestamptz updated_at
  }

  AGENT_STATE {
    string projectId PK
    string userId
    string userRequirement
    json clarifiedSpec
    json blueprint
    json taskQueue
    string sandboxId
    json tokenUsage
    string currentPhase
  }

  SANDBOX_INFO {
    string sandbox_id PK
    string user_id
    string path
    string db_type
    string db_container_id
    string backend_container_id
    string frontend_container_id
    string backend_host_port
    string frontend_host_port
  }

  DASHBOARD_USER ||--o{ DASHBOARD_OTP : requests
  DASHBOARD_USER ||--o{ PROJECT_USER : mirrored_as
  PROJECT_USER ||--o{ PROJECT : owns
  PROJECT ||--|| AGENT_STATE : stores_latest_state
  PROJECT ||--o| SANDBOX_INFO : points_to_runtime
```

Note:

- `DASHBOARD_USER` is Mongo.
- `DASHBOARD_OTP` is Mongo.
- `PROJECT_USER` and `PROJECT` are Postgres.
- `AGENT_STATE` is stored as JSON in Postgres `last_state` and checkpoints in Redis.
- `SANDBOX_INFO` is in-memory runtime state, not a DB table.
- The code uses logical relationships; not all relationships are enforced as DB foreign keys.

#### Generated App Conceptual ER Diagram

For generated applications, a common auth CRUD app looks like:

```mermaid
erDiagram
  GENERATED_USER {
    uuid id PK
    string email UK
    string username UK
    string password_hash
    timestamp created_at
    timestamp updated_at
  }

  GENERATED_RESOURCE {
    uuid id PK
    uuid user_id FK
    string title
    text content
    timestamp created_at
    timestamp updated_at
  }

  GENERATED_USER ||--o{ GENERATED_RESOURCE : owns
```

This is conceptual because actual generated tables depend on the prompt.

Example:

- Notes app: `users ||--o{ notes`
- Todo app: `users ||--o{ todo_items`, maybe `categories ||--o{ todo_items`
- Counter page: no DB entities

#### Gateway UML Class Diagram

```mermaid
classDiagram
  class DashboardUser {
    +ObjectId _id
    +String userName
    +String firstName
    +String lastName
    +String profilePhoto
    +String emailId
    +String role
    +String password
    +Date createdAt
    +Date updatedAt
  }

  class DashboardOTP {
    +ObjectId _id
    +String emailId
    +String otp
    +Date createdAt
  }

  class PublicUserDTO {
    +String user_id
    +String email
    +String display_name
    +String firstName
    +String lastName
    +String userName
    +String emailId
    +String role
    +String profilePhoto
  }

  class ProjectMetadata {
    +String project_id
    +String user_id
    +String requirement
    +String status
    +String last_event_type
    +String last_event_node
    +String last_message
    +Json last_state
    +String sandbox_id
    +Number preview_frontend_port
    +Number preview_backend_port
    +String preview_frontend_url
    +String preview_backend_url
    +Boolean preview_running
  }

  class AuthRoutes {
    +sendotp()
    +register()
    +login()
    +logout()
    +check()
  }

  class ProjectRoutes {
    +listProjects()
    +createProject()
    +getProject()
    +streamEvents()
    +submitInput()
    +cancel()
    +stopPreview()
    +restartPreview()
    +download()
  }

  class OrchestratorClient {
    +getOrchestratorHealth()
    +createProjectRun()
    +streamProjectEvents()
    +cancelProjectRun()
    +submitProjectInput()
    +stopProjectPreview()
    +restartProjectPreview()
  }

  DashboardUser --> DashboardOTP : requests OTP
  AuthRoutes --> DashboardUser
  AuthRoutes --> DashboardOTP
  AuthRoutes --> PublicUserDTO : returns
  ProjectRoutes --> ProjectMetadata
  ProjectRoutes --> OrchestratorClient
```

#### Orchestrator UML Class Diagram

```mermaid
classDiagram
  class RunCreateRequest {
    +String requirement
    +String user_id
    +Float token_budget_usd
  }

  class RunCreateResponse {
    +String project_id
    +String status
  }

  class HumanInputSubmitRequest {
    +String type
    +Any answers
    +String choice
    +String guidance
    +Dict data
  }

  class TokenUsage {
    +List calls
    +Int totalInput
    +Int totalOutput
    +Float estimatedCost
  }

  class AgentState {
    +String projectId
    +String userId
    +String userRequirement
    +String pmStatus
    +List pmQuestions
    +List pmConversation
    +Dict clarifiedSpec
    +Dict blueprint
    +Dict blueprintValidation
    +Dict taskQueue
    +List fileRegistry
    +Dict projectPatterns
    +String sandboxId
    +Boolean sandboxHealthy
    +List fileTree
    +Dict currentTask
    +Dict coderOutput
    +Dict reviewResult
    +Dict executionResult
    +Dict debugState
    +TokenUsage tokenUsage
    +String currentPhase
    +String error
  }

  class StreamEvent {
    +String type
    +String node
    +String message
    +Dict state
  }

  class SandboxInfo {
    +String sandbox_id
    +Path path
    +Path backend_path
    +Path frontend_path
    +String db_type
    +String db_container_id
    +String backend_container_id
    +String frontend_container_id
    +String backend_host_port
    +String frontend_host_port
    +String user_id
    +Float created_at
    +Int snapshot_count
    +Float preview_expires_at
  }

  AgentState *-- TokenUsage
  AgentState --> SandboxInfo : references by sandboxId
  StreamEvent --> AgentState : may include state snapshot
  RunCreateRequest --> AgentState : initializes
  RunCreateResponse --> AgentState : exposes projectId
```

#### HLD Vs LLD Interview Difference

If asked for HLD:

> The system has a React dashboard, Node gateway, FastAPI orchestrator, LangGraph workflow, storage systems, and Docker sandbox. The gateway is the secure public API and the orchestrator is the internal AI engine.

If asked for LLD:

> The gateway uses route modules, middleware, Mongoose models, Postgres project store, and an orchestrator client. The orchestrator uses FastAPI endpoints, Pydantic contracts, LangGraph nodes, event bus, input bridge, run manager, Redis checkpointing, Gemini client, and sandbox service modules.

#### Design Strengths

- Clear three-layer architecture.
- Strong separation between public backend and AI runtime.
- Node-by-node workflow is explainable and debuggable.
- `AgentState` gives a consistent workflow contract.
- `StreamEvent` gives a consistent event contract.
- Project metadata stores latest state for dashboard refresh.
- Sandbox isolates generated code from main app.
- Git snapshots allow rollback.
- Review/execution/debug loops improve reliability.

#### Design Limitations / Honest Interview Points

These are not bad to mention. They make you sound honest and technical.

1. Some relationships are logical but not enforced by DB foreign keys.
2. `AgentState` is powerful but large; state compaction is needed to control growth.
3. `last_state` in Postgres is flexible JSON, which is good for evolving workflow state but less strict for querying.
4. Sandbox state is in memory; if orchestrator restarts, running container ids may need reconnect logic.
5. Docker containers are stopped, but named DB volumes are not explicitly removed in the code path I inspected.
6. The current public API exposes preview stop/restart/cancel/download, but not a direct delete-sandbox route.

#### Best Interview Summary

> At HLD, the project is split into React frontend, Node gateway, FastAPI/LangGraph orchestrator, and Docker sandbox. At LLD, each layer is broken into focused modules: gateway routes, auth middleware, Mongoose models, project store, orchestrator client, FastAPI endpoints, Pydantic contracts, LangGraph nodes, event bus, input bridge, run manager, Redis checkpoints, Gemini client, and sandbox services.
>
> SOLID appears mainly through responsibility separation. Each module has one reason to change, new workflow steps can be added as nodes, components communicate through stable contracts like `AgentState` and `StreamEvent`, and high-level code depends on service abstractions rather than raw Docker, DB, or HTTP details.

</details>

<details id="inline-07-gateway-deep-dive">
<summary>07_gateway_deep_dive.md - Question 7: Gateway Deep Dive, File By File</summary>

### Question 7: Gateway Deep Dive, File By File

#### Short Beginner Summary

The gateway is the public backend of the project.

It sits between:

```text
React frontend
  and
Python FastAPI orchestrator
```

The browser does not directly call the orchestrator. The browser calls the gateway.

The gateway does five big jobs:

1. **Authentication:** signup, OTP, login, logout, session check.
2. **Project API:** list projects, create project, get project, cancel project, send human input.
3. **Event relay:** read orchestrator SSE events and forward them to the frontend.
4. **Preview management:** stop/restart generated app preview containers through the orchestrator.
5. **Download:** safely zip generated sandbox code and return it to the browser.

Interview line:

> The gateway is the secure product backend. It owns browser-facing APIs, auth, project ownership, project metadata, event relay, preview controls, and downloads. It keeps the frontend away from the internal FastAPI/LangGraph execution engine.

#### Gateway Folder Structure

```text
gateway/
  .dockerignore
  Dockerfile
  package.json
  package-lock.json
  src/
    index.js
    config/
      mail.js
      mongo.js
      redis.js
    middleware/
      auth.js
    models/
      otpModel.js
      userModel.js
    routes/
      auth.js
      projects.js
    services/
      orchestratorClient.js
      projectStore.js
      projectZip.js
    templates/
      emailTemplates.js
    utils/
      publicUrls.js
```

#### Gateway Module Dependency Diagram

```mermaid
flowchart TB
  Index[index.js]

  Index --> AuthRoutes[routes/auth.js]
  Index --> ProjectRoutes[routes/projects.js]
  Index --> RequireAuth[middleware/auth.js]
  Index --> MongoConfig[config/mongo.js]
  Index --> RedisConfig[config/redis.js]
  Index --> OrchestratorClient[services/orchestratorClient.js]
  Index --> ProjectStore[services/projectStore.js]

  AuthRoutes --> UserModel[models/userModel.js]
  AuthRoutes --> OTPModel[models/otpModel.js]
  AuthRoutes --> RedisConfig
  AuthRoutes --> MailConfig[config/mail.js]
  AuthRoutes --> RequireAuth
  AuthRoutes --> ProjectStore
  AuthRoutes --> EmailTemplates[templates/emailTemplates.js]

  ProjectRoutes --> OrchestratorClient
  ProjectRoutes --> ProjectStore
  ProjectRoutes --> ProjectZip[services/projectZip.js]
  ProjectRoutes --> PublicUrls[utils/publicUrls.js]

  RequireAuth --> UserModel
  RequireAuth --> RedisConfig
  ProjectStore --> PublicUrls
```

#### File 1: `gateway/package.json`

##### What this file does

This is the Node package manifest for the gateway service.

It defines:

- package name
- version
- module type
- scripts
- dependencies

Important fields:

```json
{
  "type": "module",
  "scripts": {
    "dev": "node --watch src/index.js",
    "start": "node src/index.js"
  }
}
```

##### Why `"type": "module"` matters

Because the gateway uses ES module syntax:

```js
import express from "express";
export async function ...
```

Without `"type": "module"`, Node would expect CommonJS syntax like:

```js
const express = require("express");
module.exports = ...
```

##### Dependencies and why they exist

| Dependency | Why used |
| --- | --- |
| `express` | HTTP API server |
| `cors` | Allows frontend origin to call gateway with cookies |
| `cookie-parser` | Reads JWT cookie from requests |
| `bcryptjs` | Hash and verify user passwords |
| `jsonwebtoken` | Sign and verify JWT session token |
| `mongoose` | MongoDB models for auth user and OTP |
| `nodemailer` | Send OTP/welcome emails |
| `pg` | PostgreSQL project/user metadata |
| `redis` | JWT logout token blocklist |
| `validator` | Email/password validation |
| `ws` | WebSocket relay support |
| `dotenv` | Load `.env` variables |

##### What happens if this file is wrong

- Gateway may not start.
- Node may not understand `import`.
- Dependencies may be missing.
- Docker build may fail.

#### File 2: `gateway/package-lock.json`

##### What this file does

This is the npm lockfile.

It stores the exact dependency tree installed for the gateway.

You usually do not manually edit this file.

##### Why it exists

It makes installs reproducible.

Without it, different machines may install slightly different dependency versions.

Interview answer:

> `package.json` says what libraries we need; `package-lock.json` locks the exact versions npm resolved.

#### File 3: `gateway/Dockerfile`

##### What this file does

This file builds the gateway container.

Flow:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

##### Step-by-step

| Line | Meaning |
| --- | --- |
| `FROM node:22-alpine` | Uses a lightweight Node image |
| `WORKDIR /app` | Sets `/app` as working directory |
| `COPY package.json ./` | Copies dependency manifest |
| `RUN npm install` | Installs gateway dependencies |
| `COPY . .` | Copies gateway source code |
| `EXPOSE 3000` | Documents that gateway listens on port 3000 |
| `CMD ["npm", "start"]` | Starts `node src/index.js` |

##### Why this file exists

It lets Docker Compose run the gateway as a containerized service.

#### File 4: `gateway/.dockerignore`

##### What this file does

It tells Docker not to copy unnecessary or sensitive files into the image.

Ignored:

```text
node_modules
dist
build
.DS_Store
*.log
.env
```

##### Why this matters

- Keeps Docker image smaller.
- Avoids copying local dependencies.
- Avoids copying `.env` secrets into image.
- Avoids noisy build artifacts.

#### File 5: `gateway/src/index.js`

##### What this file does

This is the gateway entrypoint.

It starts the Express server and wires the whole gateway together.

##### Main responsibilities

1. Load environment variables.
2. Create Express app.
3. Configure CORS.
4. Configure JSON body parsing.
5. Configure cookie parsing.
6. Register health route.
7. Register auth routes.
8. Register protected project routes.
9. Register error handler.
10. Create HTTP server.
11. Create WebSocket server.
12. Connect Mongo and Redis.
13. Start listening.

##### Key imports

```js
import "dotenv/config";
import cookieParser from "cookie-parser";
import cors from "cors";
import express from "express";
import { createServer } from "http";
import { WebSocket, WebSocketServer } from "ws";
```

##### Why `dotenv/config` is imported first

It loads environment variables before other modules need them.

Example env variables:

- `PORT`
- `FRONTEND_URL`
- `ORCHESTRATOR_URL`
- `MONGO_URI`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- mail settings

##### Express setup

```js
const app = express();
const port = Number(process.env.PORT || 3000);
const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";
```

The gateway defaults to port 3000.

##### CORS setup

```js
app.use(cors({ origin: frontendUrl, credentials: true }));
```

This allows the React frontend to call the gateway.

`credentials: true` is important because JWT is stored in an HTTP-only cookie. Without it, browser requests would not send the cookie.

##### JSON parser

```js
app.use(express.json({ limit: "2mb" }));
```

This parses JSON request bodies and limits payload size.

##### Cookie parser

```js
app.use(cookieParser());
```

This makes `req.cookies.token` available in auth middleware.

##### Health route

```js
GET /api/health
```

This route calls:

```js
getOrchestratorHealth()
```

If orchestrator is healthy, gateway returns:

```json
{
  "status": "ok",
  "layer": "node-express-gateway",
  "orchestrator_url": "...",
  "orchestrator": {}
}
```

If orchestrator is down, it returns status 503 with degraded status.

##### Route mounting

```js
app.use("/api/auth", authRouter);
app.use("/api/projects", requireAuth, projectsRouter);
```

Meaning:

- `/api/auth/*` handles login/register/logout/check.
- `/api/projects/*` requires authentication.

##### Error handler

```js
app.use((error, _req, res, _next) => {
  const status = error.status || 500;
  res.status(status).json({ error: error.message || "gateway error" });
});
```

This catches errors passed with `next(error)`.

##### WebSocket support

The gateway also supports:

```text
WS /ws/projects/:projectId/events
```

This is an alternative to SSE.

Flow:

1. Browser requests WebSocket upgrade.
2. Gateway checks path.
3. Gateway extracts `projectId`.
4. Gateway checks project exists.
5. Gateway connects WebSocket.
6. Gateway streams orchestrator events.
7. Gateway updates project metadata.
8. Gateway sends JSON event to WebSocket client.

##### Startup

```js
Promise.all([connectMongo(), connectRedis()]).then(() => {
  server.listen(port, ...)
})
```

Mongo is required. Redis is attempted but can be skipped if unavailable.

##### Why this file exists

It is the composition root of the gateway. It does not own business logic deeply; it wires middleware, routes, services, and server startup.

Interview answer:

> `index.js` is the gateway bootstrap file. It configures Express, mounts auth/project APIs, configures CORS/cookies, exposes health checks, sets up WebSocket event relay, connects Mongo/Redis, and starts the HTTP server.

#### File 6: `gateway/src/config/mongo.js`

##### What this file does

It connects the gateway to MongoDB.

```js
export async function connectMongo()
```

##### Logic

1. If `MONGO_URI` is missing, throw error.
2. If Mongoose is already connected, return.
3. Otherwise call `mongoose.connect(process.env.MONGO_URI)`.

##### Why Mongo is used

Mongo stores:

- dashboard auth users
- OTP records

##### Why this is separate

Database connection logic should not be mixed inside route handlers.

Interview answer:

> `mongo.js` is only responsible for connecting Mongoose to MongoDB. Auth routes use Mongo models, but they do not manage the connection themselves.

#### File 7: `gateway/src/config/redis.js`

##### What this file does

It creates and connects the Redis client.

```js
export const redisClient = createClient({ url: redisUrl });
export async function connectRedis()
```

##### Redis URL

Default:

```text
redis://redis:6379/0
```

This default works inside Docker Compose because the Redis service is named `redis`.

##### Error handling

Redis errors are logged as warnings:

```js
redisClient.on("error", ...)
```

`connectRedis()` catches connection failure and logs a warning instead of crashing.

##### Why Redis is used

Gateway uses Redis for JWT logout blocklist.

When the user logs out:

```text
token:<jwt> -> blocked
```

When the user makes a request:

```js
requireAuth checks if token:<jwt> exists
```

##### Why Redis failure does not crash gateway

The app can still run without logout blocklisting. It is degraded security, but not complete service failure.

Interview answer:

> `redis.js` creates a shared Redis client used by auth. It is mainly for token blocklisting after logout.

#### File 8: `gateway/src/config/mail.js`

##### What this file does

It sends emails through Nodemailer.

Exports:

```js
mailConfigured()
sendMail(to, subject, html)
```

##### `readMailConfig()`

Reads:

- `MAIL_HOST`
- `MAIL_PORT`
- `MAIL_SECURE`
- `MAIL_USER`
- `MAIL_PASS`

##### `mailConfigured()`

Returns true if required mail settings are present.

##### `sendMail(...)`

Creates Nodemailer transporter and sends HTML email.

##### Where this is used

`routes/auth.js` uses it for:

- OTP email
- welcome email

##### Why this is separate

Auth route should not know SMTP details.

Interview answer:

> `mail.js` isolates email provider setup. Auth routes just call `sendMail`; they do not directly configure SMTP.

#### File 9: `gateway/src/models/userModel.js`

##### What this file does

It defines the Mongo/Mongoose schema for dashboard users.

Model name:

```js
DashboardUser
```

##### Fields

| Field | Purpose |
| --- | --- |
| `userName` | Unique username |
| `firstName` | User first name |
| `lastName` | Optional last name |
| `profilePhoto` | Optional profile image URL |
| `emailId` | Unique immutable email |
| `role` | Currently only `user` |
| `password` | Hashed password |
| timestamps | `createdAt`, `updatedAt` |

##### Validation

`userName`:

- required
- unique
- trimmed
- 3-30 characters
- letters/numbers/underscore only

`firstName`:

- required
- 3-30 characters

`lastName`:

- optional
- max 30 characters

`emailId`:

- required
- unique
- lowercase
- immutable
- validated with `validator.isEmail`

`password`:

- required
- stores hash, not plain password

##### Why this model exists

It is the source of truth for dashboard authentication users.

Interview answer:

> `userModel.js` defines the real dashboard auth user stored in MongoDB. It contains login identity, profile fields, role, and hashed password.

#### File 10: `gateway/src/models/otpModel.js`

##### What this file does

It defines the Mongo/Mongoose schema for OTP records.

Model name:

```js
DashboardOTP
```

##### Fields

| Field | Purpose |
| --- | --- |
| `emailId` | Email that requested OTP |
| `otp` | 6-digit OTP string |
| `createdAt` | creation time plus TTL expiry |

##### Important TTL behavior

```js
expires: 5 * 60
```

Mongo automatically deletes OTP records after 5 minutes.

##### Why this model exists

Registration requires email verification, but OTPs should be temporary.

Interview answer:

> `otpModel.js` stores short-lived OTPs for registration. The TTL index automatically cleans them after 5 minutes.

#### File 11: `gateway/src/middleware/auth.js`

##### What this file does

It contains authentication helper logic.

Exports:

```js
publicUser(user)
requireAuth(req, res, next)
```

#### `publicUser(user)`

This converts a full Mongo user document into a safe object for frontend/API use.

It returns:

- `user_id`
- `email`
- `display_name`
- `firstName`
- `lastName`
- `userName`
- `emailId`
- `role`
- `profilePhoto`

Important:

> It does not return password.

#### `requireAuth`

This protects routes.

Step-by-step:

1. Read cookie:

   ```js
   const { token } = req.cookies;
   ```

2. If missing, return 401.
3. Verify JWT with `JWT_SECRET_KEY`.
4. Ensure payload has `emailId` and `userName`.
5. Check Redis blocklist:

   ```js
   redisClient.exists(`token:${token}`)
   ```

6. Load user from Mongo:

   ```js
   User.findOne({ $or: [{ emailId }, { userName }] })
   ```

7. If user does not exist, return 401.
8. Attach safe user to request:

   ```js
   req.user = publicUser(user)
   req.authUser = user
   ```

9. Call `next()`.

##### Why this file exists

It centralizes auth checking.

Without it, every project route would manually verify JWT, Redis, and Mongo user.

Interview answer:

> `requireAuth` is the gateway security gate. It validates the HTTP-only JWT cookie, checks Redis logout blocklist, loads the Mongo user, and attaches safe user data to the request.

#### File 12: `gateway/src/routes/auth.js`

##### What this file does

It defines all authentication APIs.

Routes:

| Route | Purpose |
| --- | --- |
| `POST /api/auth/sendotp` | Send OTP before registration |
| `POST /api/auth/register` | Register user with OTP |
| `POST /api/auth/login` | Login user |
| `POST /api/auth/logout` | Logout user and block token |
| `GET /api/auth/check` | Check current logged-in user |

#### Internal helpers

##### `cookieOptions`

```js
{
  httpOnly: true,
  sameSite: "lax",
  maxAge: 24 * 60 * 60 * 1000
}
```

Meaning:

- `httpOnly`: JavaScript in browser cannot read the cookie.
- `sameSite: "lax"`: helps reduce CSRF risk while allowing normal navigation.
- `maxAge`: cookie lasts 24 hours.

Note:

JWT itself expires in 1 hour. Cookie max-age is longer than token expiry, so after token expiry `requireAuth` will reject it even if cookie remains.

##### `signToken(user)`

Creates JWT payload:

```js
{
  emailId,
  userName,
  role: "user"
}
```

Token expiry:

```text
1 hour
```

##### `isStrongPassword(password)`

Uses `validator.isStrongPassword`.

Requires:

- min length 8
- lowercase
- uppercase
- number
- symbol

##### `generateUniqueOtp()`

Generates random 6-digit OTP and checks Mongo to avoid duplicate OTP value.

##### `persistProjectUser(user)`

Converts Mongo user to public DTO and mirrors lightweight identity to Postgres through:

```js
saveUser(...)
```

This is why Postgres project metadata can reference a user.

#### `POST /sendotp`

Step-by-step:

1. Read `emailId` and `userName`.
2. Validate both exist.
3. Check email is not already registered.
4. Check username is not taken.
5. Generate OTP.
6. Save OTP in Mongo.
7. Send OTP email.
8. Return success.

Why this route exists:

> It verifies email ownership before registration.

#### `POST /register`

Step-by-step:

1. Read registration fields.
2. Validate required fields.
3. Validate password strength.
4. Get latest OTP for email.
5. Compare submitted OTP.
6. Check duplicate email/username.
7. Hash password with bcrypt.
8. Create Mongo user.
9. Delete OTPs for that email.
10. Sign JWT.
11. Send welcome email asynchronously.
12. Save lightweight user in Postgres.
13. Set HTTP-only cookie.
14. Return safe user.

Why this route exists:

> It creates dashboard account only after OTP verification and password hashing.

#### `POST /login`

Step-by-step:

1. Accept email or username plus password.
2. Find Mongo user.
3. Compare password with bcrypt.
4. Sign JWT.
5. Mirror user into Postgres.
6. Set HTTP-only cookie.
7. Return safe user.

Why this route exists:

> It creates authenticated dashboard session.

#### `POST /logout`

Step-by-step:

1. Read token cookie.
2. If no token, return already logged out.
3. Verify token.
4. If Redis is open, store:

   ```text
   token:<jwt> = blocked
   ```

5. Set Redis expiry to JWT expiry.
6. Clear cookie.
7. Return success.

Why Redis blocklist?

JWTs are stateless. Without blocklist, a copied token may remain valid until expiry even after logout.

#### `GET /check`

Uses `requireAuth`.

If valid, returns:

```json
{
  "user": {},
  "message": "Valid User!"
}
```

Why this route exists:

> Frontend uses it on page load to restore session from cookie.

#### File 13: `gateway/src/routes/projects.js`

##### What this file does

It defines all project APIs.

All project routes are mounted behind `requireAuth` from `index.js`.

Routes:

| Route | Purpose |
| --- | --- |
| `GET /api/projects` | List user's projects |
| `POST /api/projects` | Start a new orchestrator run |
| `GET /api/projects/:projectId` | Get one project |
| `GET /api/projects/:projectId/download` | Download generated code |
| `GET /api/projects/:projectId/events` | Stream run events |
| `POST /api/projects/:projectId/input` | Send human input |
| `POST /api/projects/:projectId/cancel` | Cancel run |
| `POST /api/projects/:projectId/preview/stop` | Stop preview |
| `POST /api/projects/:projectId/preview/restart` | Restart preview |

#### Helper functions

##### `getUserId(req)`

Returns:

```js
req.user?.user_id
```

Used to scope project operations to current user.

##### `getSandboxId(project)`

Tries to find sandbox id from multiple locations:

```js
project.last_state.sandboxId
project.last_state.sandbox_id
project.sandbox_id
```

Why:

> Some state fields are camelCase from orchestrator; DB fields are snake_case. This helper handles both.

##### `stopPreviewBestEffort(project)`

Tries to stop preview for a project.

If it fails, it logs a warning instead of crashing project creation/restart.

Why:

> Preview cleanup is useful, but old preview cleanup failure should not always block the user's new project.

##### `getPreviewPatch(req, project, result, running)`

Builds preview metadata update:

- sandbox id
- frontend port
- backend port
- frontend URL
- backend URL
- preview running flag

It normalizes localhost URLs into public URLs when behind a proxy.

##### `ownsProject(req, project)`

Checks:

```js
project.user_id === req.user.user_id
```

This is used in `GET /:projectId` and `GET /:projectId/download`.

Important honest note:

> Some other project routes fetch the project but do not consistently call `ownsProject`. Since all routes require authentication but not all check ownership, a security hardening improvement would be to add the same ownership check to events/input/cancel/preview routes.

#### `GET /api/projects`

Calls:

```js
listProjects(getUserId(req))
```

Returns projects for current user.

#### `POST /api/projects`

This is the most important gateway route.

Step-by-step:

1. Validate `requirement`.
2. Build orchestrator payload:

   ```js
   {
     requirement: req.body.requirement.trim(),
     user_id: getUserId(req),
     token_budget_usd: req.body.token_budget_usd ?? 2.0
   }
   ```

3. Check if user already has a running/queued project.
4. If yes, return 409 conflict.
5. Clear active previews for this user in metadata.
6. Best-effort stop old preview containers.
7. Call orchestrator:

   ```js
   createProjectRun(payload)
   ```

8. Save project metadata:

   ```js
   saveProjectMetadata({
     project_id,
     user_id,
     requirement,
     status
   })
   ```

9. Return project/run response.

Why this route exists:

> It converts a user prompt into a tracked orchestrator run.

#### `GET /api/projects/:projectId`

Step-by-step:

1. Fetch project metadata.
2. If missing, return 404.
3. Check ownership.
4. Return project.

Why:

> Used when dashboard needs a specific project's saved metadata.

#### `GET /api/projects/:projectId/download`

Step-by-step:

1. Fetch project metadata.
2. Check ownership.
3. Extract sandbox id.
4. If no sandbox id, return 400.
5. Call `createProjectZipBuffer(sandboxId)`.
6. Set zip headers.
7. Send zip buffer.

Why download is in gateway:

> Gateway knows authenticated user and project ownership. It can safely decide whether the user may download generated code.

#### `GET /api/projects/:projectId/events`

This is SSE relay route.

Step-by-step:

1. Create `AbortController`.
2. Fetch project metadata.
3. If missing, return 404.
4. Set SSE headers:

   ```text
   Content-Type: text/event-stream
   Cache-Control: no-cache
   Connection: keep-alive
   ```

5. If browser closes connection, abort upstream orchestrator stream.
6. Call:

   ```js
   streamProjectEvents(projectId, onEvent, { signal })
   ```

7. For each event:

   - update project metadata from event
   - write SSE data to frontend

8. End response when upstream stream ends.

Why:

> The orchestrator streams raw events; the gateway relays them and persists latest project state.

#### `POST /api/projects/:projectId/input`

Step-by-step:

1. Fetch project metadata.
2. Validate input type is `pm_clarification` or `escalation`.
3. Forward request body to orchestrator:

   ```js
   submitProjectInput(projectId, req.body)
   ```

4. Return orchestrator result.

Why:

> This resumes paused human-in-the-loop workflow.

#### `POST /api/projects/:projectId/cancel`

Step-by-step:

1. Fetch project metadata.
2. Call orchestrator cancel endpoint.
3. Save metadata as cancelled.
4. Mark preview not running.
5. Return cancel result and updated project.

Why:

> Cancels long-running AI workflow and asks orchestrator to stop sandbox containers.

#### `POST /api/projects/:projectId/preview/stop`

Step-by-step:

1. Fetch project metadata.
2. Clear other active previews for user.
3. Best-effort stop those old previews.
4. Stop this project's preview through orchestrator.
5. Save metadata as preview stopped.
6. Return stopped result and updated project.

Why:

> Frees preview containers/ports without deleting generated code.

#### `POST /api/projects/:projectId/preview/restart`

Step-by-step:

1. Fetch project metadata.
2. Extract sandbox id.
3. If missing, return 400.
4. Clear other active previews for user.
5. Stop other active previews.
6. Call orchestrator restart preview endpoint.
7. Build preview metadata patch.
8. Save project metadata.
9. Return preview URLs/result.

Why:

> Recreates containers from existing sandbox files and starts generated app preview.

Interview answer:

> `projects.js` is the product API for project lifecycle. It starts runs, streams events, submits human input, cancels runs, controls previews, downloads code, and persists project metadata.

#### File 14: `gateway/src/services/orchestratorClient.js`

##### What this file does

It is the HTTP client wrapper for FastAPI orchestrator.

It keeps raw orchestrator calls out of route files.

##### Base URL

```js
const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:8000";
```

##### `readError(response)`

Reads error response body.

If body is JSON, returns stringified JSON.

If not JSON, returns plain text or status text.

Why:

> Gives better error messages when FastAPI fails.

##### `getOrchestratorHealth()`

Calls:

```text
GET /health
```

Used by gateway health endpoint.

##### `createProjectRun(payload)`

Calls:

```text
POST /runs
```

Sends:

```json
{
  "requirement": "...",
  "user_id": "...",
  "token_budget_usd": 2.0
}
```

Receives:

```json
{
  "project_id": "...",
  "status": "running"
}
```

##### `streamProjectEvents(projectId, onEvent, options)`

Calls:

```text
GET /runs/:projectId/events
```

This function manually parses SSE chunks:

1. Reads response body stream.
2. Decodes chunks using `TextDecoder`.
3. Splits by `\n\n`.
4. Finds lines starting with `data: `.
5. Parses JSON event.
6. Calls `onEvent(event)`.

Why manual parsing?

> Node's server-side fetch gives a ReadableStream, not browser `EventSource`. So the gateway parses SSE frames itself.

##### Other functions

| Function | Calls | Purpose |
| --- | --- | --- |
| `cancelProjectRun(projectId)` | `POST /runs/:id/cancel` | Cancel workflow |
| `stopProjectPreview(projectId, sandboxId)` | `POST /runs/:id/preview/stop` | Stop containers |
| `restartProjectPreview(...)` | `POST /runs/:id/preview/restart` | Recreate/start preview |
| `submitProjectInput(projectId, payload)` | `POST /runs/:id/input` | Submit PM/escalation input |

Interview answer:

> `orchestratorClient.js` is an adapter between Node gateway and Python FastAPI. If orchestrator endpoints change, most gateway routes do not need to change directly.

#### File 15: `gateway/src/services/projectStore.js`

##### What this file does

It stores and retrieves project/user metadata.

It uses:

- PostgreSQL if `DATABASE_URL` is configured.
- In-memory maps as fallback.

##### Important exports

```js
saveProjectMetadata(project)
listProjects(userId)
getProjectMetadata(projectId)
updateProjectFromEvent(projectId, event)
clearActivePreviewForUser(userId, exceptProjectId)
saveUser(user)
```

#### `createPool()`

Creates a Postgres pool.

Special handling:

- If database host includes `neon.tech`, it tries IPv4 DNS resolution.
- Uses SSL with `servername` for Neon.
- Otherwise uses normal connection string.

Why:

> Some environments have IPv6/Neon connection issues, so the code tries to resolve IPv4 explicitly.

#### Memory fallback

```js
const memoryProjects = new Map();
const memoryUsers = new Map();
```

Even if Postgres is unavailable, the gateway can still keep metadata temporarily in memory.

Limitation:

> Memory fallback disappears when gateway restarts.

#### `ensureProjectsTable()`

Creates/updates `projects` table.

Columns:

- `project_id`
- `user_id`
- `requirement`
- `status`
- `last_event_type`
- `last_event_node`
- `last_message`
- `last_state`
- `sandbox_id`
- preview ports/URLs
- `preview_running`
- timestamps

It also runs `alter table add column if not exists` for evolving schema.

#### `ensureUsersTable()`

Creates lightweight `users` table:

- `user_id`
- `email`
- `display_name`
- timestamps

#### `normalizeProject(project)`

Converts project object into consistent shape.

Important compatibility:

- reads `sandboxId` from camelCase orchestrator state
- reads `sandbox_id` from DB-style state
- normalizes preview URLs

Why:

> Orchestrator state uses JS-compatible camelCase, while Postgres metadata uses snake_case. This helper bridges both.

#### `saveProjectMetadata(project)`

1. Normalizes project.
2. Saves to memory map.
3. If Postgres is available, upserts into `projects`.

It uses:

```sql
insert ... on conflict (project_id) do update
```

Why:

> Same function can create and update project metadata.

#### `listProjects(userId)`

Returns projects owned by a user, newest first.

If DB fails, uses memory fallback.

#### `getProjectMetadata(projectId)`

Finds one project by id.

First checks memory, then Postgres.

#### `updateProjectFromEvent(projectId, event)`

This is important.

For every streamed orchestrator event, gateway updates:

- status
- last event type
- last event node
- last message
- last state
- sandbox id
- preview ports
- preview URLs
- preview running flag

Status mapping:

```text
run.completed -> completed
run.failed -> failed
run.cancelled -> cancelled
otherwise keep existing status
```

Why:

> The event stream is not only for UI; it is also used to persist latest project state.

#### `clearActivePreviewForUser(userId, exceptProjectId)`

Finds projects where:

```text
preview_running = true
```

and marks them stopped, except a project id if provided.

Why:

> Keeps one active preview per user and avoids port/container clutter.

#### `saveUser(user)`

Mirrors auth user into Postgres.

This is called during register/login through `persistProjectUser()`.

Why:

> Postgres project metadata can list projects by lightweight user id/email/display name without depending on Mongo document queries.

Interview answer:

> `projectStore.js` is the gateway persistence layer for project metadata. It updates state from every streamed event, so project history survives page refreshes.

#### File 16: `gateway/src/services/projectZip.js`

##### What this file does

It creates a downloadable zip buffer from a sandbox folder.

It does not use an external zip dependency. It manually builds ZIP local headers, central directory headers, CRC32, and end record.

##### Why this file exists

The generated app lives in:

```text
sandbox/sandbox-<id>/
```

The user needs to download that generated code.

#### Security checks

##### Safe sandbox id

```js
/^sandbox-\d+$/
```

Only ids like `sandbox-1782600778803` are accepted.

Why:

> Prevents path traversal like `../../somewhere`.

##### Path containment

The file resolves:

```js
sandboxRoot / sandboxId
```

and verifies it starts inside sandbox root.

Why:

> Prevents downloading files outside sandbox root.

##### Exclusions

Directories excluded:

- `.git`
- `node_modules`
- `dist`
- `build`
- `.vite`
- `.cache`
- `coverage`

Files excluded:

- `.env`
- `.DS_Store`
- `*.log`

Why:

- avoid huge zips
- avoid secrets
- avoid build/cache noise

#### Main function

```js
createProjectZipBuffer(sandboxId)
```

Step-by-step:

1. Validate sandbox id.
2. Resolve sandbox path.
3. Ensure path is inside sandbox root.
4. Check folder exists.
5. Recursively walk files.
6. Skip excluded files/folders.
7. Build zip file in memory.
8. Return `Buffer`.

Interview answer:

> `projectZip.js` safely packages generated code. It validates sandbox id, prevents path traversal, excludes secrets/heavy folders, and returns an in-memory zip buffer.

#### File 17: `gateway/src/templates/emailTemplates.js`

##### What this file does

It generates HTML email templates.

Exports:

```js
otpTemplate(otp)
registrationTemplate(name)
```

#### `otpTemplate(otp)`

Creates HTML email containing the OTP.

Used by:

```js
POST /api/auth/sendotp
```

#### `registrationTemplate(name)`

Creates welcome email after registration.

Used by:

```js
POST /api/auth/register
```

##### Why this file exists

It separates email HTML from auth route logic.

Without it, `auth.js` would be cluttered with long HTML strings.

Interview answer:

> `emailTemplates.js` keeps email presentation separate from authentication logic.

#### File 18: `gateway/src/utils/publicUrls.js`

##### What this file does

It builds browser-accessible preview URLs.

Exports:

```js
publicUrlForPort(port, req)
normalizePublicPreviewUrl(url, fallbackPort, req)
```

#### `publicHost(req)`

Chooses host in this order:

1. `PREVIEW_PUBLIC_HOST`
2. `PUBLIC_HOST`
3. `x-forwarded-host`
4. request `host`
5. `localhost`

#### `publicProtocol(req)`

Chooses protocol in this order:

1. `PREVIEW_PUBLIC_PROTOCOL`
2. `PUBLIC_PROTOCOL`
3. `x-forwarded-proto`
4. `http`

#### `publicUrlForPort(port, req)`

Returns:

```text
protocol://host:port
```

Example:

```text
http://localhost:15173
```

#### `normalizePublicPreviewUrl(url, fallbackPort, req)`

If orchestrator returns:

```text
http://localhost:15173
```

but gateway is behind a public host, this function converts it into the public host equivalent.

Why:

> Containers may know localhost URLs, but browser users may need URLs based on the current gateway host/proxy.

Interview answer:

> `publicUrls.js` ensures preview links are browser-accessible, especially when the app runs behind a proxy or non-local host.

#### Main Gateway Flows

#### Auth Flow Diagram

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant Auth as Gateway Auth Routes
  participant Mongo as MongoDB
  participant Mail as Mail Service
  participant Redis as Redis
  participant PG as Postgres User Mirror

  UI->>Auth: POST /api/auth/sendotp
  Auth->>Mongo: Check duplicate user/email
  Auth->>Mongo: Store OTP with TTL
  Auth->>Mail: Send OTP email
  Auth-->>UI: OTP sent

  UI->>Auth: POST /api/auth/register
  Auth->>Mongo: Validate latest OTP
  Auth->>Mongo: Create user with bcrypt hash
  Auth->>Mongo: Delete OTPs
  Auth->>PG: saveUser lightweight mirror
  Auth-->>UI: Set httpOnly cookie + return user

  UI->>Auth: POST /api/auth/logout
  Auth->>Redis: token:<jwt> = blocked until exp
  Auth-->>UI: Clear cookie
```

#### Project Run Flow Diagram

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant Gateway as Gateway projects.js
  participant Store as projectStore.js
  participant Client as orchestratorClient.js
  participant FastAPI as Python Orchestrator

  UI->>Gateway: POST /api/projects
  Gateway->>Gateway: requireAuth already attached req.user
  Gateway->>Store: listProjects(user_id)
  Gateway->>Gateway: Reject if running/queued project exists
  Gateway->>Store: clearActivePreviewForUser(user_id)
  Gateway->>Client: createProjectRun(payload)
  Client->>FastAPI: POST /runs
  FastAPI-->>Client: project_id + running
  Client-->>Gateway: run response
  Gateway->>Store: saveProjectMetadata
  Gateway-->>UI: project created
```

#### Event Stream Flow Diagram

```mermaid
sequenceDiagram
  participant UI as React EventSource
  participant Gateway as Gateway SSE Route
  participant Client as orchestratorClient.js
  participant FastAPI as FastAPI SSE
  participant Store as projectStore.js

  UI->>Gateway: GET /api/projects/:id/events
  Gateway->>Client: streamProjectEvents(id, onEvent)
  Client->>FastAPI: GET /runs/:id/events
  FastAPI-->>Client: data: StreamEvent
  Client-->>Gateway: onEvent(event)
  Gateway->>Store: updateProjectFromEvent(id, event)
  Gateway-->>UI: data: StreamEvent
```

#### Gateway API Summary

| API | Auth required? | Main file/function | Purpose |
| --- | --- | --- | --- |
| `GET /api/health` | No | `index.js` | Gateway + orchestrator health |
| `POST /api/auth/sendotp` | No | `auth.js` | Send registration OTP |
| `POST /api/auth/register` | No | `auth.js` | Register user |
| `POST /api/auth/login` | No | `auth.js` | Login user |
| `POST /api/auth/logout` | No/uses cookie if present | `auth.js` | Logout and block token |
| `GET /api/auth/check` | Yes | `auth.js + requireAuth` | Validate current session |
| `GET /api/projects` | Yes | `projects.js` | List user's projects |
| `POST /api/projects` | Yes | `projects.js` | Start orchestrator run |
| `GET /api/projects/:id` | Yes | `projects.js` | Get one project |
| `GET /api/projects/:id/events` | Yes | `projects.js` | SSE event relay |
| `POST /api/projects/:id/input` | Yes | `projects.js` | Submit human input |
| `POST /api/projects/:id/cancel` | Yes | `projects.js` | Cancel workflow |
| `POST /api/projects/:id/preview/stop` | Yes | `projects.js` | Stop preview containers |
| `POST /api/projects/:id/preview/restart` | Yes | `projects.js` | Restart preview containers |
| `GET /api/projects/:id/download` | Yes | `projects.js + projectZip.js` | Download generated source |
| `WS /ws/projects/:id/events` | Project existence checked | `index.js` | WebSocket event relay |

#### Important Interview Questions And Answers

##### Why do we need the gateway?

> Because the frontend should not directly call the internal AI orchestrator. The gateway handles auth, ownership, project metadata, streaming relay, preview control, and download authorization.

##### Why Mongo and Postgres both?

> Mongo stores full auth users and OTPs through Mongoose. Postgres stores project metadata and a lightweight user mirror for project ownership/history. They serve different purposes.

##### Why Redis?

> Redis is used for JWT logout blocklisting. When a user logs out, the current token is stored as blocked until its expiry.

##### Why does the gateway relay events instead of frontend calling FastAPI directly?

> Because the gateway can update project metadata from events and keep the frontend behind one authenticated API boundary.

##### Why is project zip done in gateway?

> The gateway knows the authenticated user and can check whether they own the project before sending generated code.

##### Why have `orchestratorClient.js`?

> It isolates FastAPI communication. Routes call named functions instead of hardcoding fetch logic everywhere.

##### What should be improved?

Good honest answer:

> `GET /:projectId` and download check ownership, but events/input/cancel/preview routes currently fetch the project without consistently calling `ownsProject`. Since all project routes require auth, they are protected from anonymous users, but I would harden authorization by adding ownership checks to every project-specific route.

#### Gateway Mental Model

Keep this in your head:

```text
index.js
  = starts gateway server and wires routes/services

auth.js
  = signup/login/logout/check

projects.js
  = project lifecycle APIs

orchestratorClient.js
  = talks to FastAPI

projectStore.js
  = saves project/user metadata

projectZip.js
  = creates safe code download

auth middleware
  = verifies cookie/JWT/Redis/Mongo user

models
  = Mongo schemas for auth user and OTP

config
  = Mongo, Redis, Mail connections
```

#### Final Interview Explanation

> The gateway is the public backend layer. Its entry file `index.js` configures Express, CORS, cookies, health checks, auth routes, protected project routes, and WebSocket event relay. Auth is handled in `routes/auth.js` using Mongoose user and OTP models, bcrypt password hashing, JWT cookies, Redis token blocklist, and Nodemailer OTP/welcome emails. Project lifecycle is handled in `routes/projects.js`, which lists projects, starts orchestrator runs, relays events, submits human input, cancels runs, manages preview stop/restart, and downloads generated code. The gateway does not directly implement LangGraph. It calls FastAPI through `orchestratorClient.js`. Project metadata is stored through `projectStore.js`, and generated code download is safely packaged by `projectZip.js`.
>
> So the gateway's job is to be the secure product API boundary between the browser and the internal AI orchestration engine.

</details>

<details id="inline-08-orchestrator-deep-dive">
<summary>08_orchestrator_deep_dive.md - Question 8: Orchestrator Deep Dive, File By File</summary>

### Question 8: Orchestrator Deep Dive, File By File

This note explains the entire `orchestrator/` layer.

Read this when you want to answer interview questions like:

- What does the orchestrator do?
- How is it connected to the gateway?
- How is the LangGraph graph created?
- How is the graph invoked?
- How does streaming work?
- How does human input pause/resume the workflow?
- How is the Docker sandbox created, restarted, stopped, and cleaned?
- Why did we keep orchestration separate from the Node gateway?

#### One-Line Summary

The orchestrator is the internal Python AI execution engine. The gateway starts a project run, the orchestrator runs a LangGraph workflow over `AgentState`, emits realtime events, creates a Docker sandbox, writes/reviews/tests generated code, checkpoints state, and finally starts a preview of the generated app.

Interview line:

> The gateway is the secure product API layer; the orchestrator is the internal AI runtime. We separated them so authentication, project ownership, and dashboard APIs do not get mixed with long-running LangGraph execution, Gemini calls, Docker sandbox control, retries, checkpoints, and generated-code execution.

#### Where The Orchestrator Sits In The Three-Layer Architecture

```text
React Frontend
  |
  | browser API calls, cookies, SSE/WebSocket
  v
Node Gateway
  |
  | internal JSON/SSE calls
  v
Python FastAPI + LangGraph Orchestrator
  |
  | Docker CLI / mounted sandbox folder / Gemini / Redis
  v
Generated Project Sandbox
```

The browser does not directly call the orchestrator in normal app flow. The frontend calls the gateway. The gateway checks authentication and project ownership, then calls the orchestrator.

#### Gateway To Orchestrator Contract

Gateway file involved:

- `gateway/src/services/orchestratorClient.js`

Orchestrator file involved:

- `orchestrator/app/main.py`

The gateway calls these orchestrator endpoints:

| Gateway action | Orchestrator endpoint | Purpose |
| --- | --- | --- |
| Health check | `GET /health` | Verify Python service is alive |
| Create project | `POST /runs` | Start a background LangGraph run |
| Stream events | `GET /runs/{project_id}/events` | Read orchestrator SSE events |
| Cancel build | `POST /runs/{project_id}/cancel` | Cancel asyncio workflow task and stop sandbox containers |
| Submit human input | `POST /runs/{project_id}/input` | Resume a paused human-input node |
| Read input history | `GET /runs/{project_id}/input` | Debug/review previous input requests |
| Stop preview | `POST /runs/{project_id}/preview/stop` | Stop generated app containers |
| Restart preview | `POST /runs/{project_id}/preview/restart` | Reconnect sandbox and restart DB/backend/frontend preview |

Important interview point:

> FastAPI endpoints are internal orchestration endpoints, not the public product API. The public product API is the Node gateway.

#### Why Orchestration Is Separate From Gateway

This is one of the most important interview answers.

##### Reason 1: Different responsibilities

The gateway owns:

- browser-facing routes
- JWT cookies
- OTP signup/login
- logout token blocklist
- project ownership
- project metadata
- download authorization
- event relay to frontend

The orchestrator owns:

- LangGraph workflow
- AI agent prompts
- Pydantic `AgentState`
- Gemini model calls
- node routing
- retry limits
- human-in-the-loop pauses
- Docker sandbox creation
- generated app execution
- git snapshots
- deployment verification

If we merged these into one FastAPI backend, one service would become both:

1. the public user/session API, and
2. the dangerous internal AI/Docker execution runtime.

That is possible, but it is harder to secure, explain, test, and evolve.

##### Reason 2: The orchestrator is long-running

A gateway route should quickly accept a request and return.

An orchestrator run can take minutes:

- clarify requirement
- design entities
- design schema
- design APIs
- design pages
- validate blueprint
- plan tasks
- create sandbox
- generate files
- review code
- execute checks
- debug failures
- verify deployment
- start preview

So the gateway starts a run and returns a `project_id`. The orchestrator continues in the background and streams events.

##### Reason 3: The orchestrator controls Docker

The orchestrator has access to the Docker socket:

```text
/var/run/docker.sock:/var/run/docker.sock
```

That gives it power to create and remove containers. We do not want the browser-facing API layer to be the same layer that directly exposes Docker control logic.

The gateway acts as a safer gate in front of that.

##### Reason 4: Python is the better home for LangGraph/Gemini workflow

LangGraph, Pydantic, async workflow state, and Python AI tooling fit naturally in the orchestrator.

Node/Express fits naturally for:

- web sessions
- browser cookies
- frontend API boundary
- project metadata routes
- SSE/WebSocket relay

So the split follows the strengths of each runtime.

##### Reason 5: Independent scaling and debugging

Gateway problems and orchestrator problems are different.

Gateway debugging:

- is the user logged in?
- is JWT valid?
- is project ownership correct?
- is Postgres metadata saved?
- is the SSE forwarded to browser?

Orchestrator debugging:

- which graph node failed?
- did Gemini return valid JSON?
- did Docker start?
- did npm install fail?
- did generated code pass review?
- did deployment verification fail?

Keeping them separate makes logs and responsibility clearer.

##### Best interview answer

> We separated the orchestrator from the gateway because the gateway is a user-facing API boundary, while the orchestrator is an internal long-running AI execution engine. The gateway handles auth, ownership, metadata, download authorization, and event relay. The orchestrator handles LangGraph, Gemini calls, retries, human input, Docker sandboxing, checkpoints, and generated-code execution. Direct frontend-to-FastAPI would either expose internal orchestration/Docker endpoints or force FastAPI to also implement all product backend responsibilities. The three-layer split is cleaner, safer, and easier to scale.

#### Orchestrator Folder Structure

```text
orchestrator/
  Dockerfile
  requirements.txt
  app/
    __init__.py
    main.py
    graph/
      __init__.py
      workflow.py
    models/
      __init__.py
      contracts.py
    nodes/
      __init__.py
      _shared.py
      agent_nodes.py
      architectAgent.py
      assembleEntryPoints.py
      blueprintValidator.py
      coderAgent.py
      contextBuilder.py
      debuggerAgent.py
      deploymentVerifier.py
      executorAgent.py
      humanEscalation.py
      humanInput.py
      patternExtractor.py
      phaseVerification.py
      plannerAgent.py
      pmAgent.py
      presentToUser.py
      reviewerAgent.py
      sandboxHealthCheck.py
      selectNextTask.py
      setupSandbox.py
      simplifyTask.py
      snapshotManager.py
      stateCompactor.py
      updateRegistry.py
    services/
      __init__.py
      event_bus.py
      gemini_client.py
      input_bridge.py
      redis_checkpoint.py
      run_manager.py
      sandbox.py
      sandbox_database.py
      sandbox_files.py
      sandbox_lifecycle.py
      sandbox_preview.py
      sandbox_process.py
      sandbox_runtime.py
      sandbox_scaffold.py
      sandbox_state.py
```

Diagram:

```mermaid
flowchart TB
  Gateway[Node Gateway] --> Main[app/main.py]
  Main --> Workflow[graph/workflow.py]
  Workflow --> Contracts[models/contracts.py]
  Workflow --> Nodes[nodes/*.py]
  Workflow --> EventBus[services/event_bus.py]
  Workflow --> Checkpoint[services/redis_checkpoint.py]
  Nodes --> Gemini[services/gemini_client.py]
  Nodes --> SandboxFacade[services/sandbox.py]
  SandboxFacade --> Runtime[services/sandbox_runtime.py]
  SandboxFacade --> Files[services/sandbox_files.py]
  SandboxFacade --> Preview[services/sandbox_preview.py]
  Runtime --> Scaffold[services/sandbox_scaffold.py]
  Runtime --> Process[services/sandbox_process.py]
  Runtime --> Database[services/sandbox_database.py]
  Process --> Docker[Docker Engine]
```

#### End-To-End Flow

```text
1. User enters requirement in React.
2. React calls gateway POST /api/projects.
3. Gateway checks auth and active project rules.
4. Gateway calls orchestrator POST /runs.
5. FastAPI creates project_id.
6. FastAPI emits run.created event.
7. FastAPI starts run_workflow(...) as an asyncio background task.
8. Gateway saves project metadata.
9. Frontend opens event stream through gateway.
10. Gateway reads orchestrator /runs/{id}/events.
11. LangGraph starts from pmAgent.
12. Every node emits node.started and node.completed.
13. Every node checkpoints AgentState to Redis if Redis is configured.
14. Orchestrator creates Docker sandbox.
15. Agents generate, review, execute, debug, and snapshot generated files.
16. Deployment verifier builds/probes generated app.
17. presentToUser starts preview servers.
18. Orchestrator emits run.completed.
19. Gateway saves last_state and forwards event to frontend.
```

#### File 1: `orchestrator/Dockerfile`

##### What it does

Builds the Python orchestrator container.

Important behavior:

- Uses `python:3.12-slim`.
- Installs `ca-certificates` and `git`.
- Copies the Docker CLI from `docker:27-cli`.
- Installs Python dependencies from `requirements.txt`.
- Runs Uvicorn on port `8000`.

##### Why Docker CLI is included

The orchestrator creates generated project containers at runtime.

It needs to run commands like:

```text
docker run ...
docker rm -f ...
docker network create ...
docker exec ...
docker port ...
```

The Dockerfile includes the Docker CLI, and the root `docker-compose.yml` mounts the host Docker socket. Together, those allow the orchestrator container to control Docker on the host.

##### What happens if this is missing

The orchestrator may still run FastAPI, but sandbox creation would fail because Python would not be able to call Docker.

#### File 2: `orchestrator/requirements.txt`

##### What it does

Defines Python dependencies:

| Package | Why used |
| --- | --- |
| `fastapi` | HTTP API for orchestration endpoints |
| `uvicorn[standard]` | ASGI server that runs FastAPI |
| `pydantic` | Validates request models and `AgentState` |
| `langgraph` | Creates the workflow graph/state machine |
| `langchain-core` | Prompt/core LangChain utilities |
| `langchain-google-genai` | Gemini model integration |
| `redis` | Redis checkpoint client |
| `python-dotenv` | Environment variable support |

##### Interview explanation

> `requirements.txt` is small because the orchestrator is focused: FastAPI for API, LangGraph for workflow, Pydantic for state contracts, Gemini client for AI calls, Redis for checkpoints.

#### File 3: `orchestrator/app/__init__.py`

This file marks `app/` as a Python package.

It allows imports such as:

```python
from app.main import app
```

The file is intentionally empty.

#### File 4: `orchestrator/app/main.py`

This is the FastAPI entrypoint.

It exposes the internal orchestration API that the gateway calls.

##### `app = FastAPI(...)`

Creates the FastAPI app:

```text
title = AI Dev Team Orchestrator
version = 1.0.0
```

##### `GET /health`

Returns:

```json
{
  "status": "ok",
  "layer": "python-fastapi-langgraph-orchestrator"
}
```

The gateway calls this in `/api/health`.

Why this exists:

- lets the gateway know the orchestrator is reachable
- helps debug startup issues
- proves the third layer is alive

##### `POST /runs`

This starts a new AI project build.

Flow:

```text
1. Generate project_id like project-<random>.
2. Append run.created event.
3. Start run_workflow(project_id, payload) using asyncio.create_task.
4. Register the task in run_manager.
5. Add callback to unregister task when done.
6. Return project_id and status=running immediately.
```

Important:

The endpoint does not wait for the whole graph to finish. It starts the graph in the background.

Why this matters:

> AI code generation is a long-running job. The API should return quickly and stream progress instead of blocking the browser for minutes.

##### `GET /runs/{project_id}/events`

Streams events as Server-Sent Events.

Each event is sent like:

```text
data: {"type":"node.started","node":"pmAgent","message":"pmAgent started","state":{...}}

```

The gateway consumes this stream and forwards it to the frontend.

##### `POST /runs/{project_id}/cancel`

Cancels the background asyncio task and stops sandbox containers.

Flow:

```text
1. run_manager.cancel_run(project_id)
2. stop_sandbox_containers(project_id)
3. If no active task exists, emit run.cancelled anyway.
4. Return cancellation result.
```

Why stop containers too?

Because cancelling the graph should also stop generated app previews. Otherwise containers may keep running and ports may remain occupied.

##### `POST /runs/{project_id}/preview/stop`

Stops preview containers.

It accepts an optional `sandbox_id`. If the gateway knows the sandbox id, it sends it. If not, FastAPI falls back to `project_id`.

##### `POST /runs/{project_id}/preview/restart`

Restarts preview containers.

It can receive:

- `sandbox_id`
- `user_id`
- preferred backend port
- preferred frontend port

Then it calls `restart_sandbox_preview(...)`.

##### `POST /runs/{project_id}/input`

Receives human input from the gateway.

Used when the graph is waiting for:

- PM clarification
- escalation decision after repeated failures

##### `GET /runs/{project_id}/input`

Returns input history from the in-memory input bridge.

Useful for debugging.

#### File 5: `orchestrator/app/graph/__init__.py`

Package marker for `app.graph`.

It is empty because the main graph is in `workflow.py`.

#### File 6: `orchestrator/app/graph/workflow.py`

This is the most important orchestrator file.

It builds and invokes the LangGraph workflow.

##### Main imports

It imports:

- `StateGraph`, `START`, `END` from LangGraph
- `AgentState`, `RunCreateRequest`, `StreamEvent`
- every node function
- every router function
- `append_event`
- `checkpoint_state`

##### `_run_node(state, node_name, fn)`

This wrapper runs around every node.

It does four things:

```text
1. Convert dict state into AgentState if needed.
2. Emit node.started event.
3. Call the actual node function.
4. Save checkpoint to Redis.
5. Emit node.completed event.
6. Return state as dict for LangGraph.
```

This wrapper is why every node automatically appears in the UI stream.

Without it:

- frontend would not know which node is running
- gateway would not receive state snapshots
- Redis checkpointing would be inconsistent
- debugging would become much harder

##### `_state(state)`

Ensures router functions always receive an `AgentState`, not a raw dict.

Why needed:

LangGraph may pass state as a dict between nodes. The project wants Pydantic validation and dot-access fields, so this helper normalizes it.

##### `_route(router)`

Wraps router functions so they can safely receive normalized state.

##### `_pm_router(state)`

Routes after `pmAgent`:

| PM status | Next node |
| --- | --- |
| `needs_clarification` | `humanInput` |
| `spec_ready` | `architectStep1` |
| anything else | `END` |

##### `_node(node_name, fn)`

Creates an async wrapper for each node.

This keeps `build_graph()` clean:

```python
graph.add_node("pmAgent", _node("pmAgent", pmAgentNode))
```

##### `build_graph()`

Creates:

```python
graph = StateGraph(AgentState)
```

Then adds all nodes and edges.

The graph has these big stages:

```text
PM / clarification
  -> Architecture blueprint
  -> Blueprint validation / repair loop
  -> Planning
  -> Sandbox setup
  -> Dev loop
  -> Deployment verification
  -> Present to user
```

##### Main LangGraph route

High-level route:

```text
START
  -> pmAgent
  -> humanInput loop if needed
  -> architectStep1
  -> architectStep2
  -> architectStep3
  -> architectStep4
  -> architectStep5
  -> blueprintValidator
  -> plannerAgent
  -> setupSandbox
  -> sandboxHealthCheck
  -> selectNextTask
  -> contextBuilder
  -> coderAgent
  -> updateRegistry
  -> reviewerAgent
  -> executorAgent
  -> snapshotManager
  -> selectNextTask again
  -> phaseVerification between phases
  -> deploymentVerifier
  -> presentToUser
  -> END
```

##### Important conditional loops

| Node | Router decision |
| --- | --- |
| `pmAgent` | ask human input or continue to architecture |
| `blueprintValidator` | repair architect step 2/3/4 or continue |
| `sandboxHealthCheck` | retry sandbox setup, fail, or continue |
| `selectNextTask` | continue dev loop, verify phase, or deploy |
| `reviewerAgent` | execute if approved, retry coding, or simplify |
| `executorAgent` | snapshot if pass, debug if fail |
| `debuggerAgent` | retry coding or escalate to human |
| `humanEscalation` | skip, guide, or simplify |
| `deploymentVerifier` | present if pass, debug if fail |

##### `run_workflow(project_id, payload)`

This is invoked by `main.py` after `POST /runs`.

Flow:

```text
1. Build/compile graph.
2. Create initial AgentState.
3. Call graph.ainvoke(state, recursion_limit=500).
4. Convert final state back to AgentState if needed.
5. Emit run.completed if success.
6. Emit run.failed if failed/error.
7. Emit run.cancelled if asyncio task is cancelled.
```

Why `recursion_limit=500`?

Because this graph can loop:

- PM clarification loop
- blueprint repair loop
- per-task dev loop
- review retry loop
- debug retry loop
- phase verification loop

The limit prevents infinite loops while allowing a large multi-step build.

#### File 7: `orchestrator/app/models/__init__.py`

Package marker for `app.models`.

It is intentionally empty.

#### File 8: `orchestrator/app/models/contracts.py`

This file defines the Pydantic models used by FastAPI and LangGraph.

##### `RunCreateRequest`

Request body for `POST /runs`.

Fields:

| Field | Meaning |
| --- | --- |
| `requirement` | User's natural language project request |
| `user_id` | User identity forwarded by gateway |
| `token_budget_usd` | Max estimated AI spend |

Why this exists:

It gives the orchestrator a validated contract for starting a run.

##### `RunCreateResponse`

Response from `POST /runs`.

Fields:

| Field | Meaning |
| --- | --- |
| `project_id` | ID used for event streaming, cancel, input, preview |
| `status` | `running` or `queued` |

##### `HumanInputSubmitRequest`

Request body for `POST /runs/{project_id}/input`.

Fields:

| Field | Meaning |
| --- | --- |
| `type` | `pm_clarification` or `escalation` |
| `answers` | answers to PM questions |
| `choice` | escalation choice: `guide`, `skip`, or `simplify` |
| `guidance` | human guidance text |
| `data` | flexible extra payload |

##### `TokenUsage`

Tracks model usage:

- individual calls
- total input tokens
- total output tokens
- estimated cost

The frontend can show cost/progress from streamed state.

##### `AgentState`

This is the shared workflow state.

Every LangGraph node receives and returns `AgentState`.

Major groups:

| Group | Fields |
| --- | --- |
| Identity | `projectId`, `userId` |
| User input | `userRequirement` |
| PM | `pmStatus`, `pmQuestions`, `pmConversation`, `clarifiedSpec` |
| Architecture | `blueprint`, `blueprintValidation` |
| Planning | `taskQueue`, `currentPhaseIndex`, `currentTaskIndex` |
| Registry/patterns | `fileRegistry`, `projectPatterns` |
| Sandbox | `sandboxId`, `sandboxHealthy`, `fileTree`, preview ports/URLs |
| Dev loop | `currentTask`, `taskStatuses`, `contextPackage`, `coderOutput`, `reviewResult`, `executionResult`, `debugState` |
| Retry control | `retryCounts`, `retryLimits` |
| Feedback/deploy | `userFeedback`, `deploymentConfig`, `deploymentAttempts` |
| Token/control | `tokenUsage`, `tokenBudget`, `currentPhase`, `error`, `terminalOutput`, `gitSnapshots` |

Why this is critical:

> `AgentState` is the single source of truth for the entire build. LangGraph routes based on it, nodes update it, events stream it, Redis checkpoints it, and the frontend displays it.

##### `StreamEvent`

The realtime event shape:

| Field | Meaning |
| --- | --- |
| `type` | event type like `node.started`, `input.requested`, `run.completed` |
| `node` | node that emitted the event |
| `message` | human-readable message |
| `state` | optional state snapshot |

#### Node Files Overview

The nodes are the actual agent workflow steps.

Each node usually follows this pattern:

```text
Input: AgentState
Work: read/update one responsibility
Output: AgentState
Router: decide next node when needed
```

#### File 9: `orchestrator/app/nodes/__init__.py`

Package marker for `app.nodes`.

It is empty.

#### File 10: `orchestrator/app/nodes/_shared.py`

Shared helper functions used across nodes.

Important helpers:

| Helper | Purpose |
| --- | --- |
| `log(state, message)` | Adds message to `state.terminalOutput` |
| `task_id(task)` | Safely extracts task id |
| `retry_key(...)` | Creates retry-counter key, optionally task-scoped |
| `retry_count(...)` | Reads retry count |
| `retry_limit(...)` | Reads configured limit from state |
| `increment_retry(...)` | Increments retry count |
| `reset_retry(...)` | Clears retry count |
| `snake_case`, `kebab_plural`, `table_name`, `camel_case` | Naming utilities |
| `clone(...)` | Deep copy |
| `now_ms()` | Timestamp |
| `merge_file_registry(...)` | Merges generated file interface metadata |
| `apply_token_delta(...)` | Adds model token/cost usage |
| `read_jsonish(...)` | Parses JSON with fallback |
| `import_statement_for(...)` | Builds ES module import statements |

Why this file exists:

Common logic like retry counters and token accounting should not be duplicated in every node.

Interview point:

> `_shared.py` supports consistency: all nodes use the same retry-counting, logging, token tracking, naming, and registry merge logic.

#### File 11: `orchestrator/app/nodes/agent_nodes.py`

Compatibility export file.

It maps older snake_case names to the current JS-style node filenames and function names.

Example idea:

```text
pm_agent -> pmAgentNode
coder_agent -> coderAgentNode
deployment_verifier -> deploymentVerifierNode
```

Why this exists:

This project was ported from a JavaScript-style LangGraph workflow. This file keeps older imports working while preserving the requested node names like `pmAgent.py`, `coderAgent.py`, etc.

#### File 12: `orchestrator/app/nodes/pmAgent.py`

The PM Agent turns a vague user requirement into a clear product specification.

##### What it does

It sends the user requirement to Gemini with a PM prompt.

The response must be one of:

1. `needs_clarification`
2. `spec_ready`

If the requirement is unclear, the PM Agent creates questions.

If the requirement is clear, it creates `clarifiedSpec`.

##### How it handles clarification

If `pmConversation` is empty:

```text
Use original requirement.
```

If the user already answered questions:

```text
Use original requirement + conversation so far.
Force final spec_ready.
```

##### Retry behavior

The PM clarification retry limit defaults to `2`.

If the PM keeps asking questions after the limit:

- it stops asking
- creates a default spec from assumptions
- moves to architecture

Why this is important:

Without a retry limit, the graph could get stuck asking clarifying questions forever.

##### Why this node exists

User prompts are often vague:

```text
"build me a notes app"
```

The downstream architecture/coding agents need structured information:

- app name
- roles
- auth requirement
- features
- database recommendation
- pages
- assumptions

The PM node creates that structure.

#### File 13: `orchestrator/app/nodes/humanInput.py`

This node pauses the graph for user clarification.

##### What it does

If `state.pmQuestions` exists:

```text
1. Call wait_for_input(projectId, "pm_clarification", questions).
2. Wait until gateway/frontend submits answers.
3. Add user's answer to pmConversation.
4. Reset pmStatus to idle.
5. Return to pmAgent.
```

##### Why this node exists

Some requirements cannot be safely assumed.

Example:

```text
"Build a booking system"
```

The system may need to ask:

- who can book?
- are there admins?
- are payments needed?
- what resources are booked?

##### What happens if missing

The PM would either:

- make too many assumptions, or
- get stuck with no way to ask the user.

#### File 14: `orchestrator/app/nodes/architectAgent.py`

This file contains five architecture nodes.

The architecture is intentionally split into five steps instead of one giant prompt.

Why split?

- Smaller prompts are easier to validate.
- Each step has one responsibility.
- Blueprint validator can route back to the exact broken step.
- It reduces hallucination and naming inconsistency.

##### `architectStep1Node`

Builds entity and relationship map.

Output:

- entities
- table names
- API paths
- model file names
- route file names
- relationships

Why needed:

Everything downstream depends on consistent entity naming.

##### `architectStep2Node`

Builds database schema.

Output:

- database type
- tables
- fields
- constraints
- foreign keys
- indexes

Why needed:

Coder Agent needs precise schema before writing models/controllers.

##### `architectStep3Node`

Builds REST API endpoint design.

Output:

- method
- path
- request body
- response body
- related table
- auth requirement
- role access

Why needed:

Frontend and backend must agree on API contracts.

##### `architectStep4Node`

Builds frontend page/component design.

Output:

- pages
- routes
- components
- which APIs each component calls
- auth requirements

Why needed:

The frontend coding tasks need a page map and API call map.

##### `architectStep5Node`

Builds folder structure and dependency plan.

Output:

- folder tree
- backend `package.json` dependencies
- frontend `package.json` dependencies

Why needed:

The sandbox scaffold and planner need to know what dependencies and folders to create.

#### File 15: `orchestrator/app/nodes/blueprintValidator.py`

Validates architecture output before planning/coding.

##### What it checks

| Check | Why |
| --- | --- |
| Entity has matching DB table | Avoid models/controllers for missing tables |
| Foreign keys reference existing tables | Avoid invalid SQL schema |
| API relatedTable exists | Avoid endpoints pointing to nonexistent DB |
| Frontend API calls exist | Avoid UI calling missing backend route |
| Auth mismatch | Avoid public pages calling protected APIs incorrectly |
| Orphan tables | Warn if DB table has no API |

##### Router behavior

If valid:

```text
blueprintValidator -> plannerAgent
```

If invalid:

```text
missing table or FK -> architectStep2
orphan endpoint/missing API -> architectStep3
auth mismatch -> architectStep4
```

##### Retry behavior

It uses `blueprintRepairs` retry limit.

After the limit, it can force proceed with warnings.

Why this exists:

Without validation, the project could waste many coding steps building from a broken blueprint.

Interview line:

> `blueprintValidator` is an early quality gate. It catches architectural inconsistencies before the expensive coding loop starts.

#### File 16: `orchestrator/app/nodes/plannerAgent.py`

Turns the validated blueprint into an ordered task queue.

##### What it creates

`state.taskQueue`, shaped like:

```text
phases:
  setup
  models
  middleware
  backend
  frontend
  integration
  deployment
```

Each task includes:

- `taskId`
- title
- description
- files to create
- files needed
- acceptance criteria
- can parallelize
- estimated tokens

##### Important design rule

The planner is told not to recreate scaffold files like:

- `backend/src/config/db.js`
- `backend/src/middleware/auth.js`
- `backend/src/index.js`
- `frontend/src/App.jsx`
- `frontend/src/utils/api.js`

Why:

Those files are created by the sandbox scaffold and later assembled automatically.

##### Why this node exists

The coder should not receive the entire app at once.

Planning breaks the app into manageable tasks so each coding/review/execution cycle is smaller and more reliable.

#### File 17: `orchestrator/app/nodes/setupSandbox.py`

Creates the generated project sandbox.

##### What it does

Calls:

```text
create_sandbox(projectId, userId, folderStructure, dependencies, dbSchema)
```

Then it seeds `fileRegistry` with scaffolded files:

- DB config
- auth middleware
- backend entry
- frontend API utility
- React main
- React App

It also records preview URLs/ports if available.

##### Why this node exists

The agents need a real workspace to write files into.

The sandbox gives them:

- backend folder
- frontend folder
- package files
- config files
- DB container
- backend container
- frontend container
- git repository

Without it, coder/executor/reviewer would only operate in memory, not against a real generated app.

#### File 18: `orchestrator/app/nodes/sandboxHealthCheck.py`

Checks whether the sandbox is usable.

##### What it checks

- backend folder exists
- frontend folder exists
- backend package exists
- frontend package exists
- git initialized
- DB container responds
- backend container responds
- frontend container responds
- node_modules installed

It has a local-only fallback for cases where folders exist but Docker/container checks are imperfect.

##### Router behavior

| Condition | Next |
| --- | --- |
| healthy | `selectNextTask` |
| unhealthy but retries remain | `setupSandbox` |
| unhealthy and retry limit reached | `presentToUser` with failure |

##### Why this node exists

It prevents the coding workflow from starting in a broken runtime.

#### File 19: `orchestrator/app/nodes/selectNextTask.py`

Chooses the next task from `taskQueue`.

##### What it does

It scans phases and tasks:

```text
first pending task -> currentTask
all tasks in phase done -> phase verification task
all phases verified -> currentPhase done
```

##### Router behavior

| Current phase | Next node |
| --- | --- |
| `done` | `presentToUser` |
| `phase_verification` | `phaseVerification` |
| has `currentTask` | `contextBuilder` |
| fallback | `presentToUser` |

##### Why this node exists

This is the task scheduler inside the graph.

Without it, the graph would not know which generated file/task to work on next.

#### File 20: `orchestrator/app/nodes/contextBuilder.py`

Builds the exact context package for the coder.

##### What it includes

- current task details
- acceptance criteria
- project patterns
- dependency interfaces
- DB schema relevant to current task
- API endpoints relevant to frontend task
- naming map
- app name
- auth requirement
- optional template file

##### Important intelligence

It automatically adds needed files depending on task type:

- backend route task needs controllers/middleware/config
- backend controller task needs models/middleware/config
- frontend page task needs API utilities/context/hooks
- integration task needs many existing files

It can also inspect existing files and extract basic exports/imports.

##### Why this node exists

LLMs produce better code when given focused context.

Without this node:

- coder may import wrong functions
- coder may miss existing files
- frontend/backend contracts may drift
- generated files may duplicate scaffold files

Interview line:

> `contextBuilder` is the retrieval/context layer for each coding task. It packages only what the coder needs, instead of dumping the whole project into every prompt.

#### File 21: `orchestrator/app/nodes/coderAgent.py`

Generates code files.

##### What it does

For every `filesToCreate` entry:

```text
1. Choose backend or frontend prompt.
2. Build file-specific prompt.
3. Include acceptance criteria and context package.
4. If retry, include reviewer/executor issues and current file content.
5. Call Gemini expecting strict JSON.
6. Write generated content into sandbox.
7. Update coderOutput.
```

##### Backend rules

The backend prompt enforces:

- ES modules
- parameterized queries
- backend layering
- routes are thin
- controllers handle request/response
- models handle DB only
- consistent response format
- JWT Bearer auth
- no hardcoded secrets

##### Frontend rules

The frontend prompt enforces:

- React functional components
- hooks
- Tailwind dark design system
- loading/error states
- controlled forms
- Vite env usage
- API utility import

##### Scaffold protection

It skips scaffold files like:

- `backend/src/index.js`
- `backend/src/config/db.js`
- `frontend/src/App.jsx`

Those are managed by scaffold/assembly logic, not arbitrary coder output.

##### Why this node exists

This is the actual code-generation worker.

But it is intentionally not allowed to do everything freely. It writes task-scoped files under strict architecture and style rules.

#### File 22: `orchestrator/app/nodes/updateRegistry.py`

Indexes generated files after coding.

##### What it does

Reads newly generated files and asks Gemini to extract:

- default export
- named exports
- exact import statement
- interface summary

Then merges those entries into `state.fileRegistry`.

##### Why this node exists

Future tasks need to import previously generated code correctly.

Example:

If a controller exports:

```text
getNotes
createNote
```

Route generation needs to know exactly what to import.

Without the registry, the coder may guess wrong import names.

#### File 23: `orchestrator/app/nodes/reviewerAgent.py`

Reviews generated code before execution.

##### What it does

It reads generated files and sends them to Gemini with a reviewer checklist.

It also performs deterministic backend layering checks in Python.

##### Reviewer checks

- imports are correct
- exports match
- async/await is correct
- response format is consistent
- auth pattern is correct
- request/response fields match
- env vars are correct
- model/controller/route layering is respected
- SQL is parameterized
- no hardcoded secrets
- acceptance criteria are met

##### Deterministic checks

The file includes Python checks for backend layering:

- route file importing models is rejected
- route file doing DB queries is rejected
- route file containing bcrypt/JWT logic is rejected
- controller file creating Router is rejected
- model file using `req`/`res` is rejected
- `bcrypt` vs `bcryptjs` mismatch is rejected

##### Router behavior

| Review result | Next |
| --- | --- |
| approved | `executorAgent` |
| rejected and retries left | `contextBuilder` |
| rejected and retry limit reached | `simplifyTask` |

##### Why this node exists

The reviewer is a quality gate before running generated code.

It catches many errors cheaper than runtime execution.

#### File 24: `orchestrator/app/nodes/executorAgent.py`

Runs basic checks against generated files.

##### What it does

Checks:

- generated files exist
- JavaScript syntax with `node --check` when Docker is available
- import paths resolve
- named imports exist in registry
- frontend does not use `process.env`
- backend does not use `import.meta.env`
- npm install works when needed

##### Router behavior

| Execution result | Next |
| --- | --- |
| pass | `snapshotManager` |
| fail | `debuggerAgent` |

##### Why this node exists

The reviewer may miss syntax/import/runtime issues. Executor catches concrete failures from files and environment.

#### File 25: `orchestrator/app/nodes/debuggerAgent.py`

Analyzes executor failures and tells coder how to fix them.

##### What it does

Reads:

- error output
- current task
- failing files
- optionally related files

Then Gemini returns:

- root cause
- fix
- affected files
- confidence

The debugger turns that into `reviewResult = rejected`, so the coder retries with targeted feedback.

##### Retry/rollback behavior

It tracks task-scoped debug attempts.

If attempts exceed the limit:

- it tries to roll back to the last good git snapshot
- if rollback fails or is exhausted, it escalates to human

##### Router behavior

| Debug tier | Next |
| --- | --- |
| tier < 3 | `contextBuilder` |
| tier >= 3 | `humanEscalation` |

##### Why this node exists

Generated code will fail sometimes. The debugger provides a controlled repair loop instead of blindly retrying.

#### File 26: `orchestrator/app/nodes/humanEscalation.py`

Pauses the graph when automated debugging fails.

##### What it asks

It sends the current task and error to the frontend through the input bridge.

User can choose:

| Choice | Meaning |
| --- | --- |
| `guide` | provide guidance and retry |
| `skip` | mark task done and continue |
| `simplify` | break task into smaller tasks |

##### Router behavior

| Human choice/state | Next |
| --- | --- |
| skipped/done | `selectNextTask` |
| guidance provided | `contextBuilder` |
| simplify | `simplifyTask` |

##### Why this node exists

Human-in-the-loop is a safety valve. If AI cannot fix something after retries, the user can decide what to do instead of the workflow failing silently.

#### File 27: `orchestrator/app/nodes/simplifyTask.py`

Breaks a repeatedly failing task into smaller subtasks.

##### What it does

Given:

- original failed task
- rejection/debug history

It asks Gemini to create 2-3 smaller subtasks.

Then it inserts those subtasks into the task queue immediately after the original task.

The original task is marked done to avoid repeated failure on the same large task.

##### Why this node exists

Sometimes the task is too broad.

Example:

```text
Build dashboard page with all CRUD, auth, filters, modals, and API integration.
```

A simpler breakdown may succeed:

```text
1. Build layout shell.
2. Build list component.
3. Add create/edit form.
```

#### File 28: `orchestrator/app/nodes/snapshotManager.py`

Saves a git snapshot after a task passes.

##### What it does

If current task passed:

```text
1. Mark task done.
2. git add -A
3. git commit
4. git tag v0.<snapshot_count>.0
5. Store snapshot metadata.
6. Reset review/execution/debug state.
7. Clear currentTask.
```

##### Why this node exists

Snapshots allow rollback after later debug failures.

Without snapshots, a bad generated file could corrupt the sandbox with no clean recovery point.

#### File 29: `orchestrator/app/nodes/phaseVerification.py`

Verifies that all files for a phase exist.

##### What it does

After all tasks in a phase are done:

- checks each `filesToCreate`
- marks `phase-N-verified` done or failed
- assembles backend entry if backend routes are ready
- assembles frontend entry if pages are ready
- assembles both during integration/deploy phase

##### Why it calls `assembleEntryPoints`

The coder is not supposed to directly rewrite main entry files like:

- `backend/src/index.js`
- `frontend/src/App.jsx`

Instead, those are assembled from generated routes/pages.

##### Why this node exists

It provides phase-level quality control and safely wires generated files into the scaffold.

#### File 30: `orchestrator/app/nodes/assembleEntryPoints.py`

Auto-generates backend and frontend entrypoint wiring.

##### `assembleBackendEntry(...)`

Finds generated route files from `fileRegistry`, imports them into `backend/src/index.js`, and mounts them with `app.use(...)`.

It determines mount paths from blueprint entity API paths.

Why:

Route files can be generated independently, then the entrypoint can be assembled consistently.

##### `assembleFrontendEntry(...)`

Finds generated page files, imports them into `frontend/src/App.jsx`, and creates React Router routes.

It can wrap routes with `AuthProvider` if an auth context exists.

Why:

Page files can be generated independently, then App routing can be assembled consistently.

##### What happens if this file is missing

Generated route/page files may exist, but the app would not actually use them.

#### File 31: `orchestrator/app/nodes/patternExtractor.py`

Extracts coding patterns from existing generated files.

##### What it does

Reads up to 8 JS/JSX files and asks Gemini to extract:

- error handling style
- response format
- auth pattern
- import style
- env var style
- naming conventions
- async pattern
- frontend API pattern

It stores these in `state.projectPatterns`.

##### Why this node exists

After a phase, the project develops its own style. Future code should match it.

This reduces inconsistency across generated files.

#### File 32: `orchestrator/app/nodes/stateCompactor.py`

Shrinks the state after phase verification.

##### What it does

For completed tasks, it keeps only:

- task id
- title
- files created
- parallelization flag

It also keeps only the latest 100 terminal messages.

##### Why this node exists

The state can become large. Large state means:

- larger event payloads
- more memory
- more prompt context
- more UI overhead

Compaction keeps the graph manageable.

#### File 33: `orchestrator/app/nodes/deploymentVerifier.py`

Creates deployment files and verifies the generated app can build/start.

##### What it does

1. Detect backend entry point.
2. Detect DB type.
3. Generate:
   - `backend/Dockerfile`
   - `frontend/Dockerfile`
   - `frontend/nginx.conf`
   - `docker-compose.yml`
   - env files if missing
4. Build with Docker Compose.
5. Start services.
6. Probe backend endpoints.
7. Probe frontend URL.
8. Check database.
9. If failed, route to debugger.

##### Fixed verification ports

The verifier uses:

- backend: `15000`
- frontend: `15173`
- database: `15432`

These are verification/preview ports for generated apps.

##### Router behavior

| Result | Next |
| --- | --- |
| pass | `presentToUser` |
| fail and attempts remain | `debuggerAgent` |
| attempts exhausted | `presentToUser` |

##### Why this node exists

File existence is not enough.

An app can have all files but still fail to:

- build Docker image
- install dependencies
- start backend
- serve frontend
- connect to DB

This node verifies the generated app more realistically.

#### File 34: `orchestrator/app/nodes/presentToUser.py`

Final node before the graph ends.

##### What it does

If state has an error or failed phase:

- logs failure and returns

Otherwise:

- sets `currentPhase = done`
- starts sandbox servers
- records preview frontend/backend URLs
- logs final dashboard messages

##### Why this node exists

The workflow needs a final handoff step that prepares what the user sees:

- final status
- preview URL
- backend URL
- warnings
- terminal output

#### Service Files Overview

Services are non-node helpers.

Nodes decide workflow logic. Services perform reusable infrastructure work.

#### File 35: `orchestrator/app/services/__init__.py`

Package marker for `app.services`.

It is empty.

#### File 36: `orchestrator/app/services/event_bus.py`

In-memory event broker for realtime streaming.

##### Internal data

```text
_events[project_id] = list of StreamEvent
_signals[project_id] = asyncio.Event
```

##### `append_event(project_id, event)`

Adds event to list and wakes stream consumers.

Used by:

- `main.py`
- `workflow.py`
- `input_bridge.py`

##### `stream_events(project_id)`

Async generator.

Behavior:

- starts cursor at 0
- yields stored events in order
- waits for new events
- sends heartbeat every 15 seconds
- stops after terminal event
- stops after around 300 seconds

Terminal events:

- `run.completed`
- `run.failed`
- `run.cancelled`

##### Why this exists

The workflow runs in a background task, but the gateway/frontend need live progress.

The event bus connects those two worlds.

Limitation:

Events are in memory. If orchestrator restarts, event history is lost. Production could use Redis Streams or database-backed events.

#### File 37: `orchestrator/app/services/run_manager.py`

Tracks active asyncio workflow tasks.

##### Functions

| Function | Purpose |
| --- | --- |
| `register_run(project_id, task)` | Save active task |
| `unregister_run(project_id)` | Remove when done |
| `cancel_run(project_id)` | Cancel active task |
| `is_running(project_id)` | Check if task still active |

##### Why this exists

FastAPI starts workflows in the background. To cancel them later, it needs a map from `project_id` to `asyncio.Task`.

#### File 38: `orchestrator/app/services/input_bridge.py`

Connects graph pauses to frontend human input.

##### Internal data

```text
_pending[(project_id, input_type)] = Future
_history[project_id] = list of requests/responses
```

##### `wait_for_input(...)`

Used by `humanInputNode` and `humanEscalationNode`.

Flow:

```text
1. Create Future.
2. Store Future in _pending.
3. Emit input.requested event.
4. Wait until submit_input resolves Future.
5. Store response in history.
6. Return response to node.
```

##### `submit_input(...)`

Called by FastAPI endpoint when gateway posts user input.

If matching pending future exists:

- resolve it
- emit `input.received`
- return accepted true

If not:

- return accepted false

##### Why this exists

LangGraph needs to pause and resume. HTTP requests are separate from the background graph task. The Future bridge connects them.

#### File 39: `orchestrator/app/services/redis_checkpoint.py`

Saves state checkpoints to Redis.

##### `checkpoint_state(project_id, node_name, state)`

If `REDIS_URL` exists:

```text
1. Connect to Redis.
2. Save checkpoint:<project_id>:<node_name>.
3. Push checkpoint key into checkpoints:<project_id>.
4. Close Redis client.
```

Why this exists:

It gives an external record of state after nodes complete.

Current limitation:

The graph does not currently resume from Redis automatically. The checkpoints are more useful for debugging/audit/future recovery.

#### File 40: `orchestrator/app/services/gemini_client.py`

Central Gemini/LLM client.

##### What it does

- Builds prompts
- Calls Gemini through `langchain-google-genai`
- Forces JSON-only responses
- Parses JSON
- Repairs some truncated JSON
- Retries parse failures
- Tracks token usage/cost
- Enforces token budget
- Provides mock responses if no API key/dependency is available

##### Important functions

| Function | Purpose |
| --- | --- |
| `_extract_json` | Removes markdown/backticks and parses JSON |
| `_repair_truncated_json` | Attempts to close broken JSON |
| `_token_counts` | Reads provider usage or estimates tokens |
| `call_json_agent` | Main LLM call |
| `safe_call_json_agent` | Returns `{ok:false}` instead of throwing for normal errors |
| `invoke_json_agent` | Older/simple helper |

##### Why this file exists

All AI nodes need consistent model behavior.

Without this central client:

- every node would duplicate parsing/retry/token logic
- error behavior would be inconsistent
- token budget would be hard to enforce

#### File 41: `orchestrator/app/services/sandbox_state.py`

Defines sandbox configuration and in-memory sandbox state.

##### Important env/config values

| Name | Meaning |
| --- | --- |
| `NETWORK_NAME` | Docker network name, default `aidev-network` |
| `DOCKER_RUN_TIMEOUT_MS` | Docker command timeout |
| `NPM_INSTALL_TIMEOUT_MS` | npm install timeout |
| `SANDBOX_FRONTEND_HOST_PORT` | base frontend preview port, default `15173` |
| `SANDBOX_BACKEND_HOST_PORT` | base backend preview port, default `15000` |
| `SANDBOX_PREVIEW_PORT_POOL_SIZE` | how many port pairs to try |
| `SANDBOX_PREVIEW_BIND_HOST` | bind host, default `127.0.0.1` |
| `SANDBOX_PREVIEW_TTL_SECONDS` | auto-stop preview TTL, default `300` |
| `PROJECT_DB_URI` | optional external project Postgres URI |

##### In-memory maps

| Map | Purpose |
| --- | --- |
| `_sandboxes` | maps sandbox id and project id to `SandboxInfo` |
| `_active_preview_by_user` | maps user id to active sandbox id |

##### `SandboxInfo`

Dataclass containing:

- sandbox paths
- DB type
- container ids/names
- host ports
- user id
- creation time
- snapshot count
- preview expiry

##### Path helpers

| Helper | Purpose |
| --- | --- |
| `_sandbox_root()` | root directory for sandboxes |
| `_sandbox_path(sandbox_id)` | actual sandbox folder path |
| `_docker_mount_path(sandbox_id)` | host path mounted into generated containers |

#### File 42: `orchestrator/app/services/sandbox.py`

Facade/export file for sandbox services.

It imports functions from smaller sandbox modules and re-exports them.

Why it exists:

Nodes can write:

```python
from ..services.sandbox import create_sandbox, read_file, write_file
```

instead of knowing whether the implementation lives in:

- `sandbox_runtime.py`
- `sandbox_files.py`
- `sandbox_preview.py`
- `sandbox_process.py`

This keeps node imports clean.

#### File 43: `orchestrator/app/services/sandbox_lifecycle.py`

Another facade/re-export file.

It collects sandbox lifecycle functions into one module.

Why both `sandbox.py` and `sandbox_lifecycle.py`?

They provide compatibility and organization while the sandbox implementation is split across smaller files.

#### File 44: `orchestrator/app/services/sandbox_process.py`

Low-level process and Docker helpers.

##### Important helpers

| Helper | Purpose |
| --- | --- |
| `_run` | Run subprocess command safely and capture output |
| `_run_with_input` | Run subprocess with stdin |
| `_run_required` | Run command and throw if non-zero |
| `_shell` | Run shell command in sandbox folder |
| `_docker_available` | Check `docker info` |
| `_requires_docker` | Reads `REQUIRE_DOCKER` flag |
| `_docker_exec` | Run command inside container |
| `_published_port` | Read host port mapped to container port |
| `_allocate_preview_ports` | Choose free backend/frontend port pair |
| `_remove_container` | `docker rm -f` wrapper |
| `_stop_containers_for_sandbox_id` | remove db/backend/frontend containers for sandbox |
| `_ensure_network` | create Docker network if missing |
| `_wait_for_container` | retry readiness command |
| `_write` | write file with parent directory creation |

##### Preview port allocation

It tries:

```text
backend: 15000 + offset
frontend: 15173 + offset
```

up to `SANDBOX_PREVIEW_PORT_POOL_SIZE`.

It checks both:

- OS port availability
- Docker published port list

##### Auto-stop

`schedule_preview_auto_stop(sandbox_id)` starts a daemon thread that waits `SANDBOX_PREVIEW_TTL_SECONDS`, then removes preview containers if the preview has not been refreshed.

Why:

Generated previews should not run forever and consume resources.

##### Stop active preview for user

`stop_active_preview_for_user(user_id)` ensures a user has only one active preview.

Why:

Avoids port conflicts and resource buildup.

#### File 45: `orchestrator/app/services/sandbox_scaffold.py`

Creates the initial generated project files.

##### What it writes

Backend:

- `package.json`
- `.env`
- `src/config/db.js`
- `src/index.js`
- `src/middleware/auth.js`

Frontend:

- `package.json`
- `.env`
- `index.html`
- `src/main.jsx`
- `src/App.jsx`
- `src/index.css`
- `tailwind.config.js`
- `postcss.config.js`
- `vite.config.js`
- `src/utils/api.js`

Root:

- `.gitignore`

##### DB-specific scaffold

If Postgres:

- writes `pg` pool config
- exports `pool` and `connectDB`

If Mongo:

- writes Mongoose config
- exports `connectDB`
- default exports mongoose

##### Why this exists

The generated project needs stable base files before AI coding starts.

This prevents the Coder Agent from wasting tasks on generic boilerplate and keeps entry files consistent.

#### File 46: `orchestrator/app/services/sandbox_runtime.py`

This is the main sandbox creation/reconnect implementation.

##### `create_sandbox(...)`

This is called by `setupSandboxNode`.

Detailed flow:

```text
1. Create sandbox_id = sandbox-<timestamp_ms>.
2. Compute sandbox path under SANDBOX_ROOT.
3. Compute Docker mount path using HOST_SANDBOX_ROOT if set.
4. Create sandbox directory.
5. Optionally create folders from architect folderStructure.
6. Detect db type from backend dependencies.
7. Create deterministic container names:
   - aidev-db-<sandbox_id>
   - aidev-backend-<sandbox_id>
   - aidev-frontend-<sandbox_id>
8. Compute database URL.
9. Scaffold backend/frontend files.
10. Initialize git and tag v0.0.0.
11. Register SandboxInfo in _sandboxes by sandbox_id and project_id.
12. Check Docker availability.
13. Stop user's previous active preview.
14. Ensure Docker network exists.
15. Allocate free preview ports.
16. Write frontend .env with browser API URL.
17. Start DB container or initialize external project DB.
18. Start backend container mounted to sandbox folder.
19. Install backend dependencies.
20. Start frontend container mounted to sandbox folder.
21. Install frontend dependencies.
22. Mark this sandbox as active for user.
23. Schedule preview auto-stop.
24. If setup fails, stop containers and raise if Docker is required.
```

##### DB container behavior

If Mongo:

- runs `mongo:7`
- uses `/data/db` volume
- waits for `mongosh ping`

If Postgres:

- runs `postgres:16-alpine`
- uses `/var/lib/postgresql/data` volume
- waits for `pg_isready`
- optionally generates tables from blueprint schema
- optionally applies project `init.sql`

If `PROJECT_DB_URI` is configured:

- uses external Postgres schema per sandbox
- does not start a local Postgres container

##### Backend container behavior

Starts `node:20-slim` with:

- mounted sandbox folder at `/app`
- working directory `/app`
- env vars for DB URL, JWT secret, port, Node env
- command `tail -f /dev/null`

Why tail?

The container stays alive for later `docker exec` commands. The server is started later when needed.

##### Frontend container behavior

Starts `node:20-slim` with:

- mounted sandbox folder at `/app`
- Vite API URL
- proxy target to backend container
- command `tail -f /dev/null`

##### `reconnect_sandbox(...)`

Used when preview needs to restart from an existing sandbox folder.

Flow:

```text
1. Check sandbox folder exists.
2. Detect DB type from backend package.json.
3. Remove old containers by name.
4. Ensure Docker network.
5. Allocate ports.
6. Start DB/backend/frontend containers.
7. Install dependencies.
8. Rebuild SandboxInfo.
9. Mark active preview.
10. Schedule auto-stop.
```

Why reconnect exists:

The orchestrator may lose in-memory `SandboxInfo` after restart, but the sandbox folder still exists on disk.

#### File 47: `orchestrator/app/services/sandbox_database.py`

Handles generated project database setup.

##### External Postgres mode

If `PROJECT_DB_URI` is set and DB type is Postgres:

- create schema named from sandbox id
- use `search_path=<schema>,public`
- initialize tables only if schema is empty

Why:

Multiple generated projects can share one external Postgres instance safely by using separate schemas.

##### Local Postgres mode

For local container Postgres:

- inspect existing table count
- apply `backend/src/db/init.sql` only if database is empty
- generate CREATE TABLE SQL from blueprint schema

##### SQL generation

`_generate_create_table_sql(db_schema)` creates:

- `CREATE TABLE IF NOT EXISTS`
- foreign key constraints
- indexes

##### Why this file exists

Database setup is complex enough to deserve its own module. It keeps sandbox runtime focused on containers and delegates SQL/schema work here.

#### File 48: `orchestrator/app/services/sandbox_files.py`

File operations, health checks, snapshots, rollback, and stop/destroy.

##### File operations

| Function | Purpose |
| --- | --- |
| `write_file` | write generated file into sandbox |
| `read_file` | read generated file |
| `get_file_list` | list sandbox files excluding `node_modules` and `.git` |
| `get_sandbox_path` | return sandbox path |
| `get_sandbox_info` | return runtime info/preview URLs |

##### Command execution

| Function | Purpose |
| --- | --- |
| `execute_command` | run command inside backend/frontend container when possible |
| `run_in_sandbox` | run shell command in sandbox folder |

##### Health check

Checks:

- folders
- package files
- git status
- DB container
- backend container
- frontend container
- backend node_modules

Returns:

```text
healthy
failures
sandboxPath
dockerEnabled
```

##### Git snapshot

`git_snapshot(...)`:

```text
git add -A
git commit --allow-empty
git tag v0.<count>.0
```

##### Rollback

`rollback(sandbox_id, tag)` runs:

```text
git checkout <tag>
```

##### Stop containers

`stop_sandbox_containers(sandbox_id)`:

- removes DB/backend/frontend containers using `docker rm -f`
- falls back to container-name discovery
- clears container ids from `SandboxInfo`
- removes active preview mapping for that user

##### Destroy sandbox

`destroy_sandbox(sandbox_id)`:

- stops containers
- deletes sandbox folder
- removes sandbox from in-memory map

Important:

The public FastAPI routes currently expose preview stop/restart and cancel, but not a direct destroy/delete endpoint. The destroy helper exists internally.

#### File 49: `orchestrator/app/services/sandbox_preview.py`

Starts and restarts preview servers.

##### `start_sandbox_servers(sandbox_id)`

Starts backend and frontend servers inside already-created containers.

Backend command:

- first checks if backend health already responds
- if not, kills old node process
- runs `npm start` in background
- logs to `/tmp/aidev-backend.log`

Frontend command:

- first checks if Vite already responds
- if not, kills old Vite process
- runs `npm run dev -- --host 0.0.0.0 --port 5173 --strictPort`
- logs to `/tmp/aidev-frontend.log`

It returns preview URLs from `get_sandbox_info`.

##### `restart_sandbox_preview(...)`

Flow:

```text
1. Stop active preview for user.
2. Stop current sandbox containers if known.
3. If sandbox info is missing or containers are gone, reconnect from disk.
4. Map project_id to SandboxInfo.
5. Mark active preview for user.
6. Schedule auto-stop.
7. Start sandbox servers.
```

Why this exists:

The user may return to an old project and click restart/open preview. The orchestrator can revive the sandbox from disk.

#### Root Compose Wiring That Makes Orchestrator Work

The root `docker-compose.yml` is not inside `orchestrator/`, but it is critical.

The orchestrator service:

- builds from `./orchestrator`
- exposes port `8000`
- loads `.env`
- mounts `./sandbox:/workspace/sandboxes`
- mounts `./tests:/tests:ro`
- mounts `/var/run/docker.sock:/var/run/docker.sock`
- depends on Redis

Why these mounts matter:

| Mount | Why |
| --- | --- |
| `./sandbox:/workspace/sandboxes` | generated code persists on host and is visible to gateway for downloads |
| `/var/run/docker.sock:/var/run/docker.sock` | orchestrator can create/stop generated app containers |
| `./tests:/tests:ro` | orchestrator tests can run inside container |

Gateway also mounts the sandbox folder read-only:

```text
./sandbox:/workspace/sandboxes:ro
```

That is how gateway can safely zip generated code without being able to write sandbox files.

#### How Streaming Works In Detail

```text
LangGraph node
  -> workflow._run_node appends StreamEvent
  -> event_bus stores event and wakes stream
  -> FastAPI /runs/{id}/events yields SSE data
  -> Gateway orchestratorClient parses SSE
  -> Gateway updates projectStore
  -> Gateway forwards SSE/WebSocket to frontend
  -> React dashboard updates UI
```

##### Event types you will see

| Event type | Meaning |
| --- | --- |
| `run.created` | FastAPI accepted run |
| `node.started` | LangGraph node started |
| `node.completed` | LangGraph node completed |
| `input.requested` | graph is waiting for human input |
| `input.received` | gateway/frontend submitted input |
| `heartbeat` | event stream is alive |
| `run.completed` | workflow completed |
| `run.failed` | workflow failed |
| `run.cancelled` | workflow cancelled |

#### How Human Input Works End To End

```text
1. pmAgent decides status = needs_clarification.
2. workflow router sends state to humanInput.
3. humanInput calls wait_for_input(...).
4. input_bridge emits input.requested event.
5. Gateway forwards event to frontend.
6. Frontend displays questions.
7. User submits answer.
8. Frontend calls gateway /api/projects/:id/input.
9. Gateway calls orchestrator /runs/:id/input.
10. input_bridge resolves the pending Future.
11. humanInput continues.
12. Graph returns to pmAgent.
13. pmAgent creates final clarifiedSpec.
```

Escalation works the same way, but with input type `escalation`.

#### How Docker Sandbox Is Created, Stopped, Restarted, And Deleted

##### Created

Created by:

```text
setupSandboxNode -> create_sandbox(...)
```

Creates:

- sandbox folder
- backend scaffold
- frontend scaffold
- git repo
- DB container or external DB schema
- backend container
- frontend container
- preview ports
- active preview mapping

##### Started

Preview servers are started by:

```text
presentToUserNode -> start_sandbox_servers(...)
```

or:

```text
Gateway preview restart -> FastAPI preview/restart -> restart_sandbox_preview(...)
```

##### Stopped

Stopped by:

```text
cancel endpoint -> stop_sandbox_containers(project_id)
preview stop endpoint -> stop_sandbox_containers(sandbox_id)
auto-stop thread -> _stop_containers_for_sandbox_id(sandbox_id)
restart preview -> stop_sandbox_containers / stop_active_preview_for_user
```

Stopping removes containers with `docker rm -f`.

##### Restarted

Restarted by:

```text
restart_sandbox_preview -> reconnect_sandbox -> start_sandbox_servers
```

This recreates containers from the sandbox folder on disk.

##### Deleted

Internal helper:

```text
destroy_sandbox(sandbox_id)
```

It:

- stops containers
- deletes sandbox folder
- removes in-memory map entries

Current public API does not expose a direct destroy/delete endpoint. Preview stop and cancel stop containers, but do not necessarily remove generated files.

#### Important Interview Questions And Answers

##### How is the graph created?

> `workflow.py` creates `StateGraph(AgentState)`, adds every node with `graph.add_node`, connects normal edges with `graph.add_edge`, connects decision points with `graph.add_conditional_edges`, then returns `graph.compile()`.

##### How is the graph invoked?

> `main.py` receives `POST /runs`, creates an asyncio background task, and calls `run_workflow(project_id, payload)`. Inside `run_workflow`, the orchestrator builds the graph, creates initial `AgentState`, and calls `await graph.ainvoke(state, {"recursion_limit": 500})`.

##### How does the frontend get progress?

> The orchestrator appends `StreamEvent` objects to `event_bus`. FastAPI streams them as SSE. The gateway reads that SSE stream, updates project metadata, and forwards the same JSON events to the browser.

##### Why not let frontend call FastAPI directly?

> Because FastAPI exposes internal control operations: start runs, cancel runs, submit workflow input, stop/restart Docker previews. The gateway protects those operations with auth, ownership, project metadata, and a stable browser-facing API.

##### Why is Docker controlled from the orchestrator?

> Generated code must run in isolation. The orchestrator owns generated-code execution, so it creates DB/backend/frontend containers, mounts the sandbox folder, installs dependencies, runs checks, starts previews, and cleans containers.

##### Why do we need `AgentState`?

> LangGraph needs a single state object that every node can read and update. `AgentState` stores requirement, spec, blueprint, task queue, sandbox info, current task, retry counts, execution result, token usage, and preview URLs.

##### Why do we checkpoint state?

> Each node writes a Redis checkpoint after completion. This gives observability and a future recovery path if the workflow fails or needs debugging.

##### Why have reviewer and executor both?

> Reviewer catches logical/design/layering problems before runtime. Executor catches concrete syntax/import/npm/environment problems. They protect against different failure types.

##### Why have debugger and simplify task?

> Debugger provides targeted repair instructions after execution failure. If repeated retries fail, simplifyTask breaks a large task into smaller ones so the workflow can continue.

#### Honest Limitations And Improvements

Use these in interviews if asked about production readiness.

1. `event_bus.py` is in-memory. Production should use Redis Streams, Kafka, or DB-backed event storage for restart-safe replay.
2. `run_manager.py` stores active tasks in memory. If orchestrator restarts, active task tracking is lost.
3. Redis checkpoints are written but not automatically used to resume graph execution yet.
4. FastAPI orchestrator endpoints do not perform user auth themselves. This is acceptable only if the gateway is the public boundary and orchestrator stays internal.
5. Docker socket access is powerful. In production, this should be isolated carefully, possibly with a worker pool, sandbox policy, or separate execution cluster.
6. Generated containers are stopped with `docker rm -f`, but named Docker volumes may remain unless separately cleaned.
7. The orchestrator builds a new graph per run. That is simple and safe, but a production version may precompile if no per-run mutation is needed.

#### Final Mental Model

Keep this in your head:

```text
main.py
  = FastAPI API for starting/cancelling/streaming/input/preview

workflow.py
  = LangGraph state machine

contracts.py
  = request models + AgentState + StreamEvent

nodes/*.py
  = individual AI workflow steps

services/event_bus.py
  = live event stream source

services/input_bridge.py
  = pause/resume human-in-the-loop bridge

services/gemini_client.py
  = strict JSON Gemini calls + token tracking

services/redis_checkpoint.py
  = node state checkpoints

services/sandbox*.py
  = generated project files, Docker containers, DB, preview, snapshots
```

Final interview answer:

> The orchestrator starts when the gateway calls `POST /runs`. FastAPI creates a project id, emits `run.created`, starts `run_workflow` as a background asyncio task, and returns immediately. `run_workflow` builds a LangGraph `StateGraph` over `AgentState`, adds all node functions and conditional routers, then invokes it with `graph.ainvoke`. Each node is wrapped by `_run_node`, so it emits `node.started`, runs the node, checkpoints state to Redis, and emits `node.completed`. The workflow clarifies requirements, designs a blueprint, validates it, plans tasks, creates a Docker sandbox, writes/reviews/executes/debugs files, snapshots progress, verifies deployment, starts preview servers, and emits `run.completed`. Events flow from orchestrator event_bus to FastAPI SSE to gateway to frontend. Sandbox containers are created and stopped by the orchestrator because generated code must run isolated from the main platform.

</details>

<details id="inline-09-frontend-deep-dive">
<summary>09_frontend_deep_dive.md - Question 9: Frontend Deep Dive, File By File</summary>

### Question 9: Frontend Deep Dive, File By File

This note explains the entire `frontend/` layer.

Read this when you want to answer interview questions like:

- What does the frontend do in this project?
- How does the frontend connect to the gateway?
- Why does the frontend not call FastAPI orchestrator directly?
- How does login/signup/OTP work from frontend?
- How does the dashboard start a project?
- How does realtime streaming work?
- How does human input appear and get submitted?
- How do preview, stop containers, restart containers, and download work?
- What does every frontend file do?

#### One-Line Summary

The frontend is a React/Vite dashboard for the AI app builder. It handles login/signup UI, accepts a natural-language project prompt, calls the Node gateway, listens to streamed project events, shows workflow node progress, displays file tree/terminal/token cost, handles human-in-the-loop questions, and gives buttons for preview, cancel, restart, stop containers, and download.

Interview line:

> The frontend is intentionally a thin dashboard. It does not run AI logic, does not talk directly to LangGraph, does not control Docker, and does not own authentication rules. It only talks to the gateway, renders state, and sends user actions.

#### Where Frontend Sits In The Three-Layer Architecture

```text
React/Vite Frontend
  |
  | HTTP JSON, cookies, EventSource SSE
  v
Node/Express Gateway
  |
  | Internal JSON/SSE
  v
FastAPI/LangGraph Orchestrator
  |
  | Docker/Gemini/Redis/Sandbox
  v
Generated App Preview
```

The frontend only knows the gateway URL.

It does not need to know:

- internal FastAPI URL
- Docker container names
- sandbox folder path
- Gemini model setup
- Redis checkpoint keys
- Postgres project table structure
- Mongo auth schema

That complexity is hidden behind the gateway.

#### Why Frontend Does Not Call Orchestrator Directly

This is an important interview question.

The orchestrator exposes powerful internal operations:

- start LangGraph run
- cancel run
- submit human input
- stop preview containers
- restart Docker sandbox
- stream raw workflow state

If the browser called FastAPI directly, then FastAPI would need to become a public web backend with:

- JWT cookie verification
- session checking
- user ownership checks
- CORS rules for browser
- project metadata storage
- download authorization
- active project restrictions

Instead, the frontend calls the gateway.

The gateway:

- verifies login
- owns cookies
- checks project metadata
- forwards safe orchestrator commands
- relays orchestrator events
- protects downloads

Best interview answer:

> The frontend only talks to the gateway because the gateway is the public API boundary. The orchestrator is an internal AI runtime with Docker and LangGraph control. Keeping the browser away from those internal endpoints makes the system safer and keeps responsibilities clean.

#### Frontend Folder Structure

```text
frontend/
  .dockerignore
  Dockerfile
  index.html
  package.json
  package-lock.json
  src/
    main.jsx
    App.jsx
    styles.css
    api/
      gateway.js
    components/
      AuthScreen.jsx
      Dashboard.jsx
      ui.jsx
```

Diagram:

```mermaid
flowchart TB
  Main[src/main.jsx] --> App[src/App.jsx]
  App --> Gateway[src/api/gateway.js]
  App --> Auth[src/components/AuthScreen.jsx]
  App --> Dashboard[src/components/Dashboard.jsx]
  Dashboard --> UI[src/components/ui.jsx]
  App --> Styles[src/styles.css]
  Auth --> Gateway
  Dashboard --> Styles
  Auth --> Styles
```

#### End-To-End Frontend Flow

```text
1. Browser loads index.html.
2. Vite loads src/main.jsx.
3. main.jsx renders App.
4. App checks session using GET /api/auth/check.
5. If no user, App shows AuthScreen.
6. User logs in or signs up.
7. AuthScreen calls gateway auth APIs.
8. Gateway sets httpOnly JWT cookie.
9. App loads health and project list.
10. App renders Dashboard.
11. User enters requirement and clicks Launch.
12. App calls POST /api/projects.
13. Gateway starts orchestrator run.
14. App opens EventSource to /api/projects/:id/events.
15. Streamed events update workflow nodes, terminal, file tree, token cost, project status.
16. If input.requested arrives, Dashboard shows human input box.
17. User submits input through gateway.
18. If run completes, Dashboard enables preview/download controls.
```

#### File 1: `frontend/package.json`

##### What it does

Defines the frontend package, scripts, and dependencies.

Important fields:

```json
{
  "name": "aidev-three-layer-frontend",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

##### Why `"type": "module"` matters

The frontend uses ES module import/export syntax:

```js
import React from "react";
export default function App() {}
```

##### Scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | starts Vite dev server on host `0.0.0.0` so Docker can expose it |
| `npm run build` | builds production static assets |
| `npm run preview` | previews the production build |

##### Dependencies

| Dependency | Why used |
| --- | --- |
| `react` | UI library |
| `react-dom` | renders React into DOM |
| `vite` | dev server and build tool |
| `@vitejs/plugin-react` | React support for Vite |
| `lucide-react` | icon components |

##### Interview line

> The frontend has very few dependencies because most business logic is not in the browser. The browser mainly renders the dashboard and calls the gateway.

#### File 2: `frontend/package-lock.json`

##### What it does

Locks exact npm dependency versions.

You normally do not manually edit this file.

Why it exists:

- reproducible installs
- same dependency tree across machines
- safer Docker builds

Interview line:

> `package.json` describes what we need; `package-lock.json` records exactly what npm installed.

#### File 3: `frontend/Dockerfile`

##### What it does

Builds the frontend container.

Flow:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

##### Why it runs dev server

This project is a local/demo three-layer app. The frontend container runs Vite dev server on port `5173` so the user can open the dashboard quickly.

##### Why expose 5173

Vite dev server runs on `5173`.

Root `docker-compose.yml` maps this to the host frontend port.

#### File 4: `frontend/.dockerignore`

##### What it does

Tells Docker not to copy unnecessary files into the image.

Ignored:

- `node_modules`
- `dist`
- `build`
- `.vite`
- `.DS_Store`
- logs

##### Why this matters

It keeps Docker builds smaller and avoids copying local generated/build files.

#### File 5: `frontend/index.html`

##### What it does

This is the HTML shell Vite serves.

It contains:

```html
<div id="root"></div>
<script type="module" src="/src/main.jsx"></script>
```

React mounts into `#root`.

##### Why it is so small

React generates the UI. HTML only provides the mount point and script entry.

#### File 6: `frontend/src/main.jsx`

##### What it does

React entrypoint.

Flow:

```text
1. Import React.
2. Import createRoot.
3. Import App.
4. Import global CSS.
5. Render <App /> inside #root.
6. Wrap in React.StrictMode.
```

##### Why `React.StrictMode`

It helps catch unsafe React patterns during development.

##### Why this file exists

This is the bridge between plain HTML and the React component tree.

#### File 7: `frontend/src/api/gateway.js`

This file centralizes all gateway-related frontend helper logic.

##### `gatewayUrl`

```js
export const gatewayUrl = import.meta.env.VITE_GATEWAY_URL || "http://localhost:3000";
```

The frontend calls the gateway at:

- `VITE_GATEWAY_URL` if configured
- otherwise `http://localhost:3000`

Why:

Different environments may have different gateway URLs.

##### `defaultPreviewFrontendUrl`

Default generated app preview:

```text
http://localhost:15173
```

This matches the orchestrator's frontend preview port default.

##### `publicUrlForPort(port)`

Builds a URL using the browser's current protocol/host plus a port.

Example:

```text
current frontend: http://192.168.1.10:5173
preview port: 15173
result: http://192.168.1.10:15173
```

Why:

If the app is not opened on localhost, preview links should use the same visible host.

##### `normalizePreviewUrl(url, fallbackPort)`

Fixes preview URLs returned by backend/orchestrator.

If the URL uses:

- `localhost`
- `127.0.0.1`
- `0.0.0.0`

it rewrites the host to the browser-visible host.

Why:

Inside Docker/server environments, a preview URL may be technically correct for the container but not correct for the user's browser. This function makes preview links usable from the browser.

##### `gatewayJson(path, options)`

Wrapper around `fetch`.

Important details:

```js
credentials: "include"
headers: { "Content-Type": "application/json" }
```

Why `credentials: "include"` matters:

The gateway uses httpOnly JWT cookies. Browser fetch will not send cookies unless credentials are included.

What it does:

```text
1. Fetch gatewayUrl + path.
2. Include cookies.
3. Parse JSON response.
4. If response is not OK, throw Error.
5. Return parsed data.
```

##### `normalizeStreamEvent(rawEvent)`

Normalizes events from the gateway.

Ensures each event has:

- `type`
- `node`
- `message`
- `state`

Why:

The UI should not crash if an event is missing a field.

#### File 8: `frontend/src/App.jsx`

This is the main frontend brain.

It owns:

- auth session state
- selected project
- project list
- streamed events
- latest orchestrator state
- launch/cancel/input/preview/download actions
- passing props into Dashboard/AuthScreen

##### Important imports

```js
import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  defaultPreviewFrontendUrl,
  gatewayJson,
  gatewayUrl,
  normalizePreviewUrl,
  normalizeStreamEvent,
  publicUrlForPort
} from "./api/gateway";
import AuthScreen from "./components/AuthScreen";
import Dashboard from "./components/Dashboard";
```

##### State variables

| State | Purpose |
| --- | --- |
| `requirement` | text prompt entered by user |
| `user` | authenticated user from gateway |
| `authChecking` | whether session check is still running |
| `project` | currently selected/active project |
| `projects` | project history list |
| `eventsByProject` | streamed events grouped by project id |
| `health` | gateway/orchestrator health |
| `isRunning` | launch/run UI loading flag |
| `error` | global UI error |
| `pendingInput` | current human input request from orchestrator |
| `inputAnswer` | user's answer/guidance text |
| `escalationChoice` | guide/skip/simplify choice |

##### Derived values

`App.jsx` computes many values from state.

Important derived values:

| Value | Purpose |
| --- | --- |
| `projectId` | current project id |
| `selectedProject` | matching project from project list |
| `events` | current project's event list |
| `latestState` | latest orchestrator state from events or stored project |
| `files` | file tree from latest state |
| `terminalLines` | terminal-style messages from events |
| `tokenUsage` | token/cost display |
| `projectStatus` | selected project status |
| `previewFrontendUrl` | normalized preview URL |
| `activeProject` | any currently running/queued project |
| `launchBlocked` | prevents launching multiple active projects |
| `canCancel` | whether cancel button is enabled |
| `hasSandbox` | whether project has sandbox id |

##### Why `latestState` is important

The orchestrator streams state snapshots.

The frontend uses the newest event with `state`:

```text
events newest -> oldest
first event with state wins
fallback to project.last_state
```

This lets the dashboard recover useful state even after selecting an old project.

##### Boot/session effect

On mount:

```text
1. GET /api/auth/check
2. If success, set user.
3. GET /api/health.
4. GET /api/projects.
5. Stop authChecking.
```

If unauthenticated:

- it does not show a scary error
- it shows `AuthScreen`

Why:

The frontend should gracefully decide whether to show login or dashboard.

##### EventSource streaming effect

When current project is `running` or `queued`, App opens:

```js
new EventSource(`${gatewayUrl}/api/projects/${projectId}/events`, { withCredentials: true })
```

For each SSE message:

```text
1. Parse JSON.
2. Normalize event.
3. Append event to eventsByProject.
4. Patch project metadata in local state.
5. If input.requested, show human input UI.
6. If input.received, clear human input UI.
7. If terminal event, set status and close stream.
```

Terminal events:

- `run.completed`
- `run.failed`
- `run.cancelled`

Why this exists:

The project build is long-running. EventSource lets the dashboard update live without polling.

##### `refreshAfterAuth(authUser)`

Called after login/signup succeeds.

It:

- stores user
- clears errors
- clears current project/events
- fetches health
- fetches projects

##### `startProject()`

Called when user clicks Launch.

Flow:

```text
1. Do nothing if launch is blocked or user missing.
2. Clear errors.
3. Set running UI state.
4. Clear pending input.
5. POST /api/projects with requirement, user_id, token_budget_usd.
6. Store returned project.
7. Add project to top of list.
8. Initialize empty events list for this project.
```

This call goes to gateway, not orchestrator directly.

##### `logout()`

Calls:

```text
POST /api/auth/logout
```

Then clears frontend state:

- user
- projects
- selected project
- events
- pending input
- running flag

##### `cancelProject(projectIdToCancel)`

Calls:

```text
POST /api/projects/:projectId/cancel
```

Then marks project as cancelled locally.

Gateway forwards cancellation to orchestrator.

Orchestrator cancels the background task and stops sandbox containers.

##### `submitHumanInput()`

Handles both PM clarification and escalation.

If pending input type is `pm_clarification`:

```json
{
  "type": "pm_clarification",
  "answers": "..."
}
```

If pending input type is `escalation`:

```json
{
  "type": "escalation",
  "choice": "guide|skip|simplify",
  "guidance": "..."
}
```

It posts to:

```text
/api/projects/:projectId/input
```

##### `stopPreview()`

Calls:

```text
POST /api/projects/:projectId/preview/stop
```

Gateway asks orchestrator to stop Docker preview containers.

##### `restartPreview()`

This is slightly more complex.

Flow:

```text
1. Open blank browser tab immediately.
2. Show "Starting preview..." in that tab.
3. POST /api/projects/:projectId/preview/restart.
4. Normalize returned preview URL.
5. If started, replace blank tab location with preview URL.
6. If failed, show error in dashboard and in blank tab.
```

Why open a blank tab first?

Browsers often block popups unless they happen directly from a user click. Opening the tab immediately keeps it user-initiated, then the app redirects it after restart completes.

##### `openPreview()`

If preview is already running:

- opens preview URL in new tab

If preview is not running:

- calls `restartPreview()`

##### `updatePreview(path)`

Shared helper used by stop/restart.

It:

- POSTs to gateway preview endpoint
- patches project state from response
- returns data

##### Render logic

`App.jsx` renders:

| Condition | UI |
| --- | --- |
| `authChecking` | loading card |
| no `user` | `AuthScreen` |
| authenticated | `Dashboard` |

It passes many props to `Dashboard` because App owns the logic and Dashboard mostly renders UI.

#### File 9: `frontend/src/components/AuthScreen.jsx`

Authentication screen.

It handles:

- login mode
- signup mode
- OTP sending
- form state
- auth errors/messages

##### `AuthField`

Small internal component for label + input.

Why:

Avoid repeating label markup for every input.

##### State

| State | Purpose |
| --- | --- |
| `mode` | `login` or `signup` |
| `form` | first name, last name, username, email, password, otp |
| `loading` | disables buttons and shows spinner |
| `message` | success message like OTP sent |
| `error` | auth error |

##### `sendOtp()`

Calls:

```text
POST /api/auth/sendotp
```

Payload:

```json
{
  "emailId": "...",
  "userName": "..."
}
```

Why username is included:

Gateway checks duplicate email/username before sending OTP.

##### `submitAuth(event)`

For signup:

```text
POST /api/auth/register
```

Payload:

- firstName
- lastName
- userName
- emailId
- password
- otp

For login:

```text
POST /api/auth/login
```

If the login field contains `@`, it sends `emailId`.

Otherwise, it sends `userName`.

After success:

```text
await onAuthenticated(data.user)
```

That calls `refreshAfterAuth` in `App.jsx`.

##### Why AuthScreen does not store token

The gateway uses httpOnly cookies.

The frontend never reads the JWT directly.

This is better because JavaScript cannot easily steal an httpOnly cookie.

The frontend simply uses:

```js
credentials: "include"
```

on gateway requests.

#### File 10: `frontend/src/components/Dashboard.jsx`

This is the main UI renderer.

It receives almost everything as props from `App.jsx`.

Why:

`App.jsx` owns state and side effects. `Dashboard.jsx` stays mostly presentational.

##### Topbar

Shows:

- app name `AgentForge`
- gateway health status

Uses:

```text
health.status === "ok"
```

##### Command row

Shows:

- authenticated user identity
- logout button
- project prompt textarea
- Launch button
- Cancel Active button

Launch calls:

```text
startProject
```

Cancel calls:

```text
cancelProject
```

##### Active project notice

If another project is running/queued:

```text
Building <project-id>. Cancel it before launching another project.
```

Why:

The gateway also blocks multiple active projects, but the frontend gives early feedback.

##### Error notice

Shows global errors from gateway or event stream.

##### Human input panel

Shown when:

```text
pendingInput != null
```

Two modes:

###### PM clarification

Displays numbered PM questions.

User types answer and clicks Send.

###### Escalation

Displays choices:

- guide
- skip
- simplify

Also displays error details from orchestrator.

If choice is `guide`, user can type guidance.

##### Summary row

Shows metrics:

- Gateway layer
- Orchestrator layer
- Current project id
- Status

##### Preview row

Buttons:

| Button | Action |
| --- | --- |
| Download Code | opens gateway download endpoint |
| Open Website | opens preview or restarts preview |
| Stop Containers | calls gateway preview stop |
| Restart Containers | calls gateway preview restart |

Important:

The frontend does not stop Docker itself. It asks gateway, which asks orchestrator.

##### Pipeline

Renders every workflow node name.

Node becomes active if any event has that node.

If any event for that node has `node.completed`, it shows completed icon.

This is how the frontend visualizes LangGraph progress.

##### Main grid

Four panels:

1. Projects
2. File Tree
3. Terminal Stream
4. Token And Cost

###### Projects panel

Shows project history and cancel button for active projects.

Clicking a project calls:

```text
setProject(item)
```

###### File Tree panel

Uses:

```text
latestState.fileTree
```

This comes from orchestrator streamed state.

###### Terminal Stream panel

Uses event messages:

```text
[node] event.type: event.message
```

If no events, falls back to:

```text
latestState.terminalOutput
```

###### Token And Cost panel

Uses:

```text
latestState.tokenUsage
```

Shows:

- input tokens
- output tokens
- estimated cost
- token source
- call count

##### Why Dashboard exists separately

It keeps rendering separate from side effects.

If everything were inside `App.jsx`, the file would be harder to read and maintain.

#### File 11: `frontend/src/components/ui.jsx`

Small reusable UI components.

##### `Panel`

Wraps dashboard card UI:

- title
- icon
- children

Used for:

- Projects
- File Tree
- Terminal Stream
- Token And Cost

##### `Metric`

Displays label/value pair.

Used in:

- summary row
- token/cost panel

##### Why this file exists

Avoids repeating small UI patterns.

It also keeps `Dashboard.jsx` cleaner.

#### File 12: `frontend/src/styles.css`

Global CSS for the full frontend.

##### What it styles

- global font/background
- dashboard shell
- topbar
- command row
- auth screen
- buttons
- notices
- human input panel
- preview row
- pipeline nodes
- project list
- file tree
- terminal panel
- metrics
- responsive layout

##### Design style

The UI uses a dark theme:

- background: dark gray
- panels: slightly lighter gray
- accent: green/emerald
- errors: red/pink
- terminal: green monospace

##### Responsive behavior

At max width `900px`:

- auth card becomes single column
- command row stacks
- summary row stacks
- dashboard grid stacks

##### Why one CSS file

This project is small. A single global stylesheet is simpler than CSS modules or a styling framework.

For a larger frontend, we might split CSS by component or use Tailwind/design-system components.

#### How Frontend Auth Works End To End

```text
1. App mounts.
2. App calls GET /api/auth/check.
3. If cookie is valid, gateway returns user.
4. App renders Dashboard.
5. If cookie is missing/invalid, App renders AuthScreen.
6. Login/signup calls gateway.
7. Gateway sets httpOnly JWT cookie.
8. Frontend does not store JWT manually.
9. Future requests include cookie via credentials: include.
```

Why this is good:

- frontend does not handle raw tokens
- XSS cannot easily read httpOnly token
- gateway keeps auth rules centralized

#### How Project Launch Works End To End

```text
User clicks Launch
  -> App.startProject()
  -> gatewayJson POST /api/projects
  -> Gateway requireAuth checks cookie/user
  -> Gateway blocks if another active project exists
  -> Gateway calls orchestrator POST /runs
  -> Orchestrator starts LangGraph background task
  -> Gateway saves project metadata
  -> Frontend stores project and opens stream
```

#### How Streaming Works End To End

```text
Orchestrator node emits event
  -> FastAPI SSE
  -> Gateway project events route
  -> Frontend EventSource
  -> App normalizes event
  -> App appends to eventsByProject
  -> Dashboard updates pipeline, terminal, file tree, cost, status
```

Why `EventSource`:

- simple browser-native SSE client
- good for one-way progress streaming
- automatic HTTP-based stream
- perfect because frontend mostly receives events, not bidirectional socket traffic

Why not polling:

- polling would repeatedly ask for status
- streaming pushes updates immediately
- lower UI delay
- cleaner for node-by-node progress

#### How Human Input Works In Frontend

When orchestrator emits:

```text
input.requested
```

`App.jsx` sets:

```text
pendingInput = event.state
```

Then `Dashboard.jsx` renders the human input panel.

User submits:

```text
submitHumanInput()
```

Then frontend calls:

```text
POST /api/projects/:projectId/input
```

Gateway forwards to orchestrator.

Orchestrator resolves the pending Future and continues LangGraph.

#### How Preview Buttons Work

##### Open Website

If preview is already running:

```text
window.open(previewFrontendUrl)
```

If not:

```text
restartPreview()
```

##### Restart Containers

Calls:

```text
POST /api/projects/:projectId/preview/restart
```

Gateway calls orchestrator.

Orchestrator reconnects/restarts sandbox Docker containers.

##### Stop Containers

Calls:

```text
POST /api/projects/:projectId/preview/stop
```

Gateway calls orchestrator.

Orchestrator removes preview containers.

##### Download Code

Opens:

```text
GET /api/projects/:projectId/download
```

Gateway checks ownership and zips sandbox files.

Frontend simply opens the URL.

#### Important Interview Questions And Answers

##### What is the frontend responsible for?

> The frontend is responsible for user interaction: auth screens, project prompt, dashboard visualization, event stream rendering, human input forms, preview buttons, and download/cancel actions. It does not implement AI workflow or Docker logic.

##### How does the frontend talk to backend?

> It talks only to the Node gateway using `gatewayJson` for JSON requests and `EventSource` for project event streaming.

##### How are cookies handled?

> The gateway sets an httpOnly JWT cookie. The frontend cannot read the token directly. It sends the cookie automatically using fetch/EventSource with `credentials: include` / `withCredentials: true`.

##### How does realtime update work?

> `App.jsx` opens an EventSource to the gateway's project events endpoint. Every event is normalized and stored in `eventsByProject`. Dashboard renders workflow node progress, terminal stream, file tree, status, and token usage from those events.

##### How does frontend know which workflow node completed?

> The orchestrator emits events with `node` and `type`. Dashboard checks whether events exist for each known node and whether any event has `type === "node.completed"`.

##### Why keep App and Dashboard separate?

> `App.jsx` owns state and side effects. `Dashboard.jsx` mostly renders UI from props. This separation makes the frontend easier to reason about.

##### Why normalize preview URLs?

> Orchestrator/gateway may return localhost-style URLs. If the browser is using another host, the preview URL must use the browser-visible host. `normalizePreviewUrl` fixes that.

##### What is a limitation of this frontend?

Good honest answer:

> The frontend state is local React state, not a formal global store. For this compact dashboard that is fine, but a larger app could use a reducer, Zustand, Redux, or React Query for cleaner state management and request caching.

#### Honest Improvements

If asked how to improve frontend production quality:

1. Add React Router for separate auth/dashboard/project pages.
2. Use a reducer or state manager for complex project/event state.
3. Add reconnect logic for EventSource instead of simply closing with an error.
4. Add loading states for preview stop/restart separately.
5. Add better sanitization before writing preview restart error into blank tab HTML.
6. Add tests for `gatewayJson`, `normalizePreviewUrl`, and event handling.
7. Add accessibility improvements for form labels, button states, and live regions.
8. Split `styles.css` into component-level styles if UI grows.

#### Final Mental Model

Keep this in your head:

```text
index.html
  = root div and script

main.jsx
  = renders React App

App.jsx
  = frontend state machine and gateway calls

api/gateway.js
  = gateway URL, fetch wrapper, preview URL helpers, event normalization

AuthScreen.jsx
  = login/signup/OTP UI

Dashboard.jsx
  = main project dashboard UI

ui.jsx
  = small reusable Panel and Metric components

styles.css
  = all frontend styling

Dockerfile/package files
  = container and dependency setup
```

Final interview explanation:

> The frontend is a React/Vite dashboard called AgentForge. It starts in `main.jsx`, renders `App.jsx`, and uses `gateway.js` to call the Node gateway with cookies included. On boot, `App.jsx` checks the session, loads health and project history, and either shows `AuthScreen` or `Dashboard`. When the user launches a project, the frontend posts the requirement to the gateway. The gateway starts the orchestrator run, and the frontend opens an EventSource stream through the gateway. Every streamed event updates local project state, pipeline nodes, terminal output, file tree, token cost, and human input UI. Preview, cancel, restart, stop containers, and download are all user actions sent to the gateway; the frontend never talks directly to FastAPI or Docker.

</details>

<details id="inline-10-generated-app-and-sandbox-output">
<summary>10_generated_app_and_sandbox_output.md - Question 10: Generated App And Sandbox Output</summary>

### Question 10: Generated App And Sandbox Output

This note explains what the system finally creates.

Read this when you want to answer interview questions like:

- What is inside the `sandbox/` folder?
- What does the generated app look like?
- How does the orchestrator create backend/frontend files?
- What is scaffolded first?
- What is generated later by AI nodes?
- How are backend routes/controllers/models supposed to be structured?
- How is frontend routing assembled?
- How are Dockerfiles and `docker-compose.yml` created?
- How does preview work?
- How does download ZIP work?
- What should we honestly say about generated app quality?

#### One-Line Summary

The final output of this platform is a generated full-stack app inside a sandbox folder. Each sandbox contains a backend app, a frontend app, environment files, package files, generated source code, Git history, optional deployment files, and Docker preview/runtime configuration. The orchestrator writes and tests the app; the gateway lets the authenticated user preview or download it.

Interview line:

> The sandbox is the generated project's isolated workspace. The orchestrator creates it, writes backend/frontend code into it, runs checks inside Docker containers, snapshots progress with Git, starts preview servers, and the gateway later exposes safe preview/download controls to the user.

#### Where Sandbox Output Fits

```text
User prompt
  -> Gateway starts project
  -> Orchestrator runs LangGraph
  -> Orchestrator creates sandbox folder
  -> Coder Agent writes generated app files
  -> Reviewer/Executor/Debugger improve them
  -> Deployment Verifier adds Docker output
  -> Preview containers run generated app
  -> Gateway downloads sandbox as ZIP
```

The generated app is not written into the main `frontend/`, `gateway/`, or `orchestrator/` code.

It is written into:

```text
sandbox/sandbox-<timestamp>/
```

Example folders currently present in this repo:

```text
sandbox/sandbox-1783585170016/
sandbox/sandbox-1783586218706/
sandbox/sandbox-1783618823432/
```

Some sandbox folders are partial scaffold-only outputs, while others are fuller generated apps with Dockerfiles and `docker-compose.yml`.

#### Generated App Lifecycle

```text
Stage 1: Sandbox folder created
Stage 2: Base backend/frontend scaffold written
Stage 3: Git initialized and tagged v0.0.0
Stage 4: DB/backend/frontend containers created
Stage 5: AI coding loop writes app-specific files
Stage 6: Entry points are assembled
Stage 7: Git snapshots saved after passing tasks
Stage 8: Deployment files generated
Stage 9: Docker Compose build/run/probe verification
Stage 10: Preview servers started
Stage 11: Gateway can download ZIP
```

#### Important Files That Create The Output

| File | Role |
| --- | --- |
| `orchestrator/app/services/sandbox_runtime.py` | Creates/reconnects sandbox, containers, ports, DB |
| `orchestrator/app/services/sandbox_scaffold.py` | Writes initial backend/frontend boilerplate |
| `orchestrator/app/nodes/setupSandbox.py` | Calls `create_sandbox` and seeds file registry |
| `orchestrator/app/nodes/coderAgent.py` | Writes generated task-specific files |
| `orchestrator/app/nodes/updateRegistry.py` | Records exports/import interfaces of generated files |
| `orchestrator/app/nodes/assembleEntryPoints.py` | Wires generated routes/pages into entry files |
| `orchestrator/app/nodes/phaseVerification.py` | Verifies phase files and triggers assembly |
| `orchestrator/app/nodes/deploymentVerifier.py` | Generates Dockerfiles/compose and verifies app |
| `orchestrator/app/services/sandbox_preview.py` | Starts/restarts preview servers |
| `gateway/src/services/projectZip.js` | Creates downloadable ZIP from sandbox |
| `gateway/src/routes/projects.js` | Exposes `/download`, preview stop/restart |

#### Stage 1: Sandbox Folder Creation

Sandbox creation starts here:

```text
setupSandboxNode
  -> create_sandbox(...)
```

`create_sandbox` creates an id like:

```text
sandbox-1783586218706
```

The id is timestamp-based:

```text
sandbox-<milliseconds>
```

The folder is created under the sandbox root:

```text
SANDBOX_ROOT
```

In this local project, the root compose file maps:

```text
./sandbox:/workspace/sandboxes
```

So the orchestrator sees:

```text
/workspace/sandboxes/sandbox-...
```

and your machine sees:

```text
./sandbox/sandbox-...
```

#### Stage 2: Initial Scaffold

The initial scaffold is created by:

```text
orchestrator/app/services/sandbox_scaffold.py
```

This is before the AI Coder Agent writes app-specific features.

##### Initial scaffold tree

```text
sandbox-<id>/
  .gitignore
  backend/
    .env
    package.json
    src/
      config/
        db.js
      index.js
      middleware/
        auth.js
      models/
      routes/
      utils/
  frontend/
    .env
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
    src/
      App.jsx
      index.css
      main.jsx
      components/
      context/
      hooks/
      pages/
      utils/
        api.js
```

This scaffold gives the generated app a predictable foundation.

##### Backend scaffold

Backend scaffold includes:

- `package.json`
- `.env`
- `src/config/db.js`
- `src/index.js`
- `src/middleware/auth.js`

##### Frontend scaffold

Frontend scaffold includes:

- `package.json`
- `.env`
- `index.html`
- `src/main.jsx`
- `src/App.jsx`
- `src/index.css`
- `src/utils/api.js`
- Tailwind/Vite config files

##### Why scaffold first?

Because the Coder Agent should focus on app-specific files, not generic boilerplate.

Without scaffold:

- every generated app may have different entrypoint style
- imports may drift
- Coder Agent may waste time recreating config files
- assembly and review become harder

Interview line:

> The scaffold provides a stable skeleton. The AI fills in app-specific models, controllers, routes, pages, components, and utilities on top of that skeleton.

#### Stage 3: Git Initialization

After scaffold, the orchestrator initializes Git inside the sandbox:

```text
git init
git config user.email aidev@example.local
git config user.name "AI Dev Team"
git add -A
git commit -m "Initial scaffold" --allow-empty
git tag v0.0.0
```

Why Git is used:

- keep snapshots after successful tasks
- enable rollback when debugging fails
- make generated progress auditable

Later, `snapshotManager.py` creates tags like:

```text
v0.1.0
v0.2.0
v0.3.0
```

#### Stage 4: Docker Runtime Containers

The orchestrator starts up to three runtime containers for the generated app:

```text
Generated DB container
Generated backend container
Generated frontend container
```

Container names follow this pattern:

```text
aidev-db-<sandbox_id>
aidev-backend-<sandbox_id>
aidev-frontend-<sandbox_id>
```

Example:

```text
aidev-db-sandbox-1783586218706
aidev-backend-sandbox-1783586218706
aidev-frontend-sandbox-1783586218706
```

##### Docker network

All generated app containers use:

```text
aidev-network
```

Why:

Backend can talk to database by container name.

Frontend dev server can proxy API calls to backend container.

##### Backend preview port

Default:

```text
15000
```

Container port:

```text
5000
```

Mapping:

```text
127.0.0.1:15000 -> container:5000
```

##### Frontend preview port

Default:

```text
15173
```

Container port:

```text
5173
```

Mapping:

```text
127.0.0.1:15173 -> container:5173
```

##### Port pool

If ports are busy, the orchestrator tries later port pairs:

```text
backend: 15000 + offset
frontend: 15173 + offset
```

Why:

Avoids conflicts if a previous preview is still using a port.

#### Stage 5: AI-Generated App Files

Once sandbox is healthy, the LangGraph dev loop starts writing generated code.

Main nodes:

```text
selectNextTask
  -> contextBuilder
  -> coderAgent
  -> updateRegistry
  -> reviewerAgent
  -> executorAgent
  -> snapshotManager
```

##### Coder Agent output

The Coder Agent writes files listed in the current task's `filesToCreate`.

Examples:

```text
backend/src/models/user.js
backend/src/controllers/authController.js
backend/src/routes/authRoutes.js
frontend/src/pages/LoginPage.jsx
frontend/src/components/Navbar.jsx
frontend/src/context/AuthContext.jsx
README.md
```

##### Example complete generated app

One generated sandbox in this repo contains a blog app:

```text
sandbox/sandbox-1783586218706/
```

It includes backend files such as:

```text
backend/src/controllers/authController.js
backend/src/controllers/blogPostTagController.js
backend/src/controllers/postController.js
backend/src/controllers/tagController.js
backend/src/controllers/userController.js
backend/src/models/blogPost.js
backend/src/models/blogPostTag.js
backend/src/models/tag.js
backend/src/models/user.js
backend/src/routes/authRoutes.js
backend/src/routes/blogPostRoutes.js
backend/src/routes/blogPostTagRoutes.js
backend/src/routes/tagRoutes.js
backend/src/routes/userRoutes.js
```

And frontend files such as:

```text
frontend/src/App.jsx
frontend/src/components/Navbar.jsx
frontend/src/components/ProtectedRoute.jsx
frontend/src/context/AuthContext.jsx
frontend/src/hooks/usePosts.js
frontend/src/pages/LoginPage.jsx
frontend/src/pages/PublicBlogHomePage.jsx
frontend/src/pages/AdminDashboardPage.jsx
frontend/src/utils/api.js
```

This is the type of full-stack output the platform is trying to create.

#### Generated Backend Structure

The intended backend layering is:

```text
backend/src/
  config/
    db.js
  middleware/
    auth.js
    validators.js
    errorHandler.js
  models/
    entityModel.js
  controllers/
    entityController.js
  routes/
    entityRoutes.js
  utils/
    helpers.js
  index.js
```

##### Intended responsibilities

| Layer | Responsibility |
| --- | --- |
| `config/` | DB connection and config |
| `models/` | database queries only |
| `controllers/` | request/response handlers and business flow |
| `routes/` | thin Express router wiring |
| `middleware/` | auth, validation, error handling |
| `utils/` | reusable helper functions |
| `index.js` | Express app setup and route mounting |

##### Why this layering matters

It follows separation of concerns:

- Routes should not contain SQL.
- Models should not know about `req`/`res`.
- Controllers should not create routers.
- DB config should be shared.
- Middleware should be reusable.

Interview line:

> The generated backend is intended to use a layered Express structure: route files only map endpoints, controllers handle HTTP logic, models handle DB queries, middleware handles auth/validation, and config handles DB connection.

##### Honest note about generated examples

Some generated sandbox examples may not perfectly follow the intended layering.

For example, an AI-generated route file may include inline async handlers and model imports. The orchestrator has reviewer checks designed to reject these patterns, but generated output quality can still vary depending on the model response, retry path, and when the sandbox was created.

Good interview answer:

> The intended architecture enforces thin routes, controllers, and models. The Reviewer Agent includes deterministic checks for layering violations. If a generated file violates the rule, the workflow should reject and retry it. For production, I would strengthen these checks further with AST/static analysis and tests.

#### Generated Frontend Structure

The intended frontend structure is:

```text
frontend/src/
  App.jsx
  main.jsx
  index.css
  utils/
    api.js
  pages/
    LoginPage.jsx
    DashboardPage.jsx
    ...
  components/
    Navbar.jsx
    Form.jsx
    Card.jsx
    ...
  context/
    AuthContext.jsx
  hooks/
    useSomething.js
```

##### Intended responsibilities

| Layer | Responsibility |
| --- | --- |
| `pages/` | route-level screens |
| `components/` | reusable UI pieces |
| `context/` | shared app state like auth |
| `hooks/` | reusable data/UI logic |
| `utils/api.js` | Axios API client |
| `App.jsx` | route assembly |
| `main.jsx` | React root render |

##### API client

Generated frontend usually uses:

```text
frontend/src/utils/api.js
```

This configures Axios with:

- base API URL
- auth token header from localStorage

Important distinction:

The generated app is separate from the main platform dashboard.

The main platform frontend uses gateway cookies.

The generated app may use localStorage JWT because it is an app generated by the AI for the user's requested product.

#### Stage 6: Entry Point Assembly

The orchestrator does not want the Coder Agent to freely rewrite key entry files repeatedly.

So these are scaffolded first:

```text
backend/src/index.js
frontend/src/App.jsx
```

Then later assembled by:

```text
orchestrator/app/nodes/assembleEntryPoints.py
```

##### Backend assembly

`assembleBackendEntry(...)`:

1. Looks at `fileRegistry`.
2. Finds generated route files.
3. Creates import statements.
4. Calculates mount path from blueprint.
5. Writes `app.use(...)` route mounts into `backend/src/index.js`.

Example final backend entry:

```text
import authRoutes from './routes/authRoutes.js';
import userRoutes from './routes/userRoutes.js';
import blogPostRoutes from './routes/blogPostRoutes.js';

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/blog-posts', blogPostRoutes);
```

##### Frontend assembly

`assembleFrontendEntry(...)`:

1. Looks at `fileRegistry`.
2. Finds generated page files.
3. Creates imports.
4. Creates React Router routes.
5. Optionally wraps routes in `AuthProvider`.
6. Writes `frontend/src/App.jsx`.

Example final frontend entry:

```text
<BrowserRouter>
  <AuthProvider>
    <Routes>
      <Route path="/" element={<PublicBlogHomePage />} />
      <Route path="login" element={<LoginPage />} />
      <Route path="admin/posts" element={<ProtectedRoute><AdminDashboardPage /></ProtectedRoute>} />
    </Routes>
  </AuthProvider>
</BrowserRouter>
```

##### Why assembly exists

If every task rewrites `App.jsx` or `index.js`, files can overwrite each other.

Assembly lets pages/routes be generated independently, then wired together consistently.

#### Stage 7: Deployment Output

Deployment files are generated by:

```text
orchestrator/app/nodes/deploymentVerifier.py
```

It writes:

```text
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
docker-compose.yml
backend/.env
frontend/.env
frontend/vite.config.js if missing
```

##### Backend Dockerfile

Typical generated backend Dockerfile:

```text
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 5000
CMD ["node", "src/index.js"]
```

##### Frontend Dockerfile

Typical generated frontend Dockerfile:

```text
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

##### Nginx config

Nginx serves the React build and proxies `/api/` to backend:

```text
location /api/ {
  proxy_pass http://backend:5000/api/;
}

location / {
  try_files $uri $uri/ /index.html;
}
```

Why:

- React frontend is served as static files.
- API calls go to backend service.
- SPA routes fall back to `index.html`.

##### Generated docker-compose.yml

Typical compose services:

```text
db
backend
frontend
```

Ports:

```text
db: 15432 -> 5432
backend: 15000 -> 5000
frontend: 15173 -> 80
```

Why these files exist:

The user should be able to run the generated app independently from the main AI platform.

Interview line:

> The generated app includes its own Dockerfiles and compose file so it can be built, run, and verified as a standalone full-stack application.

#### Stage 8: Deployment Verification

The deployment verifier does not just write files.

It also tries to verify:

```text
docker-compose build --no-cache
docker-compose up -d
backend health/API response
frontend response
database accepting connections
```

If verification fails:

```text
deploymentVerifier -> debuggerAgent
```

If pass or retry limit exhausted:

```text
deploymentVerifier -> presentToUser
```

Why:

File presence is not enough. The app should actually build and respond.

#### Stage 9: Preview Output

The preview is started by:

```text
presentToUserNode
  -> start_sandbox_servers(...)
```

or manually by frontend:

```text
Restart Containers button
  -> gateway
  -> orchestrator /preview/restart
  -> restart_sandbox_preview(...)
```

Preview URLs are stored in state:

```text
previewFrontendUrl
previewBackendUrl
previewFrontendPort
previewBackendPort
```

Gateway normalizes and stores them as project metadata:

```text
preview_frontend_url
preview_backend_url
preview_frontend_port
preview_backend_port
preview_running
```

Frontend displays:

```text
Open Website
Stop Containers
Restart Containers
```

#### Stage 10: Download ZIP

Download starts in frontend:

```text
GET /api/projects/:projectId/download
```

Gateway route:

```text
gateway/src/routes/projects.js
```

Zip builder:

```text
gateway/src/services/projectZip.js
```

##### Gateway safety checks

Before download:

1. project must exist
2. logged-in user must own project
3. project must have sandbox id
4. sandbox id must match `sandbox-\d+`
5. resolved sandbox path must stay inside sandbox root
6. sandbox folder must exist

##### What ZIP excludes

The ZIP excludes:

- `.git`
- `node_modules`
- `dist`
- `build`
- `.vite`
- `.cache`
- `coverage`
- `.env`
- `.DS_Store`
- log files

Why:

- avoid huge dependencies/build outputs
- avoid secrets in `.env`
- avoid internal Git history
- keep download clean

##### What ZIP includes

The ZIP includes useful source files:

- backend source
- frontend source
- package files
- Dockerfiles
- compose file
- README
- config templates if present

The paths in ZIP are prefixed with sandbox id:

```text
sandbox-1783586218706/backend/src/index.js
sandbox-1783586218706/frontend/src/App.jsx
...
```

#### Partial vs Complete Sandbox

Not every sandbox folder will look the same.

##### Partial scaffold sandbox

Example:

```text
sandbox/sandbox-1783585170016/
```

It mostly has:

```text
backend/src/config/db.js
backend/src/index.js
backend/src/middleware/auth.js
frontend/src/App.jsx
frontend/src/main.jsx
frontend/src/utils/api.js
```

This means the workflow likely created the scaffold but did not finish generating all app-specific files.

##### More complete sandbox

Example:

```text
sandbox/sandbox-1783586218706/
```

It includes:

- backend controllers/models/routes
- frontend pages/components/hooks/context
- README
- Dockerfiles
- nginx config
- docker-compose

This is closer to final output.

Interview answer:

> A sandbox can be partial or complete depending on how far the workflow got. The platform stores last state and events so the dashboard can show whether the run completed, failed, or was cancelled.

#### Generated App vs Main Platform

Do not confuse these two.

##### Main platform

```text
frontend/
gateway/
orchestrator/
```

This is the AI app builder platform.

##### Generated app

```text
sandbox/sandbox-<id>/backend
sandbox/sandbox-<id>/frontend
```

This is the app produced by the platform.

The main platform frontend uses:

- gateway cookies
- dashboard event streams

The generated app may use:

- localStorage JWT
- its own `/api/auth/login`
- its own backend database

That is okay because the generated app is a separate product.

#### How The Dashboard Shows Generated Output

Frontend receives orchestrator state:

```text
fileTree
previewFrontendUrl
previewBackendUrl
tokenUsage
terminalOutput
currentPhase
deploymentConfig
```

Dashboard renders:

- file tree
- terminal stream
- token/cost
- preview link
- download button
- status

The dashboard never reads sandbox files directly.

It relies on:

- streamed state for display
- gateway download endpoint for ZIP
- preview URL for opening app

#### Important Interview Questions And Answers

##### What exactly is the output of this project?

> The output is a generated full-stack app inside a sandbox folder. It contains a backend, frontend, package files, generated source code, environment templates/config, Dockerfiles, compose file, and README when generation completes.

##### Why create a sandbox folder?

> The sandbox isolates generated code from the main platform code. The orchestrator can safely write, test, snapshot, run, stop, restart, and download generated projects without modifying the platform itself.

##### Why use Docker for generated apps?

> Generated apps may have dependencies, runtime errors, and database state. Docker isolates those from the gateway/orchestrator and lets the system run DB, backend, and frontend as separate containers.

##### Why does gateway download the ZIP instead of frontend reading files?

> Browser cannot safely read server filesystem. Gateway can authenticate the user, check project ownership, validate sandbox path, exclude unsafe files, and return a clean ZIP.

##### Why exclude `.env` from ZIP?

> `.env` may contain secrets like DB URLs or JWT secrets. The download should include code, not private runtime secrets.

##### Why have generated Dockerfiles and compose?

> They make the generated app portable. The user can run it outside the AI platform with Docker Compose.

##### How is generated backend connected to frontend?

> In dev preview, frontend uses Vite API URL/proxy to call backend. In deployment output, nginx serves frontend and proxies `/api/` to backend.

##### What if generation fails halfway?

> The sandbox may contain only scaffold or partial files. The dashboard status, terminal stream, and project events show where it failed. The user can cancel, inspect, restart preview if possible, or download whatever exists if a sandbox was created.

##### Is the generated code production-ready?

Good honest answer:

> It is a strong prototype output, not something I would blindly deploy to production. The workflow has reviewer, executor, debugger, and deployment verification nodes, but I would still add formal tests, security review, stronger static analysis, dependency scanning, and manual code review before production use.

#### Honest Limitations And Improvements

1. Generated code quality depends on LLM output.
2. Some sandbox examples may not perfectly follow intended layering.
3. Reviewer checks should be strengthened with AST/static analysis.
4. Generated apps need automated unit/integration tests.
5. Docker volumes may need explicit cleanup.
6. `.env.example` should be consistently generated for every app.
7. Download ZIP should probably include a generated setup guide every time.
8. Generated app security needs deeper scanning before production use.
9. Restart/resume from Redis checkpoints is not fully automatic yet.
10. More deterministic templates could improve consistency.

#### Final Mental Model

Keep this in your head:

```text
sandbox_runtime.py
  = creates sandbox folder and Docker runtime

sandbox_scaffold.py
  = writes initial backend/frontend skeleton

coderAgent.py
  = writes app-specific source files

updateRegistry.py
  = remembers exports/imports for generated files

assembleEntryPoints.py
  = wires routes into backend and pages into frontend

deploymentVerifier.py
  = writes Dockerfiles/compose and checks build/run

sandbox_preview.py
  = starts/restarts preview servers

projectZip.js
  = creates safe downloadable ZIP
```

Final interview explanation:

> After the orchestrator understands the requirement and creates a plan, it creates a sandbox folder for the generated app. First it writes a deterministic scaffold: backend package/config/auth/index files and frontend Vite/React/Tailwind base files. Then the Coder Agent writes app-specific models, controllers, routes, pages, components, hooks, and utilities. The registry tracks exports, phase verification assembles backend and frontend entrypoints, executor/debugger/reviewer improve quality, and snapshot manager saves Git checkpoints. At the end, deployment verifier writes Dockerfiles, nginx config, and docker-compose, then attempts to build and probe the app. The preview runs in isolated Docker containers, while the gateway gives the authenticated user safe controls to open, stop, restart, or download the generated sandbox as a ZIP.

</details>

<details id="inline-11-interview-master-qa">
<summary>11_interview_master_qa.md - Question 11: Interview Master Q&A</summary>

### Question 11: Interview Master Q&A

This is the final quick-revision file.

Use this when you do not want to reread all code or all previous notes before an interview.

#### 30-Second Project Pitch

This project is an AI full-stack app builder. A user logs into a React dashboard, enters a natural-language project requirement, and the system sends that request through a Node.js gateway to a Python FastAPI/LangGraph orchestrator. The orchestrator runs a multi-agent workflow that clarifies requirements, designs architecture, plans tasks, creates a Docker sandbox, generates backend/frontend code, reviews and executes checks, snapshots progress with Git, verifies deployment, and finally starts a preview of the generated app. The dashboard streams every workflow event live and lets the user answer questions, cancel, preview, restart containers, stop containers, and download the generated code.

#### 2-Minute Architecture Explanation

The project uses a three-layer architecture.

Layer 1 is the React/Vite frontend. It is the user dashboard. It handles login/signup UI, project prompt input, live event display, file tree, terminal stream, token/cost metrics, human input forms, preview buttons, and download/cancel actions.

Layer 2 is the Node/Express gateway. It is the public backend boundary. It handles authentication, JWT cookies, OTP signup, logout blocklist, project metadata, project ownership, active project restrictions, event relay, preview controls, and safe ZIP download.

Layer 3 is the Python FastAPI/LangGraph orchestrator. It is the internal AI runtime. It handles the long-running multi-agent workflow, Gemini model calls, Pydantic `AgentState`, LangGraph routing, retries, human input pauses, Redis checkpoints, Docker sandbox creation, generated-code execution, Git snapshots, deployment verification, and preview startup.

The frontend never talks directly to FastAPI. It talks to the gateway. The gateway talks to the orchestrator. This keeps the browser-facing product API separate from the internal AI/Docker runtime.

#### 5-Minute End-To-End Flow

```text
1. User opens React dashboard.
2. Frontend checks session through gateway /api/auth/check.
3. User logs in or signs up with OTP.
4. User enters project requirement.
5. Frontend calls gateway POST /api/projects.
6. Gateway checks auth and active project rules.
7. Gateway calls orchestrator POST /runs.
8. FastAPI creates project_id and starts LangGraph in background.
9. Gateway saves project metadata.
10. Frontend opens EventSource to gateway /api/projects/:id/events.
11. Gateway streams orchestrator SSE events to frontend.
12. LangGraph runs PM, architect, validator, planner, sandbox, coding, review, execution, debug, deploy, and present nodes.
13. Orchestrator creates Docker sandbox and writes generated app files.
14. Each node emits node.started/node.completed events and checkpoints state.
15. If human input is needed, orchestrator emits input.requested.
16. Frontend shows questions/guidance box.
17. User submits answer through gateway.
18. Orchestrator resumes graph.
19. Deployment verifier writes Dockerfiles/compose and probes app.
20. Preview servers start.
21. Frontend can open preview or download generated code ZIP.
```

#### System Diagram

```mermaid
flowchart LR
  User[User] --> FE[React Frontend]
  FE -->|JSON plus cookies| GW[Node Express Gateway]
  FE -->|EventSource SSE| GW
  GW -->|internal JSON| OR[FastAPI LangGraph Orchestrator]
  OR --> LG[LangGraph Workflow]
  LG --> Gemini[Gemini Model]
  LG --> Redis[Redis Checkpoints]
  LG --> Sandbox[Docker Sandbox]
  Sandbox --> GenBE[Generated Backend]
  Sandbox --> GenFE[Generated Frontend]
  Sandbox --> GenDB[Generated DB]
  GW --> PG[(Postgres Project Metadata)]
  GW --> Mongo[(Mongo Users OTP)]
  GW --> RedisAuth[Redis Token Blocklist]
```

#### Best Answer: Why Three Layers?

We used three layers because each layer has a different responsibility.

The frontend should focus on user interaction and live dashboard rendering. The gateway should focus on browser-facing API concerns like authentication, cookies, project ownership, metadata, and downloads. The orchestrator should focus on AI workflow execution, LangGraph, Gemini calls, Docker sandboxing, retries, checkpoints, and generated-code execution.

If React talked directly to FastAPI, then FastAPI would need to become both the public web backend and the internal AI orchestrator. That would mix authentication, user sessions, project history, Docker control, and LangGraph execution in one service. It is possible, but it is harder to secure, scale, test, and explain.

Interview line:

> Three layers give us separation of concerns: React is the UI, Node gateway is the secure product API boundary, and Python orchestrator is the internal AI execution engine.

#### If Interviewer Asks: Could We Use Only FastAPI?

Yes, technically we could.

FastAPI could handle:

- auth
- sessions
- project metadata
- event streaming
- LangGraph
- Docker sandboxing

But then FastAPI would become a very large mixed-responsibility backend. It would be both public API and internal agent runtime.

Our design is better for this project because:

- Node gateway already fits the MERN-style auth/dashboard API.
- Python remains focused on AI orchestration.
- Docker control endpoints stay internal.
- Browser has one stable API boundary.
- Gateway can protect and normalize orchestrator events.
- Each layer can be debugged independently.

Balanced answer:

> Direct FastAPI would be simpler for a small prototype, but the three-layer design is cleaner for an AI app-builder where orchestration is long-running, stateful, and controls Docker.

#### Core Components And Responsibilities

| Component | Responsibility |
| --- | --- |
| React frontend | dashboard, auth UI, prompt input, event display, human input, preview/download buttons |
| Node gateway | auth, cookies, project metadata, ownership, event relay, safe download, preview controls |
| FastAPI orchestrator | internal run API, background tasks, event streaming, input bridge |
| LangGraph workflow | node-by-node AI state machine |
| Gemini client | strict JSON AI calls and token tracking |
| Redis | gateway token blocklist and orchestrator checkpoints |
| MongoDB | users and OTPs |
| Postgres | project metadata and last state |
| Docker sandbox | isolated generated app runtime |
| Gateway ZIP service | safe downloadable generated source |

#### Gateway Q&A

##### What is the gateway?

The gateway is the public backend API. It sits between the React frontend and the Python orchestrator.

It handles:

- signup/login/logout/check
- OTP emails
- JWT cookie sessions
- Redis token blocklist
- project list/create/get
- project metadata storage
- event relay
- human input forwarding
- cancel
- preview stop/restart
- generated code download

##### Why gateway instead of frontend calling orchestrator?

Because the orchestrator exposes internal control endpoints for LangGraph and Docker. The gateway protects those endpoints with authentication, ownership checks, metadata, and a stable browser-facing API.

##### How does gateway call orchestrator?

Through `gateway/src/services/orchestratorClient.js`.

It calls:

- `POST /runs`
- `GET /runs/:id/events`
- `POST /runs/:id/cancel`
- `POST /runs/:id/input`
- `POST /runs/:id/preview/stop`
- `POST /runs/:id/preview/restart`

##### How does gateway stream events?

Gateway opens the orchestrator SSE stream, parses `data:` chunks, updates project metadata using `projectStore`, and forwards the same JSON event to the frontend as SSE or WebSocket.

##### Why does gateway own download?

Because download needs auth and ownership checks. The gateway validates the sandbox id, ensures the path stays inside sandbox root, excludes unsafe files like `.env`, `.git`, `node_modules`, and returns a ZIP.

##### Honest gateway improvement

Some project-specific routes should consistently call ownership checks. Current gateway protects all project routes with login, but production should enforce ownership on every project id route, including input/cancel/preview/events.

#### Orchestrator Q&A

##### What is the orchestrator?

The orchestrator is the Python FastAPI + LangGraph AI runtime. It starts and manages long-running project generation workflows.

##### How does a run start?

Gateway calls:

```text
POST /runs
```

FastAPI:

1. creates `project_id`
2. appends `run.created`
3. starts `run_workflow(...)` as an asyncio background task
4. registers task in `run_manager`
5. returns immediately

##### How is LangGraph created?

`workflow.py` creates:

```text
StateGraph(AgentState)
```

Then it adds nodes and edges:

- `add_node`
- `add_edge`
- `add_conditional_edges`
- `compile`

##### How is LangGraph invoked?

Inside `run_workflow`:

```text
graph = build_graph()
state = AgentState(...)
await graph.ainvoke(state, {"recursion_limit": 500})
```

##### What is `AgentState`?

`AgentState` is the shared state object passed through every node. It stores:

- requirement
- clarified spec
- blueprint
- validation result
- task queue
- current task
- sandbox id
- file tree
- review result
- execution result
- retry counts
- token usage
- preview URLs
- errors

##### Why is `AgentState` important?

Because LangGraph is state-driven. Nodes update state, routers decide next step from state, events stream state, Redis checkpoints state, and frontend renders state.

##### How does streaming work in orchestrator?

Every node is wrapped by `_run_node`.

That wrapper:

1. emits `node.started`
2. runs actual node
3. checkpoints state
4. emits `node.completed`

`event_bus.py` stores events and FastAPI streams them through `/runs/:id/events`.

##### Why use LangGraph?

Because this is not a single AI call. It is a workflow with:

- multiple agents
- conditional routing
- retry loops
- human input pauses
- debugging loops
- phase verification
- final deployment verification

LangGraph gives us a structured state machine for that.

#### LangGraph Workflow Q&A

##### What does `pmAgent` do?

It turns a vague requirement into a structured spec or asks clarifying questions.

##### Why human input node?

Because some requirements need clarification. The graph can pause, emit `input.requested`, wait for the user, then continue.

##### Why five architect steps?

To split architecture into focused outputs:

1. entities and relationships
2. database schema
3. API endpoints
4. frontend pages
5. folder structure and dependencies

This makes validation and repair easier.

##### Why blueprint validator?

It catches architecture mismatches before coding starts, such as missing DB tables, invalid foreign keys, frontend calling missing APIs, or auth mismatch.

##### Why planner?

It converts the blueprint into an ordered task queue so the code generation happens in small manageable tasks.

##### Why contextBuilder?

It builds focused context for the coder: current task, relevant DB schema, API endpoints, imports, existing file interfaces, and project patterns.

##### Why coderAgent?

It writes the actual generated backend/frontend files.

##### Why updateRegistry?

It records exports/imports from generated files so future files can import them correctly.

##### Why reviewerAgent?

It catches logical, security, import, response format, and layering problems before execution.

##### Why executorAgent?

It performs concrete checks like file existence, syntax, import resolution, environment usage, and npm install.

##### Why debuggerAgent?

It analyzes execution errors and gives the coder targeted repair instructions.

##### Why simplifyTask?

If a task keeps failing, it breaks the task into smaller subtasks.

##### Why snapshotManager?

It saves Git snapshots after passing tasks, enabling rollback after later failures.

##### Why deploymentVerifier?

It generates Dockerfiles/compose and checks whether the generated app can build/start/respond.

##### Why presentToUser?

It starts preview servers and prepares final preview URLs/state for the dashboard.

#### Frontend Q&A

##### What does the frontend do?

The frontend is a React/Vite dashboard. It handles auth UI, project prompt input, project list, event stream rendering, file tree, terminal stream, token/cost display, human input forms, preview controls, cancel, and download actions.

##### How does frontend authenticate?

It calls gateway auth APIs. The gateway sets an httpOnly JWT cookie. The frontend does not read the token directly. It sends cookies using `credentials: include`.

##### How does frontend receive events?

`App.jsx` opens:

```text
EventSource /api/projects/:id/events
```

through the gateway.

##### Why EventSource?

Because workflow progress is one-way streaming from server to browser. SSE is simpler than WebSocket for this use case.

##### How does frontend handle human input?

When it receives `input.requested`, it stores `pendingInput` and Dashboard shows a question/escalation panel. User submits input to gateway `/api/projects/:id/input`.

##### How does preview work from frontend?

Frontend calls gateway preview endpoints. It never controls Docker directly.

Buttons:

- Open Website
- Stop Containers
- Restart Containers
- Download Code

#### Generated App And Sandbox Q&A

##### What is the sandbox?

The sandbox is an isolated generated project workspace:

```text
sandbox/sandbox-<timestamp>/
```

It contains generated backend, frontend, configs, Dockerfiles, compose file, README, and Git snapshots.

##### Why sandbox?

To keep generated code separate from platform code and run it safely in isolated Docker containers.

##### What gets scaffolded first?

Backend:

- package file
- `.env`
- DB config
- Express entry
- auth middleware

Frontend:

- package file
- `.env`
- Vite/React entry
- App shell
- API utility
- Tailwind config

##### What gets generated by AI later?

- backend models
- backend controllers
- backend routes
- validators
- frontend pages
- frontend components
- hooks
- context
- README
- utilities

##### How are entrypoints wired?

`assembleEntryPoints.py` wires:

- generated backend routes into `backend/src/index.js`
- generated frontend pages into `frontend/src/App.jsx`

##### What is final deployment output?

Deployment verifier writes:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.yml`

##### Is generated code production-ready?

It is a strong prototype, not blindly production-ready. It needs tests, security review, dependency scanning, and manual code review before real production deployment.

#### Docker Q&A

##### Why Docker?

Generated code must run separately from the platform. Docker isolates dependencies, runtime crashes, database state, and ports.

##### How does orchestrator control Docker?

The orchestrator container includes Docker CLI and root compose mounts:

```text
/var/run/docker.sock:/var/run/docker.sock
```

This allows orchestrator to run Docker commands on the host.

##### What containers are created per sandbox?

Usually:

- DB container
- backend container
- frontend container

Names:

```text
aidev-db-<sandbox_id>
aidev-backend-<sandbox_id>
aidev-frontend-<sandbox_id>
```

##### How are containers stopped?

Using:

```text
docker rm -f
```

via orchestrator sandbox helpers.

##### What is an improvement?

Clean Docker volumes explicitly and isolate Docker permissions more strongly in production.

#### Data Storage Q&A

##### Why MongoDB?

MongoDB stores auth users and OTP documents through Mongoose.

##### Why Postgres?

Postgres stores platform project metadata, status, last event, last state JSON, preview URL/ports, and user-project ownership records.

##### Why Redis?

Redis is used for:

- gateway logout token blocklist
- orchestrator node checkpoints

##### Why not only one database?

This project evolved with separate needs:

- Mongo fits auth/OTP document models.
- Postgres fits project metadata and relational ownership/history.
- Redis fits temporary/fast state.

In production, you could consolidate some of these, but the current split is understandable.

#### SOLID / Design Principles Q&A

##### Single Responsibility Principle

Each layer/module has one main job:

- frontend renders UI
- gateway handles public API/auth/project metadata
- orchestrator handles AI workflow
- projectZip handles ZIP creation
- event_bus handles event streaming
- sandbox_runtime handles sandbox creation

##### Open/Closed Principle

The workflow can add new nodes or routes without rewriting the whole system. New generated app features become new planned tasks.

##### Liskov Substitution Principle

Not heavily object-oriented here, but service functions keep stable contracts. For example, gateway routes can call orchestrator client functions without caring about internal fetch details.

##### Interface Segregation Principle

Modules expose focused functions. Gateway routes do not import the whole orchestrator; they use orchestratorClient. Nodes use sandbox facade instead of importing every sandbox implementation module.

##### Dependency Inversion Principle

High-level route/node logic depends on service abstractions:

- gateway routes depend on `orchestratorClient`
- nodes depend on `services.sandbox`
- workflow depends on node functions and routers

#### HLD Answer

High-level design:

> This is a three-layer event-driven AI app-builder platform. React dashboard is the presentation layer. Node gateway is the public API/security/metadata layer. Python FastAPI/LangGraph is the AI orchestration layer. Mongo stores users/OTP, Postgres stores project metadata, Redis stores temporary checkpoint/blocklist data, and Docker runs generated app sandboxes.

#### LLD Answer

Low-level design:

> Frontend `App.jsx` manages auth, project state, event stream, and user actions. Gateway Express routes call auth middleware, project store, orchestrator client, and ZIP service. Orchestrator FastAPI starts background workflow tasks. LangGraph passes `AgentState` through nodes. Each node updates state, emits events, and checkpoints to Redis. Sandbox services create folders, files, containers, ports, DB, previews, snapshots, and deployment files.

#### Most Likely Interview Questions

##### 1. Explain this project.

It is an AI app-builder platform that takes a natural-language requirement and generates a full-stack app using a multi-agent workflow. The user interacts through a React dashboard, the Node gateway handles auth/project APIs, and the Python LangGraph orchestrator generates and runs the app inside Docker sandboxes.

##### 2. Why did you use three layers?

To separate UI, public API/security, and internal AI/Docker orchestration. This keeps the browser away from internal Docker/LangGraph endpoints and makes the system easier to secure, debug, and scale.

##### 3. Why Node gateway and Python orchestrator?

Node/Express is good for web API/auth/session work. Python is better for LangGraph, Pydantic, Gemini integration, and AI workflow logic.

##### 4. How does project creation work?

Frontend calls gateway `/api/projects`, gateway authenticates user and calls orchestrator `/runs`, orchestrator starts LangGraph in background, gateway saves project metadata, frontend streams events.

##### 5. How does streaming work?

Orchestrator emits `StreamEvent` objects into event bus. FastAPI streams them as SSE. Gateway parses and forwards them to frontend. Frontend updates dashboard live.

##### 6. How does human input work?

Orchestrator emits `input.requested`, frontend shows questions, user submits answer to gateway, gateway posts to orchestrator input endpoint, input bridge resolves pending Future, graph continues.

##### 7. How is Docker sandbox created?

Orchestrator creates a sandbox folder, writes scaffold files, initializes Git, creates DB/backend/frontend containers, installs dependencies, allocates ports, and later starts preview servers.

##### 8. How is generated code verified?

Reviewer checks code quality/layering, executor checks syntax/imports/npm, debugger fixes failures, snapshot manager saves good states, and deployment verifier builds/runs/probes Docker Compose output.

##### 9. What are limitations?

Events and running tasks are in memory, Redis checkpoints are not automatic resume yet, generated code needs production review/tests, Docker socket access is powerful, and ownership checks should be hardened consistently.

##### 10. What would you improve?

Use durable event streaming, add graph resume from checkpoints, strengthen authorization, add AST/static analysis, add generated app tests, improve Docker isolation, clean volumes, and use a worker queue for orchestrator jobs.

#### Challenge Questions

##### If interviewer says: "This architecture seems overengineered."

Answer:

> For a simple CRUD app, yes, three layers may be overkill. But this is not just a CRUD app. It runs long AI workflows, streams progress, controls Docker, executes generated code, and handles user sessions/downloads. Splitting the gateway from the orchestrator keeps the risky long-running AI/Docker runtime internal and keeps the public API clean.

##### If interviewer says: "Why not WebSocket only?"

Answer:

> We mostly need one-way progress streaming from server to browser, so SSE/EventSource is simpler and fits well. WebSocket is available in gateway too, but SSE is enough for the main event stream. User input goes through normal POST requests.

##### If interviewer says: "Is Docker socket mount safe?"

Answer:

> It is powerful and should be handled carefully. For local/demo it is practical. For production, I would isolate execution in a separate worker environment, restrict permissions, use a job queue, and add cleanup/security policies.

##### If interviewer says: "What happens if orchestrator restarts?"

Answer:

> Current in-memory event bus and run manager lose active task state. Redis checkpoints keep snapshots, but automatic resume is not fully implemented. A production version should use durable event storage and resume workflows from checkpoints.

##### If interviewer says: "How do you prevent bad generated code?"

Answer:

> The system uses multiple gates: blueprint validation before coding, reviewer checks before execution, executor runtime checks, debugger repair loop, retry limits, task simplification, Git snapshots, and deployment verification. Still, generated code should undergo tests and review before production.

#### Final Cram Sheet

Remember these exact phrases:

- "Frontend is the dashboard."
- "Gateway is the secure product API boundary."
- "Orchestrator is the internal AI execution engine."
- "LangGraph runs a state machine over AgentState."
- "Every node emits events and checkpoints state."
- "Gateway relays orchestrator SSE to frontend."
- "Docker sandbox isolates generated code."
- "Generated app is separate from platform code."
- "Download is owned by gateway because it needs auth and safe path validation."
- "Three layers are for separation of concerns, security, and long-running workflow isolation."

#### Closing Interview Summary

> In short, this project is a three-layer AI software factory. The React frontend gives the user a live dashboard. The Node gateway protects the system with auth, project ownership, metadata, event relay, preview controls, and downloads. The Python orchestrator runs the actual AI workflow using LangGraph and AgentState. It creates a Docker sandbox, generates backend/frontend code, reviews it, executes checks, debugs failures, snapshots progress, verifies deployment, and starts a preview. The design is intentionally split so the browser-facing product layer stays separate from the internal AI/Docker execution layer.

</details>

<details id="inline-12-security-and-production-hardening">
<summary>12_security_and_production_hardening.md - Question 12: Security And Production Hardening</summary>

### Question 12: Security And Production Hardening

This note explains the security posture of the project.

Read this when an interviewer asks:

- Is this production-ready?
- Why is the gateway needed for security?
- How is authentication handled?
- How is project ownership enforced?
- What are the Docker sandbox risks?
- How are secrets handled?
- What could go wrong if the orchestrator is public?
- What would you improve before production?

#### One-Line Summary

The current project has a good security-oriented architecture for a prototype: the browser talks to the gateway, the gateway owns auth and project metadata, and the orchestrator stays internal for LangGraph and Docker control. However, before production, we should harden secrets handling, route-level authorization, Docker isolation, durable event storage, rate limiting, generated-code scanning, and workflow recovery.

Interview line:

> I would describe this as a strong prototype architecture, not fully production-hardened yet. The separation between gateway and orchestrator is the main security win, but production needs stronger authorization, secret hygiene, durable events, sandbox isolation, and generated-code security checks.

#### Security Boundary Diagram

```mermaid
flowchart LR
  Browser[Browser / React Frontend] -->|cookies + JSON + SSE| Gateway[Node Gateway public boundary]
  Gateway -->|internal HTTP/SSE only| Orchestrator[FastAPI Orchestrator internal]
  Gateway --> Mongo[(Mongo users + OTP)]
  Gateway --> Postgres[(Postgres project metadata)]
  Gateway --> Redis[(Redis token blocklist)]
  Orchestrator --> Redis2[(Redis checkpoints)]
  Orchestrator --> Docker[Docker Engine via socket]
  Docker --> Sandbox[Generated app containers]

  Browser -. should not access .-> Orchestrator
  Browser -. should not access .-> Docker
```

#### Current Security Strengths

##### 1. Frontend does not call orchestrator directly

The frontend calls:

```text
Node Gateway
```

not:

```text
FastAPI Orchestrator
```

Why this matters:

The orchestrator can:

- start AI runs
- cancel runs
- accept workflow input
- stop/restart Docker containers
- control generated project sandboxes

Those are internal control operations. The browser should not access them directly.

Interview answer:

> The gateway protects the orchestrator. The browser sees product APIs, not internal LangGraph/Docker APIs.

##### 2. httpOnly JWT cookie

The gateway stores the session token in an httpOnly cookie:

```text
httpOnly: true
sameSite: lax
```

Why this is good:

- frontend JavaScript cannot directly read the JWT
- reduces token theft risk from XSS
- browser automatically sends cookie to gateway

##### 3. Password hashing

Gateway uses:

```text
bcryptjs
```

Passwords are stored as hashes, not plain text.

##### 4. Strong password validation

Registration requires:

- min length 8
- lowercase
- uppercase
- number
- symbol

##### 5. OTP expiration

OTP model has TTL:

```text
5 minutes
```

This limits OTP reuse window.

##### 6. Redis logout blocklist

On logout:

```text
token:<jwt> = blocked
expireAt = token exp
```

Then `requireAuth` checks Redis to reject blocked tokens.

##### 7. Gateway ZIP download safety

Download code path validates:

- user owns project
- sandbox id matches `sandbox-\d+`
- resolved path stays inside sandbox root
- sandbox folder exists

It excludes:

- `.env`
- `.git`
- `node_modules`
- build folders
- logs

This is important because generated app folders may contain secrets, dependencies, or large build output.

##### 8. Gateway has read-only sandbox mount

In `docker-compose.yml`, gateway mounts sandbox as read-only:

```text
./sandbox:/workspace/sandboxes:ro
```

Why this is good:

The gateway can read sandbox files for ZIP download but should not write generated code.

##### 9. Orchestrator and generated apps are separated

Generated apps run in sandbox containers.

They are not executed inside the gateway or frontend process.

This isolates:

- dependencies
- runtime crashes
- ports
- database state
- generated code errors

#### Biggest Current Risks

#### Risk 1: Secrets In Repository Files

The root README has been cleaned, but the local `.env.example` currently appears to contain real-looking credentials after the commented template.

Risk:

- API keys can be abused.
- Database passwords can be leaked.
- SMTP app passwords can be used to send email.
- Even if deleted later, Git history may still contain them.

Production fix:

1. Remove all real secrets from tracked files.
2. Replace with placeholders.
3. Rotate every exposed secret.
4. Add secret scanning in CI.
5. Use a secret manager.

Examples:

- GitHub Actions secrets
- AWS Secrets Manager
- GCP Secret Manager
- Doppler
- Vault
- Docker secrets

Interview answer:

> One thing I would immediately fix before pushing publicly is secret hygiene. `.env` and `.env.example` should never contain real keys, and any exposed credentials should be rotated.

#### Risk 2: Orchestrator Has Docker Socket Access

The orchestrator compose service mounts:

```text
/var/run/docker.sock:/var/run/docker.sock
```

This allows the orchestrator container to control Docker on the host.

Why it exists:

The orchestrator needs to create generated app containers.

Why it is risky:

Docker socket access is powerful. If the orchestrator is compromised, attacker may control containers or host-level resources.

Production fixes:

- keep orchestrator private, never public
- run orchestrator in a locked-down worker environment
- use separate worker machines for generated code
- use rootless Docker or container sandboxing where possible
- use Kubernetes Jobs with restricted service accounts
- apply seccomp/AppArmor profiles
- limit container capabilities
- run generated containers as non-root
- enforce CPU/memory/time limits
- avoid mounting host-sensitive paths

Interview answer:

> Docker socket mounting is acceptable for a local prototype, but in production I would isolate sandbox execution into a restricted worker pool or container runtime with strong policies.

#### Risk 3: Some Project Routes Need Stronger Ownership Checks

Current gateway routes are protected by `requireAuth`, but ownership checks are not consistently applied to every project-id route.

Ownership is checked for:

- `GET /api/projects/:projectId`
- `GET /api/projects/:projectId/download`

But routes like events/input/cancel/preview should also consistently call:

```text
ownsProject(req, project)
```

Risk:

An authenticated user might act on another project id if they can guess it.

Production fix:

Apply ownership checks to every route containing `:projectId`:

- events
- input
- cancel
- preview stop
- preview restart

Interview answer:

> The gateway already requires login, but I would harden project-specific authorization by enforcing ownership on every route that accepts a project id.

#### Risk 4: In-Memory Event Bus And Run Manager

The orchestrator stores events and active tasks in memory:

- `event_bus.py`
- `run_manager.py`

Risk:

If orchestrator restarts:

- active task map is lost
- event history is lost
- browser stream cannot replay old events

Production fix:

- Redis Streams
- Kafka
- Postgres event table
- durable queue
- workflow resume from checkpoint

Interview answer:

> For production I would replace the in-memory event bus with durable event storage and add resume support from Redis checkpoints.

#### Risk 5: Redis Checkpoints Are Not Full Resume Yet

The orchestrator writes checkpoints:

```text
checkpoint:<project_id>:<node_name>
checkpoints:<project_id>
```

But it does not fully resume LangGraph from those checkpoints after restart.

Production fix:

- store latest checkpoint pointer
- reload `AgentState`
- resume from last safe node
- make node operations idempotent
- avoid repeating dangerous Docker operations accidentally

#### Risk 6: Generated Code Security

The system generates code using LLM output.

Risks:

- insecure auth logic
- SQL injection if model ignores rules
- exposed secrets
- unsafe dependencies
- weak validation
- XSS in generated frontend
- vulnerable npm packages
- over-broad CORS

Current protections:

- prompt rules require parameterized queries
- reviewer checks security/layering
- executor checks syntax/imports/env usage
- deployment verifier builds/probes app

Production fixes:

- static analysis
- dependency scanning
- npm audit / osv-scanner
- Semgrep rules
- generated unit/integration tests
- security review before deploy
- strict templates for auth and DB
- denylist dangerous packages/APIs

Interview answer:

> Generated code is treated as prototype output. The workflow has review and execution gates, but production would require automated security scanning and manual review.

#### Risk 7: No Rate Limiting

Current gateway routes do not show rate limiting.

Risk:

- OTP spam
- login brute force
- expensive project generation abuse
- EventSource connection abuse

Production fix:

- per-IP and per-user rate limits
- stricter OTP resend cooldown
- login attempt lockout
- token budget enforcement per user/org
- queue limits

#### Risk 8: Cookie Settings Need Production Mode

Current cookie:

```text
httpOnly: true
sameSite: lax
```

Missing for HTTPS production:

```text
secure: true
```

Production fix:

Use:

```text
secure: true
sameSite: "lax" or "strict"
domain/path carefully configured
shorter maxAge aligned with JWT expiry
```

Also note:

Current cookie `maxAge` is 24 hours, while JWT expires in 1 hour.

That is not catastrophic because JWT verification fails after 1 hour, but the browser cookie may remain longer than the token is valid.

Production fix:

Align cookie maxAge with JWT expiry.

#### Risk 9: CSRF Considerations

Because auth uses cookies, CSRF must be considered.

Current `sameSite: lax` helps for many cases.

But production should consider:

- CSRF token for state-changing routes
- origin/referer validation
- stricter SameSite where possible
- CORS allowlist

Affected routes:

- launch project
- cancel project
- submit input
- preview stop/restart
- logout

#### Risk 10: Public Ports And Network Exposure

Compose exposes:

- frontend port
- gateway port
- orchestrator port
- Postgres port
- Redis port

For local development this is convenient.

Production risk:

- orchestrator should not be publicly exposed
- Redis should not be publicly exposed
- Postgres should not be publicly exposed

Production fix:

- expose only frontend/gateway through a reverse proxy
- keep orchestrator, Redis, Postgres on private network
- use firewall/security groups
- use TLS
- use managed DBs with private access where possible

#### Risk 11: Sandbox Cleanup And Volumes

Generated containers are stopped with:

```text
docker rm -f
```

But Docker volumes may remain.

Risk:

- disk usage grows
- generated DB data persists unexpectedly

Production fix:

- explicit volume cleanup
- sandbox TTL cleanup jobs
- storage quotas
- per-user resource limits
- admin cleanup dashboard

#### Risk 12: Logs And Error Messages

The code logs errors from gateway/orchestrator/sandbox.

Risk:

- logs may expose internal paths
- generated app errors may leak env details
- model prompts/responses may include sensitive user requirements

Production fix:

- structured logs
- redact secrets
- limit error details returned to frontend
- store audit events separately
- avoid logging full env or credentials

#### Current Protection vs Production Fix

| Area | Current protection | Production hardening |
| --- | --- | --- |
| Auth | JWT cookie, bcrypt, Mongo user lookup | secure cookies, CSRF, rate limits, MFA optional |
| Logout | Redis token blocklist | ensure Redis is required/highly available |
| OTP | TTL collection | resend cooldown, attempt limit, anti-spam |
| Project ownership | checked on get/download | enforce on all project-id routes |
| Orchestrator exposure | behind gateway conceptually | private network/firewall, no public port |
| Docker sandbox | separate containers, TTL stop | restricted worker pool, quotas, rootless/non-root |
| Events | in-memory event bus | Redis Streams/Kafka/Postgres events |
| Checkpoints | Redis writes | actual resume and idempotency |
| Download | safe path, excludes secrets/deps | malware scan, size limits, audit log |
| Generated code | reviewer/executor/verifier | static analysis, tests, dependency scanning |
| Secrets | `.gitignore` excludes `.env` | clean `.env.example`, rotate leaked keys, secret manager |

#### Security Interview Q&A

##### Is this project production-ready?

Best answer:

> I would call it production-structured but not production-hardened. The architecture has the right separation between frontend, gateway, and orchestrator, but production needs stronger authorization, secret management, durable eventing, sandbox isolation, rate limiting, and generated-code scanning.

##### What is the biggest security win in the architecture?

> The browser does not talk directly to the orchestrator. The gateway is the public boundary and protects auth, ownership, project metadata, and downloads. The orchestrator remains an internal AI/Docker runtime.

##### What is the biggest current risk?

> Docker socket access and secret hygiene. The orchestrator needs Docker control for sandboxing, but that must be isolated carefully. Also, no real credentials should be committed anywhere, including `.env.example`.

##### Why is Docker sandboxing safer?

> Generated code runs in separate containers instead of the main gateway/orchestrator process. That isolates dependencies, crashes, ports, and generated app database state.

##### Is Docker sandboxing completely safe?

> No. It reduces risk, but Docker socket access and generated code execution are still powerful. Production should use stricter container isolation, resource limits, non-root users, and a separate execution environment.

##### How do you protect generated code downloads?

> Gateway checks authentication and project ownership, validates the sandbox id, ensures path containment, excludes secrets and heavy/internal folders, and returns a ZIP.

##### What happens if user guesses another project id?

> Some routes already check ownership, but I would harden all project-id routes to check ownership consistently. That is one of the first production fixes.

##### Why not expose FastAPI orchestrator publicly?

> It controls runs, input, cancellation, preview restart, and Docker sandbox operations. Those should be internal commands behind the gateway, not public browser APIs.

##### How would you secure event streaming?

> Require auth, check project ownership before streaming, use durable events, close idle streams, rate-limit connections, and avoid leaking sensitive state in event payloads.

##### How would you secure Gemini/model usage?

> Store API keys in a secret manager, enforce per-user token budgets, validate JSON output, scan generated code, rate-limit project creation, and avoid sending unnecessary sensitive data in prompts.

#### Production Hardening Roadmap

##### Phase 1: Immediate GitHub Safety

1. Clean `.env.example`.
2. Ensure `.env` is not tracked.
3. Rotate exposed Gemini, DB, Mongo, SMTP credentials.
4. Add secret scanning.
5. Keep README placeholders only.

##### Phase 2: API Authorization

1. Add `ownsProject` checks to every project route.
2. Add CSRF protection or strict origin checks.
3. Add rate limits for auth/project/input/events.
4. Align JWT expiry and cookie max age.
5. Use `secure: true` cookies in HTTPS.

##### Phase 3: Orchestrator Reliability

1. Replace in-memory event bus with Redis Streams/Postgres.
2. Make run manager durable or queue-backed.
3. Add checkpoint resume.
4. Add idempotent node operations.
5. Add better cancellation cleanup.

##### Phase 4: Sandbox Isolation

1. Move sandbox execution to separate worker hosts.
2. Remove broad Docker socket access if possible.
3. Add CPU/memory/disk quotas.
4. Run generated app containers as non-root.
5. Clean containers and volumes by TTL.
6. Restrict network egress for generated containers.

##### Phase 5: Generated Code Security

1. Add Semgrep/static analysis.
2. Add npm audit / OSV scanning.
3. Add generated tests.
4. Enforce safe templates for auth and DB.
5. Add dependency allowlist.
6. Add manual review before production deployment.

#### What To Say If Interviewer Pushes Hard

##### "This is unsafe because it runs generated code."

Answer:

> That is exactly why we isolate generated code in Docker sandboxes and keep orchestration behind the gateway. I agree that production needs stronger sandbox controls, but the architecture already separates generated runtime from the main platform.

##### "Docker socket mount is dangerous."

Answer:

> Yes, it is powerful. For a local prototype it lets the orchestrator create containers easily. For production I would move execution into a restricted worker pool or Kubernetes job system with limited privileges instead of exposing broad Docker socket access.

##### "What if someone abuses project generation?"

Answer:

> I would add per-user quotas, rate limits, token budgets, job queue limits, and admin monitoring. The current app has token budget support, but production needs enforcement at account/org level.

##### "What if event stream leaks sensitive state?"

Answer:

> The event stream should be protected by auth and ownership checks, and production should avoid sending unnecessary secrets or raw internal details in state payloads. I would also use durable event storage with redaction.

#### Final Interview Summary

> Security-wise, the strongest design decision is keeping the orchestrator internal and putting the gateway in front of it. The gateway owns auth, cookies, ownership, metadata, and downloads. The orchestrator owns AI workflow and Docker sandboxing. Current protections include httpOnly cookies, bcrypt password hashing, OTP TTL, Redis logout blocklist, safe ZIP path validation, read-only gateway sandbox mount, and isolated generated app containers. The main production gaps are secret hygiene, consistent ownership checks, Docker socket isolation, durable event storage, workflow resume, rate limiting, CSRF protection, and generated-code security scanning.

</details>

<details id="inline-13-failure-scenarios-and-debugging">
<summary>13_failure_scenarios_and_debugging.md - Failure Scenarios and Debugging Guide</summary>

### Failure Scenarios and Debugging Guide

This note explains how failures happen in this project, how the system reacts, and how you should debug it during development or in an interview.

The short interview answer is:

> We designed the project so failures are isolated by layer. The frontend shows user-facing errors, the gateway converts API/orchestrator failures into consistent HTTP responses and stores project progress, and the Python orchestrator handles complex self-repair through LangGraph, retries, rollback, human input, and sandbox cleanup. This makes debugging easier because we can identify whether the issue is UI, API gateway, workflow logic, AI generation, Docker sandbox, generated code, or infrastructure.

---

#### 1. Mental model: how failure moves through the system

The project has three major failure zones:

1. Frontend failure
   - Example: user sees "Gateway event stream disconnected."
   - Usually caused by gateway down, expired session, CORS/cookie issue, or SSE stream interruption.

2. Gateway failure
   - Example: `/api/health` returns `503 degraded`.
   - Usually caused by orchestrator unreachable, Mongo/Redis startup failure, invalid auth, project ownership issues, or orchestrator returning non-2xx.

3. Orchestrator/sandbox failure
   - Example: workflow emits `run.failed`, `debuggerAgent`, `humanEscalation`, or preview restart failure.
   - Usually caused by LLM JSON failure, token budget exceeded, Docker unavailable, generated code errors, failed npm install, bad imports, bad schema, or containers not responding.

Important point:

> Not every failure means the whole project is broken. Many failures are expected signals in the workflow. For example, `reviewerAgent` rejection, `executorAgent` failure, and `debuggerAgent` repair are normal self-healing steps.

---

#### 2. Failure flow diagram

Diagram file: **failure debugging decision tree** (diagram `failure_debugging_decision_tree.mmd` is embedded in the diagram appendix)

```mermaid
flowchart TD
    A[User reports problem] --> B{Where is symptom visible?}

    B -->|Browser UI| C[Check frontend state, console, Network tab]
    B -->|HTTP API| D[Check gateway route and gateway logs]
    B -->|Build stream| E[Check SSE events and orchestrator event bus]
    B -->|Generated app preview| F[Check sandbox containers, ports, generated app logs]
    B -->|Workflow failed| G[Check LangGraph terminal event and node logs]

    C --> C1{API response failed?}
    C1 -->|Yes| D
    C1 -->|No| C2[Inspect React state and rendering logic]

    D --> D1{Gateway can reach orchestrator?}
    D1 -->|No| D2[Fix ORCHESTRATOR_URL or orchestrator service]
    D1 -->|Yes| D3[Check route validation, auth, project metadata]

    E --> E1{Terminal event received?}
    E1 -->|run.completed| E2[Flow completed; inspect preview/download]
    E1 -->|run.failed| G
    E1 -->|run.cancelled| E3[Cancel path worked]
    E1 -->|No, stream closed| E4[Check gateway event relay and event_bus timeout]

    G --> G1{Failure type?}
    G1 -->|LLM/API| G2[Check Gemini key, JSON parse, token budget]
    G1 -->|Generated code| G3[Check reviewer/executor/debugger loop]
    G1 -->|Sandbox| F
    G1 -->|Human input| G4[Check pending input bridge]

    F --> F1{Docker available?}
    F1 -->|No| F2[Start Docker, mount socket, check REQUIRE_DOCKER]
    F1 -->|Yes| F3[Check containers, ports, npm install, app logs]
```

---

#### 3. Runtime recovery loop

Diagram file: **failure runtime recovery loop** (diagram `failure_runtime_recovery_loop.mmd` is embedded in the diagram appendix)

```mermaid
flowchart LR
    Coder[coderAgent writes code] --> Registry[updateRegistry indexes exports/imports]
    Registry --> Reviewer[reviewerAgent checks quality and layering]
    Reviewer -->|approved| Executor[executorAgent runs deterministic checks]
    Reviewer -->|rejected| RetryContext[contextBuilder adds review feedback]
    RetryContext --> Coder

    Executor -->|pass| Snapshot[snapshotManager creates git tag]
    Snapshot --> NextTask[selectNextTask]
    Executor -->|fail| Debugger[debuggerAgent finds root cause]
    Debugger -->|fixable| RetryContext
    Debugger -->|retry limit| Rollback[rollback to last good git tag]
    Rollback --> RetryContext
    Debugger -->|exhausted| Human[humanEscalation asks user]
    Human -->|guidance| RetryContext
    Human -->|skip/simplify| NextTask
```

Why this matters:

> The project does not simply generate files once and hope they work. It repeatedly reviews, executes, debugs, snapshots, and only then moves to the next task. This is the main reason the orchestrator exists separately from the gateway.

---

#### 4. Failure by layer map

Diagram file: **failure by layer map** (diagram `failure_by_layer_map.mmd` is embedded in the diagram appendix)

```mermaid
flowchart TB
    subgraph Frontend[React Frontend]
        F1[Auth check fails]
        F2[Project start error]
        F3[SSE disconnected]
        F4[Preview tab cannot open/start]
    end

    subgraph Gateway[Node Express Gateway]
        G1[Mongo/Redis startup failure]
        G2[Auth middleware rejects request]
        G3[Orchestrator fetch fails]
        G4[Download ZIP validation fails]
        G5[Project metadata not updated]
    end

    subgraph Orchestrator[FastAPI + LangGraph Orchestrator]
        O1[LLM JSON parse failure]
        O2[Token budget exceeded]
        O3[Graph node exception]
        O4[Human input not pending]
        O5[Event stream timeout]
    end

    subgraph Sandbox[Docker Sandbox + Generated App]
        S1[Docker unavailable]
        S2[Port unavailable]
        S3[npm install fails]
        S4[Generated code syntax/import error]
        S5[Preview containers fail]
    end

    Frontend --> Gateway
    Gateway --> Orchestrator
    Orchestrator --> Sandbox
```

---

#### 5. Golden debugging order

When something breaks, do not randomly open every file. Debug in this order:

1. Identify the user-visible symptom.
   - UI error?
   - HTTP error?
   - Stream stopped?
   - Workflow failed?
   - Preview not opening?

2. Check the health endpoints.
   - Gateway health tells whether Node is alive and whether it can reach Python.
   - Orchestrator health tells whether FastAPI is alive.

3. Check the latest stream event.
   - `run.created` means orchestrator accepted the job.
   - `node.started` and `node.completed` show where the workflow reached.
   - `input.requested` means the system is waiting for the user.
   - `run.failed` means graph finished with error.
   - `run.cancelled` means user cancellation path ran.
   - `heartbeat` means the stream is still alive.

4. If the failure is in generated code, check the self-repair loop.
   - `reviewerAgent` catches design/layering problems.
   - `executorAgent` catches concrete syntax/import/env problems.
   - `debuggerAgent` converts errors into repair feedback.
   - `snapshotManager` preserves known-good code.
   - `humanEscalation` is used when automated repair is exhausted.

5. If the failure is preview/sandbox, check Docker last.
   - Generated app preview depends on Docker, port allocation, containers, dependency install, and app startup.

This order prevents a common mistake: blaming frontend when the real issue is orchestrator stream failure, or blaming Python when the real issue is Docker.

---

#### 6. Safe commands to debug locally

Use these commands first because they do not expose secrets and do not delete anything.

From the repository root:

```bash
docker compose ps
```

```bash
docker compose logs gateway
```

```bash
docker compose logs orchestrator
```

```bash
docker compose logs frontend
```

```bash
curl http://localhost:3000/api/health
```

```bash
curl http://localhost:8000/health
```

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

```bash
find sandbox -maxdepth 2 -type d | sort
```

For generated preview containers, look for container names like:

```text
aidev-db-sandbox-...
aidev-backend-sandbox-...
aidev-frontend-sandbox-...
```

Then inspect logs for the relevant generated app container:

```bash
docker logs CONTAINER_NAME
```

If you enter a generated sandbox folder, useful checks are:

```bash
ls
```

```bash
git status
```

```bash
find . -maxdepth 3 -type f | sort
```

Avoid printing `.env` files in screenshots or interviews because they can contain secrets.

---

#### 7. Common failure scenarios

##### Scenario 1: Frontend shows "Gateway event stream disconnected."

Where the error is shown:

- `frontend/src/App.jsx`
- The `EventSource` connection has an `onerror` handler.

What happened:

The React app opened an SSE connection to:

```text
/api/projects/:projectId/events
```

That gateway stream disconnected unexpectedly.

Likely causes:

- Gateway process stopped.
- User session cookie expired or missing.
- Gateway route returned an error.
- Gateway could not connect to orchestrator stream.
- Orchestrator stream ended after timeout.
- Browser/network interruption.

Where to debug:

- Browser DevTools Network tab.
- Gateway route: `gateway/src/routes/projects.js`.
- Gateway orchestrator client: `gateway/src/services/orchestratorClient.js`.
- Orchestrator event bus: `orchestrator/app/services/event_bus.py`.

Why the project handles it this way:

The frontend should not know LangGraph internals. It only knows that the stream disconnected and shows a user-facing error. Deeper diagnosis belongs in gateway/orchestrator logs.

Interview answer:

> If the stream disconnects, I first check whether Gateway is alive, then whether Gateway can reach the orchestrator SSE endpoint. The frontend only shows a generic stream error because it is intentionally decoupled from orchestration internals.

---

##### Scenario 2: `/api/health` returns `503 degraded`

Where it happens:

- `gateway/src/index.js`
- Health route calls `getOrchestratorHealth()`.

What happened:

Gateway is alive, but it could not get a successful health response from FastAPI.

Likely causes:

- Orchestrator container/process is down.
- `ORCHESTRATOR_URL` points to the wrong host/port.
- Docker Compose service DNS is wrong.
- FastAPI crashed during startup.

Where to debug:

- `gateway/src/services/orchestratorClient.js`
- `orchestrator/app/main.py`
- Gateway logs.
- Orchestrator logs.

Useful commands:

```bash
curl http://localhost:3000/api/health
```

```bash
curl http://localhost:8000/health
```

Interview answer:

> A degraded gateway health response means the public API layer is alive but its dependency, the orchestrator, is unhealthy or unreachable. That separation is useful because it tells us the frontend-to-gateway path is fine and narrows debugging to gateway-orchestrator connectivity.

---

##### Scenario 3: Gateway startup fails

Where it happens:

- `gateway/src/index.js`
- Startup waits for `connectMongo()` and `connectRedis()`.

What happened:

Gateway does not start listening until MongoDB and Redis connections succeed.

Likely causes:

- Mongo URI is invalid.
- Redis URL is invalid.
- Docker Compose dependencies are not up.
- Network/DNS issue.
- Secret or environment variable missing.

Why this is good:

Gateway depends on Mongo for auth/user data and Redis for token blacklist/session-related behavior. Starting without those dependencies would create confusing partial behavior.

Interview answer:

> Gateway fails fast when Mongo or Redis is unavailable. That is better than accepting user traffic while core auth/session storage is broken.

---

##### Scenario 4: Signup OTP is not sent

Where it happens:

- `gateway/src/routes/auth.js`
- `/api/auth/sendotp`
- `sendMail()` from `gateway/src/config/mail.js`

What happened:

The user attempted signup, but OTP sending or OTP storage failed.

Likely causes:

- Email or username missing.
- Email already registered.
- Username already taken.
- Mail credentials/provider issue.
- Mongo write failure for OTP.

Where to debug:

- Gateway route `/sendotp`.
- Mongo OTP model.
- Mail config.
- Gateway logs.

What to say in interview:

> OTP generation is handled in Gateway because it belongs to public user/auth concerns, not AI orchestration. The OTP is persisted first, then email is sent. If this fails, the user never reaches project generation, so we debug it as a gateway/auth issue.

---

##### Scenario 5: Login fails or session check fails

Where it happens:

- `gateway/src/routes/auth.js`
- `gateway/src/middleware/auth.js`
- Frontend boot logic in `frontend/src/App.jsx`

What happened:

The frontend calls:

```text
/api/auth/check
```

If the cookie is invalid/missing, the frontend shows the auth screen.

Likely causes:

- Wrong password.
- JWT secret mismatch.
- Cookie not set because CORS/credentials config is wrong.
- Redis blacklist contains token after logout.
- Browser blocked cookies.

Where to debug:

- Browser DevTools Application/Cookies.
- Frontend API helper: `frontend/src/api/gateway.js`.
- Auth middleware: `gateway/src/middleware/auth.js`.
- Gateway auth routes.

Interview answer:

> Auth is intentionally centralized in Gateway. The frontend never talks directly to the orchestrator, and the orchestrator does not need to understand browser cookies or user login.

---

##### Scenario 6: Project launch returns `409`

Where it happens:

- `gateway/src/routes/projects.js`
- `router.post("/")`

What happened:

Gateway found an existing project with status `running` or `queued` for the same user.

Why this was added:

The system prevents one user from launching multiple simultaneous builds. This avoids:

- Multiple expensive LLM workflows.
- Preview port conflicts.
- Too many Docker containers.
- Confusing UI state.
- Cross-project active preview confusion.

What to tell interviewer:

> We intentionally allow one active build per user to protect compute, token budget, Docker resources, and UI consistency. In production we could move this to a stronger distributed lock or queue.

---

##### Scenario 7: Project launch fails because orchestrator is unreachable

Where it happens:

- Frontend calls Gateway: `POST /api/projects`
- Gateway calls Orchestrator: `POST /runs`
- Code: `gateway/src/services/orchestratorClient.js`

What happened:

Gateway accepted the user request but could not create a run in FastAPI.

Likely causes:

- Orchestrator service down.
- Wrong `ORCHESTRATOR_URL`.
- FastAPI exception.
- Network issue between Node container and Python container.

What user sees:

The frontend catches `startError` and displays the message returned by Gateway.

Interview answer:

> Gateway is the synchronous boundary. It either gets a `project_id` from the orchestrator or returns a clear error. The expensive workflow runs async after run creation.

---

##### Scenario 8: Orchestrator accepts run but no events appear

Where it happens:

- `orchestrator/app/main.py`
- `orchestrator/app/services/event_bus.py`
- `gateway/src/services/orchestratorClient.js`

What happened:

The run was created, but the event stream is not delivering events.

Likely causes:

- Event stream connected after in-memory events were lost because orchestrator restarted.
- Orchestrator task crashed before emitting enough events.
- Gateway stream parser failed because response is not valid SSE.
- The event bus timed out after its stream window.

Important detail:

The event bus is currently in memory. That is simple for development, but not production durable. If the orchestrator restarts, old in-memory events are lost.

Production improvement:

- Store events in Redis Streams, Postgres, or another durable event log.
- Resume stream using cursor/last event ID.

Interview answer:

> For this version, events are in-memory and relayed through Gateway. It is simple and fast for a prototype, but a production version should use durable event storage so refreshes and restarts do not lose stream history.

---

##### Scenario 9: Workflow emits `run.failed`

Where it happens:

- `orchestrator/app/graph/workflow.py`
- `run_workflow()`

What happened:

LangGraph completed with `currentPhase == "failed"` or `state.error`, or an unhandled exception occurred.

How the code handles it:

- Each node is wrapped by `_run_node()`.
- `_run_node()` emits `node.started`.
- Node runs.
- State is checkpointed.
- `_run_node()` emits `node.completed`.
- If graph fails, `run_workflow()` emits `run.failed`.

Where to debug:

- The last `node.started` event without a matching `node.completed`.
- The `message` in `run.failed`.
- The node file corresponding to the last node.

Interview answer:

> A `run.failed` event is the orchestrator's terminal failure signal. I debug backward from the last completed node and inspect state.error or executionResult.errors to know whether it was an AI, workflow, sandbox, or generated-code issue.

---

##### Scenario 10: User cancels project

Where it happens:

- Frontend: `cancelProject()` in `frontend/src/App.jsx`
- Gateway: `POST /api/projects/:projectId/cancel`
- Orchestrator: `POST /runs/:projectId/cancel`
- Run manager: `orchestrator/app/services/run_manager.py`

What happened:

Gateway requests orchestrator cancellation, then marks project metadata as cancelled.

How cleanup works:

- Orchestrator calls `cancel_run(project_id)`.
- It also calls sandbox cleanup through `stop_sandbox_containers(project_id)`.
- If no active task exists, orchestrator still emits `run.cancelled` with message "No active workflow task found".

Why this is good:

The UI can show cancellation even if the workflow had already ended. It is safer to make cancel idempotent from the user perspective.

Interview answer:

> Cancel is best-effort and idempotent. If a workflow task is active, it is cancelled. If it already finished, the system still updates project state and tries sandbox cleanup.

---

##### Scenario 11: Gemini API key missing

Where it happens:

- `orchestrator/app/services/gemini_client.py`

What happened:

`GEMINI_API_KEY` is not set.

How the code handles it:

The orchestrator falls back to `_mock_agent_response()`.

Why this exists:

It allows local development and tests to run without calling the real model.

Risk:

Mock output is not as capable as live Gemini output, so generated app quality may be limited.

Interview answer:

> Missing Gemini credentials do not crash the system immediately. We use a mock fallback so the workflow remains testable locally. In production, I would probably fail fast or disable project generation if the real model key is missing.

---

##### Scenario 12: Gemini returns invalid or truncated JSON

Where it happens:

- `orchestrator/app/services/gemini_client.py`
- `_extract_json()`
- `_repair_truncated_json()`
- `call_json_agent()`

What happened:

LLM output was not valid JSON even though the prompt requested strict JSON.

How the code handles it:

- Removes markdown code fences.
- Extracts content between JSON brackets.
- Repairs truncated strings/brackets.
- Special-cases partial `files` arrays.
- Retries up to 3 attempts.
- On final failure raises `JSON_PARSE_FAILED after 3 attempts`.

Why this is important:

Every agent node depends on structured output. Invalid JSON can corrupt planning, file generation, reviews, and debugging.

Interview answer:

> LLMs are probabilistic, so we do not trust raw text. We enforce strict JSON parsing, try repair for common truncation cases, retry three times, and only then fail the node.

---

##### Scenario 13: Token budget exceeded

Where it happens:

- `orchestrator/app/services/gemini_client.py`
- `call_json_agent()`

What happened:

The accumulated estimated cost reached the configured project budget.

How the code handles it:

If `current_cost >= token_budget`, it raises:

```text
TOKEN_BUDGET_EXCEEDED
```

Why this exists:

Agentic loops can be expensive because they involve multiple nodes, retries, reviews, debugging, and deployment verification.

Interview answer:

> Token budget is a safety guard. Without it, one difficult generated app could loop through many agent calls and create unpredictable cost.

---

##### Scenario 14: PM asks for clarification but user input is stuck

Where it happens:

- `orchestrator/app/nodes/pmAgent.py`
- `orchestrator/app/nodes/humanInput.py`
- `orchestrator/app/services/input_bridge.py`
- Frontend `pendingInput` state in `frontend/src/App.jsx`

What happened:

The PM determined the requirement was unclear and routed to `humanInput`.

The system emits:

```text
input.requested
```

Frontend shows a form. User submits response to:

```text
/api/projects/:projectId/input
```

Likely causes if stuck:

- Frontend did not receive `input.requested`.
- User submitted wrong input type.
- Orchestrator restarted and lost in-memory pending input.
- User submitted after the future was already cleared.

Code behavior:

If no pending future exists, `submit_input()` returns:

```json
{ "accepted": false, "message": "No matching pending input request" }
```

Interview answer:

> Human input is modeled as an asynchronous wait in the orchestrator. The frontend only submits the answer through Gateway. If there is no pending input future, the orchestrator rejects the answer instead of applying it to the wrong state.

---

##### Scenario 15: Blueprint validation keeps looping

Where it happens:

- `orchestrator/app/nodes/blueprintValidator.py`
- `orchestrator/app/graph/workflow.py`

What happened:

The architecture blueprint is incomplete or inconsistent, so the validator routes back to a specific architect step.

Why this exists:

Bad architecture early creates worse generated code later. The validator catches missing models, endpoints, data relationships, or frontend/backend contract mismatches before planning tasks.

Risk if missing:

- Planner may create tasks from incomplete design.
- Coder may generate inconsistent API fields.
- Executor/debugger would waste time fixing avoidable downstream issues.

Interview answer:

> Blueprint validation is an early quality gate. It is cheaper to fix architecture before generating many files than to debug dozens of generated code errors later.

---

##### Scenario 16: Sandbox health check fails

Where it happens:

- `orchestrator/app/nodes/sandboxHealthCheck.py`
- `orchestrator/app/services/sandbox_files.py`

What happened:

The scaffold or Docker environment is not healthy.

Health check verifies:

- Backend folder exists.
- Frontend folder exists.
- Backend `package.json` exists.
- Frontend `package.json` exists.
- Git is initialized.
- DB container responds, if present.
- Backend container responds, if present.
- Frontend container responds, if present.
- Backend `node_modules` exists, if running with Docker.

How the code handles it:

- If failures are only Docker/container/node_modules related but sandbox path exists, it may allow local-only fallback.
- Otherwise it retries sandbox setup.
- After retry limit, it marks phase as failed and routes toward `presentToUser`.

Interview answer:

> Sandbox health check validates that the generated app has a safe workspace before coding begins. It prevents the system from writing code into a broken environment.

---

##### Scenario 17: Docker unavailable

Where it happens:

- `orchestrator/app/services/sandbox_process.py`
- `orchestrator/app/services/sandbox_runtime.py`

What happened:

The orchestrator cannot run `docker info`.

Likely causes:

- Docker Desktop is not running.
- Orchestrator container does not have Docker socket mounted.
- Current user cannot access Docker.
- `REQUIRE_DOCKER=true` but Docker is unavailable.

How the code handles it:

If Docker is required and unavailable, `create_sandbox()` raises a clear runtime error instructing to start Docker and ensure socket mount.

Interview answer:

> Docker is used to isolate generated apps. If Docker is unavailable and required, we fail sandbox setup instead of running generated code directly in the orchestrator process.

---

##### Scenario 18: No free preview ports

Where it happens:

- `orchestrator/app/services/sandbox_process.py`
- `_allocate_preview_ports()`

What happened:

The configured backend/frontend port ranges are full.

Likely causes:

- Old preview containers are still running.
- Another process is using the preview ports.
- Port pool size is too small.

Code behavior:

The allocator checks both local socket availability and Docker-published ports. If no pair is available, it raises:

```text
No free preview port pair found
```

Interview answer:

> Preview ports are dynamically allocated from a controlled range. The allocator checks host ports and Docker-published ports to reduce collision risk.

---

##### Scenario 19: npm install fails

Where it happens:

- `orchestrator/app/services/sandbox_runtime.py`
- `orchestrator/app/nodes/executorAgent.py`
- `orchestrator/app/nodes/deploymentVerifier.py`

What happened:

Dependencies for generated backend/frontend could not be installed.

Likely causes:

- Invalid package name/version generated.
- Network issue inside container.
- Package lock conflict.
- Generated package.json missing required dependency.

Current behavior:

- During sandbox setup, npm install output is printed but not always fatal.
- During executor checks, npm install result is added to outputs as ok or warning.
- During deployment verifier, Docker build failure becomes a real deployment error.

Interview answer:

> Dependency install is checked at multiple points. Lightweight executor checks catch obvious issues during coding, while deployment verification catches final build failures more strictly.

---

##### Scenario 20: Generated code has syntax error

Where it happens:

- `orchestrator/app/nodes/executorAgent.py`

What happened:

Generated `.js` file fails `node --check`.

How it is handled:

- Executor marks `executionResult.result = "fail"`.
- Error details are stored in `executionResult.errors`.
- Router sends flow to `debuggerAgent`.
- Debugger reads error and code context.
- Debugger produces root cause and fix.
- Coder retries with the debug feedback.

Interview answer:

> Syntax errors are not terminal immediately. They enter the automated repair loop through executor and debugger.

---

##### Scenario 21: Generated code has import/export mismatch

Where it happens:

- `orchestrator/app/nodes/executorAgent.py`
- `orchestrator/app/nodes/updateRegistry.py`
- `orchestrator/app/nodes/contextBuilder.py`

What happened:

A generated file imports something that does not exist or imports a named export that the target file does not provide.

Why the project can detect it:

- `updateRegistry` stores file interfaces, exports, and import statements.
- `contextBuilder` gives the coder relevant surrounding files and interfaces.
- `executorAgent` checks import resolution and named exports.

Interview answer:

> The file registry acts like project memory. It lets later nodes know what files exist and what they export, reducing broken imports as the generated codebase grows.

---

##### Scenario 22: Frontend generated code uses `process.env`

Where it happens:

- `orchestrator/app/nodes/executorAgent.py`

What happened:

Generated React frontend code used Node-style environment access.

Why this is wrong:

Vite frontend code should use:

```text
import.meta.env
```

Backend Node code should use:

```text
process.env
```

Executor catches both wrong directions:

- Frontend using `process.env`.
- Backend using `import.meta.env`.

Interview answer:

> The executor includes framework-specific checks, not just syntax checks. This catches mistakes that might compile in one environment but fail at runtime in another.

---

##### Scenario 23: Reviewer rejects code repeatedly

Where it happens:

- `orchestrator/app/nodes/reviewerAgent.py`

What happened:

The generated code violates review rules or backend layering rules.

Examples:

- Route files contain database queries.
- Route files contain bcrypt/JWT business logic.
- Controllers create routers.
- Models use Express `req`/`res`.
- Backend imports native `bcrypt` while package uses `bcryptjs`.

How it is handled:

- Reviewer increments `reviewRejections`.
- If below retry limit, routes back to `contextBuilder`.
- If retry limit reached, routes to `simplifyTask`.

Why this is important:

It keeps generated code aligned with the architecture, not just functional.

Interview answer:

> Reviewer enforces architectural quality before execution. If the coder repeatedly fails, we simplify the task instead of wasting unlimited retries.

---

##### Scenario 24: Debugger cannot fix the issue

Where it happens:

- `orchestrator/app/nodes/debuggerAgent.py`

What happened:

The executor failed, debugger tried to diagnose, but retry attempts were exhausted.

How it is handled:

1. Debugger attempts specific fixes.
2. If retry limit is reached and there are completed tasks, it tries rollback to the last good git tag.
3. If rollback is not possible or debugging remains exhausted, it escalates to human.

Why this is good:

It prevents infinite repair loops.

Interview answer:

> Debugger has a bounded retry strategy. It tries local fixes, then rollback, then human escalation. This gives resilience without unbounded cost or endless loops.

---

##### Scenario 25: Snapshot/rollback does not work

Where it happens:

- `orchestrator/app/services/sandbox_files.py`
- `snapshot()`
- `rollback()`

What happened:

Git snapshot or checkout failed.

Likely causes:

- Git not initialized in sandbox.
- Tag does not exist.
- Sandbox folder missing.
- File permissions issue.

Why snapshots exist:

Each successful task creates a known-good checkpoint. If later code breaks the project, rollback can restore a stable point.

Interview answer:

> We use git inside the sandbox as a simple local checkpoint system. It is lightweight and gives the debugger a safe recovery mechanism.

---

##### Scenario 26: Deployment verifier fails

Where it happens:

- `orchestrator/app/nodes/deploymentVerifier.py`

What happened:

The final generated app could not be built or started using Docker Compose.

Deployment verifier checks:

- Writes backend Dockerfile.
- Writes frontend Dockerfile.
- Writes frontend Nginx config.
- Writes docker-compose.yml.
- Runs Docker Compose build.
- Starts services.
- Probes backend health-like paths.
- Probes frontend root.
- Checks database readiness.

How it is handled:

- On failure, it records errors in `executionResult.errors`.
- Router sends to `debuggerAgent` if deployment repair attempts remain.
- After deployment repair limit, it routes to `presentToUser` with warnings.

Interview answer:

> Deployment verification is the final integration test. It checks not only code files but whether the generated backend, frontend, and database can run together.

---

##### Scenario 27: Preview restart fails

Where it happens:

- Frontend: `restartPreview()`
- Gateway: `POST /api/projects/:projectId/preview/restart`
- Orchestrator: `restart_sandbox_preview()`
- Sandbox runtime: `reconnect_sandbox()`

What happened:

The generated app exists, but preview containers could not be restarted.

Likely causes:

- No sandbox id yet.
- Sandbox folder missing.
- Docker unavailable.
- Port unavailable.
- npm install failed.
- Generated app crashes on startup.

Frontend behavior:

The frontend opens a blank tab first to avoid popup blocking. If restart fails, it writes the failure message into that tab.

Interview answer:

> Preview restart is treated separately from workflow completion. A project can have generated code but still need manual preview repair if containers or ports fail.

---

##### Scenario 28: Download ZIP fails

Where it happens:

- `gateway/src/routes/projects.js`
- `gateway/src/services/projectZip.js`

What happened:

Gateway could not package the generated sandbox files.

Possible error messages:

- `project has no sandbox id yet`
- `invalid sandbox id`
- `invalid sandbox path`
- `sandbox folder not found`
- `sandbox path is not a folder`
- `sandbox has no downloadable files`

Security behavior:

The ZIP creator validates sandbox ID/path and excludes risky or heavy files such as:

- `.env`
- `.git`
- `node_modules`
- build outputs
- logs

Interview answer:

> Download is intentionally served through Gateway so we can enforce ownership checks and sanitize the archive before sending generated code to the user.

---

##### Scenario 29: Orchestrator restart loses active run state

Where it happens:

- `orchestrator/app/services/run_manager.py`
- `orchestrator/app/services/event_bus.py`
- `orchestrator/app/services/input_bridge.py`
- `orchestrator/app/services/sandbox_state.py`

What happened:

Some state is in memory:

- Active asyncio tasks.
- Event bus events.
- Pending human input futures.
- Sandbox metadata map.

If orchestrator restarts, that in-memory state can disappear.

What is already better:

- `redis_checkpoint.py` checkpoints node state, so there is some persistent workflow progress.

Production improvement:

- Durable run manager.
- Durable event stream.
- Durable pending input table.
- Recover sandbox metadata by scanning sandbox folder and Docker labels.
- Resume workflow from checkpoint.

Interview answer:

> Current implementation is prototype-friendly. It checkpoints state, but active tasks and live event streams are still process-local. In production I would make those durable.

---

##### Scenario 30: Project ownership/security bug

Where it happens:

- `gateway/src/routes/projects.js`

Current good behavior:

- Project list is scoped to user.
- Project detail checks ownership.
- Download checks ownership.

Important hardening note:

Some mutation routes should also consistently verify project ownership before allowing input/cancel/preview operations. Authentication exists through `requireAuth`, but ownership should be applied consistently on every project-specific route.

Why this matters:

If a user guesses another project ID, they should not be able to affect that project.

Interview answer:

> A production-grade gateway should apply ownership checks to every project-specific route. The gateway is the correct place for this because it owns auth and user/project authorization.

---

#### 8. Debugging by layer

##### Frontend debugging

Main files:

- `frontend/src/App.jsx`
- `frontend/src/api/gateway.js`
- `frontend/src/components/AuthScreen.jsx`
- `frontend/src/components/Dashboard.jsx`

Check:

- Browser console errors.
- Network request status.
- Request URL: is it going to Gateway?
- Cookies: is the auth cookie present?
- SSE connection: is `/api/projects/:id/events` pending or failed?
- UI state: `error`, `pendingInput`, `isRunning`, `projectStatus`.

Common frontend symptoms:

- Auth screen appears unexpectedly: session check failed.
- Launch button disabled: active project exists or `isRunning` true.
- Stream disconnected: EventSource failed.
- Preview opens blank/failure page: restart preview failed.

##### Gateway debugging

Main files:

- `gateway/src/index.js`
- `gateway/src/routes/auth.js`
- `gateway/src/routes/projects.js`
- `gateway/src/services/orchestratorClient.js`
- `gateway/src/services/projectStore.js`
- `gateway/src/services/projectZip.js`

Check:

- Did Gateway start, or did Mongo/Redis connection fail?
- Does `/api/health` say `ok` or `degraded`?
- Is request authenticated?
- Does project belong to the logged-in user?
- Did orchestrator return non-2xx?
- Did Gateway parse and relay SSE events correctly?

Gateway's role in failures:

Gateway should convert internal failure details into safe API errors for frontend. It should not expose secrets or raw stack traces.

##### Orchestrator debugging

Main files:

- `orchestrator/app/main.py`
- `orchestrator/app/graph/workflow.py`
- `orchestrator/app/services/event_bus.py`
- `orchestrator/app/services/input_bridge.py`
- `orchestrator/app/services/gemini_client.py`
- `orchestrator/app/nodes/*.py`

Check:

- Last workflow event.
- Last completed node.
- `state.error`.
- `executionResult.errors`.
- Retry counters.
- Token usage.
- Whether the graph is waiting for human input.

Orchestrator's role in failures:

The orchestrator should own long-running, stateful, agentic failure recovery. This is exactly why we separated it from Gateway.

##### Sandbox/Docker debugging

Main files:

- `orchestrator/app/services/sandbox_runtime.py`
- `orchestrator/app/services/sandbox_process.py`
- `orchestrator/app/services/sandbox_files.py`
- `orchestrator/app/services/sandbox_database.py`
- `orchestrator/app/services/sandbox_preview.py`

Check:

- Is Docker available?
- Are generated containers running?
- Are ports mapped?
- Did npm install complete?
- Does backend respond?
- Does frontend respond?
- Is DB ready?
- Does generated code have correct env vars?

Sandbox's role in failures:

The sandbox isolates generated code from platform code. If generated app code crashes, it should not crash Gateway or Orchestrator.

---

#### 9. How to read workflow events during debugging

The event stream is your timeline.

Important event types:

| Event type | Meaning | Debug action |
|---|---|---|
| `run.created` | Orchestrator accepted the job | Gateway-to-orchestrator create path works |
| `node.started` | A node began execution | If stuck here, inspect that node |
| `node.completed` | A node completed and state checkpointed | Move to next node |
| `input.requested` | Workflow is waiting for user | Submit human input from UI |
| `input.received` | User answer reached orchestrator | Flow should continue |
| `heartbeat` | Stream alive but no new event | Wait or inspect long-running node |
| `run.completed` | Workflow succeeded | Check preview/download |
| `run.failed` | Workflow terminal failure | Inspect `message`, `state.error`, and last node |
| `run.cancelled` | User cancellation completed | Check cleanup if containers remain |

Interview answer:

> The stream is not just UI decoration; it is the debugging timeline. It shows the current node, state snapshots, terminal result, and whether the workflow is waiting for a user.

---

#### 10. Why separating Gateway and Orchestrator helps debugging

If frontend talked directly to FastAPI and FastAPI handled auth, events, project metadata, LLM workflow, and Docker, failures would be harder to isolate.

With three layers:

| Failure | Layer responsible | Reason |
|---|---|---|
| Login/OTP/cookie issue | Gateway | Public API/auth concern |
| Project list wrong | Gateway | Project metadata concern |
| SSE disconnected | Frontend + Gateway + Orchestrator | Trace from UI to event relay to event bus |
| LLM JSON failure | Orchestrator | AI workflow concern |
| Generated import error | Orchestrator | Code generation validation concern |
| Docker unavailable | Orchestrator/Sandbox | Runtime isolation concern |
| Download blocked | Gateway | Ownership and archive safety concern |

My honest view:

> For this kind of project, the three-layer architecture is the better choice. Direct frontend-to-FastAPI would look simpler at first, but it would mix browser/auth/API responsibilities with long-running agent orchestration and Docker sandbox control. That makes debugging, scaling, security, and interview explanation weaker.

---

#### 11. Interview Q&A

##### Q1. What happens if the model fails?

The orchestrator model client catches most model errors through `safe_call_json_agent()`. For normal parsing/provider failures, the node records an error and routes according to graph logic. For token budget exceeded, it raises because budget exhaustion is a hard stop. The project also has mock fallback if the API key is missing, which helps local testing.

##### Q2. What happens if the generated code is wrong?

Wrong generated code goes through reviewer, executor, debugger, and retry loop. Reviewer catches architectural/code-quality issues. Executor catches deterministic issues like missing files, syntax errors, imports, and env variable misuse. Debugger reads the error and generates targeted repair feedback. If retries fail, rollback or human escalation happens.

##### Q3. What happens if Docker is not running?

Sandbox setup checks Docker availability using `docker info`. If Docker is required and unavailable, sandbox creation fails with a clear error. This is safer than running generated code inside the orchestrator process.

##### Q4. What happens if a preview container fails?

Preview restart returns a structured result with `started`, ports, URLs, and errors. Gateway stores that status in project metadata. Frontend either opens the preview URL or displays the failure message.

##### Q5. What happens if the user refreshes during a build?

Gateway stores project metadata, so the project list can be reloaded. But current event streaming is process-memory based in the orchestrator, so a production version should persist event history and support resumable streams.

##### Q6. What happens if the user cancels during a build?

Frontend calls Gateway, Gateway calls Orchestrator, Orchestrator cancels the active asyncio task and attempts sandbox cleanup. Gateway marks the project cancelled so the UI can stop showing it as running.

##### Q7. How do retries work?

Retries are tracked in state using retry counters and limits. Different failure types have different counters, such as sandbox setup retries, review rejections, debug attempts, PM clarifications, and deployment repairs. This prevents infinite loops.

##### Q8. Why do we need human escalation?

Because AI self-repair cannot safely solve every issue. If the debugger is exhausted or confidence is too low, the system asks for human guidance. That is better than endlessly burning tokens or making random code changes.

##### Q9. What production improvements would you make?

I would add durable event storage, durable pending input, distributed run locks, stronger ownership checks on every project route, Docker resource limits, image scanning, secrets management, observability with trace IDs, and a worker queue for orchestrator runs.

##### Q10. How would you debug a failed interview demo quickly?

I would:

1. Check `/api/health`.
2. Check `docker compose ps`.
3. Check Gateway logs.
4. Check Orchestrator logs.
5. Inspect latest UI event.
6. If preview failed, check generated sandbox containers.
7. If generated code failed, read `executionResult.errors` and last node.

That gives a structured answer instead of guessing.

---

#### 12. The most important thing to remember

This project has two categories of failures:

1. Platform failures
   - Gateway down.
   - Orchestrator down.
   - Mongo/Redis unavailable.
   - Docker unavailable.
   - Event stream disconnected.

2. Productive workflow failures
   - Reviewer rejects code.
   - Executor catches syntax/import issues.
   - Debugger loops.
   - Deployment verifier fails and triggers repair.

In an interview, emphasize this:

> Some failures are not bugs; they are part of the agentic control loop. The system is designed to detect bad intermediate output, repair it, and only expose a terminal failure when recovery is exhausted.

</details>

<details id="inline-14-database-and-storage-deep-dive">
<summary>14_database_and_storage_deep_dive.md - Database and Storage Deep Dive</summary>

### Database and Storage Deep Dive

This note explains every important storage decision in the project: what is stored, where it is stored, why that storage was chosen, how the data flows, and what you should say in an interview.

The short interview answer is:

> This project uses different storage types for different responsibilities. MongoDB stores dashboard auth users and OTPs because that part came from a document-style auth module. PostgreSQL stores platform project metadata because project runs need structured querying, status tracking, ownership, preview URLs, and JSON state snapshots. Redis is used for fast temporary state like token blacklist and workflow checkpoints. The orchestrator also keeps live run tasks, events, pending human inputs, and sandbox metadata in memory because those are active runtime coordination objects. Generated app source code is stored on the filesystem under sandbox folders, and generated app data is stored either in a per-sandbox Docker database container or an external Postgres schema.

---

#### 1. Big picture: this project has two storage worlds

Do not mix these two in your head:

1. Platform storage
   - Stores the AI app builder's own data.
   - Examples: dashboard users, OTPs, project metadata, run status, preview ports, workflow checkpoints.
   - Used by the real frontend/gateway/orchestrator platform.

2. Generated app storage
   - Stores data for the app that the AI generates.
   - Example: if user asks for a todo app, the generated app gets its own `users`, `todos`, `categories`, etc.
   - Created inside each sandbox.

Interview wording:

> The platform database is for managing the AI builder itself. The generated app database is for the application produced by the AI. Keeping those separate prevents generated code from corrupting platform data.

---

#### 2. Storage architecture diagram

Diagram file: **database storage architecture** (diagram `database_storage_architecture.mmd` is embedded in the diagram appendix)

```mermaid
flowchart TB
    User[Browser User] --> Frontend[React Frontend]
    Frontend --> Gateway[Node Express Gateway]
    Gateway --> Mongo[(MongoDB)]
    Gateway --> PlatformPostgres[(Platform PostgreSQL)]
    Gateway --> GatewayRedis[(Redis)]
    Gateway --> Orchestrator[FastAPI LangGraph Orchestrator]

    Orchestrator --> CheckpointRedis[(Redis Checkpoints)]
    Orchestrator --> MemoryState[In-memory runtime maps]
    Orchestrator --> SandboxFS[Sandbox filesystem]
    Orchestrator --> DockerDB[(Per-sandbox Docker DB)]
    Orchestrator --> ExternalProjectDB[(Optional external project PostgreSQL)]

    SandboxFS --> GeneratedBackend[Generated Express Backend]
    SandboxFS --> GeneratedFrontend[Generated React Frontend]
    GeneratedBackend --> DockerDB
    GeneratedBackend --> ExternalProjectDB

    Mongo -. stores .-> AuthUsers[DashboardUser]
    Mongo -. stores .-> OTP[DashboardOTP]
    PlatformPostgres -. stores .-> Projects[projects]
    PlatformPostgres -. stores .-> Users[users]
    GatewayRedis -. stores .-> TokenBlacklist[token blocklist]
    CheckpointRedis -. stores .-> WorkflowSnapshots[AgentState checkpoints]
    MemoryState -. contains .-> EventsTasksInputs[events, tasks, pending input, sandbox map]
```

---

#### 3. Storage summary table

| Storage | Used by | Stores | Persistence | Why used |
|---|---|---|---|---|
| MongoDB | Gateway auth | Dashboard users and OTPs | Persistent | Flexible auth document models, TTL OTP expiry |
| PostgreSQL | Gateway project store | Platform users and project metadata | Persistent | Structured project status, ownership, preview fields, JSON state |
| Redis | Gateway auth + Orchestrator | Token blacklist and workflow checkpoints | Semi-persistent/cache depending deployment | Fast key-value temporary state |
| In-memory Python maps | Orchestrator | Active tasks, events, pending input, sandbox metadata | Lost on orchestrator restart | Simple live coordination for prototype |
| Filesystem sandbox | Orchestrator/generated app | Generated source files, package files, git repo | Persistent while folder exists | Real editable app workspace |
| Docker volumes/containers | Generated app runtime | Generated app DB data | Depends container/volume lifecycle | Isolated per generated app |
| Optional external project Postgres | Generated app runtime | Per-sandbox schema for generated app | Persistent external DB | Lets generated apps use managed Postgres |

The important architectural point:

> We do not use one database for everything because each data type has different lifetime, query pattern, isolation need, and risk level.

---

#### 4. Platform database ER diagram

Diagram file: **platform storage ER diagram** (diagram `platform_storage_er_diagram.mmd` is embedded in the diagram appendix)

```mermaid
erDiagram
    DASHBOARD_USER {
        string userName PK
        string firstName
        string lastName
        string profilePhoto
        string emailId UK
        string role
        string password_hash
        datetime createdAt
        datetime updatedAt
    }

    DASHBOARD_OTP {
        string emailId
        string otp
        datetime createdAt_TTL
    }

    PLATFORM_USER {
        text user_id PK
        text email UK
        text display_name
        timestamptz created_at
        timestamptz updated_at
    }

    PROJECT {
        text project_id PK
        text user_id FK
        text requirement
        text status
        text last_event_type
        text last_event_node
        text last_message
        jsonb last_state
        text sandbox_id
        int preview_frontend_port
        int preview_backend_port
        text preview_frontend_url
        text preview_backend_url
        boolean preview_running
        timestamptz created_at
        timestamptz updated_at
    }

    PLATFORM_USER ||--o{ PROJECT : owns
    DASHBOARD_USER ||--o{ DASHBOARD_OTP : requests
```

Important nuance:

Mongo `DashboardUser` and Postgres `users` are related conceptually, but they are not joined directly in code. When a dashboard user logs in/registers, Gateway syncs a public user record into the platform `users` table through `saveUser()`.

---

#### 5. Why MongoDB is used

MongoDB is used in the Gateway auth module.

Relevant files:

- `gateway/src/config/mongo.js`
- `gateway/src/models/userModel.js`
- `gateway/src/models/otpModel.js`
- `gateway/src/routes/auth.js`

##### 5.1 `connectMongo()`

File:

```text
gateway/src/config/mongo.js
```

What it does:

- Requires `MONGO_URI`.
- Connects Mongoose to MongoDB.
- If already connected, it returns without reconnecting.
- If `MONGO_URI` is missing, Gateway startup fails.

Why fail if Mongo is missing?

Because dashboard auth depends on Mongo. If users cannot login/register reliably, the public API should not start in a half-broken state.

Interview answer:

> Mongo is required for the dashboard auth module. Gateway fails fast when Mongo is missing so we do not accept user traffic without a working auth store.

##### 5.2 `DashboardUser` model

File:

```text
gateway/src/models/userModel.js
```

Stores:

- `userName`
- `firstName`
- `lastName`
- `profilePhoto`
- `emailId`
- `role`
- `password`
- timestamps

Key validation rules:

- `userName` is unique.
- `emailId` is unique and immutable.
- Email is validated using `validator.isEmail`.
- Username allows letters, numbers, and underscores.
- Password is required, and the route hashes it before saving.
- Role is restricted to `"user"`.

Why this model exists:

This is the dashboard account model. It is not the generated app's user model. It belongs to the app-builder platform.

Interview answer:

> `DashboardUser` represents a user of the AI app builder, not a user of the generated app. That distinction matters because generated app users must be isolated from platform users.

##### 5.3 `DashboardOTP` model

File:

```text
gateway/src/models/otpModel.js
```

Stores:

- `emailId`
- `otp`
- `createdAt`

Important feature:

`createdAt` has:

```text
expires: 5 * 60
```

That means MongoDB TTL index automatically expires OTP documents after 5 minutes.

Why Mongo is nice here:

TTL expiry is simple and natural in Mongo/Mongoose. OTPs are temporary documents, and automatic expiry avoids manual cleanup jobs.

Interview answer:

> OTPs are short-lived verification records. Mongo TTL expiry lets the database clean them automatically after five minutes.

---

#### 6. Why PostgreSQL is used for platform project metadata

PostgreSQL is used by Gateway's `projectStore`.

Relevant file:

```text
gateway/src/services/projectStore.js
```

It stores:

- Platform users.
- Project metadata.
- Last workflow event.
- Last workflow state snapshot.
- Sandbox ID.
- Preview ports and URLs.
- Preview running status.

##### 6.1 Why not store projects only in Mongo?

You could, but Postgres is a better fit for project metadata because:

- Project rows have clear structured fields.
- We frequently query by `user_id`.
- We sort by `updated_at`.
- We enforce primary keys and unique email.
- We store `last_state` as `jsonb`, so we still get flexible workflow state snapshots.
- It maps well to production reporting and admin dashboards.

Interview answer:

> We use Postgres for platform project metadata because project runs are structured business records. They need ownership, status, timestamps, preview fields, and queryability. JSONB gives flexibility for workflow state without losing relational structure.

##### 6.2 The `projects` table

Created in:

```text
ensureProjectsTable()
```

Columns:

| Column | Meaning |
|---|---|
| `project_id` | Primary ID returned by orchestrator |
| `user_id` | Owner of project |
| `requirement` | User's original prompt |
| `status` | `running`, `queued`, `completed`, `failed`, `cancelled` |
| `last_event_type` | Latest workflow event type |
| `last_event_node` | Latest node that emitted event |
| `last_message` | Latest event message |
| `last_state` | JSONB snapshot of latest AgentState |
| `sandbox_id` | Generated sandbox folder/container ID |
| `preview_frontend_port` | Host port for generated frontend |
| `preview_backend_port` | Host port for generated backend |
| `preview_frontend_url` | Public/local URL for preview frontend |
| `preview_backend_url` | Public/local URL for preview backend |
| `preview_running` | Whether preview is considered active |
| `created_at` | Created timestamp |
| `updated_at` | Updated timestamp |

Why `last_state` is JSONB:

The LangGraph `AgentState` contains many fields and can evolve over time. Storing the latest state as JSONB avoids constant SQL migrations for every internal workflow field, while still keeping top-level project fields relational.

Good interview line:

> We relationalize stable metadata and put evolving workflow state into JSONB. That is a practical hybrid design.

##### 6.3 The `users` table

Created in:

```text
ensureUsersTable()
```

Columns:

| Column | Meaning |
|---|---|
| `user_id` | Platform-level public user ID |
| `email` | Unique email |
| `display_name` | Name shown in dashboard |
| `created_at` | Creation time |
| `updated_at` | Update time |

Why this table exists when Mongo already has `DashboardUser`:

Mongo stores the full auth account. Postgres stores a lightweight platform user record for project ownership/reporting. This avoids joining project metadata to a Mongo collection.

Interview answer:

> Gateway syncs a minimal user projection into Postgres so project metadata can remain relational and queryable by `user_id`, while Mongo continues to own the full auth document.

##### 6.4 Memory fallback inside `projectStore`

`projectStore.js` has:

```text
memoryProjects = new Map()
memoryUsers = new Map()
```

Why:

- If `DATABASE_URL` is missing, project metadata can still work during local/demo mode.
- If a DB sync/read fails, the code logs a warning and falls back to memory.

Important limitation:

Memory fallback is not durable. If Gateway restarts, memory-only projects disappear.

Interview answer:

> The memory maps are a development fallback, not a production database. In production, `DATABASE_URL` should be configured and DB failures should be handled with stronger alerting.

---

#### 7. Redis usage

Redis is used in two places:

1. Gateway Redis client.
2. Orchestrator workflow checkpointing.

Relevant files:

- `gateway/src/config/redis.js`
- `gateway/src/routes/auth.js`
- `gateway/src/middleware/auth.js`
- `orchestrator/app/services/redis_checkpoint.py`

##### 7.1 Gateway Redis

Gateway creates a Redis client from:

```text
REDIS_URL
```

Default:

```text
redis://redis:6379/0
```

Redis is optional in the Gateway connection logic. If Redis cannot connect, it logs a warning and continues.

Why optional?

The main app can still run, but logout token blacklist may be weaker if Redis is unavailable.

##### 7.2 Token blacklist

On logout:

- Gateway reads cookie token.
- Verifies JWT.
- If Redis is open, stores:

```text
token:<jwt>
```

- Expiry is set to the token's original expiry time.

Why:

JWTs are stateless by default. If a user logs out, the server needs a way to reject that token before natural expiry. Redis is a good fit because blacklist entries are temporary and fast.

Interview answer:

> JWTs do not automatically become invalid on logout. Redis gives us a temporary blacklist until the token's expiry time.

##### 7.3 Orchestrator checkpoints

File:

```text
orchestrator/app/services/redis_checkpoint.py
```

For every completed node, workflow wrapper calls:

```text
checkpoint_state(project_id, node_name, next_state)
```

Redis keys:

```text
checkpoint:<project_id>:<node_name>
checkpoints:<project_id>
```

What is stored:

- Serialized `AgentState`.
- A list of checkpoint keys for that project.

Why:

LangGraph workflows are long-running and stateful. Checkpoints give a record of state after nodes complete.

Current limitation:

The project writes checkpoints but does not fully implement automatic recovery/resume from Redis after orchestrator restart.

Interview answer:

> Redis checkpointing gives us a foundation for recovery and debugging. The current project writes node-level state snapshots; a production version should add resume-from-checkpoint.

---

#### 8. In-memory orchestrator state

The orchestrator stores some data in Python process memory.

Relevant files:

- `orchestrator/app/services/run_manager.py`
- `orchestrator/app/services/event_bus.py`
- `orchestrator/app/services/input_bridge.py`
- `orchestrator/app/services/sandbox_state.py`

##### 8.1 Active workflow tasks

File:

```text
run_manager.py
```

Stores:

```text
_running_tasks: dict[str, asyncio.Task]
```

Why:

When a user creates a run, FastAPI starts `run_workflow()` as an async background task. To cancel it later, the orchestrator needs to remember the task object.

Limitation:

If orchestrator restarts, active task objects are lost.

##### 8.2 Event bus

File:

```text
event_bus.py
```

Stores:

```text
_events: dict[str, list[StreamEvent]]
_signals: dict[str, asyncio.Event]
```

Why:

The frontend needs real-time workflow events. The event bus collects events and streams them through SSE.

Behavior:

- Streams old events from cursor.
- Emits heartbeat every 15 seconds during inactivity.
- Stops on `run.completed`, `run.failed`, or `run.cancelled`.
- Stops after about 300 seconds.

Limitation:

Events are not durable. If orchestrator restarts, live event history is lost.

##### 8.3 Pending human input

File:

```text
input_bridge.py
```

Stores:

```text
_pending: dict[tuple[str, str], asyncio.Future]
_history: dict[str, list[dict]]
```

Why:

Some workflow nodes need user input, such as PM clarification or human escalation. The orchestrator waits on a future, and Gateway/frontend submit the response later.

Limitation:

Pending futures are process-local. If orchestrator restarts while waiting for human input, that pending request is lost.

##### 8.4 Sandbox metadata

File:

```text
sandbox_state.py
```

Stores:

```text
_sandboxes: dict[str, SandboxInfo]
_active_preview_by_user: dict[str, str]
```

Why:

The orchestrator needs to know which sandbox folder, containers, ports, DB type, and user are associated with each project.

Limitation:

Sandbox folders may still exist after restart, but the in-memory `SandboxInfo` map is lost unless reconnected.

Interview answer:

> In-memory state is acceptable for live coordination in a prototype, but production should persist active runs, events, pending input, and sandbox metadata so restarts are recoverable.

---

#### 9. AgentState as the main workflow data model

File:

```text
orchestrator/app/models/contracts.py
```

`AgentState` is the central state object passed through LangGraph.

It contains:

- Run identity: `projectId`, `userId`
- Requirement/spec: `userRequirement`, `clarifiedSpec`
- Architecture blueprint: entities, DB schema, API endpoints, pages, dependencies
- Planner state: task queue, current phase/task indexes
- File registry: generated files, exports, imports, interfaces
- Sandbox state: `sandboxId`, health, file tree, preview ports/URLs
- Dev-loop state: current task, coder output, review result, execution result, debug state
- Retry counts and retry limits
- Deployment config and attempts
- Token usage and token budget
- Terminal output and errors

Why this is important:

`AgentState` acts like the memory of the whole AI software team. Each node reads and updates part of it.

Interview answer:

> Instead of passing many separate variables between agents, we use a shared typed state object. This makes the workflow explicit, serializable, checkpointable, and easier to inspect.

---

#### 10. Generated app database lifecycle

Diagram file: **generated app database lifecycle** (diagram `generated_app_database_lifecycle.mmd` is embedded in the diagram appendix)

```mermaid
sequenceDiagram
    participant Architect as architectStep2
    participant Setup as setupSandbox
    participant Runtime as sandbox_runtime
    participant DB as Sandbox DB
    participant Backend as Generated Backend

    Architect->>Architect: Designs dbSchema with databaseType, tables, FKs, indexes
    Architect->>Setup: AgentState.blueprint.dbSchema
    Setup->>Runtime: create_sandbox(projectId, userId, folderStructure, dependencies, dbSchema)
    Runtime->>Runtime: Decide db_type from dependencies/db schema
    Runtime->>DB: Start Postgres or Mongo container OR initialize external Postgres schema
    Runtime->>DB: Apply generated CREATE TABLE SQL or init.sql when available
    Runtime->>Backend: Write backend .env DATABASE_URL
    Backend->>DB: connectDB() connects generated app to its DB
```

Generated app storage starts at architecture time:

1. `architectStep2` designs DB schema.
2. Schema is stored in `AgentState.blueprint.dbSchema`.
3. `setupSandboxNode()` passes DB schema into `create_sandbox()`.
4. `create_sandbox()` chooses Postgres or Mongo.
5. Scaffold writes backend DB config.
6. Sandbox starts DB container or initializes external schema.
7. Generated backend connects using `DATABASE_URL`.

---

#### 11. How generated DB type is chosen

There are two related decisions:

##### 11.1 Architecture-level decision

`architectStep2` asks the model to choose:

```text
PostgreSQL | MongoDB
```

and explain `databaseReason`.

##### 11.2 Sandbox runtime decision

`create_sandbox()` checks backend dependencies:

```text
mongoose -> mongo
otherwise -> postgres
```

`setupSandboxNode()` also seeds file registry differently depending on whether the blueprint says Mongo or Postgres.

Why:

Generated code needs matching database dependencies and scaffold files.

Interview answer:

> The architecture node decides the intended database type, and sandbox setup turns that decision into actual backend config, dependencies, and a running database environment.

---

#### 12. Generated app Postgres path

If generated app uses Postgres:

- `backend/src/config/db.js` exports `pool` and `connectDB`.
- Generated backend uses `pg.Pool`.
- `DATABASE_URL` points either to:
  - per-sandbox Postgres Docker container, or
  - external project Postgres with schema-specific search path.

Per-sandbox DB URL pattern:

```text
postgresql://postgres:postgres@aidev-db-sandbox-...:5432/appdb
```

This is written only as an example pattern; do not put real production credentials in docs.

##### 12.1 Per-sandbox Postgres container

Created in:

```text
sandbox_runtime.py
```

Container name:

```text
aidev-db-<sandbox_id>
```

Docker volume:

```text
aidev-dbdata-<sandbox_id>
```

Readiness check:

```text
pg_isready -U postgres
```

Table creation:

- `_generate_create_table_sql(db_schema)` creates SQL from blueprint.
- `_initialize_postgres_from_project_sql()` applies generated `backend/src/db/init.sql` if present and tables do not already exist.

Why this is good:

Each generated app gets isolated database state. A broken generated app cannot touch platform Postgres.

##### 12.2 External project Postgres

If `PROJECT_DB_URI` exists, generated Postgres apps can use an external DB.

Instead of creating all app tables in public schema, the code creates a per-sandbox schema:

```text
project_<sandbox_id>
```

Then it adds a search path option to the generated app DB URL:

```text
search_path=<project_schema>,public
```

Why this is good:

Multiple generated apps can share one managed Postgres database while still being isolated by schema.

Interview answer:

> For generated apps, we either start a dedicated Docker DB container or create a sandbox-specific schema in an external Postgres DB. That gives isolation per generated project.

---

#### 13. Generated app Mongo path

If generated app uses Mongo:

- Scaffold writes Mongoose config.
- Generated backend calls `mongoose.connect(process.env.DATABASE_URL)`.
- Sandbox starts a `mongo:7` container.
- Container name:

```text
aidev-db-<sandbox_id>
```

DB URL pattern:

```text
mongodb://aidev-db-sandbox-...:27017/appdb
```

Readiness check:

```text
mongosh --eval 'db.runCommand({ping:1})' --quiet
```

Why this exists:

Some generated apps may be simpler with document data, especially flexible content or nested records.

Interview answer:

> The generated app database is not fixed. The architect can choose MongoDB or PostgreSQL based on the app requirements, and sandbox setup creates the matching runtime environment.

---

#### 14. Filesystem storage

Generated app source code is stored on disk under the sandbox root.

Relevant files:

- `orchestrator/app/services/sandbox_state.py`
- `orchestrator/app/services/sandbox_files.py`
- `orchestrator/app/services/sandbox_runtime.py`
- `orchestrator/app/services/sandbox_scaffold.py`

Default root:

```text
/tmp/aidev-sandboxes
```

In Docker Compose, the repo has:

```text
./sandbox:/workspace/sandboxes
```

Important environment variables:

| Variable | Meaning |
|---|---|
| `SANDBOX_ROOT` or `SANDBOX_DIR` | Where sandbox folders are stored inside orchestrator |
| `HOST_SANDBOX_ROOT` | Host path mounted into Docker containers |
| `SANDBOX_FRONTEND_HOST_PORT` | Preview frontend base port |
| `SANDBOX_BACKEND_HOST_PORT` | Preview backend base port |
| `SANDBOX_PREVIEW_PORT_POOL_SIZE` | Number of port pairs available |
| `SANDBOX_PREVIEW_TTL_SECONDS` | Auto-stop time for preview containers |

What is stored in sandbox filesystem:

- `backend/package.json`
- `frontend/package.json`
- `backend/src/...`
- `frontend/src/...`
- `backend/.env`
- `frontend/.env`
- `docker-compose.yml` for generated app deployment verification
- generated Dockerfiles
- `.git` repository for snapshots and rollback

Why filesystem is used:

The output is real source code, not just database records. It must be editable, executable, zipped, previewed, and versioned.

Interview answer:

> Generated code belongs on the filesystem because it is an actual project workspace. We use database storage for metadata and filesystem storage for code artifacts.

---

#### 15. Git snapshots as storage

Inside each sandbox, the orchestrator initializes Git:

- `git init`
- `git add -A`
- `git commit -m "Initial scaffold"`
- `git tag v0.0.0`

Later, `snapshotManager` creates additional tags.

Why this matters:

Git becomes a lightweight versioned storage mechanism for generated source code.

Used for:

- Known-good checkpoints.
- Debug rollback.
- Tracking generated file evolution.

Interview answer:

> We use Git inside the sandbox as a local checkpoint system. It lets the debugger roll back to the last known-good generated code state.

---

#### 16. Project metadata update flow

Diagram file: **project metadata update flow** (diagram `project_metadata_update_flow.mmd` is embedded in the diagram appendix)

```mermaid
sequenceDiagram
    participant UI as React Frontend
    participant GW as Gateway
    participant OR as Orchestrator
    participant PG as Platform PostgreSQL
    participant MEM as Gateway memory map

    UI->>GW: POST /api/projects
    GW->>OR: POST /runs
    OR-->>GW: project_id, status=running
    GW->>MEM: saveProjectMetadata()
    GW->>PG: upsert projects row
    GW-->>UI: project response

    UI->>GW: GET /api/projects/:id/events
    GW->>OR: GET /runs/:id/events
    OR-->>GW: SSE events with state
    GW->>MEM: updateProjectFromEvent()
    GW->>PG: update last event, status, last_state, sandbox, preview fields
    GW-->>UI: relay SSE event
```

The project metadata gets updated at two main times:

1. When a project is created.
2. Whenever the event stream emits workflow progress.

Why event-based updates are useful:

The frontend can refresh and still show the latest project status because Gateway has been saving the last known event and state.

---

#### 17. Data lifecycle by object

##### 17.1 Dashboard user lifecycle

1. User requests OTP.
2. OTP is stored in Mongo.
3. OTP email is sent.
4. User registers with OTP.
5. Gateway validates OTP.
6. Gateway hashes password and stores `DashboardUser`.
7. Gateway deletes OTP documents for that email.
8. Gateway syncs public user into Postgres `users`.
9. Gateway sets JWT cookie.

Storage used:

- MongoDB for full auth user and OTP.
- PostgreSQL for public platform user projection.
- Redis later for token blacklist on logout.

##### 17.2 Project lifecycle

1. User submits requirement.
2. Gateway creates run in orchestrator.
3. Gateway stores project metadata in memory and Postgres.
4. Orchestrator emits events.
5. Gateway updates latest event and latest state in Postgres.
6. When workflow completes, project becomes `completed`.
7. Preview fields are saved.
8. Download uses project metadata to find sandbox ID.

Storage used:

- PostgreSQL for durable project metadata.
- Gateway memory for fast fallback.
- Orchestrator memory for live events.
- Redis for checkpoints.
- Filesystem for generated app code.

##### 17.3 Generated app lifecycle

1. Architect designs app DB schema.
2. Sandbox setup creates source folders.
3. Sandbox setup creates DB config.
4. Docker starts app DB container or external schema.
5. Coder writes generated models/routes/controllers.
6. Executor validates code.
7. Snapshot stores Git tag.
8. Deployment verifier writes Docker Compose files and checks runtime.
9. User previews or downloads generated app.

Storage used:

- Filesystem for generated source.
- Git for code snapshots.
- Docker DB container/volume or external schema for generated app data.

---

#### 18. Why not use only one database?

This is an interview favorite.

Bad answer:

> We used many databases because different parts were available.

Good answer:

> We used different storage mechanisms because the data has different lifecycle and access patterns.

Detailed reasoning:

| Data | Best storage | Reason |
|---|---|---|
| OTP | Mongo TTL document | Short-lived, auto-expiring |
| Dashboard auth user | Mongo/Mongoose | Existing document-style auth module |
| Project run metadata | Postgres | Structured status, ownership, timestamps |
| Workflow latest state | Postgres JSONB | Evolving state but tied to project row |
| Token blacklist | Redis | Temporary fast key-value data |
| Node checkpoints | Redis | Fast serialized workflow snapshots |
| Live events/tasks | Memory | Active process coordination |
| Generated source code | Filesystem | Real editable project files |
| Generated app data | Per-sandbox DB | Isolation from platform and other generated apps |

Interview answer:

> A single database would simplify deployment but make the design less correct. OTPs, project metadata, live tasks, generated code, and generated app data are not the same kind of data.

---

#### 19. What is durable and what is not?

| Data | Durable now? | Notes |
|---|---|---|
| Dashboard users | Yes | MongoDB |
| OTPs | Temporarily | MongoDB TTL expires them |
| Project metadata | Yes if `DATABASE_URL` configured | Falls back to memory otherwise |
| Public platform users | Yes if `DATABASE_URL` configured | Synced from auth |
| Redis token blacklist | Depends Redis persistence | Usually temporary |
| Redis checkpoints | Depends Redis persistence | Written but not fully used for resume |
| Active workflow task objects | No | Python memory only |
| SSE event history | No | Python memory only |
| Pending human input future | No | Python memory only |
| Sandbox metadata map | No | Python memory only |
| Sandbox source code | Yes while folder exists | Filesystem |
| Generated DB container data | Depends volume/container cleanup | Docker-managed |
| External project DB schema | Yes | Managed external DB |

Interview answer:

> The platform has durable records for users/projects, but active workflow coordination is still in-memory. That is acceptable for prototype simplicity, but production needs durable run/event/input state.

---

#### 20. Storage security considerations

##### 20.1 Secrets

Secrets should not be stored in Git or exposed in docs.

Sensitive values include:

- `MONGO_URI`
- `DATABASE_URL`
- `PROJECT_DB_URI`
- `GEMINI_API_KEY`
- `JWT_SECRET_KEY`
- mail credentials

Generated app `.env` files are excluded from ZIP download by Gateway's project ZIP service.

##### 20.2 Passwords

Dashboard passwords are hashed with bcrypt before storing in Mongo.

Generated apps are instructed to store `password_hash`, not plain passwords.

##### 20.3 Project ownership

Project metadata includes `user_id`.

Gateway uses it to scope project list and should enforce it consistently on all project-specific routes.

##### 20.4 Generated app database isolation

Generated app data must not share platform tables.

Current isolation methods:

- Separate Docker DB container per sandbox.
- Or external Postgres schema per sandbox.

Interview answer:

> The most important storage security boundary is between platform data and generated app data. Generated code should never have access to the platform auth or project metadata database.

---

#### 21. Production improvements

If asked "what would you improve?", say:

1. Use one clear platform identity source.
   - Today auth user is in Mongo and public platform user is in Postgres.
   - Production could keep this split, but it needs explicit identity-sync guarantees.

2. Add migrations.
   - Current Postgres tables are created with `create table if not exists` and `alter table add column`.
   - Production should use Prisma, Knex, Flyway, Liquibase, Alembic, or another migration system.

3. Make workflow events durable.
   - Use Redis Streams, Postgres event table, Kafka, or another event log.

4. Make pending human input durable.
   - Store pending input request in DB with status.

5. Resume workflows from checkpoints.
   - Redis checkpoints exist but full resume logic should be added.

6. Persist sandbox metadata.
   - Store sandbox ID, container names, ports, created time, expiry time, and status.

7. Add cleanup jobs.
   - Old sandboxes.
   - Old Docker volumes.
   - Expired previews.
   - Failed run artifacts.

8. Add DB indexes.
   - `projects(user_id, updated_at)`
   - `projects(status)`
   - generated app foreign key indexes.

9. Encrypt/separate secrets.
   - Use secret manager instead of `.env`.

10. Add backup strategy.
   - Platform Postgres backups.
   - Mongo backups.
   - Generated app artifact retention.

Interview answer:

> The biggest production gap is durability for orchestration runtime state. Users/projects are persisted, but live events, active tasks, and pending inputs need durable storage for restart recovery.

---

#### 22. Debugging database/storage issues

##### 22.1 Gateway cannot start

Likely cause:

- `MONGO_URI` missing or invalid.

Why:

`connectMongo()` throws if `MONGO_URI` is missing.

Check:

```bash
docker compose logs gateway
```

##### 22.2 Projects disappear after restart

Likely cause:

- `DATABASE_URL` missing or Postgres sync failed.
- Gateway was using memory fallback.

Check:

```bash
docker compose logs gateway
```

Look for:

```text
Project metadata DB sync skipped
```

##### 22.3 Logout does not invalidate old token

Likely cause:

- Redis unavailable.

Check:

```bash
docker compose logs gateway
```

Look for:

```text
Gateway Redis connection skipped
```

##### 22.4 Workflow state not recoverable after orchestrator restart

Likely cause:

- Active tasks/events/pending inputs are in memory.
- Redis checkpointing exists but resume logic is not implemented.

Check:

```bash
docker compose logs orchestrator
```

##### 22.5 Generated app DB not connecting

Likely causes:

- DB container not running.
- `DATABASE_URL` in generated backend `.env` is wrong.
- DB readiness failed.
- Generated model code uses wrong DB library.
- External project DB schema initialization failed.

Check:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

```bash
docker logs CONTAINER_NAME
```

##### 22.6 ZIP download misses files

Likely cause:

- ZIP service intentionally excludes `.env`, `.git`, `node_modules`, logs, build outputs.

This is expected and safer.

---

#### 23. Interview Q&A

##### Q1. Why are MongoDB and PostgreSQL both used?

MongoDB is used for dashboard auth users and OTPs, including TTL expiry for OTP. PostgreSQL is used for structured platform project metadata and user projection. They serve different responsibilities.

##### Q2. Why not store generated app code in the database?

Generated code is a real project workspace. It needs directories, package files, Dockerfiles, Git snapshots, npm install, preview, and ZIP download. Filesystem storage is the natural fit.

##### Q3. Why use Redis?

Redis is good for temporary fast state: token blacklist and workflow checkpoints. It avoids putting short-lived key-value data into the main relational DB.

##### Q4. Is Redis required?

Gateway continues if Redis is unavailable, but logout blacklist becomes weaker. Orchestrator checkpoints only write if `REDIS_URL` exists. Production should treat Redis availability more seriously.

##### Q5. What data is lost if orchestrator restarts?

Active task objects, in-memory event history, pending human input futures, and sandbox metadata maps can be lost. Redis checkpoints and filesystem sandboxes may remain.

##### Q6. What data is lost if Gateway restarts?

If Postgres is configured, project metadata survives. If Gateway was running memory-only because `DATABASE_URL` was missing or broken, memory-only project metadata is lost.

##### Q7. How is generated app database isolated?

Either each sandbox gets its own DB container and Docker volume, or external Postgres uses one schema per sandbox. This keeps generated app data separate from platform data.

##### Q8. Why store `last_state` as JSONB?

LangGraph state evolves frequently. JSONB lets us store the latest workflow snapshot without adding SQL columns for every internal agent field.

##### Q9. What is the cleanest future design?

Use Postgres as the primary platform DB with migrations, keep Redis for queues/events/checkpoints, keep object/filesystem storage for generated artifacts, and use separate generated-app databases or schemas for sandbox isolation.

##### Q10. What is the biggest risk in current storage design?

The biggest risk is process-local orchestrator state. If the orchestrator restarts, active runs and pending inputs are not fully recoverable even though checkpoints are written.

---

#### 24. Final mental model

Remember this:

```text
MongoDB       = dashboard auth and OTP
PostgreSQL   = platform users and project metadata
Redis        = temporary fast state and checkpoints
Memory       = live orchestration coordination
Filesystem   = generated source code
Docker DB    = generated app runtime data
External DB  = optional generated app schemas
```

Best interview closing line:

> The storage design separates platform identity, project metadata, workflow runtime state, generated source artifacts, and generated app data. That separation makes the system easier to debug, safer to run, and easier to evolve toward production.

</details>

<details id="inline-15-demo-script">
<summary>15_demo_script.md - Demo Script</summary>

### Demo Script

This file is your practical live-demo script for the project. Use it before an interview, presentation, code walkthrough, or GitHub demo.

The goal of the demo is not just to show buttons. The goal is to prove that you understand:

- what problem the project solves
- why the architecture has three layers
- how the request flows end-to-end
- how LangGraph agents build the app
- how events stream back to the dashboard
- how generated code is sandboxed, previewed, and downloaded
- what to say if something fails during the demo

---

#### 1. Demo objective

Say this:

> I am going to demo AgentForge, a three-layer AI full-stack app builder. The user enters a natural-language app requirement, and the platform generates a real full-stack app inside an isolated Docker sandbox. The React dashboard shows live progress while a Node gateway protects the public API and a Python LangGraph orchestrator runs the AI workflow.

What you want the interviewer to notice:

- The project is not just a chatbot.
- It has a frontend dashboard, secure gateway, internal orchestrator, event streaming, generated code, Docker sandbox, and preview/download flow.
- The architecture is explainable and defensible.

---

#### 2. Demo flow diagram

Diagram file: **demo flow** (diagram `demo_flow.mmd` is embedded in the diagram appendix)

```mermaid
flowchart TD
    A[Open AgentForge dashboard] --> B[Login or signup]
    B --> C[Explain three-layer architecture]
    C --> D[Enter project prompt]
    D --> E[Click Launch]
    E --> F[Show live workflow pipeline]
    F --> G{Human input requested?}
    G -->|Yes| H[Answer PM clarification or escalation]
    G -->|No| I[Continue watching events]
    H --> I
    I --> J[Show file tree and terminal stream]
    J --> K{Run completed?}
    K -->|Yes| L[Open generated website preview]
    K -->|Failed| M[Explain failure handling and debugger loop]
    L --> N[Download generated source ZIP]
    M --> N
    N --> O[Close with architecture and production improvements]
```

---

#### 3. One-minute opening pitch

Use this when the interviewer says, "Show me your project."

Say:

> This project is called AgentForge. It is an AI app-builder platform. A user logs into a React dashboard, writes a prompt like "build a todo app with login, categories, and due dates", and the system generates a full-stack application.
>
> The important part is the architecture. The frontend does not talk directly to the AI orchestrator. It talks to a Node/Express gateway. The gateway handles authentication, cookies, project ownership, project metadata, event relay, preview controls, and safe code download. Behind that, a Python FastAPI orchestrator runs a LangGraph workflow with multiple nodes like PM, architect, planner, coder, reviewer, executor, debugger, deployment verifier, and presenter.
>
> Generated code is created inside a Docker sandbox, so the AI-generated app is isolated from the platform itself. The dashboard streams progress live through server-sent events.

Do not rush this. This is your frame. Everything else in the demo supports this explanation.

---

#### 4. Pre-demo checklist

Before showing the project:

1. Make sure Docker is running.
2. Make sure `.env` exists locally but do not open it during the demo.
3. Start the stack.
4. Open the frontend dashboard.
5. Confirm Gateway health shows online.
6. Prepare one clean app prompt.
7. Keep a backup explanation ready in case LLM/Docker takes too long.

Safe commands:

```bash
docker compose ps
```

```bash
curl http://localhost:3000/api/health
```

```bash
curl http://localhost:8000/health
```

If asked how to start:

```bash
docker compose up --build
```

Only run this when you actually want to start the project. It can take time because images and npm dependencies may build/install.

---

#### 5. Suggested demo prompt

Use a prompt that is impressive but not too huge.

Recommended:

```text
Build a todo app with login, categories, due dates, priority levels, and a dashboard showing pending and completed tasks.
```

Why this is good:

- It naturally requires frontend, backend, database, auth, models, routes, pages, and components.
- It is familiar to interviewers.
- It is not too complex.
- It shows the value of architect/planner/coder/reviewer workflow.

Avoid prompts that are too broad:

```text
Build a complete Amazon clone.
```

Why avoid:

- Too large.
- More likely to hit token budget, retries, dependency issues, or long runtime.
- Harder to explain in a short demo.

---

#### 6. Demo timeline

Diagram file: **demo timeline** (diagram `demo_timeline.mmd` is embedded in the diagram appendix)

```mermaid
sequenceDiagram
    participant Presenter as You
    participant UI as React Dashboard
    participant GW as Gateway
    participant OR as Orchestrator
    participant LG as LangGraph
    participant SB as Docker Sandbox

    Presenter->>UI: Open dashboard
    Presenter->>UI: Login/signup
    Presenter->>UI: Enter project prompt
    UI->>GW: POST /api/projects
    GW->>OR: POST /runs
    OR->>LG: Start background workflow
    OR-->>GW: project_id
    GW-->>UI: Project created
    UI->>GW: EventSource /events
    GW->>OR: SSE /runs/:id/events
    LG-->>UI: Live node events through Gateway
    LG->>SB: Create sandbox and generate code
    SB-->>LG: Files, checks, preview URLs
    LG-->>UI: run.completed or run.failed
    Presenter->>UI: Open preview/download code
```

Suggested timing:

| Time | Action |
|---|---|
| 0:00-0:45 | Opening pitch |
| 0:45-1:30 | Show architecture at high level |
| 1:30-2:30 | Login/dashboard overview |
| 2:30-3:00 | Enter prompt and launch |
| 3:00-6:00 | Explain live nodes while workflow runs |
| 6:00-8:00 | Show file tree, terminal, token metrics |
| 8:00-10:00 | Preview/download/generated code |
| 10:00-12:00 | Failure handling and production improvements |

---

#### 7. Step-by-step demo script

##### Step 1: Open the dashboard

Click:

- Open frontend URL.

Say:

> This is the React/Vite frontend. It is intentionally only the user interface. It does not run the AI workflow directly. It talks to the Node gateway.

Point out:

- AgentForge title.
- Gateway health indicator.
- Login/signup screen if not authenticated.

If health says not online:

Say:

> This health indicator comes from the gateway. If it is degraded, I check whether the gateway can reach the Python orchestrator. This is one advantage of the layered design: failures are easier to isolate.

---

##### Step 2: Login or signup

Click:

- Login if you already have an account.
- Or signup with OTP if demoing auth.

Say:

> Authentication is handled by the gateway, not the orchestrator. The gateway owns OTP, JWT cookies, Mongo user storage, Redis token blocklist, and session checks. The orchestrator should not be responsible for browser login.

Mention briefly:

- MongoDB stores dashboard users and OTPs.
- OTPs expire automatically.
- Gateway sets an httpOnly cookie.

Do not open `.env` or show secrets.

---

##### Step 3: Show the dashboard layout

Point to:

- Project prompt box.
- Launch button.
- Cancel Active button.
- Metrics row.
- Preview controls.
- Pipeline nodes.
- Projects list.
- File tree.
- Terminal stream.
- Token usage.

Say:

> This dashboard is designed around a long-running AI workflow. A normal request/response UI would not be enough because app generation takes time. That is why we stream node events back to the frontend.

Important explanation:

> The pipeline view maps to LangGraph nodes. As the orchestrator emits `node.started` and `node.completed`, the dashboard updates in real time.

---

##### Step 4: Enter the project prompt

Paste:

```text
Build a todo app with login, categories, due dates, priority levels, and a dashboard showing pending and completed tasks.
```

Say:

> This prompt is intentionally product-level, not code-level. The system will turn it into architecture, database schema, API endpoints, frontend pages, tasks, and then code.

---

##### Step 5: Click Launch

Click:

- `Launch`

Say:

> When I click Launch, the frontend calls `POST /api/projects` on the gateway. The gateway checks authentication, checks whether this user already has an active project, stores metadata, and then calls `POST /runs` on the orchestrator.

Then explain the async boundary:

> The orchestrator returns a project ID quickly and starts the LangGraph workflow as a background task. The frontend then opens an EventSource stream through the gateway to watch progress.

Do not over-explain yet. Let the UI start showing events.

---

##### Step 6: Explain the three-layer call flow

Say:

> The browser only sees the gateway. The gateway is the secure public API boundary. The Python orchestrator is internal and focuses on AI workflow and Docker sandboxing. This avoids exposing Docker-control and LangGraph endpoints directly to the browser.

Use this diagram mentally:

```text
React UI -> Node Gateway -> FastAPI Orchestrator -> LangGraph -> Docker Sandbox
```

If asked "why not direct frontend to FastAPI?":

Say:

> Direct frontend-to-FastAPI would be simpler for a tiny prototype, but here FastAPI controls long-running AI agents and Docker containers. We do not want browser-facing auth, cookies, project metadata, downloads, and Docker orchestration all mixed in one service. The gateway gives us a clean security and product API boundary.

---

##### Step 7: Explain the live workflow nodes

As nodes activate, say:

> Each node has a specific responsibility. This is not one giant prompt. It is a controlled workflow where each step updates shared `AgentState`.

Quick node talk track:

| Node/stage | What to say |
|---|---|
| `pmAgent` | Clarifies the requirement and decides if user input is needed |
| `architectStep1` | Identifies entities and naming map |
| `architectStep2` | Designs database schema |
| `architectStep3` | Designs REST API endpoints |
| `architectStep4` | Designs frontend pages/components |
| `architectStep5` | Decides folder structure and dependencies |
| `blueprintValidator` | Checks architecture consistency before coding |
| `plannerAgent` | Breaks the app into buildable tasks |
| `setupSandbox` | Creates filesystem workspace and Docker runtime |
| `sandboxHealthCheck` | Verifies folders, package files, Git, containers |
| `selectNextTask` | Chooses the next planned task |
| `contextBuilder` | Collects relevant files/interfaces for the coder |
| `coderAgent` | Writes generated source files |
| `updateRegistry` | Indexes exports/imports/file interfaces |
| `reviewerAgent` | Reviews code and enforces layering |
| `executorAgent` | Runs deterministic syntax/import/env checks |
| `snapshotManager` | Saves a Git checkpoint after successful task |
| `debuggerAgent` | Diagnoses failures and gives repair feedback |
| `deploymentVerifier` | Builds/runs final app and probes services |
| `presentToUser` | Produces final output state and preview info |

Short interview line:

> The workflow is designed like a real engineering team: PM, architect, planner, coder, reviewer, tester, debugger, deployment verifier.

---

##### Step 8: If PM clarification appears

If the UI shows "PM Clarification":

Say:

> This is human-in-the-loop behavior. The PM node decided the requirement needed clarification, so the orchestrator paused and emitted an `input.requested` event. The frontend shows the question, and when I answer, Gateway forwards it back to the orchestrator.

Type an answer like:

```text
Use email/password login. Users can create, edit, complete, and delete their own tasks. Categories should be user-specific.
```

Click:

- `Send`

Say:

> After the answer is submitted, the orchestrator resumes the graph from the human input node.

---

##### Step 9: Show file tree

Point to:

- File Tree panel.

Say:

> As the workflow writes files into the sandbox, the state includes a file tree. This lets the dashboard show that real backend and frontend files are being generated, not just text output.

Mention:

- Backend files.
- Frontend files.
- Config files.
- Generated Docker/deployment files if present.

Good line:

> The generated app lives as a real project on disk, so it can be previewed, zipped, downloaded, or inspected later.

---

##### Step 10: Show terminal stream

Point to:

- Terminal Stream panel.

Say:

> The terminal stream is the workflow timeline. It shows which node emitted which event and message. This is extremely helpful for debugging because we can see where the workflow is currently running or where it failed.

Explain event types:

| Event | Meaning |
|---|---|
| `run.created` | Orchestrator accepted the run |
| `node.started` | A workflow node started |
| `node.completed` | A workflow node completed |
| `input.requested` | Orchestrator is waiting for user |
| `input.received` | User response arrived |
| `heartbeat` | Stream is still alive |
| `run.completed` | Generation succeeded |
| `run.failed` | Workflow ended with failure |
| `run.cancelled` | User cancelled |

---

##### Step 11: Explain review/debug/self-healing

When reviewer/executor/debugger nodes appear, say:

> Generated code is not trusted blindly. After code is written, the reviewer checks quality and layering. Then the executor runs deterministic checks like file existence, JavaScript syntax, import resolution, and environment variable usage. If something fails, the debugger reads the error and routes the workflow back for repair.

Important:

> Some failures inside the workflow are normal. A reviewer rejection or executor failure is not necessarily a failed project. It can be part of the self-repair loop.

Interview line:

> The project turns AI uncertainty into a controlled retry/debug loop.

---

##### Step 12: Show token/cost metrics

Point to:

- Token usage / cost metric.

Say:

> Because agentic workflows can call the model many times, the project tracks token usage and estimated cost. There is also a token budget guard so a difficult app does not loop forever and create unpredictable cost.

If asked why:

> Cost control is important for production AI systems. Long-running multi-agent generation needs budget limits.

---

##### Step 13: Wait for completion

If `run.completed` appears:

Say:

> The workflow completed. At this point we have generated source files, sandbox metadata, preview ports, and downloadable code.

If `run.failed` appears:

Say:

> This run failed after the recovery path was exhausted. That is still useful because the system emits a terminal event with state and error details. In production I would persist durable events and add stronger run recovery.

Then move to failure-handling explanation instead of panicking.

---

##### Step 14: Open generated website

Click:

- `Open Website`

Say:

> This opens the generated frontend running in the sandbox preview environment. The generated frontend calls its generated backend, and that backend connects to the generated app database.

If preview does not open:

Say:

> Preview is separate from generation. The code may be generated, but containers or ports can still fail. That is why the dashboard has restart/stop controls and why the orchestrator has deployment verification.

Good backup:

> If the live preview is slow, I can still show the generated files and explain the Docker preview path.

---

##### Step 15: Download generated code

Click:

- `Download Code`

Say:

> Download goes through the gateway, not directly from the filesystem. The gateway checks authentication and ownership, validates the sandbox ID, prevents path traversal, and excludes unsafe files like `.env`, `.git`, `node_modules`, build outputs, and logs.

Interview line:

> Gateway owns downloads because downloads are a security boundary.

---

##### Step 16: Show generated code structure

If you open the downloaded/generated folder, point out:

```text
backend/
frontend/
docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
```

Say:

> The output is a real full-stack project. Backend, frontend, database config, and deployment files are generated separately.

If showing generated backend:

> The generated backend follows Express layering: routes, middleware, config, models, controllers/services depending on what the app required.

If showing generated frontend:

> The generated frontend uses React/Vite and calls the generated backend through an API helper.

---

#### 8. Demo talk track by screen section

##### Gateway status

Say:

> This tells me the public API layer is reachable and whether it can reach the orchestrator.

##### Prompt box

Say:

> The user gives product requirements, not code instructions.

##### Launch button

Say:

> Launch creates a project run through Gateway and starts LangGraph asynchronously.

##### Cancel Active

Say:

> Cancel calls Gateway, Gateway calls orchestrator cancel, and the orchestrator attempts sandbox cleanup.

##### Pipeline

Say:

> This is the LangGraph workflow visualized as nodes.

##### Projects list

Say:

> Gateway persists project metadata, so the dashboard can show prior runs and status.

##### File tree

Say:

> This comes from the sandbox file system and proves the workflow is producing actual files.

##### Terminal stream

Say:

> This is the event stream. It is the best debugging timeline.

##### Token usage

Say:

> This tracks cost because multi-agent workflows can become expensive.

##### Preview controls

Say:

> These control generated app containers, not the platform containers.

---

#### 9. Architecture explanation during demo

Diagram file: **demo architecture talk track** (diagram `demo_architecture_talk_track.mmd` is embedded in the diagram appendix)

```mermaid
flowchart LR
    FE[React Frontend] -->|auth/project/events/preview/download| GW[Node Gateway]
    GW -->|protected internal calls| OR[FastAPI Orchestrator]
    OR -->|state machine| LG[LangGraph]
    LG -->|structured JSON calls| LLM[Gemini]
    LG -->|files/commands/db/containers| SB[Docker Sandbox]

    GW --> Mongo[(Mongo Auth + OTP)]
    GW --> PG[(Postgres Projects)]
    GW --> Redis[(Redis Token Blocklist)]
    OR --> Redis2[(Redis Checkpoints)]
    SB --> FS[Generated Source Files]
    SB --> GenDB[(Generated App DB)]
```

Say:

> The architecture is intentionally separated by responsibility. React handles user interaction. Gateway handles public API concerns. FastAPI orchestrator handles internal AI execution. Docker sandbox isolates generated code.

Then say:

> This design makes security and debugging easier. If login fails, I debug Gateway/Mongo. If event streaming fails, I debug Gateway-to-Orchestrator SSE. If generated code fails, I debug the LangGraph review/executor/debugger loop. If preview fails, I debug Docker sandbox.

---

#### 10. What to say if the demo is slow

If the workflow is still running:

Say:

> This is a long-running workflow because it is doing architecture, planning, generation, review, execution, debugging, and deployment verification. That is why the event stream is important: the user can see progress instead of waiting on a blank loading spinner.

Then show:

- pipeline nodes
- terminal stream
- file tree
- token usage
- project status

Good line:

> Even while it runs, we can tell exactly what stage it is in.

---

#### 11. What to say if the demo fails

Do not panic. A failed run can still demonstrate engineering maturity.

Say:

> The run failed, but this actually shows how the system reports failures. The dashboard receives a `run.failed` event, and the terminal stream shows the last node and error message. In this architecture, I can isolate whether the failure is frontend, gateway, orchestrator, LLM, Docker, or generated code.

Then explain:

| Failure | What you would inspect |
|---|---|
| Gateway health degraded | Gateway logs and orchestrator health |
| Event stream disconnected | Frontend EventSource, Gateway event relay, orchestrator event bus |
| Gemini JSON error | `gemini_client.py` parsing/retry logic |
| Docker unavailable | Docker socket, sandbox setup, preview containers |
| Generated code error | reviewer/executor/debugger nodes |
| Preview failed | sandbox containers, ports, generated app logs |

Strong recovery line:

> The important thing is that the system fails observably. It emits state and events instead of silently hanging.

---

#### 12. Five-minute demo version

Use this if time is short.

1. Show dashboard.
2. Say one-minute project pitch.
3. Explain three layers.
4. Enter prompt.
5. Click Launch.
6. Show pipeline and terminal events.
7. Explain PM/architect/planner/coder/reviewer/executor/debugger.
8. Show file tree.
9. Open preview if ready.
10. Download code if ready.
11. Close with production improvements.

Short closing:

> This project demonstrates a complete AI app-builder architecture: secure dashboard, gateway boundary, internal LangGraph orchestration, sandboxed generated code, live event streaming, and preview/download output.

---

#### 13. Two-minute demo version

Use this if the interviewer says, "Briefly show me."

Say:

> This is AgentForge. The user enters a natural-language requirement here. The frontend calls the Node gateway, and the gateway calls a Python LangGraph orchestrator. The orchestrator runs multiple agents: PM, architect, planner, coder, reviewer, executor, debugger, and deployment verifier. Each node streams events back to this dashboard. The generated app is written into a Docker sandbox, and the user can preview or download it.

Then show:

- Prompt box.
- Pipeline.
- Terminal stream.
- File tree.
- Preview/download buttons.

Close:

> The main design decision is separating the public product API from the internal AI/Docker runtime.

---

#### 14. Deep technical demo version

Use this if the interviewer is technical.

Talk through exact calls:

1. `frontend/src/App.jsx`
   - `startProject()`
   - calls Gateway `POST /api/projects`

2. `gateway/src/routes/projects.js`
   - checks requirement
   - checks active project
   - clears active preview
   - calls `createProjectRun()`
   - saves project metadata

3. `gateway/src/services/orchestratorClient.js`
   - sends `POST /runs`
   - opens `/runs/:projectId/events`
   - parses SSE chunks

4. `orchestrator/app/main.py`
   - creates `project_id`
   - appends `run.created`
   - creates background task for `run_workflow()`

5. `orchestrator/app/graph/workflow.py`
   - builds `StateGraph(AgentState)`
   - wraps each node with `_run_node()`
   - emits `node.started` and `node.completed`
   - checkpoints state

6. `orchestrator/app/services/sandbox_runtime.py`
   - creates sandbox folder
   - writes scaffold
   - initializes Git
   - starts DB/backend/frontend containers

7. `orchestrator/app/nodes/executorAgent.py`
   - checks generated files
   - validates syntax/imports/env usage

8. `orchestrator/app/nodes/deploymentVerifier.py`
   - writes Dockerfiles/compose
   - builds and probes services

9. `gateway/src/services/projectZip.js`
   - safely packages generated source code

Good deep line:

> The entire workflow revolves around `AgentState`. Every node reads and updates the same typed state object, which makes the workflow serializable and checkpointable.

---

#### 15. Demo Q&A cheat sheet

##### Q: Why not just call FastAPI directly from React?

Say:

> Because FastAPI controls internal AI workflow and Docker sandbox operations. The gateway protects that internal runtime with auth, ownership checks, metadata, and safe downloads.

##### Q: What makes this agentic?

Say:

> It is not one prompt. It is a stateful LangGraph workflow with specialized nodes, conditional routing, retries, human input, debugging, and deployment verification.

##### Q: How do you know generated code works?

Say:

> We do not fully trust generation. Reviewer checks code quality and architecture, executor runs deterministic checks, debugger repairs failures, and deployment verifier builds/runs the final app.

##### Q: How is generated code isolated?

Say:

> It is written into a sandbox folder and run in Docker containers with separate backend, frontend, and database runtime.

##### Q: What happens if generated code fails?

Say:

> Executor records errors, debugger identifies root cause, the workflow routes back to context/coder, and after retry limits it can rollback or escalate to human.

##### Q: Where is project state stored?

Say:

> Gateway stores project metadata in Postgres with memory fallback. The orchestrator has live in-memory events and writes Redis checkpoints. Generated code is stored on the filesystem.

##### Q: What would you improve for production?

Say:

> Durable event storage, resumable workflows, stronger ownership checks on all project routes, Docker resource limits, secret management, observability, queues/workers, and cleanup jobs for sandboxes and volumes.

##### Q: What is the hardest part of the project?

Say:

> The hardest part is controlling AI output. The system solves that by breaking generation into stages, enforcing JSON contracts, validating architecture, checking imports/exports, and adding a debug loop.

---

#### 16. Things not to do in demo

Do not:

- open `.env`
- show real API keys
- promise perfect generated code every time
- say the project is production-ready without caveats
- manually edit generated code during the main demo
- launch a very complex prompt
- ignore errors in the terminal stream
- say "it just uses AI" without explaining the workflow

Better wording:

> This is a working prototype with strong architectural foundations. Production hardening would focus on durable orchestration, resource controls, stronger authz, and observability.

---

#### 17. Final closing script

Say:

> To summarize, AgentForge is a three-layer AI app-builder. React gives the user a live dashboard. Node Gateway provides the secure public API boundary with auth, project metadata, event relay, preview controls, and downloads. Python FastAPI and LangGraph handle the internal AI workflow, model calls, retries, human input, Docker sandboxing, generated-code validation, and deployment verification.
>
> The biggest design idea is separation of concerns. Browser-facing product logic is separated from internal AI orchestration and generated-code execution. That makes the system easier to secure, debug, scale, and explain.

If you want a shorter final line:

> This is not just code generation; it is an end-to-end AI software development pipeline with live orchestration, validation, sandboxing, preview, and download.

</details>

<details id="inline-16-one-page-cheatsheet">
<summary>16_one_page_cheatsheet.md - One Page Cheatsheet</summary>

### One Page Cheatsheet

Use this as your fastest revision sheet before an interview or demo.

---

#### 1. 30-second pitch

AgentForge is a three-layer AI full-stack app builder. A user logs into a React dashboard, enters a natural-language app requirement, and the system generates a full-stack app inside an isolated Docker sandbox. The frontend streams live progress from a Node/Express gateway, while a Python FastAPI/LangGraph orchestrator runs agents for PM clarification, architecture, planning, coding, review, execution, debugging, deployment verification, preview, and download.

Best line:

> This is not just code generation; it is an end-to-end AI software development pipeline with live orchestration, validation, sandboxing, preview, and download.

---

#### 2. One diagram to remember

Diagram file: **one page cheatsheet map** (diagram `one_page_cheatsheet_map.mmd` is embedded in the diagram appendix)

```mermaid
flowchart LR
    U[User] --> FE[React Frontend]
    FE -->|JSON + cookies + SSE| GW[Node Gateway]
    GW -->|internal HTTP/SSE| OR[FastAPI Orchestrator]
    OR --> LG[LangGraph Workflow]
    LG --> LLM[Gemini JSON Agents]
    LG --> SB[Docker Sandbox]
    SB --> GEN[Generated Full-stack App]

    GW --> Mongo[(Mongo auth + OTP)]
    GW --> PG[(Postgres projects + last_state)]
    GW --> RedisA[(Redis token blocklist)]
    OR --> RedisB[(Redis checkpoints)]
    SB --> FS[Generated files + Git snapshots]
    SB --> DB[(Generated app DB)]
```

---

#### 3. Why three layers?

Say:

> We used three layers to separate user-facing product API concerns from internal AI/Docker orchestration.

Layer responsibilities:

| Layer | Responsibility |
|---|---|
| Frontend | UI, prompt, auth screens, event display, human input, preview/download buttons |
| Gateway | Auth, cookies, project ownership, metadata, event relay, preview controls, safe ZIP download |
| Orchestrator | LangGraph, Gemini calls, retries, checkpoints, Docker sandbox, generated-code execution |

Why not direct React to FastAPI?

> Direct FastAPI would be simpler for a small prototype, but here FastAPI controls long-running agents and Docker containers. The gateway keeps browser-facing auth, metadata, downloads, and ownership separate from internal orchestration.

---

#### 4. End-to-end flow

1. User logs in/signs up.
2. Frontend calls `GET /api/auth/check`.
3. User enters prompt.
4. Frontend calls Gateway `POST /api/projects`.
5. Gateway checks auth and active-project rule.
6. Gateway calls Orchestrator `POST /runs`.
7. Orchestrator creates `project_id`.
8. Orchestrator starts `run_workflow()` as background task.
9. Frontend opens EventSource to Gateway `/api/projects/:id/events`.
10. Gateway relays Orchestrator SSE events.
11. LangGraph runs nodes.
12. Sandbox creates generated app files and containers.
13. Reviewer/executor/debugger validate and repair.
14. Deployment verifier checks final runtime.
15. User opens preview or downloads code ZIP.

---

#### 5. LangGraph node story

Say:

> The workflow behaves like an AI software team.

| Stage | Nodes | Purpose |
|---|---|---|
| Product | `pmAgent`, `humanInput` | Clarify requirement |
| Architecture | `architectStep1-5`, `blueprintValidator` | Entities, DB schema, APIs, pages, dependencies |
| Planning | `plannerAgent`, `selectNextTask` | Break project into tasks |
| Sandbox | `setupSandbox`, `sandboxHealthCheck` | Create isolated workspace/runtime |
| Coding | `contextBuilder`, `coderAgent`, `updateRegistry` | Generate files with context |
| Quality | `reviewerAgent`, `executorAgent` | Review, syntax/import/env checks |
| Recovery | `debuggerAgent`, `simplifyTask`, `humanEscalation` | Repair or ask user |
| Finish | `phaseVerification`, `patternExtractor`, `stateCompactor`, `deploymentVerifier`, `presentToUser` | Verify and present output |

Best line:

> It is not one giant prompt. It is a controlled state machine with specialized nodes, retries, human input, and deployment verification.

---

#### 6. Key files to mention

Frontend:

- `frontend/src/App.jsx` — main state, project launch, EventSource, preview actions.
- `frontend/src/api/gateway.js` — Gateway fetch helper and URL normalization.
- `frontend/src/components/Dashboard.jsx` — pipeline, terminal, file tree, preview controls.

Gateway:

- `gateway/src/index.js` — Express app, health, routes, WebSocket/SSE relay.
- `gateway/src/routes/auth.js` — OTP, register, login, logout, check.
- `gateway/src/routes/projects.js` — create project, events, input, cancel, preview, download.
- `gateway/src/services/orchestratorClient.js` — calls FastAPI.
- `gateway/src/services/projectStore.js` — Postgres project metadata with memory fallback.
- `gateway/src/services/projectZip.js` — safe generated-code ZIP.

Orchestrator:

- `orchestrator/app/main.py` — FastAPI run/events/cancel/input/preview endpoints.
- `orchestrator/app/graph/workflow.py` — builds/invokes LangGraph.
- `orchestrator/app/models/contracts.py` — `AgentState`, request models, `StreamEvent`.
- `orchestrator/app/services/gemini_client.py` — strict JSON LLM calls, retries, token budget.
- `orchestrator/app/services/event_bus.py` — SSE event broker.
- `orchestrator/app/services/input_bridge.py` — human input futures.
- `orchestrator/app/services/sandbox*.py` — Docker, files, DB, preview, snapshots.

---

#### 7. Storage quick map

| Store | Data |
|---|---|
| MongoDB | Dashboard users and OTPs |
| PostgreSQL | Platform users, project metadata, `last_state` JSONB |
| Redis | Token blocklist and workflow checkpoints |
| Python memory | Active tasks, events, pending input, sandbox map |
| Filesystem | Generated source code |
| Git in sandbox | Snapshots and rollback tags |
| Docker DB/external schema | Generated app data |

Best line:

> Platform data and generated app data are separated so generated code cannot corrupt platform auth or project metadata.

---

#### 8. Failure handling quick map

| Failure | Handling |
|---|---|
| Gateway cannot reach orchestrator | `/api/health` returns degraded |
| Event stream disconnects | Frontend shows stream error |
| Gemini bad JSON | JSON extraction/repair/retry, then node failure |
| Token budget exceeded | Hard stop |
| PM needs clarification | `input.requested`, UI answer, resume |
| Sandbox unhealthy | Retry setup, then fail/present |
| Reviewer rejects | Route back to context/coder or simplify |
| Executor fails | Route to debugger |
| Debugger exhausted | Rollback or human escalation |
| Preview fails | Restart/stop controls and error message |
| Download risk | Gateway validates sandbox and excludes unsafe files |

Best line:

> Some failures are not bugs; they are part of the agentic control loop.

---

#### 9. SOLID answer

Say:

> The project follows SOLID mainly through separation of responsibilities and replaceable modules.

Examples:

- Single Responsibility: frontend UI, gateway auth/metadata, orchestrator workflow, sandbox services.
- Open/Closed: add new LangGraph node without rewriting frontend/gateway.
- Liskov/Interface idea: nodes follow `AgentState -> AgentState`.
- Interface Segregation: gateway exposes simple HTTP endpoints; orchestrator hides internal Docker/LLM details.
- Dependency Inversion: frontend depends on Gateway API, not on LangGraph/Docker internals.

---

#### 10. Demo script in 45 seconds

Say:

> I enter a prompt here and click Launch. The frontend calls Gateway. Gateway authenticates the user and creates a project run in the orchestrator. The orchestrator starts LangGraph in the background and streams events back through Gateway. These pipeline nodes show the AI team working: PM, architect, planner, coder, reviewer, executor, debugger, and deployment verifier. The generated app is written into a Docker sandbox. When it completes, I can open the generated website or download the generated source code safely through Gateway.

---

#### 11. Most likely interview questions

##### Why three layers?

Separation of concerns and security. Browser-facing auth/metadata/downloads stay in Gateway; internal AI/Docker orchestration stays in Python.

##### Why LangGraph?

Because app generation is a multi-step, stateful workflow with conditional routing, retries, human input, and failure recovery.

##### Why Docker sandbox?

To isolate generated code from platform code and run generated backend/frontend/database safely.

##### How streaming works?

Orchestrator emits `StreamEvent`s. Gateway opens orchestrator SSE, updates project metadata, and forwards events to frontend EventSource.

##### How generated code is validated?

Reviewer checks architecture/layering. Executor checks files, syntax, imports, and env usage. Debugger repairs failures. Deployment verifier builds/runs final app.

##### What is `AgentState`?

The typed shared workflow memory passed between LangGraph nodes. It stores requirement, blueprint, task queue, file registry, sandbox info, retries, token usage, errors, and output.

##### What would you improve?

Durable event storage, resumable workflows, stronger ownership checks on all project routes, Docker resource limits, secret manager, observability, queue workers, cleanup jobs.

---

#### 12. Golden closing line

Say:

> The core idea is controlled AI software generation. We do not just ask an LLM for code; we orchestrate a software-development workflow with architecture, planning, validation, execution, debugging, sandboxing, and delivery.

</details>

<details id="inline-readme">
<summary>README.md - Original Study README / Index</summary>

### AIDevFinalThreeLayer Study Notes

This folder contains deep study notes for common project questions. Each note is written for later revision, interview preparation, and architecture explanation.

#### Questions

1. **Why did we use three-layer architecture?** (copied below from `01_three_layer_architecture.md`)
2. **Explain the project architecture in detail** (copied below from `02_project_architecture.md`)
3. **High-level project overview for beginners** (copied below from `03_high_level_project_overview.md`)
4. **Workflow nodes deep dive** (copied below from `04_workflow_nodes_deep_dive.md`)
5. **Project call flow and sandbox lifecycle** (copied below from `05_project_call_flow_and_sandbox_lifecycle.md`)
6. **SOLID principles, HLD, LLD, models, ERD, and UML** (copied below from `06_solid_hld_lld_models_erd_uml.md`)
7. **Gateway deep dive, file by file** (copied below from `07_gateway_deep_dive.md`)
8. **Orchestrator deep dive, file by file** (copied below from `08_orchestrator_deep_dive.md`)
9. **Frontend deep dive, file by file** (copied below from `09_frontend_deep_dive.md`)
10. **Generated app and sandbox output** (copied below from `10_generated_app_and_sandbox_output.md`)
11. **Interview master Q&A** (copied below from `11_interview_master_qa.md`)
12. **Security and production hardening** (copied below from `12_security_and_production_hardening.md`)
13. **Failure scenarios and debugging** (copied below from `13_failure_scenarios_and_debugging.md`)
14. **Database and storage deep dive** (copied below from `14_database_and_storage_deep_dive.md`)
15. **Demo script** (copied below from `15_demo_script.md`)
16. **One page cheatsheet** (copied below from `16_one_page_cheatsheet.md`)

#### Diagrams

- **Three-layer architecture** (diagram `three_layer_architecture.mmd` is embedded in the diagram appendix)
- **Direct frontend-to-FastAPI alternative** (diagram `direct_frontend_to_fastapi_alternative.mmd` is embedded in the diagram appendix)
- **Responsibility split** (diagram `responsibility_split.mmd` is embedded in the diagram appendix)
- **Overall project architecture** (diagram `overall_project_architecture.mmd` is embedded in the diagram appendix)
- **Project run and event flow** (diagram `project_run_event_flow.mmd` is embedded in the diagram appendix)
- **Orchestrator workflow** (diagram `orchestrator_workflow.mmd` is embedded in the diagram appendix)
- **Data storage map** (diagram `data_storage_map.mmd` is embedded in the diagram appendix)
- **High-level project overview** (diagram `high_level_project_overview.mmd` is embedded in the diagram appendix)
- **Workflow node stages** (diagram `workflow_node_stages.mmd` is embedded in the diagram appendix)
- **End-to-end project call chain** (diagram `end_to_end_call_chain.mmd` is embedded in the diagram appendix)
- **Gateway to orchestrator event relay** (diagram `gateway_orchestrator_event_relay.mmd` is embedded in the diagram appendix)
- **Sandbox Docker lifecycle** (diagram `sandbox_docker_lifecycle.mmd` is embedded in the diagram appendix)
- **HLD component diagram** (diagram `hld_component_diagram.mmd` is embedded in the diagram appendix)
- **LLD module diagram** (diagram `lld_module_diagram.mmd` is embedded in the diagram appendix)
- **SOLID responsibility map** (diagram `solid_responsibility_map.mmd` is embedded in the diagram appendix)
- **Platform ER diagram** (diagram `platform_er_diagram.mmd` is embedded in the diagram appendix)
- **Generated app conceptual ER diagram** (diagram `generated_app_conceptual_er_diagram.mmd` is embedded in the diagram appendix)
- **Gateway UML class diagram** (diagram `gateway_uml_class_diagram.mmd` is embedded in the diagram appendix)
- **Orchestrator UML class diagram** (diagram `orchestrator_uml_class_diagram.mmd` is embedded in the diagram appendix)
- **Gateway module dependency diagram** (diagram `gateway_module_dependency.mmd` is embedded in the diagram appendix)
- **Gateway auth flow** (diagram `gateway_auth_flow.mmd` is embedded in the diagram appendix)
- **Gateway project run flow** (diagram `gateway_project_run_flow.mmd` is embedded in the diagram appendix)
- **Gateway event stream flow** (diagram `gateway_event_stream_flow.mmd` is embedded in the diagram appendix)
- **Gateway file map** (diagram `gateway_file_map.mmd` is embedded in the diagram appendix)
- **Gateway project creation flow** (diagram `gateway_project_creation_flow.mmd` is embedded in the diagram appendix)
- **Gateway event relay flow** (diagram `gateway_event_relay_flow.mmd` is embedded in the diagram appendix)
- **Orchestrator gateway connection** (diagram `orchestrator_gateway_connection.mmd` is embedded in the diagram appendix)
- **Orchestrator LangGraph workflow detailed** (diagram `orchestrator_langgraph_workflow_detailed.mmd` is embedded in the diagram appendix)
- **Orchestrator node wrapper and streaming** (diagram `orchestrator_node_wrapper_streaming.mmd` is embedded in the diagram appendix)
- **Orchestrator human input flow** (diagram `orchestrator_human_input_flow.mmd` is embedded in the diagram appendix)
- **Orchestrator sandbox lifecycle detailed** (diagram `orchestrator_sandbox_lifecycle_detailed.mmd` is embedded in the diagram appendix)
- **Orchestrator file map** (diagram `orchestrator_file_map.mmd` is embedded in the diagram appendix)
- **Frontend file map** (diagram `frontend_file_map.mmd` is embedded in the diagram appendix)
- **Frontend auth flow** (diagram `frontend_auth_flow.mmd` is embedded in the diagram appendix)
- **Frontend project stream flow** (diagram `frontend_project_stream_flow.mmd` is embedded in the diagram appendix)
- **Frontend human input flow** (diagram `frontend_human_input_flow.mmd` is embedded in the diagram appendix)
- **Frontend preview actions** (diagram `frontend_preview_actions.mmd` is embedded in the diagram appendix)
- **Generated app lifecycle** (diagram `generated_app_lifecycle.mmd` is embedded in the diagram appendix)
- **Generated sandbox tree** (diagram `generated_sandbox_tree.mmd` is embedded in the diagram appendix)
- **Generated backend layering** (diagram `generated_backend_layering.mmd` is embedded in the diagram appendix)
- **Generated preview and download flow** (diagram `generated_preview_and_download_flow.mmd` is embedded in the diagram appendix)
- **Generated deployment output** (diagram `generated_deployment_output.mmd` is embedded in the diagram appendix)
- **Interview master architecture** (diagram `interview_master_architecture.mmd` is embedded in the diagram appendix)
- **Interview answer flow** (diagram `interview_answer_flow.mmd` is embedded in the diagram appendix)
- **Interview runtime sequence** (diagram `interview_runtime_sequence.mmd` is embedded in the diagram appendix)
- **Security boundary diagram** (diagram `security_boundary_diagram.mmd` is embedded in the diagram appendix)
- **Security risk to fix map** (diagram `security_risk_to_fix_map.mmd` is embedded in the diagram appendix)
- **Security production roadmap** (diagram `security_production_roadmap.mmd` is embedded in the diagram appendix)
- **Failure debugging decision tree** (diagram `failure_debugging_decision_tree.mmd` is embedded in the diagram appendix)
- **Failure runtime recovery loop** (diagram `failure_runtime_recovery_loop.mmd` is embedded in the diagram appendix)
- **Failure by layer map** (diagram `failure_by_layer_map.mmd` is embedded in the diagram appendix)
- **Database storage architecture** (diagram `database_storage_architecture.mmd` is embedded in the diagram appendix)
- **Platform storage ER diagram** (diagram `platform_storage_er_diagram.mmd` is embedded in the diagram appendix)
- **Generated app database lifecycle** (diagram `generated_app_database_lifecycle.mmd` is embedded in the diagram appendix)
- **Project metadata update flow** (diagram `project_metadata_update_flow.mmd` is embedded in the diagram appendix)
- **Demo flow** (diagram `demo_flow.mmd` is embedded in the diagram appendix)
- **Demo timeline** (diagram `demo_timeline.mmd` is embedded in the diagram appendix)
- **Demo architecture talk track** (diagram `demo_architecture_talk_track.mmd` is embedded in the diagram appendix)
- **One page cheatsheet map** (diagram `one_page_cheatsheet_map.mmd` is embedded in the diagram appendix)

</details>

## Complete Inline Mermaid Diagram Appendix

Every local `study/diagrams/*.mmd` file is copied below as a renderable GitHub Mermaid block.

| Original Diagram File | Diagram |
| --- | --- |
| `three_layer_architecture.mmd` | [Three-layer architecture](#diagram-three-layer-architecture) |
| `direct_frontend_to_fastapi_alternative.mmd` | [Direct frontend-to-FastAPI alternative](#diagram-direct-frontend-to-fastapi-alternative) |
| `responsibility_split.mmd` | [Responsibility split](#diagram-responsibility-split) |
| `overall_project_architecture.mmd` | [Overall project architecture](#diagram-overall-project-architecture) |
| `project_run_event_flow.mmd` | [Project run and event flow](#diagram-project-run-event-flow) |
| `orchestrator_workflow.mmd` | [Orchestrator workflow](#diagram-orchestrator-workflow) |
| `data_storage_map.mmd` | [Data storage map](#diagram-data-storage-map) |
| `high_level_project_overview.mmd` | [High-level project overview](#diagram-high-level-project-overview) |
| `workflow_node_stages.mmd` | [Workflow node stages](#diagram-workflow-node-stages) |
| `end_to_end_call_chain.mmd` | [End-to-end project call chain](#diagram-end-to-end-call-chain) |
| `gateway_orchestrator_event_relay.mmd` | [Gateway to orchestrator event relay](#diagram-gateway-orchestrator-event-relay) |
| `sandbox_docker_lifecycle.mmd` | [Sandbox Docker lifecycle](#diagram-sandbox-docker-lifecycle) |
| `hld_component_diagram.mmd` | [HLD component diagram](#diagram-hld-component-diagram) |
| `lld_module_diagram.mmd` | [LLD module diagram](#diagram-lld-module-diagram) |
| `solid_responsibility_map.mmd` | [SOLID responsibility map](#diagram-solid-responsibility-map) |
| `platform_er_diagram.mmd` | [Platform ER diagram](#diagram-platform-er-diagram) |
| `generated_app_conceptual_er_diagram.mmd` | [Generated app conceptual ER diagram](#diagram-generated-app-conceptual-er-diagram) |
| `gateway_uml_class_diagram.mmd` | [Gateway UML class diagram](#diagram-gateway-uml-class-diagram) |
| `orchestrator_uml_class_diagram.mmd` | [Orchestrator UML class diagram](#diagram-orchestrator-uml-class-diagram) |
| `gateway_module_dependency.mmd` | [Gateway module dependency diagram](#diagram-gateway-module-dependency) |
| `gateway_auth_flow.mmd` | [Gateway auth flow](#diagram-gateway-auth-flow) |
| `gateway_project_run_flow.mmd` | [Gateway project run flow](#diagram-gateway-project-run-flow) |
| `gateway_event_stream_flow.mmd` | [Gateway event stream flow](#diagram-gateway-event-stream-flow) |
| `gateway_file_map.mmd` | [Gateway file map](#diagram-gateway-file-map) |
| `gateway_project_creation_flow.mmd` | [Gateway project creation flow](#diagram-gateway-project-creation-flow) |
| `gateway_event_relay_flow.mmd` | [Gateway event relay flow](#diagram-gateway-event-relay-flow) |
| `orchestrator_gateway_connection.mmd` | [Orchestrator gateway connection](#diagram-orchestrator-gateway-connection) |
| `orchestrator_langgraph_workflow_detailed.mmd` | [Orchestrator LangGraph workflow detailed](#diagram-orchestrator-langgraph-workflow-detailed) |
| `orchestrator_node_wrapper_streaming.mmd` | [Orchestrator node wrapper and streaming](#diagram-orchestrator-node-wrapper-streaming) |
| `orchestrator_human_input_flow.mmd` | [Orchestrator human input flow](#diagram-orchestrator-human-input-flow) |
| `orchestrator_sandbox_lifecycle_detailed.mmd` | [Orchestrator sandbox lifecycle detailed](#diagram-orchestrator-sandbox-lifecycle-detailed) |
| `orchestrator_file_map.mmd` | [Orchestrator file map](#diagram-orchestrator-file-map) |
| `frontend_file_map.mmd` | [Frontend file map](#diagram-frontend-file-map) |
| `frontend_auth_flow.mmd` | [Frontend auth flow](#diagram-frontend-auth-flow) |
| `frontend_project_stream_flow.mmd` | [Frontend project stream flow](#diagram-frontend-project-stream-flow) |
| `frontend_human_input_flow.mmd` | [Frontend human input flow](#diagram-frontend-human-input-flow) |
| `frontend_preview_actions.mmd` | [Frontend preview actions](#diagram-frontend-preview-actions) |
| `generated_app_lifecycle.mmd` | [Generated app lifecycle](#diagram-generated-app-lifecycle) |
| `generated_sandbox_tree.mmd` | [Generated sandbox tree](#diagram-generated-sandbox-tree) |
| `generated_backend_layering.mmd` | [Generated backend layering](#diagram-generated-backend-layering) |
| `generated_preview_and_download_flow.mmd` | [Generated preview and download flow](#diagram-generated-preview-and-download-flow) |
| `generated_deployment_output.mmd` | [Generated deployment output](#diagram-generated-deployment-output) |
| `interview_master_architecture.mmd` | [Interview master architecture](#diagram-interview-master-architecture) |
| `interview_answer_flow.mmd` | [Interview answer flow](#diagram-interview-answer-flow) |
| `interview_runtime_sequence.mmd` | [Interview runtime sequence](#diagram-interview-runtime-sequence) |
| `security_boundary_diagram.mmd` | [Security boundary diagram](#diagram-security-boundary-diagram) |
| `security_risk_to_fix_map.mmd` | [Security risk to fix map](#diagram-security-risk-to-fix-map) |
| `security_production_roadmap.mmd` | [Security production roadmap](#diagram-security-production-roadmap) |
| `failure_debugging_decision_tree.mmd` | [Failure debugging decision tree](#diagram-failure-debugging-decision-tree) |
| `failure_runtime_recovery_loop.mmd` | [Failure runtime recovery loop](#diagram-failure-runtime-recovery-loop) |
| `failure_by_layer_map.mmd` | [Failure by layer map](#diagram-failure-by-layer-map) |
| `database_storage_architecture.mmd` | [Database storage architecture](#diagram-database-storage-architecture) |
| `platform_storage_er_diagram.mmd` | [Platform storage ER diagram](#diagram-platform-storage-er-diagram) |
| `generated_app_database_lifecycle.mmd` | [Generated app database lifecycle](#diagram-generated-app-database-lifecycle) |
| `project_metadata_update_flow.mmd` | [Project metadata update flow](#diagram-project-metadata-update-flow) |
| `demo_flow.mmd` | [Demo flow](#diagram-demo-flow) |
| `demo_timeline.mmd` | [Demo timeline](#diagram-demo-timeline) |
| `demo_architecture_talk_track.mmd` | [Demo architecture talk track](#diagram-demo-architecture-talk-track) |
| `one_page_cheatsheet_map.mmd` | [One page cheatsheet map](#diagram-one-page-cheatsheet-map) |

<details id="diagram-three-layer-architecture">
<summary>Three-layer architecture (three_layer_architecture.mmd)</summary>

```mermaid
flowchart LR
  User[User] --> Frontend[React + Vite Dashboard]
  Frontend --> Gateway[Node.js + Express Gateway]
  Gateway --> Orchestrator[Python FastAPI + LangGraph Orchestrator]
  Gateway --> Mongo[(MongoDB Auth + OTP)]
  Gateway --> Postgres[(Postgres Project Metadata)]
  Gateway --> Redis[(Redis Token Blocklist)]
  Orchestrator --> RedisCheckpoints[(Redis Checkpoints)]
  Orchestrator --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated React + Express App]
```

</details>

<details id="diagram-direct-frontend-to-fastapi-alternative">
<summary>Direct frontend-to-FastAPI alternative (direct_frontend_to_fastapi_alternative.mmd)</summary>

```mermaid
flowchart LR
  User[User] --> Frontend[React Dashboard]
  Frontend --> FastAPI[FastAPI Backend + Orchestrator]
  FastAPI --> AuthDB[(Auth DB)]
  FastAPI --> ProjectDB[(Project DB)]
  FastAPI --> Redis[(Redis)]
  FastAPI --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated App]
```

</details>

<details id="diagram-responsibility-split">
<summary>Responsibility split (responsibility_split.mmd)</summary>

```mermaid
flowchart TB
  subgraph Frontend["Layer 1: Frontend"]
    F1[Forms and buttons]
    F2[Pipeline UI]
    F3[Terminal stream]
    F4[Human input panel]
  end

  subgraph Gateway["Layer 2: Gateway"]
    G1[Auth and cookies]
    G2[Project ownership]
    G3[Project metadata]
    G4[SSE and WebSocket relay]
    G5[Cancel, preview, download APIs]
  end

  subgraph Orchestrator["Layer 3: Orchestrator"]
    O1[LangGraph workflow]
    O2[AgentState]
    O3[Gemini calls]
    O4[Docker sandbox]
    O5[Review, execute, debug loop]
  end

  Frontend --> Gateway
  Gateway --> Orchestrator
```

</details>

<details id="diagram-overall-project-architecture">
<summary>Overall project architecture (overall_project_architecture.mmd)</summary>

```mermaid
flowchart LR
  User[User] --> Browser[React + Vite Frontend]

  Browser -->|HTTP JSON + cookies| Gateway[Node.js Express Gateway]
  Browser -->|SSE events| Gateway

  Gateway -->|Auth records + OTP| Mongo[(MongoDB)]
  Gateway -->|Project metadata| Postgres[(Postgres)]
  Gateway -->|JWT logout blocklist| RedisGateway[(Redis)]

  Gateway -->|POST /runs| Orchestrator[Python FastAPI Orchestrator]
  Gateway -->|GET /runs/:id/events| Orchestrator
  Gateway -->|cancel/input/preview commands| Orchestrator

  Orchestrator -->|LangGraph state| Graph[LangGraph Workflow]
  Graph --> Gemini[Gemini LLM]
  Graph --> Checkpoints[(Redis Checkpoints)]
  Graph --> Sandbox[Docker Sandbox]
  Sandbox --> GeneratedApp[Generated Full-Stack App]
  Sandbox --> Git[Git Snapshots]
```

</details>

<details id="diagram-project-run-event-flow">
<summary>Project run and event flow (project_run_event_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant U as User
  participant F as React Frontend
  participant G as Node Gateway
  participant O as FastAPI Orchestrator
  participant LG as LangGraph
  participant S as Sandbox
  participant DB as Databases

  U->>F: Enter requirement and click build
  F->>G: POST /api/projects
  G->>G: Verify JWT cookie and user
  G->>DB: Check active project and save metadata
  G->>O: POST /runs
  O->>LG: Start async workflow
  O-->>G: project_id + running
  G-->>F: Project created
  F->>G: GET /api/projects/:id/events
  G->>O: GET /runs/:id/events
  LG->>S: Create files, run commands, start preview
  LG-->>O: Emit node events
  O-->>G: SSE events
  G->>DB: Update last_state and metadata
  G-->>F: SSE events
  F->>F: Update pipeline, terminal, file tree, preview
```

</details>

<details id="diagram-orchestrator-workflow">
<summary>Orchestrator workflow (orchestrator_workflow.mmd)</summary>

```mermaid
flowchart TD
  Start([Start]) --> PM[pmAgent]
  PM -->|needs clarification| HumanInput[humanInput]
  HumanInput --> PM
  PM -->|spec ready| A1[architectStep1]
  A1 --> A2[architectStep2]
  A2 --> A3[architectStep3]
  A3 --> A4[architectStep4]
  A4 --> A5[architectStep5]
  A5 --> Validator[blueprintValidator]
  Validator -->|repair needed| A2
  Validator -->|valid| Planner[plannerAgent]
  Planner --> Setup[setupSandbox]
  Setup --> Health[sandboxHealthCheck]
  Health -->|retry setup| Setup
  Health -->|healthy| Select[selectNextTask]
  Select -->|task exists| Context[contextBuilder]
  Context --> Coder[coderAgent]
  Coder --> Registry[updateRegistry]
  Registry --> Reviewer[reviewerAgent]
  Reviewer -->|approved| Executor[executorAgent]
  Reviewer -->|needs changes| Context
  Reviewer -->|too complex| Simplify[simplifyTask]
  Simplify --> Select
  Executor -->|passed| Snapshot[snapshotManager]
  Snapshot --> Select
  Executor -->|failed| Debugger[debuggerAgent]
  Debugger -->|retry| Context
  Debugger -->|needs human| Escalation[humanEscalation]
  Escalation --> Select
  Escalation --> Context
  Select -->|phase done| PhaseVerify[phaseVerification]
  PhaseVerify --> Patterns[patternExtractor]
  Patterns --> Compact[stateCompactor]
  Compact --> Select
  Select -->|all tasks done| Deploy[deploymentVerifier]
  Deploy -->|repair| Debugger
  Deploy -->|ready| Present[presentToUser]
  Present --> End([End])
```

</details>

<details id="diagram-data-storage-map">
<summary>Data storage map (data_storage_map.mmd)</summary>

```mermaid
flowchart TB
  Gateway[Node Gateway]
  Orchestrator[Python Orchestrator]

  Gateway --> Mongo[(MongoDB)]
  Gateway --> Postgres[(Postgres)]
  Gateway --> RedisAuth[(Redis Auth Blocklist)]

  Orchestrator --> RedisCheckpoint[(Redis Checkpoints)]
  Orchestrator --> SandboxFS[Sandbox Filesystem]
  Orchestrator --> Docker[Docker Containers]
  Orchestrator --> Git[Git Snapshots]

  Mongo --> M1[Users and OTP records]
  Postgres --> P1[Project metadata and latest state]
  RedisAuth --> R1[Logged-out JWT blocklist]
  RedisCheckpoint --> R2[Node-by-node AgentState snapshots]
  SandboxFS --> S1[Generated source code]
  Docker --> D1[Generated app runtime]
  Git --> G1[Recovery snapshots]
```

</details>

<details id="diagram-high-level-project-overview">
<summary>High-level project overview (high_level_project_overview.mmd)</summary>

```mermaid
flowchart LR
  User[User] --> UI[React Dashboard]
  UI --> Gateway[Node Gateway]
  Gateway --> AI[Python AI Orchestrator]
  AI --> Agents[AI Agent Workflow]
  Agents --> Sandbox[Generated App Sandbox]
  Sandbox --> Preview[Live Preview + Downloadable Code]
  Preview --> User
```

</details>

<details id="diagram-workflow-node-stages">
<summary>Workflow node stages (workflow_node_stages.mmd)</summary>

```mermaid
flowchart LR
  Req[Requirement Understanding] --> Design[Architecture Design]
  Design --> Validation[Blueprint Validation]
  Validation --> Planning[Task Planning]
  Planning --> Sandbox[Sandbox Setup]
  Sandbox --> DevLoop[Code Review Execute Debug Loop]
  DevLoop --> Phase[Phase Verification]
  Phase --> Consistency[Pattern Extraction + State Compaction]
  Consistency --> Deploy[Deployment Verification]
  Deploy --> Handoff[Present To User]

  Req -.-> PM[pmAgent + humanInput]
  Design -.-> Arch[architectStep1-5]
  Validation -.-> BV[blueprintValidator]
  Planning -.-> Plan[plannerAgent + selectNextTask]
  Sandbox -.-> SH[setupSandbox + sandboxHealthCheck]
  DevLoop -.-> Loop[contextBuilder + coderAgent + updateRegistry + reviewerAgent + executorAgent + debuggerAgent + simplifyTask + humanEscalation + snapshotManager]
  Phase -.-> PV[phaseVerification + assembleEntryPoints]
  Consistency -.-> PC[patternExtractor + stateCompactor]
  Deploy -.-> DV[deploymentVerifier]
  Handoff -.-> PU[presentToUser]
```

</details>

<details id="diagram-end-to-end-call-chain">
<summary>End-to-end project call chain (end_to_end_call_chain.mmd)</summary>

```mermaid
sequenceDiagram
  participant U as User
  participant F as React Frontend
  participant G as Node Gateway
  participant O as FastAPI Orchestrator
  participant LG as LangGraph
  participant N as Workflow Nodes
  participant S as Sandbox Service
  participant D as Docker
  participant DB as Project Store

  U->>F: Click Build
  F->>G: POST /api/projects
  G->>G: Authenticate user and check active project
  G->>O: POST /runs
  O->>O: Create project_id
  O->>LG: asyncio.create_task(run_workflow)
  LG->>N: Execute graph nodes
  N->>S: create_sandbox / write_file / execute_command
  S->>D: docker run / docker exec / docker rm
  O-->>G: Return project_id + running
  G->>DB: Save project metadata
  G-->>F: Return project created
```

</details>

<details id="diagram-gateway-orchestrator-event-relay">
<summary>Gateway to orchestrator event relay (gateway_orchestrator_event_relay.mmd)</summary>

```mermaid
sequenceDiagram
  participant Node as LangGraph Node
  participant Bus as Event Bus
  participant API as FastAPI SSE Endpoint
  participant Gateway as Node Gateway
  participant Store as Project Store
  participant UI as React EventSource

  Node->>Bus: append_event(projectId, StreamEvent)
  Bus-->>API: stream_events(projectId)
  API-->>Gateway: data: JSON event
  Gateway->>Store: updateProjectFromEvent
  Gateway-->>UI: data: JSON event
  UI->>UI: update pipeline, terminal, fileTree, preview
```

</details>

<details id="diagram-sandbox-docker-lifecycle">
<summary>Sandbox Docker lifecycle (sandbox_docker_lifecycle.mmd)</summary>

```mermaid
flowchart TD
  A[setupSandbox node] --> B[create_sandbox]
  B --> C[Create sandbox folder]
  C --> D[Scaffold backend/frontend files]
  D --> E[Initialize Git and v0.0.0 tag]
  E --> F{Docker available?}
  F -->|No| G[Local-only sandbox fallback or error if Docker required]
  F -->|Yes| H[Stop user's old active preview]
  H --> I[Ensure aidev-network]
  I --> J[Allocate backend/frontend host ports]
  J --> K[Start DB container]
  K --> L[Start backend container]
  L --> M[npm install backend]
  M --> N[Start frontend container]
  N --> O[npm install frontend]
  O --> P[Save SandboxInfo and active preview mapping]
  P --> Q[Schedule auto-stop]
  Q --> R[Coder writes files into sandbox]
  R --> S[presentToUser/start_sandbox_servers]
  S --> T[Run npm start backend and npm run dev frontend]
  T --> U[Preview URLs returned]

  U --> V[preview stop/cancel/auto-stop]
  V --> W[docker rm -f DB/backend/frontend containers]
  W --> X[Sandbox files remain]

  U --> Y[destroy_sandbox if called internally]
  Y --> Z[Stop containers + delete sandbox folder]
```

</details>

<details id="diagram-hld-component-diagram">
<summary>HLD component diagram (hld_component_diagram.mmd)</summary>

```mermaid
flowchart LR
  User[User] --> Frontend[React Dashboard]

  Frontend -->|JSON + cookies| Gateway[Node Express Gateway]
  Frontend -->|SSE EventSource| Gateway

  Gateway --> AuthDB[(MongoDB Auth Users + OTPs)]
  Gateway --> ProjectDB[(PostgreSQL Users + Projects)]
  Gateway --> RedisAuth[(Redis Token Blocklist)]
  Gateway -->|HTTP JSON/SSE| Orchestrator[FastAPI Orchestrator]

  Orchestrator --> Graph[LangGraph Workflow]
  Graph --> Nodes[Workflow Nodes]
  Nodes --> Gemini[Gemini LLM]
  Nodes --> RedisCheckpoints[(Redis Checkpoints)]
  Nodes --> Sandbox[Sandbox Services]
  Sandbox --> Docker[Docker DB + Backend + Frontend Containers]
  Sandbox --> Files[Generated Files + Git Snapshots]
```

</details>

<details id="diagram-lld-module-diagram">
<summary>LLD module diagram (lld_module_diagram.mmd)</summary>

```mermaid
flowchart TB
  subgraph Frontend["frontend/src"]
    App[App.jsx]
    Api[gateway.js]
    AuthUI[AuthScreen.jsx]
    Dashboard[Dashboard.jsx]
  end

  subgraph Gateway["gateway/src"]
    Index[index.js]
    AuthRoutes[routes/auth.js]
    ProjectRoutes[routes/projects.js]
    AuthMiddleware[middleware/auth.js]
    UserModel[models/userModel.js]
    OtpModel[models/otpModel.js]
    ProjectStore[services/projectStore.js]
    OrchestratorClient[services/orchestratorClient.js]
    Zip[services/projectZip.js]
  end

  subgraph Orchestrator["orchestrator/app"]
    Main[main.py]
    Contracts[models/contracts.py]
    Workflow[graph/workflow.py]
    Nodes[nodes/*.py]
    EventBus[services/event_bus.py]
    InputBridge[services/input_bridge.py]
    RunManager[services/run_manager.py]
    Gemini[services/gemini_client.py]
    RedisCheckpoint[services/redis_checkpoint.py]
    Sandbox[services/sandbox_*.py]
  end

  App --> Api
  Api --> ProjectRoutes
  Api --> AuthRoutes
  Index --> AuthRoutes
  Index --> ProjectRoutes
  ProjectRoutes --> OrchestratorClient
  ProjectRoutes --> ProjectStore
  AuthRoutes --> UserModel
  AuthRoutes --> OtpModel
  AuthRoutes --> ProjectStore
  AuthMiddleware --> UserModel
  OrchestratorClient --> Main
  Main --> Workflow
  Workflow --> Nodes
  Workflow --> EventBus
  Workflow --> RedisCheckpoint
  Nodes --> Gemini
  Nodes --> Sandbox
  Nodes --> InputBridge
  Main --> RunManager
```

</details>

<details id="diagram-solid-responsibility-map">
<summary>SOLID responsibility map (solid_responsibility_map.mmd)</summary>

```mermaid
flowchart TB
  SOLID[SOLID in this project]

  SOLID --> SRP[Single Responsibility]
  SRP --> SRP1[Frontend UI only]
  SRP --> SRP2[Gateway auth/projects/events]
  SRP --> SRP3[Orchestrator AI workflow]
  SRP --> SRP4[Sandbox Docker/files]
  SRP --> SRP5[One node = one workflow role]

  SOLID --> OCP[Open/Closed]
  OCP --> OCP1[Add new LangGraph node]
  OCP --> OCP2[Swap/extend service implementation]
  OCP --> OCP3[Add new gateway route using service layer]

  SOLID --> LSP[Liskov Substitution]
  LSP --> LSP1[Nodes preserve AgentState contract]
  LSP --> LSP2[Events preserve StreamEvent shape]
  LSP --> LSP3[Project store functions can use DB or memory]

  SOLID --> ISP[Interface Segregation]
  ISP --> ISP1[Small service functions]
  ISP --> ISP2[Focused route modules]
  ISP --> ISP3[Focused sandbox modules]

  SOLID --> DIP[Dependency Inversion]
  DIP --> DIP1[Routes call orchestratorClient]
  DIP --> DIP2[Nodes call sandbox facade]
  DIP --> DIP3[Workflow calls node functions through contracts]
```

</details>

<details id="diagram-platform-er-diagram">
<summary>Platform ER diagram (platform_er_diagram.mmd)</summary>

```mermaid
erDiagram
  DASHBOARD_USER {
    ObjectId _id PK
    string userName UK
    string firstName
    string lastName
    string profilePhoto
    string emailId UK
    string role
    string password_hash
    datetime createdAt
    datetime updatedAt
  }

  DASHBOARD_OTP {
    ObjectId _id PK
    string emailId
    string otp
    datetime createdAt_TTL_5min
  }

  PROJECT_USER {
    text user_id PK
    text email UK
    text display_name
    timestamptz created_at
    timestamptz updated_at
  }

  PROJECT {
    text project_id PK
    text user_id
    text requirement
    text status
    text last_event_type
    text last_event_node
    text last_message
    jsonb last_state
    text sandbox_id
    int preview_frontend_port
    int preview_backend_port
    text preview_frontend_url
    text preview_backend_url
    boolean preview_running
    timestamptz created_at
    timestamptz updated_at
  }

  AGENT_STATE {
    string projectId PK
    string userId
    string userRequirement
    json clarifiedSpec
    json blueprint
    json taskQueue
    string sandboxId
    json tokenUsage
    string currentPhase
  }

  SANDBOX_INFO {
    string sandbox_id PK
    string user_id
    string path
    string db_type
    string db_container_id
    string backend_container_id
    string frontend_container_id
    string backend_host_port
    string frontend_host_port
  }

  DASHBOARD_USER ||--o{ DASHBOARD_OTP : requests
  DASHBOARD_USER ||--o{ PROJECT_USER : mirrored_as
  PROJECT_USER ||--o{ PROJECT : owns
  PROJECT ||--|| AGENT_STATE : stores_latest_state
  PROJECT ||--o| SANDBOX_INFO : points_to_runtime
```

</details>

<details id="diagram-generated-app-conceptual-er-diagram">
<summary>Generated app conceptual ER diagram (generated_app_conceptual_er_diagram.mmd)</summary>

```mermaid
erDiagram
  GENERATED_USER {
    uuid id PK
    string email UK
    string username UK
    string password_hash
    timestamp created_at
    timestamp updated_at
  }

  GENERATED_RESOURCE {
    uuid id PK
    uuid user_id FK
    string title
    text content
    timestamp created_at
    timestamp updated_at
  }

  GENERATED_USER ||--o{ GENERATED_RESOURCE : owns
```

</details>

<details id="diagram-gateway-uml-class-diagram">
<summary>Gateway UML class diagram (gateway_uml_class_diagram.mmd)</summary>

```mermaid
classDiagram
  class DashboardUser {
    +ObjectId _id
    +String userName
    +String firstName
    +String lastName
    +String profilePhoto
    +String emailId
    +String role
    +String password
    +Date createdAt
    +Date updatedAt
  }

  class DashboardOTP {
    +ObjectId _id
    +String emailId
    +String otp
    +Date createdAt
  }

  class PublicUserDTO {
    +String user_id
    +String email
    +String display_name
    +String firstName
    +String lastName
    +String userName
    +String emailId
    +String role
    +String profilePhoto
  }

  class ProjectMetadata {
    +String project_id
    +String user_id
    +String requirement
    +String status
    +String last_event_type
    +String last_event_node
    +String last_message
    +Json last_state
    +String sandbox_id
    +Number preview_frontend_port
    +Number preview_backend_port
    +String preview_frontend_url
    +String preview_backend_url
    +Boolean preview_running
  }

  class AuthRoutes {
    +sendotp()
    +register()
    +login()
    +logout()
    +check()
  }

  class ProjectRoutes {
    +listProjects()
    +createProject()
    +getProject()
    +streamEvents()
    +submitInput()
    +cancel()
    +stopPreview()
    +restartPreview()
    +download()
  }

  class OrchestratorClient {
    +getOrchestratorHealth()
    +createProjectRun()
    +streamProjectEvents()
    +cancelProjectRun()
    +submitProjectInput()
    +stopProjectPreview()
    +restartProjectPreview()
  }

  DashboardUser --> DashboardOTP : requests OTP
  AuthRoutes --> DashboardUser
  AuthRoutes --> DashboardOTP
  AuthRoutes --> PublicUserDTO : returns
  ProjectRoutes --> ProjectMetadata
  ProjectRoutes --> OrchestratorClient
```

</details>

<details id="diagram-orchestrator-uml-class-diagram">
<summary>Orchestrator UML class diagram (orchestrator_uml_class_diagram.mmd)</summary>

```mermaid
classDiagram
  class RunCreateRequest {
    +String requirement
    +String user_id
    +Float token_budget_usd
  }

  class RunCreateResponse {
    +String project_id
    +String status
  }

  class HumanInputSubmitRequest {
    +String type
    +Any answers
    +String choice
    +String guidance
    +Dict data
  }

  class TokenUsage {
    +List calls
    +Int totalInput
    +Int totalOutput
    +Float estimatedCost
  }

  class AgentState {
    +String projectId
    +String userId
    +String userRequirement
    +String pmStatus
    +List pmQuestions
    +List pmConversation
    +Dict clarifiedSpec
    +Dict blueprint
    +Dict blueprintValidation
    +Dict taskQueue
    +List fileRegistry
    +Dict projectPatterns
    +String sandboxId
    +Boolean sandboxHealthy
    +List fileTree
    +Dict currentTask
    +Dict coderOutput
    +Dict reviewResult
    +Dict executionResult
    +Dict debugState
    +TokenUsage tokenUsage
    +String currentPhase
    +String error
  }

  class StreamEvent {
    +String type
    +String node
    +String message
    +Dict state
  }

  class SandboxInfo {
    +String sandbox_id
    +Path path
    +Path backend_path
    +Path frontend_path
    +String db_type
    +String db_container_id
    +String backend_container_id
    +String frontend_container_id
    +String backend_host_port
    +String frontend_host_port
    +String user_id
    +Float created_at
    +Int snapshot_count
    +Float preview_expires_at
  }

  AgentState *-- TokenUsage
  AgentState --> SandboxInfo : references by sandboxId
  StreamEvent --> AgentState : may include state snapshot
  RunCreateRequest --> AgentState : initializes
  RunCreateResponse --> AgentState : exposes projectId
```

</details>

<details id="diagram-gateway-module-dependency">
<summary>Gateway module dependency diagram (gateway_module_dependency.mmd)</summary>

```mermaid
flowchart TB
  Index[index.js]

  Index --> AuthRoutes[routes/auth.js]
  Index --> ProjectRoutes[routes/projects.js]
  Index --> RequireAuth[middleware/auth.js]
  Index --> MongoConfig[config/mongo.js]
  Index --> RedisConfig[config/redis.js]
  Index --> OrchestratorClient[services/orchestratorClient.js]
  Index --> ProjectStore[services/projectStore.js]

  AuthRoutes --> UserModel[models/userModel.js]
  AuthRoutes --> OTPModel[models/otpModel.js]
  AuthRoutes --> RedisConfig
  AuthRoutes --> MailConfig[config/mail.js]
  AuthRoutes --> RequireAuth
  AuthRoutes --> ProjectStore
  AuthRoutes --> EmailTemplates[templates/emailTemplates.js]

  ProjectRoutes --> OrchestratorClient
  ProjectRoutes --> ProjectStore
  ProjectRoutes --> ProjectZip[services/projectZip.js]
  ProjectRoutes --> PublicUrls[utils/publicUrls.js]

  RequireAuth --> UserModel
  RequireAuth --> RedisConfig
  ProjectStore --> PublicUrls
```

</details>

<details id="diagram-gateway-auth-flow">
<summary>Gateway auth flow (gateway_auth_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant Auth as Gateway Auth Routes
  participant Mongo as MongoDB
  participant Mail as Mail Service
  participant Redis as Redis
  participant PG as Postgres User Mirror

  UI->>Auth: POST /api/auth/sendotp
  Auth->>Mongo: Check duplicate user/email
  Auth->>Mongo: Store OTP with TTL
  Auth->>Mail: Send OTP email
  Auth-->>UI: OTP sent

  UI->>Auth: POST /api/auth/register
  Auth->>Mongo: Validate latest OTP
  Auth->>Mongo: Create user with bcrypt hash
  Auth->>Mongo: Delete OTPs
  Auth->>PG: saveUser lightweight mirror
  Auth-->>UI: Set httpOnly cookie + return user

  UI->>Auth: POST /api/auth/logout
  Auth->>Redis: token:<jwt> = blocked until exp
  Auth-->>UI: Clear cookie
```

</details>

<details id="diagram-gateway-project-run-flow">
<summary>Gateway project run flow (gateway_project_run_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant Gateway as Gateway projects.js
  participant Store as projectStore.js
  participant Client as orchestratorClient.js
  participant FastAPI as Python Orchestrator

  UI->>Gateway: POST /api/projects
  Gateway->>Gateway: requireAuth already attached req.user
  Gateway->>Store: listProjects(user_id)
  Gateway->>Gateway: Reject if running/queued project exists
  Gateway->>Store: clearActivePreviewForUser(user_id)
  Gateway->>Client: createProjectRun(payload)
  Client->>FastAPI: POST /runs
  FastAPI-->>Client: project_id + running
  Client-->>Gateway: run response
  Gateway->>Store: saveProjectMetadata
  Gateway-->>UI: project created
```

</details>

<details id="diagram-gateway-event-stream-flow">
<summary>Gateway event stream flow (gateway_event_stream_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React EventSource
  participant Gateway as Gateway SSE Route
  participant Client as orchestratorClient.js
  participant FastAPI as FastAPI SSE
  participant Store as projectStore.js

  UI->>Gateway: GET /api/projects/:id/events
  Gateway->>Client: streamProjectEvents(id, onEvent)
  Client->>FastAPI: GET /runs/:id/events
  FastAPI-->>Client: data: StreamEvent
  Client-->>Gateway: onEvent(event)
  Gateway->>Store: updateProjectFromEvent(id, event)
  Gateway-->>UI: data: StreamEvent
```

</details>

<details id="diagram-gateway-file-map">
<summary>Gateway file map (gateway_file_map.mmd)</summary>

```mermaid
flowchart TB
  Index[src/index.js]

  Index --> AuthRoutes[src/routes/auth.js]
  Index --> ProjectRoutes[src/routes/projects.js]
  Index --> AuthMiddleware[src/middleware/auth.js]
  Index --> MongoConfig[src/config/mongo.js]
  Index --> RedisConfig[src/config/redis.js]
  Index --> OrchestratorClient[src/services/orchestratorClient.js]
  Index --> ProjectStore[src/services/projectStore.js]

  AuthRoutes --> UserModel[src/models/userModel.js]
  AuthRoutes --> OtpModel[src/models/otpModel.js]
  AuthRoutes --> MailConfig[src/config/mail.js]
  AuthRoutes --> RedisConfig
  AuthRoutes --> EmailTemplates[src/templates/emailTemplates.js]
  AuthRoutes --> ProjectStore
  AuthRoutes --> AuthMiddleware

  AuthMiddleware --> UserModel
  AuthMiddleware --> RedisConfig

  ProjectRoutes --> OrchestratorClient
  ProjectRoutes --> ProjectStore
  ProjectRoutes --> ProjectZip[src/services/projectZip.js]
  ProjectRoutes --> PublicUrls[src/utils/publicUrls.js]

  ProjectStore --> PublicUrls
```

</details>

<details id="diagram-gateway-project-creation-flow">
<summary>Gateway project creation flow (gateway_project_creation_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant MW as requireAuth
  participant Projects as Gateway Project Routes
  participant Store as ProjectStore
  participant Orch as OrchestratorClient
  participant FastAPI as Python FastAPI

  UI->>MW: POST /api/projects with cookie
  MW->>MW: Verify JWT + Redis blocklist + Mongo user
  MW->>Projects: req.user attached
  Projects->>Store: listProjects(user_id)
  Store-->>Projects: existing projects
  Projects->>Store: clearActivePreviewForUser(user_id)
  Projects->>Orch: createProjectRun(payload)
  Orch->>FastAPI: POST /runs
  FastAPI-->>Orch: project_id + running
  Orch-->>Projects: run response
  Projects->>Store: saveProjectMetadata(...)
  Projects-->>UI: 201 project created
```

</details>

<details id="diagram-gateway-event-relay-flow">
<summary>Gateway event relay flow (gateway_event_relay_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React EventSource
  participant Gateway as Gateway /api/projects/:id/events
  participant Client as orchestratorClient.streamProjectEvents
  participant FastAPI as FastAPI /runs/:id/events
  participant Store as ProjectStore

  UI->>Gateway: GET /api/projects/:id/events
  Gateway->>Client: streamProjectEvents(projectId, onEvent)
  Client->>FastAPI: GET /runs/:id/events
  FastAPI-->>Client: data: JSON event
  Client->>Gateway: onEvent(event)
  Gateway->>Store: updateProjectFromEvent(event)
  Gateway-->>UI: data: JSON event
```

</details>

<details id="diagram-orchestrator-gateway-connection">
<summary>Orchestrator gateway connection (orchestrator_gateway_connection.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as React Frontend
  participant GW as Node Gateway
  participant API as FastAPI main.py
  participant RM as run_manager.py
  participant WF as workflow.py
  participant EB as event_bus.py

  UI->>GW: POST /api/projects
  GW->>GW: authenticate user and save metadata
  GW->>API: POST /runs
  API->>EB: append run.created
  API->>WF: asyncio.create_task(run_workflow)
  API->>RM: register_run(project_id, task)
  API-->>GW: project_id + running
  GW-->>UI: created project

  UI->>GW: GET /api/projects/:id/events
  GW->>API: GET /runs/:id/events
  API->>EB: stream_events(project_id)
  EB-->>API: StreamEvent
  API-->>GW: SSE data event
  GW->>GW: update projectStore
  GW-->>UI: SSE/WebSocket JSON event
```

</details>

<details id="diagram-orchestrator-langgraph-workflow-detailed">
<summary>Orchestrator LangGraph workflow detailed (orchestrator_langgraph_workflow_detailed.mmd)</summary>

```mermaid
flowchart TD
  START([START]) --> PM[pmAgent]
  PM -->|needs_clarification| HumanInput[humanInput]
  HumanInput --> PM
  PM -->|spec_ready| A1[architectStep1 entities]
  A1 --> A2[architectStep2 database schema]
  A2 --> A3[architectStep3 API endpoints]
  A3 --> A4[architectStep4 frontend pages]
  A4 --> A5[architectStep5 folders and deps]
  A5 --> BV[blueprintValidator]
  BV -->|repair DB| A2
  BV -->|repair API| A3
  BV -->|repair pages| A4
  BV -->|valid| Planner[plannerAgent]
  Planner --> Setup[setupSandbox]
  Setup --> Health[sandboxHealthCheck]
  Health -->|retry| Setup
  Health -->|healthy| Select[selectNextTask]
  Select -->|task| Context[contextBuilder]
  Context --> Coder[coderAgent]
  Coder --> Registry[updateRegistry]
  Registry --> Reviewer[reviewerAgent]
  Reviewer -->|approved| Executor[executorAgent]
  Reviewer -->|rejected retry| Context
  Reviewer -->|retry limit| Simplify[simplifyTask]
  Executor -->|pass| Snapshot[snapshotManager]
  Executor -->|fail| Debugger[debuggerAgent]
  Debugger -->|retry| Context
  Debugger -->|escalate| Escalation[humanEscalation]
  Escalation -->|guide| Context
  Escalation -->|skip| Select
  Escalation -->|simplify| Simplify
  Simplify --> Select
  Snapshot --> Select
  Select -->|phase done| PhaseVerify[phaseVerification]
  PhaseVerify --> Pattern[patternExtractor]
  Pattern --> Compact[stateCompactor]
  Compact --> Select
  Select -->|all done| Deploy[deploymentVerifier]
  Deploy -->|fail repair| Debugger
  Deploy -->|pass or exhausted| Present[presentToUser]
  Present --> END([END])
```

</details>

<details id="diagram-orchestrator-node-wrapper-streaming">
<summary>Orchestrator node wrapper and streaming (orchestrator_node_wrapper_streaming.mmd)</summary>

```mermaid
sequenceDiagram
  participant LG as LangGraph
  participant Wrap as workflow._run_node
  participant Node as Actual node function
  participant EB as event_bus
  participant Redis as Redis checkpoint
  participant GW as Gateway stream relay
  participant UI as React dashboard

  LG->>Wrap: invoke node with AgentState
  Wrap->>EB: append node.started with state
  EB-->>GW: SSE event
  GW-->>UI: forwarded event
  Wrap->>Node: await node(state)
  Node-->>Wrap: next AgentState
  Wrap->>Redis: checkpoint_state(project_id,node,state)
  Wrap->>EB: append node.completed with state
  EB-->>GW: SSE event
  GW-->>UI: forwarded event
  Wrap-->>LG: state as dict
```

</details>

<details id="diagram-orchestrator-human-input-flow">
<summary>Orchestrator human input flow (orchestrator_human_input_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant PM as pmAgent
  participant HI as humanInput node
  participant Bridge as input_bridge.py
  participant EB as event_bus.py
  participant GW as Gateway
  participant UI as React UI

  PM->>PM: sets pmStatus=needs_clarification
  PM-->>HI: router sends graph to humanInput
  HI->>Bridge: wait_for_input(project_id, pm_clarification)
  Bridge->>EB: append input.requested
  EB-->>GW: SSE input.requested
  GW-->>UI: display questions
  UI->>GW: POST /api/projects/:id/input
  GW->>Bridge: via FastAPI POST /runs/:id/input
  Bridge->>Bridge: resolve pending Future
  Bridge->>EB: append input.received
  Bridge-->>HI: return answers
  HI-->>PM: graph loops back to pmAgent
```

</details>

<details id="diagram-orchestrator-sandbox-lifecycle-detailed">
<summary>Orchestrator sandbox lifecycle detailed (orchestrator_sandbox_lifecycle_detailed.mmd)</summary>

```mermaid
flowchart TD
  Setup[setupSandboxNode] --> Create[create_sandbox]
  Create --> ID[Create sandbox timestamp id]
  ID --> Paths[Resolve SANDBOX_ROOT and HOST_SANDBOX_ROOT]
  Paths --> Scaffold[sandbox_scaffold writes backend and frontend boilerplate]
  Scaffold --> Git[git init commit tag v0.0.0]
  Git --> Register[Register SandboxInfo by sandbox_id and project_id]
  Register --> DockerCheck{Docker available?}
  DockerCheck -->|no and required| Fail[raise setup error]
  DockerCheck -->|yes| StopOld[stop_active_preview_for_user]
  StopOld --> Network[ensure aidev-network]
  Network --> Ports[allocate backend/frontend preview ports]
  Ports --> DB{DB type}
  DB -->|Postgres| Pg[run postgres container or external schema]
  DB -->|Mongo| Mongo[run mongo container]
  Pg --> Backend[run backend node container mounted to sandbox]
  Mongo --> Backend
  Backend --> NpmB[npm install backend]
  NpmB --> Frontend[run frontend node container mounted to sandbox]
  Frontend --> NpmF[npm install frontend]
  NpmF --> Active[mark active preview for user]
  Active --> TTL[schedule auto-stop TTL]
  TTL --> Health[sandboxHealthCheck]
  Health --> Present[presentToUser starts npm start and Vite]
  Present --> URLs[frontendUrl and backendUrl streamed in state]
  URLs --> Stop[preview stop/cancel/TTL uses docker rm -f]
  Stop --> Restart[restart preview can reconnect_sandbox from disk]
```

</details>

<details id="diagram-orchestrator-file-map">
<summary>Orchestrator file map (orchestrator_file_map.mmd)</summary>

```mermaid
flowchart TB
  Main[main.py FastAPI endpoints]
  Workflow[graph/workflow.py LangGraph]
  Contracts[models/contracts.py AgentState]
  Nodes[nodes/*.py workflow steps]
  Services[services/*.py infrastructure]

  Main --> Workflow
  Main --> EventBus[event_bus.py]
  Main --> RunManager[run_manager.py]
  Main --> InputBridge[input_bridge.py]
  Main --> SandboxFacade[sandbox.py]

  Workflow --> Contracts
  Workflow --> Nodes
  Workflow --> EventBus
  Workflow --> Checkpoint[redis_checkpoint.py]

  Nodes --> Gemini[gemini_client.py]
  Nodes --> SandboxFacade
  Nodes --> Shared[_shared.py]

  SandboxFacade --> Runtime[sandbox_runtime.py]
  SandboxFacade --> Files[sandbox_files.py]
  SandboxFacade --> Preview[sandbox_preview.py]
  Runtime --> Scaffold[sandbox_scaffold.py]
  Runtime --> Process[sandbox_process.py]
  Runtime --> Database[sandbox_database.py]
  Runtime --> State[sandbox_state.py]
  Files --> Process
  Preview --> Runtime
```

</details>

<details id="diagram-frontend-file-map">
<summary>Frontend file map (frontend_file_map.mmd)</summary>

```mermaid
flowchart TB
  HTML[index.html] --> Main[src/main.jsx]
  Main --> App[src/App.jsx]
  App --> Gateway[src/api/gateway.js]
  App --> Auth[src/components/AuthScreen.jsx]
  App --> Dashboard[src/components/Dashboard.jsx]
  Dashboard --> UI[src/components/ui.jsx]
  Main --> Styles[src/styles.css]
  Auth --> Styles
  Dashboard --> Styles
  Docker[Dockerfile] --> Vite[Vite dev server port 5173]
  Package[package.json and package-lock.json] --> Dependencies[React Vite lucide-react]
```

</details>

<details id="diagram-frontend-auth-flow">
<summary>Frontend auth flow (frontend_auth_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant Browser as Browser
  participant App as App.jsx
  participant Auth as AuthScreen.jsx
  participant API as gateway.js
  participant GW as Node Gateway

  Browser->>App: load React app
  App->>API: gatewayJson GET /api/auth/check
  API->>GW: fetch with credentials include
  GW-->>API: user or unauthenticated
  API-->>App: response/error
  App-->>Auth: render if no user
  Auth->>API: POST /api/auth/sendotp for signup
  API->>GW: send OTP request
  GW-->>API: OTP sent
  Auth->>API: POST /api/auth/login or /register
  API->>GW: credentials include
  GW-->>API: Set httpOnly cookie and user
  API-->>Auth: user
  Auth->>App: onAuthenticated(user)
  App->>API: GET /api/health and /api/projects
  App-->>Browser: render Dashboard
```

</details>

<details id="diagram-frontend-project-stream-flow">
<summary>Frontend project stream flow (frontend_project_stream_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant User as User
  participant App as App.jsx
  participant API as gateway.js
  participant GW as Node Gateway
  participant Orch as Orchestrator
  participant Dash as Dashboard.jsx

  User->>App: click Launch
  App->>API: gatewayJson POST /api/projects
  API->>GW: requirement + cookie
  GW->>Orch: POST /runs
  Orch-->>GW: project_id running
  GW-->>API: project metadata
  API-->>App: project created
  App->>GW: EventSource /api/projects/:id/events
  GW->>Orch: GET /runs/:id/events
  Orch-->>GW: SSE StreamEvent
  GW-->>App: SSE JSON event
  App->>App: append to eventsByProject
  App->>Dash: pass events latestState files tokenUsage
  Dash-->>User: update pipeline terminal file tree cost
```

</details>

<details id="diagram-frontend-human-input-flow">
<summary>Frontend human input flow (frontend_human_input_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant Orch as Orchestrator
  participant GW as Gateway
  participant App as App.jsx
  participant Dash as Dashboard.jsx
  participant User as User

  Orch-->>GW: SSE input.requested
  GW-->>App: EventSource message
  App->>App: setPendingInput(event.state)
  App->>Dash: pendingInput prop
  Dash-->>User: show questions or escalation choices
  User->>Dash: type answer and click Send
  Dash->>App: submitHumanInput()
  App->>GW: POST /api/projects/:id/input
  GW->>Orch: POST /runs/:id/input
  Orch-->>GW: accepted true
  GW-->>App: accepted true
  App->>App: clear pendingInput
```

</details>

<details id="diagram-frontend-preview-actions">
<summary>Frontend preview actions (frontend_preview_actions.mmd)</summary>

```mermaid
flowchart TD
  User[User clicks preview action] --> Choice{Action}
  Choice --> Open[Open Website]
  Choice --> Stop[Stop Containers]
  Choice --> Restart[Restart Containers]
  Choice --> Download[Download Code]

  Open --> Running{preview_running?}
  Running -->|yes| WindowOpen[window.open normalized preview URL]
  Running -->|no| Restart

  Stop --> GWStop[POST gateway /api/projects/:id/preview/stop]
  Restart --> BlankTab[open blank tab immediately]
  BlankTab --> GWRestart[POST gateway /api/projects/:id/preview/restart]
  GWRestart --> Normalize[normalizePreviewUrl]
  Normalize --> ReplaceTab[replace blank tab with preview URL]

  Download --> GWDownload[GET gateway /api/projects/:id/download]

  GWStop --> Gateway[Gateway checks auth and project]
  GWRestart --> Gateway
  GWDownload --> Gateway
  Gateway --> Orchestrator[Orchestrator stops or restarts sandbox containers]
  Gateway --> Zip[Gateway zips sandbox for download]
```

</details>

<details id="diagram-generated-app-lifecycle">
<summary>Generated app lifecycle (generated_app_lifecycle.mmd)</summary>

```mermaid
flowchart TD
  Prompt[User project prompt] --> Spec[PM and Architect create spec and blueprint]
  Spec --> Plan[Planner creates task queue]
  Plan --> Sandbox[setupSandbox creates sandbox folder]
  Sandbox --> Scaffold[sandbox_scaffold writes base backend and frontend]
  Scaffold --> Git[git init and tag v0.0.0]
  Git --> Runtime[Docker DB backend frontend containers]
  Runtime --> CodeLoop[Coder Reviewer Executor Debugger loop]
  CodeLoop --> Registry[updateRegistry tracks exports and imports]
  Registry --> Assembly[assembleEntryPoints wires routes and pages]
  Assembly --> Snapshots[snapshotManager saves task snapshots]
  Snapshots --> Deploy[deploymentVerifier writes Dockerfiles compose nginx]
  Deploy --> Preview[presentToUser starts preview servers]
  Preview --> Download[Gateway can download clean ZIP]
```

</details>

<details id="diagram-generated-sandbox-tree">
<summary>Generated sandbox tree (generated_sandbox_tree.mmd)</summary>

```mermaid
flowchart TB
  Root[sandbox/sandbox-id]
  Root --> Gitignore[.gitignore]
  Root --> Backend[backend]
  Root --> Frontend[frontend]
  Root --> Compose[docker-compose.yml after deployment verification]
  Root --> Readme[README.md when generated]

  Backend --> BEnv[.env excluded from ZIP]
  Backend --> BPkg[package.json package-lock.json]
  Backend --> BSrc[src]
  BSrc --> Config[config/db.js]
  BSrc --> Middleware[middleware/auth validators errorHandler]
  BSrc --> Models[models entity DB functions]
  BSrc --> Controllers[controllers request handlers]
  BSrc --> Routes[routes Express routers]
  BSrc --> BIndex[index.js route mounts]

  Frontend --> FEnv[.env excluded from ZIP]
  Frontend --> FPkg[package.json package-lock.json]
  Frontend --> FSrc[src]
  Frontend --> Vite[vite tailwind postcss config]
  FSrc --> Pages[pages route screens]
  FSrc --> Components[components reusable UI]
  FSrc --> Context[context AuthContext]
  FSrc --> Hooks[hooks data logic]
  FSrc --> Api[utils/api.js]
  FSrc --> App[App.jsx route assembly]
```

</details>

<details id="diagram-generated-backend-layering">
<summary>Generated backend layering (generated_backend_layering.mmd)</summary>

```mermaid
flowchart TB
  Client[Generated frontend or browser] --> Routes[backend/src/routes/*.js]
  Routes --> Middleware[backend/src/middleware/*.js]
  Routes --> Controllers[backend/src/controllers/*.js]
  Controllers --> Models[backend/src/models/*.js]
  Models --> DB[(Generated app DB)]
  Controllers --> Utils[backend/src/utils/*.js]
  Index[backend/src/index.js] --> Routes
  Config[backend/src/config/db.js] --> Models

  Routes -. intended .-> Thin[Routes should only wire endpoints]
  Controllers -. intended .-> HTTP[Controllers handle req res]
  Models -. intended .-> SQL[Models handle DB queries only]
```

</details>

<details id="diagram-generated-preview-and-download-flow">
<summary>Generated preview and download flow (generated_preview_and_download_flow.mmd)</summary>

```mermaid
sequenceDiagram
  participant UI as Platform Frontend
  participant GW as Gateway
  participant OR as Orchestrator
  participant Docker as Docker Engine
  participant Sandbox as sandbox folder

  UI->>GW: POST /api/projects/:id/preview/restart
  GW->>OR: POST /runs/:id/preview/restart
  OR->>Docker: stop old containers
  OR->>Sandbox: read generated backend/frontend files
  OR->>Docker: run DB backend frontend containers
  OR->>Docker: npm install and start servers
  OR-->>GW: frontendUrl backendUrl ports
  GW-->>UI: normalized preview metadata
  UI-->>UI: open preview URL

  UI->>GW: GET /api/projects/:id/download
  GW->>GW: auth and ownership check
  GW->>Sandbox: walk files excluding env git node_modules build logs
  GW-->>UI: ZIP buffer
```

</details>

<details id="diagram-generated-deployment-output">
<summary>Generated deployment output (generated_deployment_output.mmd)</summary>

```mermaid
flowchart LR
  Verifier[deploymentVerifier.py] --> BackendDocker[backend/Dockerfile]
  Verifier --> FrontendDocker[frontend/Dockerfile]
  Verifier --> Nginx[frontend/nginx.conf]
  Verifier --> Compose[docker-compose.yml]
  Verifier --> Env[backend and frontend env files if missing]

  Compose --> DB[db service postgres or mongo]
  Compose --> Backend[backend service port 15000 to 5000]
  Compose --> Frontend[frontend service port 15173 to 80]
  Frontend --> Nginx
  Nginx --> Static[serve React dist]
  Nginx --> Proxy[proxy /api to backend:5000]
  Backend --> DB
```

</details>

<details id="diagram-interview-master-architecture">
<summary>Interview master architecture (interview_master_architecture.mmd)</summary>

```mermaid
flowchart LR
  FE[React Frontend Dashboard] -->|JSON cookies SSE| GW[Node Gateway Public API]
  GW -->|internal JSON SSE| OR[FastAPI LangGraph Orchestrator]
  OR --> LG[AgentState Workflow]
  LG --> AI[Gemini Agents]
  LG --> SB[Docker Sandbox]
  SB --> OUT[Generated Full Stack App]
  GW --> AUTH[Mongo Users OTP]
  GW --> META[Postgres Project Metadata]
  GW --> REDIS[Redis Blocklist Checkpoints]
  OR --> REDIS
```

</details>

<details id="diagram-interview-answer-flow">
<summary>Interview answer flow (interview_answer_flow.mmd)</summary>

```mermaid
flowchart TD
  Q[Interviewer question] --> Type{Question type}
  Type --> Arch[Architecture]
  Type --> Flow[End to end flow]
  Type --> Why[Why decision]
  Type --> Deep[Deep component]
  Type --> Limits[Limitations]

  Arch --> A1[Explain three layers and responsibilities]
  Flow --> F1[User prompt to gateway to orchestrator to sandbox to preview]
  Why --> W1[Separation security scaling debugging]
  Deep --> D1[Pick exact file or node and explain role plus reason]
  Limits --> L1[Admit current limits and give production improvement]

  A1 --> Close[Connect back to generated app builder goal]
  F1 --> Close
  W1 --> Close
  D1 --> Close
  L1 --> Close
```

</details>

<details id="diagram-interview-runtime-sequence">
<summary>Interview runtime sequence (interview_runtime_sequence.mmd)</summary>

```mermaid
sequenceDiagram
  participant User
  participant FE as React Frontend
  participant GW as Node Gateway
  participant OR as FastAPI Orchestrator
  participant LG as LangGraph
  participant SB as Docker Sandbox

  User->>FE: enter requirement and launch
  FE->>GW: POST /api/projects
  GW->>GW: auth ownership active-run checks
  GW->>OR: POST /runs
  OR->>LG: start run_workflow in background
  OR-->>GW: project_id running
  GW-->>FE: project metadata
  FE->>GW: EventSource /api/projects/:id/events
  GW->>OR: GET /runs/:id/events
  LG->>OR: append StreamEvent
  OR-->>GW: SSE event
  GW-->>FE: forwarded event
  LG->>SB: create scaffold write code run checks
  SB-->>LG: files ports preview result
  LG->>OR: run.completed with state
  OR-->>GW: final SSE event
  GW-->>FE: dashboard shows preview/download
```

</details>

<details id="diagram-security-boundary-diagram">
<summary>Security boundary diagram (security_boundary_diagram.mmd)</summary>

```mermaid
flowchart LR
  Browser[Browser React frontend] -->|public HTTP cookies SSE| Gateway[Node gateway public boundary]
  Gateway -->|internal HTTP SSE| Orchestrator[FastAPI orchestrator internal]
  Gateway --> Mongo[(Mongo users OTP)]
  Gateway --> Postgres[(Postgres project metadata)]
  Gateway --> Redis[(Redis token blocklist)]
  Orchestrator --> Redis2[(Redis checkpoints)]
  Orchestrator --> Docker[Docker engine via socket]
  Docker --> Sandbox[Generated app sandbox containers]
  Browser -. blocked by design .-> Orchestrator
  Browser -. blocked by design .-> Docker
```

</details>

<details id="diagram-security-risk-to-fix-map">
<summary>Security risk to fix map (security_risk_to_fix_map.mmd)</summary>

```mermaid
flowchart TB
  Secrets[Secrets in files] --> SecretFix[Remove rotate scan use secret manager]
  DockerSock[Docker socket access] --> DockerFix[Private worker pool restricted runtime quotas]
  Ownership[Incomplete project ownership checks] --> OwnershipFix[ownsProject on every project-id route]
  Events[In-memory event bus] --> EventsFix[Redis Streams Kafka or Postgres events]
  Checkpoints[Checkpoint without resume] --> CheckpointFix[Load latest AgentState and resume idempotently]
  Generated[Generated code risk] --> GeneratedFix[Static analysis dependency scanning tests review]
  Cookies[Cookie production settings] --> CookieFix[secure true CSRF origin checks align expiry]
  Abuse[OTP login project abuse] --> AbuseFix[Rate limits cooldown quotas token budgets]
  Cleanup[Containers volumes remain] --> CleanupFix[TTL cleanup volume pruning quotas]
```

</details>

<details id="diagram-security-production-roadmap">
<summary>Security production roadmap (security_production_roadmap.mmd)</summary>

```mermaid
flowchart LR
  P1[Phase 1 GitHub safety] --> P2[Phase 2 API authorization]
  P2 --> P3[Phase 3 Orchestrator reliability]
  P3 --> P4[Phase 4 Sandbox isolation]
  P4 --> P5[Phase 5 Generated code security]

  P1 --> S1[Clean env examples rotate secrets scan]
  P2 --> S2[Ownership checks CSRF rate limits secure cookies]
  P3 --> S3[Durable events job queue checkpoint resume]
  P4 --> S4[Worker pool quotas non-root restricted Docker]
  P5 --> S5[Semgrep npm audit tests dependency allowlist]
```

</details>

<details id="diagram-failure-debugging-decision-tree">
<summary>Failure debugging decision tree (failure_debugging_decision_tree.mmd)</summary>

```mermaid
flowchart TD
    A[User reports problem] --> B{Where is symptom visible?}

    B -->|Browser UI| C[Check frontend state, console, Network tab]
    B -->|HTTP API| D[Check gateway route and gateway logs]
    B -->|Build stream| E[Check SSE events and orchestrator event bus]
    B -->|Generated app preview| F[Check sandbox containers, ports, generated app logs]
    B -->|Workflow failed| G[Check LangGraph terminal event and node logs]

    C --> C1{API response failed?}
    C1 -->|Yes| D
    C1 -->|No| C2[Inspect React state and rendering logic]

    D --> D1{Gateway can reach orchestrator?}
    D1 -->|No| D2[Fix ORCHESTRATOR_URL or orchestrator service]
    D1 -->|Yes| D3[Check route validation, auth, project metadata]

    E --> E1{Terminal event received?}
    E1 -->|run.completed| E2[Flow completed; inspect preview/download]
    E1 -->|run.failed| G
    E1 -->|run.cancelled| E3[Cancel path worked]
    E1 -->|No, stream closed| E4[Check gateway event relay and event_bus timeout]

    G --> G1{Failure type?}
    G1 -->|LLM/API| G2[Check Gemini key, JSON parse, token budget]
    G1 -->|Generated code| G3[Check reviewer/executor/debugger loop]
    G1 -->|Sandbox| F
    G1 -->|Human input| G4[Check pending input bridge]

    F --> F1{Docker available?}
    F1 -->|No| F2[Start Docker, mount socket, check REQUIRE_DOCKER]
    F1 -->|Yes| F3[Check containers, ports, npm install, app logs]
```

</details>

<details id="diagram-failure-runtime-recovery-loop">
<summary>Failure runtime recovery loop (failure_runtime_recovery_loop.mmd)</summary>

```mermaid
flowchart LR
    Coder[coderAgent writes code] --> Registry[updateRegistry indexes exports/imports]
    Registry --> Reviewer[reviewerAgent checks quality and layering]
    Reviewer -->|approved| Executor[executorAgent runs deterministic checks]
    Reviewer -->|rejected| RetryContext[contextBuilder adds review feedback]
    RetryContext --> Coder

    Executor -->|pass| Snapshot[snapshotManager creates git tag]
    Snapshot --> NextTask[selectNextTask]
    Executor -->|fail| Debugger[debuggerAgent finds root cause]
    Debugger -->|fixable| RetryContext
    Debugger -->|retry limit| Rollback[rollback to last good git tag]
    Rollback --> RetryContext
    Debugger -->|exhausted| Human[humanEscalation asks user]
    Human -->|guidance| RetryContext
    Human -->|skip/simplify| NextTask
```

</details>

<details id="diagram-failure-by-layer-map">
<summary>Failure by layer map (failure_by_layer_map.mmd)</summary>

```mermaid
flowchart TB
    subgraph Frontend[React Frontend]
        F1[Auth check fails]
        F2[Project start error]
        F3[SSE disconnected]
        F4[Preview tab cannot open/start]
    end

    subgraph Gateway[Node Express Gateway]
        G1[Mongo/Redis startup failure]
        G2[Auth middleware rejects request]
        G3[Orchestrator fetch fails]
        G4[Download ZIP validation fails]
        G5[Project metadata not updated]
    end

    subgraph Orchestrator[FastAPI + LangGraph Orchestrator]
        O1[LLM JSON parse failure]
        O2[Token budget exceeded]
        O3[Graph node exception]
        O4[Human input not pending]
        O5[Event stream timeout]
    end

    subgraph Sandbox[Docker Sandbox + Generated App]
        S1[Docker unavailable]
        S2[Port unavailable]
        S3[npm install fails]
        S4[Generated code syntax/import error]
        S5[Preview containers fail]
    end

    Frontend --> Gateway
    Gateway --> Orchestrator
    Orchestrator --> Sandbox
```

</details>

<details id="diagram-database-storage-architecture">
<summary>Database storage architecture (database_storage_architecture.mmd)</summary>

```mermaid
flowchart TB
    User[Browser User] --> Frontend[React Frontend]
    Frontend --> Gateway[Node Express Gateway]
    Gateway --> Mongo[(MongoDB)]
    Gateway --> PlatformPostgres[(Platform PostgreSQL)]
    Gateway --> GatewayRedis[(Redis)]
    Gateway --> Orchestrator[FastAPI LangGraph Orchestrator]

    Orchestrator --> CheckpointRedis[(Redis Checkpoints)]
    Orchestrator --> MemoryState[In-memory runtime maps]
    Orchestrator --> SandboxFS[Sandbox filesystem]
    Orchestrator --> DockerDB[(Per-sandbox Docker DB)]
    Orchestrator --> ExternalProjectDB[(Optional external project PostgreSQL)]

    SandboxFS --> GeneratedBackend[Generated Express Backend]
    SandboxFS --> GeneratedFrontend[Generated React Frontend]
    GeneratedBackend --> DockerDB
    GeneratedBackend --> ExternalProjectDB

    Mongo -. stores .-> AuthUsers[DashboardUser]
    Mongo -. stores .-> OTP[DashboardOTP]
    PlatformPostgres -. stores .-> Projects[projects]
    PlatformPostgres -. stores .-> Users[users]
    GatewayRedis -. stores .-> TokenBlacklist[token blocklist]
    CheckpointRedis -. stores .-> WorkflowSnapshots[AgentState checkpoints]
    MemoryState -. contains .-> EventsTasksInputs[events, tasks, pending input, sandbox map]
```

</details>

<details id="diagram-platform-storage-er-diagram">
<summary>Platform storage ER diagram (platform_storage_er_diagram.mmd)</summary>

```mermaid
erDiagram
    DASHBOARD_USER {
        string userName PK
        string firstName
        string lastName
        string profilePhoto
        string emailId UK
        string role
        string password_hash
        datetime createdAt
        datetime updatedAt
    }

    DASHBOARD_OTP {
        string emailId
        string otp
        datetime createdAt_TTL
    }

    PLATFORM_USER {
        text user_id PK
        text email UK
        text display_name
        timestamptz created_at
        timestamptz updated_at
    }

    PROJECT {
        text project_id PK
        text user_id FK
        text requirement
        text status
        text last_event_type
        text last_event_node
        text last_message
        jsonb last_state
        text sandbox_id
        int preview_frontend_port
        int preview_backend_port
        text preview_frontend_url
        text preview_backend_url
        boolean preview_running
        timestamptz created_at
        timestamptz updated_at
    }

    PLATFORM_USER ||--o{ PROJECT : owns
    DASHBOARD_USER ||--o{ DASHBOARD_OTP : requests
```

</details>

<details id="diagram-generated-app-database-lifecycle">
<summary>Generated app database lifecycle (generated_app_database_lifecycle.mmd)</summary>

```mermaid
sequenceDiagram
    participant Architect as architectStep2
    participant Setup as setupSandbox
    participant Runtime as sandbox_runtime
    participant DB as Sandbox DB
    participant Backend as Generated Backend

    Architect->>Architect: Designs dbSchema with databaseType, tables, FKs, indexes
    Architect->>Setup: AgentState.blueprint.dbSchema
    Setup->>Runtime: create_sandbox(projectId, userId, folderStructure, dependencies, dbSchema)
    Runtime->>Runtime: Decide db_type from dependencies/db schema
    Runtime->>DB: Start Postgres or Mongo container OR initialize external Postgres schema
    Runtime->>DB: Apply generated CREATE TABLE SQL or init.sql when available
    Runtime->>Backend: Write backend .env DATABASE_URL
    Backend->>DB: connectDB() connects generated app to its DB
```

</details>

<details id="diagram-project-metadata-update-flow">
<summary>Project metadata update flow (project_metadata_update_flow.mmd)</summary>

```mermaid
sequenceDiagram
    participant UI as React Frontend
    participant GW as Gateway
    participant OR as Orchestrator
    participant PG as Platform PostgreSQL
    participant MEM as Gateway memory map

    UI->>GW: POST /api/projects
    GW->>OR: POST /runs
    OR-->>GW: project_id, status=running
    GW->>MEM: saveProjectMetadata()
    GW->>PG: upsert projects row
    GW-->>UI: project response

    UI->>GW: GET /api/projects/:id/events
    GW->>OR: GET /runs/:id/events
    OR-->>GW: SSE events with state
    GW->>MEM: updateProjectFromEvent()
    GW->>PG: update last event, status, last_state, sandbox, preview fields
    GW-->>UI: relay SSE event
```

</details>

<details id="diagram-demo-flow">
<summary>Demo flow (demo_flow.mmd)</summary>

```mermaid
flowchart TD
    A[Open AgentForge dashboard] --> B[Login or signup]
    B --> C[Explain three-layer architecture]
    C --> D[Enter project prompt]
    D --> E[Click Launch]
    E --> F[Show live workflow pipeline]
    F --> G{Human input requested?}
    G -->|Yes| H[Answer PM clarification or escalation]
    G -->|No| I[Continue watching events]
    H --> I
    I --> J[Show file tree and terminal stream]
    J --> K{Run completed?}
    K -->|Yes| L[Open generated website preview]
    K -->|Failed| M[Explain failure handling and debugger loop]
    L --> N[Download generated source ZIP]
    M --> N
    N --> O[Close with architecture and production improvements]
```

</details>

<details id="diagram-demo-timeline">
<summary>Demo timeline (demo_timeline.mmd)</summary>

```mermaid
sequenceDiagram
    participant Presenter as You
    participant UI as React Dashboard
    participant GW as Gateway
    participant OR as Orchestrator
    participant LG as LangGraph
    participant SB as Docker Sandbox

    Presenter->>UI: Open dashboard
    Presenter->>UI: Login/signup
    Presenter->>UI: Enter project prompt
    UI->>GW: POST /api/projects
    GW->>OR: POST /runs
    OR->>LG: Start background workflow
    OR-->>GW: project_id
    GW-->>UI: Project created
    UI->>GW: EventSource /events
    GW->>OR: SSE /runs/:id/events
    LG-->>UI: Live node events through Gateway
    LG->>SB: Create sandbox and generate code
    SB-->>LG: Files, checks, preview URLs
    LG-->>UI: run.completed or run.failed
    Presenter->>UI: Open preview/download code
```

</details>

<details id="diagram-demo-architecture-talk-track">
<summary>Demo architecture talk track (demo_architecture_talk_track.mmd)</summary>

```mermaid
flowchart LR
    FE[React Frontend] -->|auth/project/events/preview/download| GW[Node Gateway]
    GW -->|protected internal calls| OR[FastAPI Orchestrator]
    OR -->|state machine| LG[LangGraph]
    LG -->|structured JSON calls| LLM[Gemini]
    LG -->|files/commands/db/containers| SB[Docker Sandbox]

    GW --> Mongo[(Mongo Auth + OTP)]
    GW --> PG[(Postgres Projects)]
    GW --> Redis[(Redis Token Blocklist)]
    OR --> Redis2[(Redis Checkpoints)]
    SB --> FS[Generated Source Files]
    SB --> GenDB[(Generated App DB)]
```

</details>

<details id="diagram-one-page-cheatsheet-map">
<summary>One page cheatsheet map (one_page_cheatsheet_map.mmd)</summary>

```mermaid
flowchart LR
    U[User] --> FE[React Frontend]
    FE -->|JSON + cookies + SSE| GW[Node Gateway]
    GW -->|internal HTTP/SSE| OR[FastAPI Orchestrator]
    OR --> LG[LangGraph Workflow]
    LG --> LLM[Gemini JSON Agents]
    LG --> SB[Docker Sandbox]
    SB --> GEN[Generated Full-stack App]

    GW --> Mongo[(Mongo auth + OTP)]
    GW --> PG[(Postgres projects + last_state)]
    GW --> RedisA[(Redis token blocklist)]
    OR --> RedisB[(Redis checkpoints)]
    SB --> FS[Generated files + Git snapshots]
    SB --> DB[(Generated app DB)]
```

</details>
