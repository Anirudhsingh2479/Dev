# AIDevFinalThreeLayer Tests

These tests play the same role as the old `AIDevFinal/tests` folder: they check the workflow pieces separately before trusting the full app.

## Commands

```bash
npm run test:orchestrator
npm run test:gateway
npm run test:all:mock
```

`test:orchestrator` runs inside the `orchestrator` Docker container because that container already has Python, Pydantic, LangGraph, and the orchestrator dependencies installed. If you install the Python dependencies locally, you can also run:

```bash
npm run test:orchestrator:local
```

## What They Test

- `tests/orchestrator/test_graph_skeleton.py`
  Checks the LangGraph flow with mocked nodes: PM clarification, architect chain, validator, planner, sandbox health, task loop, deployment verifier, and final presentation.

- `tests/orchestrator/test_blueprint_validator.py`
  Checks validator logic with broken and clean blueprints: missing tables, bad foreign keys, orphan APIs, missing frontend APIs, auth mismatch, orphan tables, router targets, and force-proceed after retry limit.

- `tests/orchestrator/test_retry_limits.py`
  Checks retry counters and routing limits for reviewer, debugger, deployment verifier, and default retry limit values.

- `tests/orchestrator/test_select_next_task.py`
  Checks task selection, phase verification, and final completion routing.

- `tests/gateway/test-project-zip.js`
  Checks generated-code zip creation and makes sure heavy/secret paths like `node_modules`, `.git`, `dist`, and `.env` are excluded.

## Test Types

- Safe mock/logic tests: `test:all:mock`
- No Gemini API required
- No Docker required
- No generated project is built during these tests

The full app still needs manual or integration testing with Docker because it starts real sandbox containers and streams live events.
