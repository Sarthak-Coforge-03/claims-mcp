"""Unit tests for the reflection's two code checks, passed to the model review as hints.

Each test builds its own steps with JSON tool results, the shape McpToolGateway returns.
"""

import json
from datetime import date

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.reflect.decision_checks import find_decision_issues
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import RequestOutcome, ThoughtDecision
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.request_decision import RequestDecision
from claims_mcp.host.state.thought import Thought


def build_escalation_step() -> ReActStep:
    """Return a finished flag_for_human_review step whose result is escalation esc-123."""
    return ReActStep(
        thought=Thought(
            established_facts="",
            decision=ThoughtDecision.CONTINUE,
            next_action="Call flag_for_human_review.",
            request_decision=None,
        ),
        action=ToolCall(
            id="toolu_1",
            name="flag_for_human_review",
            arguments={"employee_id": "E004", "request": "ship", "reason": "ESC-7: shipping"},
        ),
        tool_result=ToolResult(
            tool_call_id="toolu_1",
            content=json.dumps({"escalation_id": "esc-123"}),
            is_error=False,
        ),
        observation="",
    )


def build_state(steps: list[ReActStep], outcome: RequestOutcome, rule_id: str) -> AgentState:
    """Return a finished state holding the given steps and a draft with outcome and rule_id."""
    return AgentState(
        request="A request.",
        today=date(2026, 11, 27),
        tool_specs=[],
        max_steps=5,
        steps=steps,
        request_decision=RequestDecision(
            outcome=outcome,
            rule_id=rule_id,
            policy_rule_id=None,
            eligible_from_date=None,
            escalation_id="esc-123",
            response="Reply to the employee.",
        ),
    )


def test_escalate_under_known_rule_with_filed_escalation_has_no_issues():
    """Escalate under ESC-7 after a successful flag_for_human_review call: no issues."""
    state = build_state([build_escalation_step()], RequestOutcome.ESCALATE, "ESC-7")

    decision_issues = find_decision_issues(state)

    assert decision_issues == []


def test_unknown_rule_id_is_an_issue():
    """A rule_id that is no rule in the requirements, e.g. "Unclear request", is reported."""
    state = build_state([build_escalation_step()], RequestOutcome.ESCALATE, "Unclear request")

    decision_issues = find_decision_issues(state)

    assert decision_issues == ["rule_id Unclear request is not a rule in docs/requirements.md."]


def test_escalate_without_flag_call_is_an_issue():
    """Escalate with no successful flag_for_human_review call: nothing was actually escalated."""
    state = build_state([], RequestOutcome.ESCALATE, "ESC-4")

    decision_issues = find_decision_issues(state)

    assert decision_issues == [
        "Outcome is escalate, but flag_for_human_review never returned a result."
    ]
