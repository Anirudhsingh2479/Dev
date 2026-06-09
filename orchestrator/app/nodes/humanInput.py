from __future__ import annotations

from ..models.contracts import AgentState
from ._shared import log
from ..services.input_bridge import wait_for_input


async def humanInputNode(state: AgentState) -> AgentState:
    questions = state.pmQuestions or []
    if not questions:
        log(state, "Human input skipped because there are no questions")
        return state

    response = await wait_for_input(state.projectId, "pm_clarification", {"questions": questions})
    answer = response.get("answers") or response.get("data", {}).get("answers") or response
    state.pmConversation.append({"role": "user", "answers": answer})
    state.pmStatus = "idle"
    log(state, "Human input received dashboard answers")
    return state
