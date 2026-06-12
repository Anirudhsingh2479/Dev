import unittest
from unittest.mock import patch

try:
    from orchestrator.app.models.contracts import AgentState
    from orchestrator.app.nodes._shared import increment_retry, reset_retry, retry_count, retry_limit
    from orchestrator.app.nodes.debuggerAgent import debuggerAgentNode, debuggerRouter
    from orchestrator.app.nodes.deploymentVerifier import deploymentVerifierRouter
    from orchestrator.app.nodes.reviewerAgent import reviewerRouter
except ModuleNotFoundError:
    from app.models.contracts import AgentState
    from app.nodes._shared import increment_retry, reset_retry, retry_count, retry_limit
    from app.nodes.debuggerAgent import debuggerAgentNode, debuggerRouter
    from app.nodes.deploymentVerifier import deploymentVerifierRouter
    from app.nodes.reviewerAgent import reviewerRouter


def base_state():
    state = AgentState(projectId="project-test")
    state.currentTask = {"taskId": "task-1", "title": "Build one file", "filesToCreate": ["backend/src/index.js"]}
    return state


class RetryLimitTests(unittest.IsolatedAsyncioTestCase):
    def test_default_retry_limits_are_set(self):
        state = base_state()

        self.assertEqual(retry_limit(state, "blueprintRepairs", 99), 2)
        self.assertEqual(retry_limit(state, "reviewRejections", 99), 2)
        self.assertEqual(retry_limit(state, "debugAttempts", 99), 3)
        self.assertEqual(retry_limit(state, "deploymentRepairs", 99), 2)

    def test_retry_counter_is_task_scoped(self):
        state = base_state()
        task_a = {"taskId": "task-a"}
        task_b = {"taskId": "task-b"}

        self.assertEqual(increment_retry(state, "reviewRejections", task_a), 1)
        self.assertEqual(increment_retry(state, "reviewRejections", task_a), 2)
        self.assertEqual(increment_retry(state, "reviewRejections", task_b), 1)
        self.assertEqual(retry_count(state, "reviewRejections", task_a), 2)
        self.assertEqual(retry_count(state, "reviewRejections", task_b), 1)

        reset_retry(state, "reviewRejections", task_a)
        self.assertEqual(retry_count(state, "reviewRejections", task_a), 0)
        self.assertEqual(retry_count(state, "reviewRejections", task_b), 1)

    def test_reviewer_routes_to_simplify_after_limit(self):
        state = base_state()
        state.reviewResult = {"verdict": "rejected", "issues": ["bad import"], "reviewCycle": 2}
        state.retryCounts["reviewRejections:task-1"] = 2

        self.assertEqual(reviewerRouter(state), "simplifyTask")

    def test_reviewer_routes_back_to_context_before_limit(self):
        state = base_state()
        state.reviewResult = {"verdict": "rejected", "issues": ["bad import"], "reviewCycle": 1}
        state.retryCounts["reviewRejections:task-1"] = 1

        self.assertEqual(reviewerRouter(state), "contextBuilder")

    async def test_debugger_escalates_after_three_attempts_without_rollback(self):
        state = base_state()
        state.sandboxId = "sandbox-test"
        state.executionResult = {"result": "fail", "output": "", "errors": "SyntaxError"}
        state.debugState = {"tier": 1, "attempts": 0, "maxAttempts": 3, "rollbackAttempted": False}
        state.retryCounts["debugAttempts:task-1"] = 2

        with patch(f"{debuggerAgentNode.__module__}.rollback", return_value={"success": False}):
            result = await debuggerAgentNode(state)

        self.assertEqual(result.debugState["tier"], 3)
        self.assertTrue(result.debugState["rollbackAttempted"])
        self.assertEqual(debuggerRouter(result), "humanEscalation")

    def test_deployment_routes_to_debugger_until_limit_then_present(self):
        state = base_state()
        state.executionResult = {"result": "fail", "output": "", "errors": "frontend failed"}
        state.deploymentAttempts = 1
        self.assertEqual(deploymentVerifierRouter(state), "debuggerAgent")

        state.deploymentAttempts = 2
        self.assertEqual(deploymentVerifierRouter(state), "presentToUser")


if __name__ == "__main__":
    unittest.main()
