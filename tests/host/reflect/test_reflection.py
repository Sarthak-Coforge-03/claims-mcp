"""Unit tests for reflection: CRITIQUE reviews the draft; REVISE runs only if the critique fails.

The model is a fake: complete_structured replays the critique, then the revised decision.
"""

import json
from datetime import date

import pytest

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.reflect.run_reflection import run_reflection
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.request_decision import RequestDecision
from claims_mcp.host.state.request_outcome import RequestOutcome
from claims_mcp.host.state.thought import Thought
from claims_mcp.host.state.thought_decision import ThoughtDecision
from fakes.fake_chat_model_adapter import FakeChatModelAdapter

DRAFT_DECISION = RequestDecision(
    outcome=RequestOutcome.APPROVE,
    rule_id="ELG-2",
    policy_rule_id="POL-STD-MONITOR",
    eligible_from_date=None,
    escalation_id=None,
    response="Approved under ELG-2; your new monitor arrives Friday.",
)
REVISED_DECISION = RequestDecision(
    outcome=RequestOutcome.APPROVE,
    rule_id="ELG-2",
    policy_rule_id="POL-STD-MONITOR",
    eligible_from_date=None,
    escalation_id=None,
    response="Approved under ELG-2 (POL-STD-MONITOR).",
)
SATISFIED_CRITIQUE = Critique(
    addresses_request=True,
    follows_policy=True,
    avoids_unconfirmed_promises=True,
    matches_tool_results=True,
    issues=[],
)
PROMISE_CRITIQUE = Critique(
    addresses_request=True,
    follows_policy=True,
    avoids_unconfirmed_promises=False,
    matches_tool_results=True,
    issues=["Promises delivery on Friday; no tool result confirms a delivery date."],
)


def build_state(request_decision: RequestDecision) -> AgentState:
    """Return a finished E001 monitor run: one ELG-2 eligibility step and the given draft."""
    eligibility_step = ReActStep(
        thought=Thought(
            established_facts="",
            decision=ThoughtDecision.CONTINUE,
            next_action="Call check_request_eligibility.",
            request_decision=None,
        ),
        action=ToolCall(
            id="toolu_1",
            name="check_request_eligibility",
            arguments={"employee_id": "E001", "item": "monitor"},
        ),
        tool_result=ToolResult(
            tool_call_id="toolu_1",
            content=json.dumps({"rule_id": "ELG-2", "policy_rule_id": "POL-STD-MONITOR"}),
            is_error=False,
        ),
        observation="ELG-2 applies.",
    )
    return AgentState(
        request="Employee E001: my monitor is old, I'd like a new one.",
        today=date(2026, 11, 27),
        tool_specs=[],
        max_steps=5,
        steps=[eligibility_step],
        request_decision=request_decision,
    )


@pytest.mark.anyio
async def test_reflection_satisfied_critique_keeps_draft_without_revising():
    """A critique with all four answers yes and no issues: the draft is final, REVISE never runs."""
    adapter = FakeChatModelAdapter([], [SATISFIED_CRITIQUE])
    state = build_state(DRAFT_DECISION)

    await run_reflection(state, adapter)

    assert state.request_decision == DRAFT_DECISION
    assert state.reflection.revised_decision is None
    assert len(adapter.received_calls) == 1


@pytest.mark.anyio
async def test_reflection_failed_critique_replaces_draft_with_revision():
    """A critique flagging a promised delivery date: REVISE's decision becomes final, draft kept."""
    adapter = FakeChatModelAdapter([], [PROMISE_CRITIQUE, REVISED_DECISION])
    state = build_state(DRAFT_DECISION)

    await run_reflection(state, adapter)

    assert state.request_decision == REVISED_DECISION
    assert state.reflection.draft_decision == DRAFT_DECISION
    assert state.reflection.revised_decision == REVISED_DECISION


@pytest.mark.anyio
async def test_reflection_passes_code_check_issues_to_critique():
    """An unknown rule_id ("Unclear request") is a code-check issue shown in CRITIQUE's view."""
    unknown_rule_decision = DRAFT_DECISION.model_copy(update={"rule_id": "Unclear request"})
    adapter = FakeChatModelAdapter([], [SATISFIED_CRITIQUE])
    state = build_state(unknown_rule_decision)

    await run_reflection(state, adapter)

    critique_view = adapter.received_calls[0]["conversation"].messages[0].text
    assert (
        "Code checks found:\n- rule_id Unclear request is not a rule in docs/requirements.md."
    ) in critique_view
