"""Compatibility exports for older imports.

The orchestrator now mirrors the JavaScript project file names:
pmAgent.py, architectAgent.py, coderAgent.py, updateRegistry.py, etc.
This module keeps the previous snake_case imports working.
"""

from .architectAgent import (
    architectStep1Node as architect_step_1,
    architectStep2Node as architect_step_2,
    architectStep3Node as architect_step_3,
    architectStep4Node as architect_step_4,
    architectStep5Node as architect_step_5,
)
from .blueprintValidator import (
    blueprintValidatorNode as blueprint_validator,
    blueprintValidatorRouter as blueprint_validator_router,
)
from .coderAgent import coderAgentNode as coder_agent
from .contextBuilder import contextBuilderNode as context_builder
from .debuggerAgent import debuggerAgentNode as debugger_agent, debuggerRouter as debugger_router
from .deploymentVerifier import (
    deploymentVerifierNode as deployment_verifier,
    deploymentVerifierRouter as deployment_verifier_router,
)
from .executorAgent import executorAgentNode as executor_agent, executorRouter as executor_router
from .humanEscalation import (
    humanEscalationNode as human_escalation,
    humanEscalationRouter as human_escalation_router,
)
from .humanInput import humanInputNode as human_input
from .patternExtractor import patternExtractorNode as pattern_extractor
from .phaseVerification import (
    phaseVerificationNode as phase_verification,
    phaseVerificationRouter as phase_verification_router,
)
from .plannerAgent import plannerAgentNode as planner_agent
from .pmAgent import pmAgentNode as pm_agent
from .presentToUser import presentToUserNode as present_to_user
from .reviewerAgent import reviewerAgentNode as reviewer_agent, reviewerRouter as reviewer_router
from .sandboxHealthCheck import (
    sandboxHealthCheckNode as sandbox_health_check,
    sandboxHealthRouter as sandbox_health_router,
)
from .selectNextTask import selectNextTaskNode as select_next_task, selectNextTaskRouter as select_next_task_router
from .setupSandbox import setupSandboxNode as setup_sandbox
from .simplifyTask import simplifyTaskNode as simplify_task
from .snapshotManager import snapshotManagerNode as snapshot_manager
from .stateCompactor import stateCompactorNode as state_compactor
from .updateRegistry import updateRegistryNode as update_registry
