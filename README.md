# AI Dev Team Three Layer

AI Dev Team Three Layer is a full-stack AI application builder. The user enters a product requirement in a React dashboard, the Node.js gateway creates and tracks the project, and the Python FastAPI/LangGraph orchestrator turns that requirement into a generated full-stack application inside an isolated Docker sandbox.

The system is designed like a small AI software team: product clarification, architecture, validation, planning, coding, review, execution, debugging, phase verification, deployment verification, live preview, and final download all run as controlled workflow steps instead of one large prompt.

This README is self-contained for GitHub. The Mermaid architecture diagrams are embedded directly in this file, so the repository can be understood without pushing any separate notes folder.

## Contents

- [Platform Overview](#platform-overview)
- [Architecture](#architecture)
- [Request Lifecycle](#request-lifecycle)
- [LangGraph Orchestrator](#langgraph-orchestrator)
- [Frontend Layer](#frontend-layer)
- [Gateway Layer](#gateway-layer)
- [Sandbox And Generated Apps](#sandbox-and-generated-apps)
- [Data And Persistence](#data-and-persistence)
- [Security Model](#security-model)
- [Failure Recovery](#failure-recovery)
- [Repository Layout](#repository-layout)
- [Run Locally](#run-locally)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Diagram Reference](#diagram-reference)

## Platform Overview

The project converts a natural-language app idea into runnable source code. It streams progress to the browser while the backend creates the project structure, writes files, runs commands, fixes errors, starts previews, and prepares a ZIP download.

Core capabilities:

- Requirement intake from a browser dashboard.
- Authenticated user sessions and project ownership.
- One active build per user to keep sandbox and preview resources controlled.
- Live SSE and WebSocket event streaming.
- LangGraph workflow with named AI and utility nodes.
- Gemini-backed structured JSON agent calls.
- Redis checkpointing after every workflow node.
- Docker-backed sandbox workspaces for generated projects.
- Review, execution, debugging, retry limits, and human escalation.
- Preview stop/restart and generated source ZIP download.

## Architecture

The project is split into three runtime layers.

| Layer | Directory | Runtime | Main Responsibility |
| --- | --- | --- | --- |
| Frontend | `frontend/` | React + Vite | UI, auth screens, prompt entry, event stream display, file tree, terminal output, preview/download controls |
| Gateway | `gateway/` | Node.js + Express | Public API, cookies/JWT, auth routes, project metadata, ownership checks, orchestrator relay, preview/download endpoints |
| Orchestrator | `orchestrator/` | Python + FastAPI + LangGraph | AI workflow, agent state, Gemini calls, sandbox lifecycle, code generation, review, execution, debugging, final verification |

The browser only talks to the gateway. The gateway calls the orchestrator through internal JSON HTTP/SSE APIs. This keeps authentication, project metadata, and public API behavior separate from the long-running AI runtime that touches Docker, files, commands, and generated app previews.

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

## Request Lifecycle

A normal project build moves through these stages:

1. User signs up or logs in through the React dashboard.
2. Frontend checks the session using `GET /api/auth/check`.
3. User submits a requirement to `POST /api/projects`.
4. Gateway validates authentication, project ownership, active run status, and request shape.
5. Gateway calls the orchestrator with `POST /runs`.
6. Orchestrator creates a `project_id`, stores the first event, and starts `run_workflow()` in the background.
7. Frontend opens `GET /api/projects/:projectId/events` or the WebSocket event route.
8. Gateway relays orchestrator SSE events to the browser and updates project metadata from each event.
9. LangGraph runs product, architecture, planning, sandbox, coding, review, execution, debugging, and verification nodes.
10. Generated files, terminal output, preview URLs, cost data, and final status stream back to the dashboard.
11. User opens the generated app preview or downloads the generated code ZIP.

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

## LangGraph Orchestrator

The orchestrator is the execution engine. It owns the `AgentState` object, routes it through LangGraph nodes, checkpoints it to Redis, and emits `StreamEvent` objects after node start/completion and run-level state changes.

### Main Workflow Stages

| Stage | Nodes | Purpose |
| --- | --- | --- |
| Product clarification | `pmAgent`, `humanInput` | Convert the initial requirement into a usable product spec, asking the user for missing input when needed |
| Architecture | `architectStep1` to `architectStep5` | Design entities, database schema, API endpoints, frontend pages, folder structure, and dependencies |
| Validation | `blueprintValidator` | Detect mismatched tables, routes, pages, auth assumptions, orphan models, and broken blueprint relationships |
| Planning | `plannerAgent`, `selectNextTask` | Break the app into phases and choose the next implementation task |
| Sandbox setup | `setupSandbox`, `sandboxHealthCheck` | Create or verify the isolated generated-app workspace |
| Coding loop | `contextBuilder`, `coderAgent`, `updateRegistry` | Build context, write files, and track generated file metadata |
| Quality loop | `reviewerAgent`, `executorAgent`, `debuggerAgent` | Review code, run checks/commands, fix failures, or escalate when retries are exhausted |
| Phase close | `phaseVerification`, `patternExtractor`, `stateCompactor` | Verify phase output, learn project patterns, and compact state before continuing |
| Finalization | `deploymentVerifier`, `presentToUser` | Confirm preview/deployment readiness and return final output to the user |

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

### State Contract

Important `AgentState` fields include:

| Area | Fields |
| --- | --- |
| Identity | `projectId`, `userId` |
| Input | `userRequirement`, `clarifiedSpec`, `userFeedback` |
| Product | `pmStatus`, `pmConversation` |
| Architecture | `blueprint`, `blueprintValidation` |
| Planning | `taskQueue`, `currentPhaseIndex`, `currentTaskIndex`, `currentTask`, `taskStatuses` |
| Patterns | `fileRegistry`, `projectPatterns`, `contextPackage` |
| Sandbox | `sandboxId`, `sandboxHealthy`, `fileTree`, `previewFrontendUrl`, `previewBackendUrl` |
| Dev loop | `coderOutput`, `reviewResult`, `executionResult`, `debugState`, `retryCounts`, `retryLimits` |
| Deployment | `deploymentConfig`, `deploymentAttempts`, `userSatisfied` |
| Control | `tokenUsage`, `tokenBudget`, `currentPhase`, `error`, `terminalOutput`, `gitSnapshots` |

### Stream Event Contract

Events use the same basic shape from orchestrator to gateway to frontend:

```json
{
  "type": "node.completed",
  "node": "coderAgent",
  "message": "coderAgent completed",
  "state": {}
}
```

Typical event types include `run.created`, `node.started`, `node.completed`, `run.completed`, `run.failed`, `run.cancelled`, `preview.started`, and `preview.stopped`.

## Frontend Layer

The frontend is the operator console for generated app builds. It handles authentication screens, current user state, project launch, live event consumption, visual pipeline state, file tree display, terminal output, token/cost UI, preview buttons, human input prompts, cancellation, and download actions.

Important frontend files:

| File | Role |
| --- | --- |
| `frontend/src/App.jsx` | Top-level application state, auth check, project creation, EventSource connection, preview/download/cancel actions |
| `frontend/src/api/gateway.js` | Gateway request helper and public URL normalization |
| `frontend/src/components/AuthScreen.jsx` | Login, registration, and OTP user flow |
| `frontend/src/components/Dashboard.jsx` | Main project dashboard, pipeline, stream output, file tree, preview actions |
| `frontend/src/components/ui.jsx` | Shared UI primitives |
| `frontend/src/styles.css` | Dashboard visual system and layout |

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

## Gateway Layer

The gateway is the public backend. It protects the orchestrator from direct browser access and centralizes user-facing product behavior.

Gateway responsibilities:

- CORS, JSON parsing, cookie parsing, and HTTP server setup.
- MongoDB-backed auth and OTP registration flow.
- Password hashing with `bcryptjs`.
- JWT session cookie creation and validation.
- Redis-backed token blocklist on logout.
- PostgreSQL project/user metadata storage through `projectStore`.
- Project creation and one-active-run-per-user enforcement.
- SSE and WebSocket relay from orchestrator to frontend.
- Preview stop/restart routing.
- Generated code ZIP creation with secret/heavy path filtering.

Important gateway files:

| File | Role |
| --- | --- |
| `gateway/src/index.js` | Express app, health route, auth/projects route mounting, WebSocket upgrade handling |
| `gateway/src/routes/auth.js` | OTP, register, login, logout, session check |
| `gateway/src/routes/projects.js` | Project list/create/read/events/input/cancel/preview/download routes |
| `gateway/src/services/orchestratorClient.js` | Internal HTTP/SSE client for FastAPI orchestrator |
| `gateway/src/services/projectStore.js` | Project metadata persistence with database-backed behavior and fallback logic |
| `gateway/src/services/projectZip.js` | Safe generated source ZIP packaging |
| `gateway/src/utils/publicUrls.js` | Preview URL normalization for local or public hosts |

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

## Sandbox And Generated Apps

The sandbox layer is where generated source code is written and validated. The orchestrator treats generated apps as isolated workspaces under the configured sandbox root, then uses sandbox services for file writes, process execution, preview lifecycle, runtime checks, database setup, and snapshots.

Sandbox responsibilities:

- Create a generated app workspace.
- Scaffold frontend and backend entry points.
- Write generated files safely inside the sandbox path.
- Install dependencies and run project commands with timeouts.
- Run backend/frontend checks and capture terminal output.
- Start preview services on assigned ports.
- Stop or restart preview containers on request.
- Exclude secrets, `.git`, `node_modules`, build output, and other heavy files from downloads.
- Capture Git snapshots after meaningful generated-code changes.

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

## Data And Persistence

The platform uses multiple storage systems because each data type has a different lifecycle.

| Store | Owner | Data |
| --- | --- | --- |
| MongoDB | Gateway | Dashboard users, OTP records, auth-related profile data |
| PostgreSQL | Gateway | Platform users, project metadata, current status, last event, preview URL/port metadata, last state JSON |
| Redis | Gateway | Token blocklist for logout/session invalidation |
| Redis | Orchestrator | Workflow checkpoints and event replay support |
| Filesystem | Orchestrator/Sandbox | Generated app source files and sandbox workspace output |
| Git | Orchestrator/Sandbox | Snapshots of generated code after important steps |
| Generated app database | Sandbox/generated app | Application-specific tables created for the generated project |

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

## Security Model

The main security boundary is between the public gateway and the internal orchestrator. The frontend never receives direct access to Docker or the AI runtime. Project routes require authentication, project lookup, and ownership checks before returning metadata, streaming events, controlling previews, or downloading code.

Current safeguards include:

- HTTP-only JWT cookie for sessions.
- Strong password validation during registration.
- OTP-based registration flow.
- Redis token blocklist for logout.
- Auth middleware on project routes.
- One active generated build per user.
- Gateway-controlled preview and download routes.
- ZIP filtering for generated code downloads.
- Sandbox path separation for generated project files.
- Retry limits and escalation paths inside the AI workflow.

Production hardening areas:

- Rotate all leaked development credentials and keep only placeholders in committed env examples.
- Use HTTPS and secure cookie settings in production.
- Add rate limiting to auth, project creation, preview, and download endpoints.
- Isolate Docker execution with stricter resource, network, and filesystem policies.
- Add centralized audit logs for project creation, preview access, command execution, and downloads.
- Use managed secrets instead of checked-in files or plain environment examples.

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

## Failure Recovery

Failures are expected in an AI code generation pipeline, so the workflow routes errors instead of collapsing immediately. Review failures return to context and coding. Execution failures go to the debugger. Repeated failures can simplify the task or escalate to the user. Sandbox setup and deployment verification also have bounded retry paths.

Recovery behavior:

- Blueprint issues route back to the relevant architect step.
- Review rejections route back into the implementation loop.
- Runtime errors route to `debuggerAgent`.
- Debug retries are capped by `retryLimits`.
- Phase verification can route back to debugging when output is incomplete.
- Human escalation can guide, skip, simplify, or continue based on user input.
- `run.failed` events preserve final state for the dashboard and metadata store.

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

## Repository Layout

```text
AIDevFinalThreeLayer/
  frontend/                  React + Vite dashboard
  gateway/                   Node.js + Express public API gateway
  orchestrator/              FastAPI + LangGraph AI workflow engine
  infra/                     SQL schema and infrastructure assets
  sandbox/                   Host-mounted generated app workspaces
  tests/                     Gateway and orchestrator tests
  docs/                      Additional architecture PDFs and markdown docs
  docker-compose.yml         Local multi-service setup
  docker-compose.aws.yml     AWS-oriented service setup
  package.json               Root-level test scripts
  README.md                  Self-contained GitHub documentation
```

## Run Locally

### Docker Compose

```bash
cp .env.example .env
# Replace placeholders in .env before starting the platform.
docker compose up --build
```

Service URLs:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Gateway health | `http://localhost:3000/api/health` |
| Orchestrator health | `http://localhost:8000/health` |

### Run Layers Separately

Orchestrator:

```bash
cd orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Gateway:

```bash
cd gateway
npm install
npm run dev
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Committed configuration examples should contain placeholders only.

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

## API Reference

### Gateway API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check gateway health and orchestrator reachability |
| `POST` | `/api/auth/sendotp` | Send registration OTP |
| `POST` | `/api/auth/register` | Register a user after OTP validation |
| `POST` | `/api/auth/login` | Login and set JWT cookie |
| `POST` | `/api/auth/logout` | Clear cookie and blocklist token |
| `GET` | `/api/auth/check` | Validate current authenticated session |
| `GET` | `/api/projects` | List projects owned by the current user |
| `POST` | `/api/projects` | Start a new project run |
| `GET` | `/api/projects/:projectId` | Read project metadata |
| `GET` | `/api/projects/:projectId/events` | Stream project events through SSE |
| `POST` | `/api/projects/:projectId/input` | Submit human clarification or escalation input |
| `POST` | `/api/projects/:projectId/cancel` | Cancel a running project |
| `POST` | `/api/projects/:projectId/preview/stop` | Stop preview containers |
| `POST` | `/api/projects/:projectId/preview/restart` | Restart generated app preview |
| `GET` | `/api/projects/:projectId/download` | Download generated source ZIP |
| `WS` | `/ws/projects/:projectId/events` | Receive project events through WebSocket |

### Orchestrator API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check orchestrator health |
| `POST` | `/runs` | Create a project run and start workflow in background |
| `GET` | `/runs/:projectId/events` | Stream raw orchestrator events through SSE |
| `POST` | `/runs/:projectId/input` | Submit human input to a waiting workflow |
| `GET` | `/runs/:projectId/input` | Read input history |
| `POST` | `/runs/:projectId/cancel` | Cancel workflow and clean sandbox containers |
| `POST` | `/runs/:projectId/preview/stop` | Stop sandbox preview containers |
| `POST` | `/runs/:projectId/preview/restart` | Restart sandbox preview containers |

## Testing

Root scripts:

```bash
npm run test:orchestrator
npm run test:gateway
npm run test:all:mock
```

Local orchestrator tests, when Python dependencies are installed outside Docker:

```bash
npm run test:orchestrator:local
```

Test areas:

- LangGraph skeleton and routing behavior.
- Blueprint validator consistency checks.
- Retry limit and fallback routing.
- Task selection and phase verification.
- Gateway generated-code ZIP filtering.

## Diagram Reference

The diagrams below are embedded directly as Mermaid blocks. They are grouped by the part of the system they describe.

### System Architecture

- [Three Layer Architecture](#diagram-three-layer-architecture)
- [Overall Project Architecture](#diagram-overall-project-architecture)
- [High Level Platform Overview](#diagram-high-level-platform-overview)
- [High Level Component Design](#diagram-high-level-component-design)
- [Low Level Module Design](#diagram-low-level-module-design)
- [Layer Responsibility Split](#diagram-layer-responsibility-split)
- [SOLID Responsibility Map](#diagram-solid-responsibility-map)
- [Direct Frontend To FastAPI Alternative](#diagram-direct-frontend-to-fastapi-alternative)
- [End To End System Map](#diagram-end-to-end-system-map)

### Runtime And Orchestration

- [Project Run And Event Flow](#diagram-project-run-and-event-flow)
- [End To End Call Chain](#diagram-end-to-end-call-chain)
- [Orchestrator Workflow](#diagram-orchestrator-workflow)
- [Workflow Node Stages](#diagram-workflow-node-stages)
- [Detailed LangGraph Workflow](#diagram-detailed-langgraph-workflow)
- [Node Wrapper And Streaming](#diagram-node-wrapper-and-streaming)
- [Orchestrator Gateway Connection](#diagram-orchestrator-gateway-connection)
- [Human Input Through Orchestrator](#diagram-human-input-through-orchestrator)
- [Detailed Sandbox Lifecycle](#diagram-detailed-sandbox-lifecycle)
- [Orchestrator File Map](#diagram-orchestrator-file-map)
- [Orchestrator Class Model](#diagram-orchestrator-class-model)

### Gateway

- [Gateway Auth Flow](#diagram-gateway-auth-flow)
- [Gateway Project Creation Flow](#diagram-gateway-project-creation-flow)
- [Gateway Project Run Flow](#diagram-gateway-project-run-flow)
- [Gateway Event Stream Flow](#diagram-gateway-event-stream-flow)
- [Gateway Event Relay Flow](#diagram-gateway-event-relay-flow)
- [Gateway To Orchestrator Relay](#diagram-gateway-to-orchestrator-relay)
- [Gateway File Map](#diagram-gateway-file-map)
- [Gateway Module Dependencies](#diagram-gateway-module-dependencies)
- [Gateway Class Model](#diagram-gateway-class-model)

### Frontend

- [Frontend File Map](#diagram-frontend-file-map)
- [Frontend Auth Flow](#diagram-frontend-auth-flow)
- [Frontend Project Stream Flow](#diagram-frontend-project-stream-flow)
- [Frontend Human Input Flow](#diagram-frontend-human-input-flow)
- [Frontend Preview Actions](#diagram-frontend-preview-actions)

### Generated Application And Sandbox

- [Sandbox Docker Lifecycle](#diagram-sandbox-docker-lifecycle)
- [Generated Application Lifecycle](#diagram-generated-application-lifecycle)
- [Generated Sandbox Tree](#diagram-generated-sandbox-tree)
- [Generated Backend Layering](#diagram-generated-backend-layering)
- [Preview And Download Flow](#diagram-preview-and-download-flow)
- [Generated Deployment Output](#diagram-generated-deployment-output)
- [Generated App Database Lifecycle](#diagram-generated-app-database-lifecycle)

### Data And Storage

- [Data Storage Map](#diagram-data-storage-map)
- [Database Storage Architecture](#diagram-database-storage-architecture)
- [Platform ER Model](#diagram-platform-er-model)
- [Platform Storage ER Model](#diagram-platform-storage-er-model)
- [Generated App Conceptual ER Model](#diagram-generated-app-conceptual-er-model)
- [Project Metadata Update Flow](#diagram-project-metadata-update-flow)

### Security And Failure Handling

- [Security Boundary](#diagram-security-boundary)
- [Security Risk To Fix Map](#diagram-security-risk-to-fix-map)
- [Security Production Roadmap](#diagram-security-production-roadmap)
- [Failure Map By Layer](#diagram-failure-map-by-layer)
- [Failure Debugging Decision Tree](#diagram-failure-debugging-decision-tree)
- [Runtime Recovery Loop](#diagram-runtime-recovery-loop)

### Demo And Explanation

- [Demo Flow](#diagram-demo-flow)
- [Demo Timeline](#diagram-demo-timeline)
- [Demo Architecture Walkthrough](#diagram-demo-architecture-walkthrough)
- [Architecture Explanation Map](#diagram-architecture-explanation-map)
- [Explanation Flow](#diagram-explanation-flow)
- [Runtime Explanation Sequence](#diagram-runtime-explanation-sequence)

### System Architecture

<details id="diagram-three-layer-architecture">
<summary>Three Layer Architecture</summary>

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

<details id="diagram-overall-project-architecture">
<summary>Overall Project Architecture</summary>

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

<details id="diagram-high-level-platform-overview">
<summary>High Level Platform Overview</summary>

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

<details id="diagram-high-level-component-design">
<summary>High Level Component Design</summary>

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

<details id="diagram-low-level-module-design">
<summary>Low Level Module Design</summary>

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

<details id="diagram-layer-responsibility-split">
<summary>Layer Responsibility Split</summary>

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

<details id="diagram-solid-responsibility-map">
<summary>SOLID Responsibility Map</summary>

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

<details id="diagram-direct-frontend-to-fastapi-alternative">
<summary>Direct Frontend To FastAPI Alternative</summary>

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

<details id="diagram-end-to-end-system-map">
<summary>End To End System Map</summary>

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

### Runtime And Orchestration

<details id="diagram-project-run-and-event-flow">
<summary>Project Run And Event Flow</summary>

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

<details id="diagram-end-to-end-call-chain">
<summary>End To End Call Chain</summary>

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

<details id="diagram-orchestrator-workflow">
<summary>Orchestrator Workflow</summary>

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

<details id="diagram-workflow-node-stages">
<summary>Workflow Node Stages</summary>

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

<details id="diagram-detailed-langgraph-workflow">
<summary>Detailed LangGraph Workflow</summary>

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

<details id="diagram-node-wrapper-and-streaming">
<summary>Node Wrapper And Streaming</summary>

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

<details id="diagram-orchestrator-gateway-connection">
<summary>Orchestrator Gateway Connection</summary>

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

<details id="diagram-human-input-through-orchestrator">
<summary>Human Input Through Orchestrator</summary>

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
  GW-->>UI: display prompts
  UI->>GW: POST /api/projects/:id/input
  GW->>Bridge: via FastAPI POST /runs/:id/input
  Bridge->>Bridge: resolve pending Future
  Bridge->>EB: append input.received
  Bridge-->>HI: return answers
  HI-->>PM: graph loops back to pmAgent
```

</details>

<details id="diagram-detailed-sandbox-lifecycle">
<summary>Detailed Sandbox Lifecycle</summary>

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
<summary>Orchestrator File Map</summary>

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

<details id="diagram-orchestrator-class-model">
<summary>Orchestrator Class Model</summary>

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
    +List clarificationPrompts
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

### Gateway

<details id="diagram-gateway-auth-flow">
<summary>Gateway Auth Flow</summary>

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

<details id="diagram-gateway-project-creation-flow">
<summary>Gateway Project Creation Flow</summary>

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

<details id="diagram-gateway-project-run-flow">
<summary>Gateway Project Run Flow</summary>

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
<summary>Gateway Event Stream Flow</summary>

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

<details id="diagram-gateway-event-relay-flow">
<summary>Gateway Event Relay Flow</summary>

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

<details id="diagram-gateway-to-orchestrator-relay">
<summary>Gateway To Orchestrator Relay</summary>

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

<details id="diagram-gateway-file-map">
<summary>Gateway File Map</summary>

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

<details id="diagram-gateway-module-dependencies">
<summary>Gateway Module Dependencies</summary>

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

<details id="diagram-gateway-class-model">
<summary>Gateway Class Model</summary>

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

### Frontend

<details id="diagram-frontend-file-map">
<summary>Frontend File Map</summary>

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
<summary>Frontend Auth Flow</summary>

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
<summary>Frontend Project Stream Flow</summary>

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
<summary>Frontend Human Input Flow</summary>

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
  Dash-->>User: show prompts or escalation choices
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
<summary>Frontend Preview Actions</summary>

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

### Generated Application And Sandbox

<details id="diagram-sandbox-docker-lifecycle">
<summary>Sandbox Docker Lifecycle</summary>

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

<details id="diagram-generated-application-lifecycle">
<summary>Generated Application Lifecycle</summary>

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
<summary>Generated Sandbox Tree</summary>

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
<summary>Generated Backend Layering</summary>

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

<details id="diagram-preview-and-download-flow">
<summary>Preview And Download Flow</summary>

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
<summary>Generated Deployment Output</summary>

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

<details id="diagram-generated-app-database-lifecycle">
<summary>Generated App Database Lifecycle</summary>

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

### Data And Storage

<details id="diagram-data-storage-map">
<summary>Data Storage Map</summary>

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

<details id="diagram-database-storage-architecture">
<summary>Database Storage Architecture</summary>

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

<details id="diagram-platform-er-model">
<summary>Platform ER Model</summary>

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

<details id="diagram-platform-storage-er-model">
<summary>Platform Storage ER Model</summary>

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

<details id="diagram-generated-app-conceptual-er-model">
<summary>Generated App Conceptual ER Model</summary>

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

<details id="diagram-project-metadata-update-flow">
<summary>Project Metadata Update Flow</summary>

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

### Security And Failure Handling

<details id="diagram-security-boundary">
<summary>Security Boundary</summary>

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
<summary>Security Risk To Fix Map</summary>

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
<summary>Security Production Roadmap</summary>

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

<details id="diagram-failure-map-by-layer">
<summary>Failure Map By Layer</summary>

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

<details id="diagram-failure-debugging-decision-tree">
<summary>Failure Debugging Decision Tree</summary>

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

<details id="diagram-runtime-recovery-loop">
<summary>Runtime Recovery Loop</summary>

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

### Demo And Explanation

<details id="diagram-demo-flow">
<summary>Demo Flow</summary>

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
<summary>Demo Timeline</summary>

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

<details id="diagram-demo-architecture-walkthrough">
<summary>Demo Architecture Walkthrough</summary>

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

<details id="diagram-architecture-explanation-map">
<summary>Architecture Explanation Map</summary>

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

<details id="diagram-explanation-flow">
<summary>Explanation Flow</summary>

```mermaid
flowchart TD
  Q[Reviewer prompt] --> Type{Topic type}
  Type --> Arch[Architecture]
  Type --> Flow[End to end flow]
  Type --> Why[Architecture rationale]
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

<details id="diagram-runtime-explanation-sequence">
<summary>Runtime Explanation Sequence</summary>

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

