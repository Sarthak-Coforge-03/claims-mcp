"""Unit tests for the THINK, ACT and OBSERVE nodes: what each writes into the state, where it goes.

The model and tools are fakes. THINK alone chooses its next phase; ACT and OBSERVE always move on.
"""

from datetime import date

import pytest

from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.react.act_node import run_act_node
from claims_mcp.host.react.observe_node import run_observe_node
from claims_mcp.host.react.think_node import run_think_node
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.agent_stop_reason import AgentStopReason
from claims_mcp.host.state.react_phase import ReactPhase
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.thought import Thought
from claims_mcp.host.state.thought_decision import ThoughtDecision
from fakes.fake_chat_model_adapter import FakeChatModelAdapter
from fakes.fake_tool_gateway import FakeToolGateway

EMPLOYEE_LOOKUP = ToolCall(
    id="toolu_1", name="get_employee_info", arguments={"employee_id": "E001"}
)
LOOKUP_RESULT = '{"employee_id": "E001", "role": "standard"}'
LOOKUP_THOUGHT = Thought(
    established_facts="Nothing is known yet.",
    decision=ThoughtDecision.CONTINUE,
    next_action="Call get_employee_info for E001.",
    final_answer=None,
)
FINISH_THOUGHT = Thought(
    established_facts="ELG-2 applies under POL-STD-MONITOR.",
    decision=ThoughtDecision.FINISH,
    next_action=None,
    final_answer="Approved under ELG-2 (POL-STD-MONITOR).",
)


def build_turn(text: str, tool_calls: list[ToolCall]) -> ModelTurn:
    """Return a model reply with the given text and tool calls (an ACT or OBSERVE reply)."""
    return ModelTurn(
        text=text,
        reasoning_summary="",
        tool_calls=tool_calls,
        stop_reason="tool_use" if tool_calls else "end_turn",
        provider_content=[],
    )


def build_state(steps: list[ReActStep], next_phase: ReactPhase) -> AgentState:
    """Return an E001 monitor request state holding the given steps, about to run next_phase."""
    return AgentState(
        request="Employee E001: my monitor is old, I'd like a new one.",
        today=date(2026, 11, 27),
        tool_specs=[],
        max_steps=10,
        steps=steps,
        next_phase=next_phase,
    )


@pytest.mark.anyio
async def test_think_node_continue_starts_step_and_goes_to_act():
    """A CONTINUE thought starts a new step holding it, and the next phase is ACT."""
    adapter = FakeChatModelAdapter([], [LOOKUP_THOUGHT])
    state = build_state([], ReactPhase.THINK)

    await run_think_node(state, adapter)

    assert state.steps == [ReActStep(thought=LOOKUP_THOUGHT)]
    assert state.next_phase == ReactPhase.ACT


@pytest.mark.anyio
async def test_think_node_finish_sets_final_answer_and_goes_to_done():
    """A FINISH thought sets final_answer and FINAL_ANSWER, and the next phase is DONE."""
    adapter = FakeChatModelAdapter([], [FINISH_THOUGHT])
    state = build_state([], ReactPhase.THINK)

    await run_think_node(state, adapter)

    assert state.final_answer == "Approved under ELG-2 (POL-STD-MONITOR)."
    assert state.stop_reason == AgentStopReason.FINAL_ANSWER
    assert state.next_phase == ReactPhase.DONE


@pytest.mark.anyio
async def test_act_node_one_tool_call_runs_it_and_goes_to_observe():
    """One tool call is recorded as the action, run through the gateway, then OBSERVE is next."""
    adapter = FakeChatModelAdapter([build_turn("", [EMPLOYEE_LOOKUP])], [])
    tool_gateway = FakeToolGateway({"get_employee_info": LOOKUP_RESULT})
    state = build_state([ReActStep(thought=LOOKUP_THOUGHT)], ReactPhase.ACT)

    await run_act_node(state, adapter, tool_gateway)

    assert state.current_step == ReActStep(
        thought=LOOKUP_THOUGHT,
        action=EMPLOYEE_LOOKUP,
        tool_result=ToolResult(tool_call_id="toolu_1", content=LOOKUP_RESULT, is_error=False),
    )
    assert state.next_phase == ReactPhase.OBSERVE


@pytest.mark.anyio
async def test_act_node_without_tool_call_records_error_and_still_goes_to_observe():
    """A text reply with no tool call is an action_error, no tool runs, OBSERVE is still next."""
    adapter = FakeChatModelAdapter([build_turn("It's approved.", [])], [])
    tool_gateway = FakeToolGateway({"get_employee_info": LOOKUP_RESULT})
    state = build_state([ReActStep(thought=LOOKUP_THOUGHT)], ReactPhase.ACT)

    await run_act_node(state, adapter, tool_gateway)

    assert state.current_step.action_error == "ACT made 0 tool calls; it replied: It's approved."
    assert tool_gateway.received_tool_calls == []
    assert state.next_phase == ReactPhase.OBSERVE


@pytest.mark.anyio
async def test_observe_node_records_reading_and_goes_to_think():
    """OBSERVE's reply text becomes the step's observation, and THINK is always next."""
    adapter = FakeChatModelAdapter([build_turn("E001 is a standard employee.", [])], [])
    acted_step = ReActStep(
        thought=LOOKUP_THOUGHT,
        action=EMPLOYEE_LOOKUP,
        tool_result=ToolResult(tool_call_id="toolu_1", content=LOOKUP_RESULT, is_error=False),
    )
    state = build_state([acted_step], ReactPhase.OBSERVE)

    await run_observe_node(state, adapter)

    assert state.current_step.observation == "E001 is a standard employee."
    assert state.next_phase == ReactPhase.THINK
