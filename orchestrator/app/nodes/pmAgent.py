from __future__ import annotations

import json

from ..models.contracts import AgentState
from ..services.gemini_client import safe_call_json_agent
from ._shared import apply_token_delta, increment_retry, log, retry_limit


PM_PROMPT = """You are the PM Agent in an AI software development team.

ROLE: You are a senior project manager who converts vague requirements into clear, actionable specifications.

GOAL: Analyze the user's project requirement and either:
1. Ask clarifying questions if the requirement is ambiguous
2. Generate a complete project specification if the requirement is clear enough

BOUNDARIES:
- Max 5-8 clarifying questions (pick the most important ones)
- Do NOT ask about tech stack - it's fixed: React (Vite) frontend + Express.js backend + PostgreSQL or MongoDB
- Do NOT ask obvious questions. If someone says "todo app", you KNOW it needs CRUD operations
- Make reasonable assumptions for minor details and state them in the spec
- Focus questions on BUSINESS LOGIC ambiguity (user roles, permissions, data relationships, workflows)

OUTPUT FORMAT - You MUST return one of two JSON formats:

FORMAT 1 - When you need more information:
{
  "status": "needs_clarification",
  "questions": ["Question 1?", "Question 2?"],
  "assumptions": ["Assumption I'm making if you don't answer..."]
}

FORMAT 2 - When you have enough information to create a spec:
{
  "status": "spec_ready",
  "spec": {
    "appName": "my-app",
    "description": "One-line description",
    "userRoles": ["admin", "user"],
    "authRequired": true,
    "features": [
      {
        "name": "Feature Name",
        "description": "What it does",
        "subFeatures": ["sub1", "sub2"],
        "userAccess": ["admin", "user"]
      }
    ],
    "databaseRecommendation": "PostgreSQL or MongoDB",
    "databaseReason": "Why this DB fits",
    "pages": [
      {
        "name": "Page Name",
        "route": "/route",
        "description": "What this page shows",
        "requiresAuth": true
      }
    ],
    "assumptions": ["Things I decided on my own"]
  }
}

RULES:
- Be concise in questions. No fluff.
- If the requirement is already detailed enough, go straight to spec_ready.
- Always include "assumptions" to show what you decided without asking.
- The spec should be COMPLETE enough for an architect to design the database and APIs from it."""


async def pmAgentNode(state: AgentState) -> AgentState:
    if not state.pmConversation:
        user_prompt = f'User\'s project requirement:\n"{state.userRequirement}"'
    else:
        user_prompt = f'Original requirement:\n"{state.userRequirement}"\n\nConversation so far:\n'
        for entry in state.pmConversation:
            if entry.get("role") == "pm":
                user_prompt += f"PM Questions: {json.dumps(entry.get('questions', []))}\n"
            elif entry.get("role") == "user":
                user_prompt += f"User Answers: {entry.get('answers')}\n"
        user_prompt += '\nNow generate the FINAL spec incorporating all the user\'s answers. Return status: "spec_ready".'

    result = await safe_call_json_agent(
        agent_name="pmAgent",
        system_prompt=PM_PROMPT,
        user_prompt=user_prompt,
        current_cost=state.tokenUsage.estimatedCost,
        token_budget=state.tokenBudget,
    )
    apply_token_delta(state, "pmAgent", result["tokens"])
    if not result["ok"]:
        state.error = f"pmAgent failed: {result['error']}"
        log(state, state.error)
        return state

    response = result["parsed"] or {}
    if response.get("status") == "needs_clarification":
        next_round = increment_retry(state, "pmClarifications")
        max_rounds = retry_limit(state, "pmClarifications", 2)
        if next_round > max_rounds:
            assumptions = response.get("assumptions", [])
            state.pmStatus = "spec_ready"
            state.pmQuestions = []
            state.clarifiedSpec = {
                "appName": "generated-app",
                "description": state.userRequirement,
                "userRoles": ["user"],
                "authRequired": True,
                "features": [{
                    "name": "Core Requirement",
                    "description": state.userRequirement,
                    "subFeatures": [],
                    "userAccess": ["user"],
                }],
                "databaseRecommendation": "PostgreSQL",
                "databaseReason": "Default relational database for generated CRUD-style apps.",
                "pages": [{"name": "Home", "route": "/", "description": "Main app page", "requiresAuth": False}],
                "assumptions": assumptions + [
                    f"PM clarification retry limit reached after {max_rounds} round(s); proceeding with reasonable defaults."
                ],
            }
            state.pmConversation.append({
                "role": "pm",
                "spec": state.clarifiedSpec,
                "retryLimitReached": True,
            })
            state.currentPhase = "architect"
            log(state, f"PM clarification retry limit reached ({max_rounds}); proceeding with assumptions")
            return state
        state.pmStatus = "needs_clarification"
        state.pmQuestions = response.get("questions", [])
        state.pmConversation.append({"role": "pm", "questions": state.pmQuestions, "assumptions": response.get("assumptions", [])})
        state.currentPhase = "pm"
        log(state, f"PM Agent needs clarification ({next_round}/{max_rounds})")
        return state

    spec = response.get("spec") or response
    state.pmStatus = "spec_ready"
    state.pmQuestions = []
    state.clarifiedSpec = spec
    state.pmConversation = [{"role": "pm", "spec": spec}]
    state.currentPhase = "architect"
    log(state, "PM Agent produced clarifiedSpec")
    return state
