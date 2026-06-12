import unittest

try:
    from orchestrator.app.models.contracts import AgentState
    from orchestrator.app.nodes.blueprintValidator import blueprintValidatorNode, blueprintValidatorRouter
except ModuleNotFoundError:
    from app.models.contracts import AgentState
    from app.nodes.blueprintValidator import blueprintValidatorNode, blueprintValidatorRouter


def state_with_blueprint(blueprint, cycles=0, retry_limit=2):
    state = AgentState(projectId="project-test")
    state.blueprint = blueprint
    state.blueprintValidation = {
        "isValid": False,
        "issues": [],
        "validationCycles": cycles,
    }
    state.retryLimits["blueprintRepairs"] = retry_limit
    return state


class BlueprintValidatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_detects_missing_table_for_entity(self):
        state = state_with_blueprint({
            "entities": [{"name": "User"}, {"name": "Comment"}],
            "dbSchema": {"tables": [{"name": "users", "fields": [{"name": "id"}]}]},
            "apiEndpoints": [],
            "frontendPages": [],
        })

        result = await blueprintValidatorNode(state)

        self.assertFalse(result.blueprintValidation["isValid"])
        self.assertTrue(any(issue["type"] == "missing_table" for issue in result.blueprintValidation["issues"]))
        self.assertEqual(blueprintValidatorRouter(result), "architectStep2")

    async def test_detects_invalid_foreign_key(self):
        state = state_with_blueprint({
            "entities": [],
            "dbSchema": {
                "tables": [{
                    "name": "tasks",
                    "fields": [{"name": "id"}, {"name": "category_id"}],
                    "foreignKeys": [{"field": "category_id", "references": "ghost_table(id)"}],
                }],
            },
            "apiEndpoints": [],
            "frontendPages": [],
        })

        result = await blueprintValidatorNode(state)

        self.assertTrue(any(issue["type"] == "invalid_foreign_key" for issue in result.blueprintValidation["issues"]))
        self.assertEqual(blueprintValidatorRouter(result), "architectStep2")

    async def test_detects_orphan_endpoint_and_missing_frontend_api(self):
        state = state_with_blueprint({
            "entities": [],
            "dbSchema": {"tables": [{"name": "users", "fields": [{"name": "id"}]}]},
            "apiEndpoints": [{"method": "GET", "path": "/api/tasks", "relatedTable": "tasks"}],
            "frontendPages": [{
                "name": "Dashboard",
                "requiresAuth": False,
                "components": [{"name": "TaskList", "apiCalls": ["/api/missing"]}],
            }],
        })

        result = await blueprintValidatorNode(state)

        issue_types = {issue["type"] for issue in result.blueprintValidation["issues"]}
        self.assertIn("orphan_endpoint", issue_types)
        self.assertIn("missing_api", issue_types)
        self.assertEqual(blueprintValidatorRouter(result), "architectStep3")

    async def test_detects_auth_mismatch_and_orphan_table_warning(self):
        state = state_with_blueprint({
            "entities": [],
            "dbSchema": {
                "tables": [
                    {"name": "tasks", "fields": [{"name": "id"}]},
                    {"name": "reports", "fields": [{"name": "id"}]},
                ],
            },
            "apiEndpoints": [{"method": "GET", "path": "/api/tasks", "relatedTable": "tasks", "requiresAuth": True}],
            "frontendPages": [{
                "name": "PublicDashboard",
                "requiresAuth": False,
                "components": [{"name": "TaskList", "apiCalls": ["/api/tasks"]}],
            }],
        })

        result = await blueprintValidatorNode(state)

        issue_types = {issue["type"] for issue in result.blueprintValidation["issues"]}
        self.assertIn("auth_mismatch", issue_types)
        self.assertIn("orphan_table", issue_types)
        self.assertFalse(result.blueprintValidation["isValid"])
        self.assertEqual(blueprintValidatorRouter(result), "architectStep4")

    async def test_clean_blueprint_passes(self):
        state = state_with_blueprint({
            "entities": [{"name": "Task"}],
            "dbSchema": {"tables": [{"name": "tasks", "fields": [{"name": "id"}]}]},
            "apiEndpoints": [{"method": "GET", "path": "/api/tasks", "relatedTable": "tasks"}],
            "frontendPages": [{
                "name": "Dashboard",
                "requiresAuth": False,
                "components": [{"name": "TaskList", "apiCalls": ["/api/tasks"]}],
            }],
        })

        result = await blueprintValidatorNode(state)

        self.assertTrue(result.blueprintValidation["isValid"])
        self.assertEqual(result.blueprintValidation["issues"], [])
        self.assertEqual(blueprintValidatorRouter(result), "__end__")

    async def test_force_proceeds_after_retry_limit(self):
        state = state_with_blueprint({
            "entities": [{"name": "Ghost"}],
            "dbSchema": {"tables": []},
            "apiEndpoints": [{"method": "GET", "path": "/api/ghosts", "relatedTable": "ghosts"}],
            "frontendPages": [],
        }, cycles=2, retry_limit=2)

        result = await blueprintValidatorNode(state)

        self.assertTrue(result.blueprintValidation["isValid"])
        self.assertEqual(result.blueprintValidation["validationCycles"], 3)
        self.assertEqual(result.currentPhase, "planner")


if __name__ == "__main__":
    unittest.main()
