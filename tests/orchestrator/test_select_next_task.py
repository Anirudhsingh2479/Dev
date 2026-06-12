import unittest

try:
    from orchestrator.app.models.contracts import AgentState
    from orchestrator.app.nodes.selectNextTask import selectNextTaskNode, selectNextTaskRouter
except ModuleNotFoundError:
    from app.models.contracts import AgentState
    from app.nodes.selectNextTask import selectNextTaskNode, selectNextTaskRouter


class SelectNextTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_selects_first_pending_task(self):
        state = AgentState(projectId="project-test")
        state.taskQueue = {
            "phases": [{
                "phaseNumber": 1,
                "phaseName": "setup",
                "tasks": [
                    {"taskId": "setup-1", "title": "Create package"},
                    {"taskId": "setup-2", "title": "Create readme"},
                ],
            }],
        }

        result = await selectNextTaskNode(state)

        self.assertEqual(result.currentTask["taskId"], "setup-1")
        self.assertEqual(result.taskStatuses["setup-1"], "in_progress")
        self.assertEqual(result.currentPhase, "dev_loop")
        self.assertEqual(selectNextTaskRouter(result), "contextBuilder")

    async def test_selects_phase_verification_after_tasks_done(self):
        state = AgentState(projectId="project-test")
        state.taskQueue = {
            "phases": [{
                "phaseNumber": 1,
                "phaseName": "frontend",
                "tasks": [
                    {"taskId": "ui-1", "title": "Create page"},
                    {"taskId": "ui-2", "title": "Create component"},
                ],
            }],
        }
        state.taskStatuses = {"ui-1": "done", "ui-2": "done"}

        result = await selectNextTaskNode(state)

        self.assertEqual(result.currentPhase, "phase_verification")
        self.assertEqual(result.currentTask["taskId"], "phase-1-verify")
        self.assertEqual(selectNextTaskRouter(result), "phaseVerification")

    async def test_finishes_after_phase_verified(self):
        state = AgentState(projectId="project-test")
        state.taskQueue = {
            "phases": [{
                "phaseNumber": 1,
                "phaseName": "frontend",
                "tasks": [{"taskId": "ui-1", "title": "Create page"}],
            }],
        }
        state.taskStatuses = {"ui-1": "done", "phase-1-verified": "done"}

        result = await selectNextTaskNode(state)

        self.assertIsNone(result.currentTask)
        self.assertEqual(result.currentPhase, "done")
        self.assertEqual(selectNextTaskRouter(result), "presentToUser")


if __name__ == "__main__":
    unittest.main()
