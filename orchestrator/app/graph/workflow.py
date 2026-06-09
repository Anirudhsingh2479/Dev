import asyncio

from langgraph.graph import END, START, StateGraph
from ..models.contracts import AgentState, RunCreateRequest, StreamEvent
from ..nodes.architectAgent import (
    architectStep1Node,
    architectStep2Node,
    architectStep3Node,
    architectStep4Node,
    architectStep5Node,
)
from ..nodes.blueprintValidator import blueprintValidatorNode, blueprintValidatorRouter
from ..nodes.coderAgent import coderAgentNode
from ..nodes.contextBuilder import contextBuilderNode
from ..nodes.debuggerAgent import debuggerAgentNode, debuggerRouter
from ..nodes.deploymentVerifier import deploymentVerifierNode, deploymentVerifierRouter
from ..nodes.executorAgent import executorAgentNode, executorRouter
from ..nodes.humanEscalation import humanEscalationNode, humanEscalationRouter
from ..nodes.humanInput import humanInputNode
from ..nodes.patternExtractor import patternExtractorNode
from ..nodes.phaseVerification import phaseVerificationNode, phaseVerificationRouter
from ..nodes.plannerAgent import plannerAgentNode
from ..nodes.pmAgent import pmAgentNode
from ..nodes.presentToUser import presentToUserNode
from ..nodes.reviewerAgent import reviewerAgentNode, reviewerRouter
from ..nodes.sandboxHealthCheck import sandboxHealthCheckNode, sandboxHealthRouter
from ..nodes.selectNextTask import selectNextTaskNode, selectNextTaskRouter
from ..nodes.setupSandbox import setupSandboxNode
from ..nodes.simplifyTask import simplifyTaskNode
from ..nodes.snapshotManager import snapshotManagerNode
from ..nodes.stateCompactor import stateCompactorNode
from ..nodes.updateRegistry import updateRegistryNode
from ..services.event_bus import append_event
from ..services.redis_checkpoint import checkpoint_state


async def _run_node(state: AgentState, node_name: str, fn):
    if isinstance(state, dict):
        state = AgentState.model_validate(state)
    await append_event(
        state.projectId,
        StreamEvent(type="node.started", node=node_name, message=f"{node_name} started", state=state.model_dump()),
    )
    next_state = await fn(state)
    await checkpoint_state(state.projectId, node_name, next_state)
    await append_event(
        state.projectId,
        StreamEvent(type="node.completed", node=node_name, message=f"{node_name} completed", state=next_state.model_dump()),
    )
    return next_state.model_dump()


def _state(state) -> AgentState:
    return AgentState.model_validate(state) if isinstance(state, dict) else state


def _route(router):
    return lambda state: router(_state(state))


def _pm_router(state: AgentState) -> str:
    state = _state(state)
    if state.pmStatus == "needs_clarification":
        return "humanInput"
    if state.pmStatus == "spec_ready":
        return "architectStep1"
    return "__end__"


def _node(node_name: str, fn):
    async def wrapped(state):
        return await _run_node(state, node_name, fn)

    return wrapped


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("pmAgent", _node("pmAgent", pmAgentNode))
    graph.add_node("humanInput", _node("humanInput", humanInputNode))
    graph.add_node("architectStep1", _node("architectStep1", architectStep1Node))
    graph.add_node("architectStep2", _node("architectStep2", architectStep2Node))
    graph.add_node("architectStep3", _node("architectStep3", architectStep3Node))
    graph.add_node("architectStep4", _node("architectStep4", architectStep4Node))
    graph.add_node("architectStep5", _node("architectStep5", architectStep5Node))
    graph.add_node("blueprintValidator", _node("blueprintValidator", blueprintValidatorNode))
    graph.add_node("plannerAgent", _node("plannerAgent", plannerAgentNode))
    graph.add_node("setupSandbox", _node("setupSandbox", setupSandboxNode))
    graph.add_node("sandboxHealthCheck", _node("sandboxHealthCheck", sandboxHealthCheckNode))
    graph.add_node("selectNextTask", _node("selectNextTask", selectNextTaskNode))
    graph.add_node("contextBuilder", _node("contextBuilder", contextBuilderNode))
    graph.add_node("coderAgent", _node("coderAgent", coderAgentNode))
    graph.add_node("updateRegistry", _node("updateRegistry", updateRegistryNode))
    graph.add_node("reviewerAgent", _node("reviewerAgent", reviewerAgentNode))
    graph.add_node("executorAgent", _node("executorAgent", executorAgentNode))
    graph.add_node("snapshotManager", _node("snapshotManager", snapshotManagerNode))
    graph.add_node("debuggerAgent", _node("debuggerAgent", debuggerAgentNode))
    graph.add_node("simplifyTask", _node("simplifyTask", simplifyTaskNode))
    graph.add_node("humanEscalation", _node("humanEscalation", humanEscalationNode))
    graph.add_node("phaseVerification", _node("phaseVerification", phaseVerificationNode))
    graph.add_node("patternExtractor", _node("patternExtractor", patternExtractorNode))
    graph.add_node("stateCompactor", _node("stateCompactor", stateCompactorNode))
    graph.add_node("presentToUser", _node("presentToUser", presentToUserNode))
    graph.add_node("deploymentVerifier", _node("deploymentVerifier", deploymentVerifierNode))

    graph.add_edge(START, "pmAgent")
    graph.add_conditional_edges("pmAgent", _pm_router, {
        "humanInput": "humanInput",
        "architectStep1": "architectStep1",
        "__end__": END,
    })
    graph.add_edge("humanInput", "pmAgent")

    graph.add_edge("architectStep1", "architectStep2")
    graph.add_edge("architectStep2", "architectStep3")
    graph.add_edge("architectStep3", "architectStep4")
    graph.add_edge("architectStep4", "architectStep5")
    graph.add_edge("architectStep5", "blueprintValidator")
    graph.add_conditional_edges("blueprintValidator", _route(blueprintValidatorRouter), {
        "__end__": "plannerAgent",
        "architectStep2": "architectStep2",
        "architectStep3": "architectStep3",
        "architectStep4": "architectStep4",
    })

    graph.add_edge("plannerAgent", "setupSandbox")
    graph.add_edge("setupSandbox", "sandboxHealthCheck")
    graph.add_conditional_edges("sandboxHealthCheck", _route(sandboxHealthRouter), {
        "__end__": "selectNextTask",
        "setupSandbox": "setupSandbox",
        "presentToUser": "presentToUser",
    })

    graph.add_conditional_edges("selectNextTask", _route(selectNextTaskRouter), {
        "contextBuilder": "contextBuilder",
        "phaseVerification": "phaseVerification",
        "presentToUser": "deploymentVerifier",
    })
    graph.add_edge("contextBuilder", "coderAgent")
    graph.add_edge("coderAgent", "updateRegistry")
    graph.add_edge("updateRegistry", "reviewerAgent")
    graph.add_conditional_edges("reviewerAgent", _route(reviewerRouter), {
        "executorAgent": "executorAgent",
        "contextBuilder": "contextBuilder",
        "simplifyTask": "simplifyTask",
    })
    graph.add_conditional_edges("executorAgent", _route(executorRouter), {
        "snapshotManager": "snapshotManager",
        "debuggerAgent": "debuggerAgent",
    })
    graph.add_edge("snapshotManager", "selectNextTask")
    graph.add_conditional_edges("debuggerAgent", _route(debuggerRouter), {
        "contextBuilder": "contextBuilder",
        "humanEscalation": "humanEscalation",
    })
    graph.add_conditional_edges("humanEscalation", _route(humanEscalationRouter), {
        "selectNextTask": "selectNextTask",
        "contextBuilder": "contextBuilder",
        "simplifyTask": "simplifyTask",
    })
    graph.add_edge("simplifyTask", "selectNextTask")
    graph.add_conditional_edges("phaseVerification", _route(phaseVerificationRouter), {
        "patternExtractor": "patternExtractor",
    })
    graph.add_edge("patternExtractor", "stateCompactor")
    graph.add_edge("stateCompactor", "selectNextTask")
    graph.add_edge("presentToUser", END)
    graph.add_conditional_edges("deploymentVerifier", _route(deploymentVerifierRouter), {
        "presentToUser": "presentToUser",
        "debuggerAgent": "debuggerAgent",
    })

    return graph.compile()


async def run_workflow(project_id: str, payload: RunCreateRequest) -> None:
    graph = build_graph()
    state = AgentState(
        projectId=project_id,
        userId=payload.user_id,
        userRequirement=payload.requirement,
        tokenBudget=payload.token_budget_usd,
    )
    try:
        final_state = await graph.ainvoke(state, {"recursion_limit": 500})
        if isinstance(final_state, dict):
            final_state = AgentState.model_validate(final_state)
        if final_state.currentPhase == "failed" or final_state.error:
            await append_event(
                project_id,
                StreamEvent(type="run.failed", node="graph", message=final_state.error or "Workflow stopped by retry limit", state=final_state.model_dump()),
            )
            return
        await append_event(
            project_id,
            StreamEvent(type="run.completed", node="graph", message="Workflow completed", state=final_state.model_dump()),
        )
    except asyncio.CancelledError:
        state.currentPhase = "cancelled"
        await append_event(
            project_id,
            StreamEvent(type="run.cancelled", node="graph", message="Workflow cancelled by user", state=state.model_dump()),
        )
        raise
    except Exception as error:
        await append_event(
            project_id,
            StreamEvent(type="run.failed", node="graph", message=str(error), state=state.model_dump()),
        )
