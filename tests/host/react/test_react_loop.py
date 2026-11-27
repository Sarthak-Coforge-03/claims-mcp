"""Unit tests for the ReAct loop driver: phase order, the step limit, and which call gets tools.

The model and tools are fakes, so these run with no network and no MCP server.
"""

from datetime import date

import pytest

from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.react.react_loop import run_react_loop
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.agent_stop_reason import AgentStopReason
from claims_mcp.host.state.request_decision import RequestDecision
from claims_mcp.host.state.request_outcome import RequestOutcome
from claims_mcp.host.state.thought import Thought
from claims_mcp.host.state.thought_decision import ThoughtDecision
from fakes.fake_chat_model_adapter import FakeChatModelAdapter
from fakes.fake_tool_gateway import FakeToolGateway

EMPLOYEE_LOOKUP = ToolCall(
    id="toolu_1", name="get_employee_info", arguments={"employee_id": "E001"}
)
LOOKUP_THOUGHT = Thought(
    established_facts="Nothing is known yet.",
    decision=ThoughtDecision.CONTINUE,
    next_action="Call get_employee_info for E001.",
    request_decision=None,
)
FINISH_THOUGHT = Thought(
    established_facts="ELG-2 applies under POL-STD-MONITOR.",
    decision=ThoughtDecision.FINISH,
    next_action=None,
    request_decision=RequestDecision(
        outcome=RequestOutcome.APPROVE,
        rule_id="ELG-2",
        policy_rule_id="POL-STD-MONITOR",
        eligible_from_date=None,
        escalation_id=None,
        response="Approved under ELG-2 (POL-STD-MONITOR).",
    ),
)
ACT_TURN = ModelTurn(
    text="",
    reasoning_summary="",
    tool_calls=[EMPLOYEE_LOOKUP],
    stop_reason="tool_use",
    provider_content=[],
)
OBSERVE_TURN = ModelTurn(
    text="E001 is a standard employee.",
    reasoning_summary="",
    tool_calls=[],
    stop_reason="end_turn",
    provider_content=[],
)


async def run_loop(adapter: FakeChatModelAdapter, max_steps: int) -> AgentState:
    """Run the loop on an E001 monitor request with a canned get_employee_info result."""
    tool_gateway = FakeToolGateway({"get_employee_info": '{"role": "standard"}'})
    state = AgentState(
        request="Employee E001: my monitor is old, I'd like a new one.",
        today=date(2026, 11, 27),
        tool_specs=[
            ToolSpec(
                name="get_employee_info",
                description="Use first for every request.",
                input_schema={"type": "object"},
            )
        ],
        max_steps=max_steps,
    )
    return await run_react_loop(state, adapter, tool_gateway)


@pytest.mark.anyio
async def test_react_loop_runs_one_cycle_then_finishes_with_think_decision():
    """THINK, ACT, OBSERVE, then a FINISH thought: the run ends with THINK's approve under ELG-2."""
    adapter = FakeChatModelAdapter([ACT_TURN, OBSERVE_TURN], [LOOKUP_THOUGHT, FINISH_THOUGHT])

    final_state = await run_loop(adapter, max_steps=5)

    assert final_state.request_decision.outcome == RequestOutcome.APPROVE
    assert final_state.request_decision.rule_id == "ELG-2"
    assert final_state.stop_reason == AgentStopReason.FINAL_ANSWER
    assert [call["method"] for call in adapter.received_calls] == [
        "complete_structured",
        "complete",
        "complete",
        "complete_structured",
    ]


@pytest.mark.anyio
async def test_react_loop_think_never_finishing_stops_at_step_limit():
    """A THINK that always continues stops after max_steps=2 cycles: STEP_LIMIT, no decision."""
    adapter = FakeChatModelAdapter(
        [ACT_TURN, OBSERVE_TURN, ACT_TURN, OBSERVE_TURN], [LOOKUP_THOUGHT]
    )

    final_state = await run_loop(adapter, max_steps=2)

    assert final_state.stop_reason == AgentStopReason.STEP_LIMIT
    assert final_state.request_decision is None
    assert len(final_state.steps) == 2


@pytest.mark.anyio
async def test_react_loop_only_act_is_sent_tools():
    """THINK and OBSERVE get no tools; ACT gets get_employee_info (THINK, ACT, OBSERVE, THINK)."""
    adapter = FakeChatModelAdapter([ACT_TURN, OBSERVE_TURN], [LOOKUP_THOUGHT, FINISH_THOUGHT])

    await run_loop(adapter, max_steps=5)

    tools_sent_per_call = [
        [tool_spec.name for tool_spec in received_call["conversation"].tool_specs]
        for received_call in adapter.received_calls
    ]
    assert tools_sent_per_call == [[], ["get_employee_info"], [], []]
