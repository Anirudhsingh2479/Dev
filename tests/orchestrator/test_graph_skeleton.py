import unittest

from langgraph.graph import END, START, StateGraph

try:
    from orchestrator.app.models.contracts import AgentState
except ModuleNotFoundError:
    from app.models.contracts import AgentState


class GraphSkeletonTests(unittest.IsolatedAsyncioTestCase):
    async def test_three_layer_workflow_order_with_mock_nodes(self):
        node_order = []

        async def pm_agent(state):
            node_order.append("pmAgent")
            if not state.pmConversation:
                state.pmStatus = "needs_clarification"
                state.pmQuestions = ["What should the app do?"]
                state.pmConversation.append({"role": "pm", "questions": state.pmQuestions})
            else:
                state.pmStatus = "spec_ready"
                state.clarifiedSpec = {"appName": "test-app", "features": ["notes"]}
            return state

        async def human_input(state):
            node_order.append("humanInput")
            state.pmConversation.append({"role": "user", "answers": "Build notes"})
            return state

        def architect_step(name, key, value):
            async def node(state):
                node_order.append(name)
                state.blueprint[key] = value
                return state
            return node

        async def validator(state):
            node_order.append("blueprintValidator")
            state.blueprintValidation = {"isValid": True, "issues": [], "validationCycles": 1}
            return state

        async def planner(state):
            node_order.append("plannerAgent")
            state.taskQueue = {"phases": [{"phaseNumber": 1, "tasks": [{"taskId": "task-1"}]}]}
            return state

        async def setup_sandbox(state):
            node_order.append("setupSandbox")
            state.sandboxId = "sandbox-test"
            return state

        async def health(state):
            node_order.append("sandboxHealthCheck")
            state.sandboxHealthy = True
            return state

        async def select_next(state):
            node_order.append("selectNextTask")
            if state.taskStatuses.get("task-1") == "done":
                state.currentTask = None
                state.currentPhase = "done"
            else:
                state.currentTask = {"taskId": "task-1", "title": "Create page"}
                state.taskStatuses["task-1"] = "in_progress"
                state.currentPhase = "dev_loop"
            return state

        async def context(state):
            node_order.append("contextBuilder")
            state.contextPackage = {"task": state.currentTask}
            return state

        async def coder(state):
            node_order.append("coderAgent")
            state.coderOutput = {"files": [{"path": "frontend/src/App.jsx"}]}
            return state

        async def registry(state):
            node_order.append("updateRegistry")
            state.fileRegistry.append({"path": "frontend/src/App.jsx"})
            return state

        async def reviewer(state):
            node_order.append("reviewerAgent")
            state.reviewResult = {"verdict": "approved", "issues": [], "reviewCycle": 1}
            return state

        async def executor(state):
            node_order.append("executorAgent")
            state.executionResult = {"result": "pass", "output": "ok", "errors": ""}
            return state

        async def snapshot(state):
            node_order.append("snapshotManager")
            state.taskStatuses["task-1"] = "done"
            state.currentTask = None
            return state

        async def deployment(state):
            node_order.append("deploymentVerifier")
            state.executionResult = {"result": "pass", "output": "deploy ok", "errors": ""}
            return state

        async def present(state):
            node_order.append("presentToUser")
            state.currentPhase = "done"
            return state

        def pm_router(state):
            if state.pmStatus == "needs_clarification":
                return "humanInput"
            if state.pmStatus == "spec_ready":
                return "architectStep1"
            return "__end__"

        def select_router(state):
            return "deploymentVerifier" if state.currentPhase == "done" else "contextBuilder"

        graph = StateGraph(AgentState)
        graph.add_node("pmAgent", pm_agent)
        graph.add_node("humanInput", human_input)
        graph.add_node("architectStep1", architect_step("architectStep1", "entities", [{"name": "Note"}]))
        graph.add_node("architectStep2", architect_step("architectStep2", "dbSchema", {"tables": [{"name": "notes"}]}))
        graph.add_node("architectStep3", architect_step("architectStep3", "apiEndpoints", [{"path": "/api/notes"}]))
        graph.add_node("architectStep4", architect_step("architectStep4", "frontendPages", [{"name": "Home"}]))
        graph.add_node("architectStep5", architect_step("architectStep5", "folderStructure", "backend/\nfrontend/"))
        graph.add_node("blueprintValidator", validator)
        graph.add_node("plannerAgent", planner)
        graph.add_node("setupSandbox", setup_sandbox)
        graph.add_node("sandboxHealthCheck", health)
        graph.add_node("selectNextTask", select_next)
        graph.add_node("contextBuilder", context)
        graph.add_node("coderAgent", coder)
        graph.add_node("updateRegistry", registry)
        graph.add_node("reviewerAgent", reviewer)
        graph.add_node("executorAgent", executor)
        graph.add_node("snapshotManager", snapshot)
        graph.add_node("deploymentVerifier", deployment)
        graph.add_node("presentToUser", present)

        graph.add_edge(START, "pmAgent")
        graph.add_conditional_edges("pmAgent", pm_router, {
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
        graph.add_edge("blueprintValidator", "plannerAgent")
        graph.add_edge("plannerAgent", "setupSandbox")
        graph.add_edge("setupSandbox", "sandboxHealthCheck")
        graph.add_edge("sandboxHealthCheck", "selectNextTask")
        graph.add_conditional_edges("selectNextTask", select_router, {
            "contextBuilder": "contextBuilder",
            "deploymentVerifier": "deploymentVerifier",
        })
        graph.add_edge("contextBuilder", "coderAgent")
        graph.add_edge("coderAgent", "updateRegistry")
        graph.add_edge("updateRegistry", "reviewerAgent")
        graph.add_edge("reviewerAgent", "executorAgent")
        graph.add_edge("executorAgent", "snapshotManager")
        graph.add_edge("snapshotManager", "selectNextTask")
        graph.add_edge("deploymentVerifier", "presentToUser")
        graph.add_edge("presentToUser", END)

        final_state = await graph.compile().ainvoke(AgentState(projectId="project-test", userRequirement="Build notes"))
        if isinstance(final_state, dict):
            final_state = AgentState.model_validate(final_state)

        self.assertEqual(final_state.pmStatus, "spec_ready")
        self.assertEqual(final_state.sandboxId, "sandbox-test")
        self.assertEqual(final_state.taskStatuses["task-1"], "done")
        self.assertEqual(node_order, [
            "pmAgent",
            "humanInput",
            "pmAgent",
            "architectStep1",
            "architectStep2",
            "architectStep3",
            "architectStep4",
            "architectStep5",
            "blueprintValidator",
            "plannerAgent",
            "setupSandbox",
            "sandboxHealthCheck",
            "selectNextTask",
            "contextBuilder",
            "coderAgent",
            "updateRegistry",
            "reviewerAgent",
            "executorAgent",
            "snapshotManager",
            "selectNextTask",
            "deploymentVerifier",
            "presentToUser",
        ])


if __name__ == "__main__":
    unittest.main()
