"""Unit tests for the phase views: each phase is shown only its slice of the shared AgentState.

The state holds one finished step (employee lookup) and a current step (eligibility check).
"""

from datetime import date

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.react.views import build_act_view, build_observe_view, build_think_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import PlanSource, ThoughtDecision
from claims_mcp.host.state.plan import Plan
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.thought import Thought

LOOKUP_RESULT = '{"employee_id": "E001", "role": "standard", "hire_date": "2019-04-01"}'
LOOKUP_OBSERVATION = "E001 is a standard employee hired 2019-04-01."
ELIGIBILITY_RESULT = '{"rule_id": "ELG-2", "policy_rule_id": "POL-STD-MONITOR"}'
ELIGIBILITY_NEXT_ACTION = "Call check_request_eligibility for E001 and monitor."


def build_lookup_step() -> ReActStep:
    """Return a finished step: get_employee_info for E001, its raw result and its observation."""
    return ReActStep(
        thought=Thought(
            established_facts="Nothing yet.",
            decision=ThoughtDecision.CONTINUE,
            next_action="Call get_employee_info for E001.",
            request_decision=None,
        ),
        action=ToolCall(id="toolu_1", name="get_employee_info", arguments={"employee_id": "E001"}),
        tool_result=ToolResult(tool_call_id="toolu_1", content=LOOKUP_RESULT, is_error=False),
        observation=LOOKUP_OBSERVATION,
    )


def build_eligibility_step(tool_result: ToolResult | None, action_error: str | None) -> ReActStep:
    """Return the current step: THINK chose the eligibility check; ACT's outcome as given."""
    return ReActStep(
        thought=Thought(
            established_facts=LOOKUP_OBSERVATION,
            decision=ThoughtDecision.CONTINUE,
            next_action=ELIGIBILITY_NEXT_ACTION,
            request_decision=None,
        ),
        action=ToolCall(
            id="toolu_2",
            name="check_request_eligibility",
            arguments={"employee_id": "E001", "item": "monitor"},
        ),
        tool_result=tool_result,
        action_error=action_error,
    )


def build_state(steps: list[ReActStep]) -> AgentState:
    """Return the state of an E001 monitor request on 2026-11-27 holding the given steps."""
    return AgentState(
        request="Employee E001: my monitor is old, I'd like a new one.",
        today=date(2026, 11, 27),
        tool_specs=[
            ToolSpec(
                name="get_employee_info",
                description="Use first for every request.",
                input_schema={"type": "object"},
            )
        ],
        max_steps=10,
        steps=steps,
    )


def test_think_view_shows_observations_but_not_raw_tool_results():
    """THINK reasons from OBSERVE's reading: the observation is shown, the raw JSON is not."""
    state = build_state([build_lookup_step()])

    think_view = build_think_view(state)

    assert LOOKUP_OBSERVATION in think_view
    assert LOOKUP_RESULT not in think_view


def test_think_view_shows_the_plan_with_its_source_when_set():
    """With a plan in the state, THINK's view holds it under a heading naming its template."""
    state = build_state([])
    state.plan = Plan(
        source=PlanSource.MCP_TEMPLATE,
        template_name="replacement_request",
        text="- Call check_request_eligibility(employee_id, item).",
    )

    think_view = build_think_view(state)

    assert (
        "Plan (from MCP template replacement_request):\n"
        "- Call check_request_eligibility(employee_id, item)."
    ) in think_view


def test_act_view_shows_only_request_and_current_next_action():
    """ACT sees the request and THINK's next_action; earlier observations are hidden from it."""
    eligibility_result = ToolResult(
        tool_call_id="toolu_2", content=ELIGIBILITY_RESULT, is_error=False
    )
    state = build_state(
        [build_lookup_step(), build_eligibility_step(eligibility_result, action_error=None)]
    )

    act_view = build_act_view(state)

    assert act_view == (
        "Request: Employee E001: my monitor is old, I'd like a new one.\n"
        f"Next action: {ELIGIBILITY_NEXT_ACTION}"
    )


def test_observe_view_shows_current_raw_result_but_not_earlier_steps():
    """OBSERVE reads the current raw tool result; the earlier lookup step is not shown to it."""
    eligibility_result = ToolResult(
        tool_call_id="toolu_2", content=ELIGIBILITY_RESULT, is_error=False
    )
    state = build_state(
        [build_lookup_step(), build_eligibility_step(eligibility_result, action_error=None)]
    )

    observe_view = build_observe_view(state)

    assert ELIGIBILITY_RESULT in observe_view
    assert LOOKUP_OBSERVATION not in observe_view


def test_observe_view_shows_action_error_when_no_tool_ran():
    """When ACT made no usable tool call, OBSERVE is shown the action_error instead of a result."""
    action_error = "ACT made 0 tool calls; it replied: It's approved."
    state = build_state([build_eligibility_step(tool_result=None, action_error=action_error)])

    observe_view = build_observe_view(state)

    assert f"Action error: {action_error}" in observe_view
