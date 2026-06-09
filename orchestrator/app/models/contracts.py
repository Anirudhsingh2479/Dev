from typing import Any, Literal
from pydantic import BaseModel, Field


class RunCreateRequest(BaseModel):
    requirement: str = Field(min_length=3)
    user_id: str = Field(default="demo-user")
    token_budget_usd: float = Field(default=2.0, gt=0)


class RunCreateResponse(BaseModel):
    project_id: str
    status: Literal["running", "queued"]


class HumanInputSubmitRequest(BaseModel):
    type: Literal["pm_clarification", "escalation"]
    answers: Any | None = None
    choice: Literal["guide", "skip", "simplify"] | None = None
    guidance: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    calls: list[dict[str, Any]] = Field(default_factory=list)
    totalInput: int = 0
    totalOutput: int = 0
    estimatedCost: float = 0.0


class AgentState(BaseModel):
    # Run identity
    projectId: str
    userId: str = "demo-user"

    # User input
    userRequirement: str = ""

    # PM Agent
    pmStatus: str = "idle"
    pmQuestions: list[str] = Field(default_factory=list)
    pmConversation: list[dict[str, Any]] = Field(default_factory=list)
    clarifiedSpec: dict[str, Any] | None = None

    # Architect + validator
    blueprint: dict[str, Any] = Field(default_factory=lambda: {
        "entities": [],
        "dbSchema": {},
        "apiEndpoints": [],
        "frontendPages": [],
        "folderStructure": "",
        "dependencies": {},
    })
    blueprintValidation: dict[str, Any] = Field(default_factory=lambda: {
        "isValid": False,
        "issues": [],
        "validationCycles": 0,
    })

    # Planner
    taskQueue: dict[str, Any] = Field(default_factory=lambda: {"phases": []})
    currentPhaseIndex: int = 0
    currentTaskIndex: int = 0

    # Registry + patterns
    fileRegistry: list[dict[str, Any]] = Field(default_factory=list)
    projectPatterns: dict[str, str] = Field(default_factory=lambda: {
        "errorHandling": "",
        "namingConvention": "",
        "responseFormat": "",
        "importStyle": "",
        "stateManagement": "",
        "commentStyle": "",
    })

    # Sandbox
    sandboxId: str = ""
    sandboxHealthy: bool = False
    fileTree: list[str] = Field(default_factory=list)
    previewFrontendPort: int | None = None
    previewBackendPort: int | None = None
    previewFrontendUrl: str | None = None
    previewBackendUrl: str | None = None

    # Dev loop
    currentTask: dict[str, Any] | None = None
    taskStatuses: dict[str, str] = Field(default_factory=dict)
    contextPackage: dict[str, Any] | None = None
    coderOutput: dict[str, Any] | None = None
    reviewResult: dict[str, Any] = Field(default_factory=lambda: {
        "verdict": "",
        "issues": [],
        "reviewCycle": 0,
    })
    executionResult: dict[str, Any] = Field(default_factory=lambda: {
        "result": "",
        "output": "",
        "errors": "",
    })
    debugState: dict[str, Any] = Field(default_factory=lambda: {
        "tier": 1,
        "attempts": 0,
        "maxAttempts": 3,
        "rollbackAttempted": False,
    })
    retryCounts: dict[str, int] = Field(default_factory=dict)
    retryLimits: dict[str, int] = Field(default_factory=lambda: {
        "pmClarifications": 2,
        "blueprintRepairs": 2,
        "sandboxSetup": 2,
        "reviewRejections": 2,
        "debugAttempts": 3,
        "deploymentRepairs": 2,
    })

    # Feedback + deploy
    userFeedback: list[dict[str, Any]] = Field(default_factory=list)
    feedbackIteration: int = 0
    maxFeedbackIterations: int = 3
    scopeDrift: float = 0.0
    userSatisfied: bool = False
    deploymentConfig: dict[str, Any] = Field(default_factory=lambda: {
        "platform": "",
        "files": [],
        "instructions": [],
    })
    deploymentAttempts: int = 0

    # Token + control
    tokenUsage: TokenUsage = Field(default_factory=TokenUsage)
    tokenBudget: float = 2.0
    currentPhase: str = "pm"
    error: str | None = None
    terminalOutput: list[str] = Field(default_factory=list)
    gitSnapshots: list[Any] = Field(default_factory=list)


class StreamEvent(BaseModel):
    type: str
    node: str | None = None
    message: str
    state: dict[str, Any] | None = None
