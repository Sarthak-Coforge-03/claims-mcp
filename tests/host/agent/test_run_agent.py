"""Unit tests for run_agent: plan, the ReAct loop, then reflection only when there is a decision.

The model, tools and templates are fakes. SELECT returns no template, so WRITE plans each run.
"""

from datetime import date

import pytest

from claims_mcp.host.agent.run_agent import run_agent
from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.plan.template_selection import TemplateSelection
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.enums import (
    AgentStopReason,
    RequesterType,
    RequestOutcome,
    ThoughtDecision,
)
from claims_mcp.host.state.request_decision import RequestDecision
from claims_mcp.host.state.thought import Thought
from fakes.fake_chat_model_adapter import FakeChatModelAdapter
from fakes.fake_template_gateway import FakeTemplateGateway
from fakes.fake_tool_gateway import FakeToolGateway

NO_TEMPLATE_SELECTION = TemplateSelection(
    template_name=None, item="monitor", reason="it is old", quantity="1"
)
FINISH_THOUGHT = Thought(
    established_facts="ELG-2 applies.",
    decision=ThoughtDecision.FINISH,
    next_action=None,
    request_decision=RequestDecision(
        outcome=RequestOutcome.APPROVE,
        rule_id="ELG-2",
        policy_rule_id="POL-STD-MONITOR",
        eligible_from_date=None,
        escalation_id=None,
        response="Approved under ELG-2.",
    ),
)
CONTINUE_THOUGHT = Thought(
    established_facts="Nothing yet.",
    decision=ThoughtDecision.CONTINUE,
    next_action="Call get_employee_info for E001.",
    request_decision=None,
)
SATISFIED_CRITIQUE = Critique(
    addresses_request=True,
    follows_policy=True,
    avoids_unconfirmed_promises=True,
    matches_tool_results=True,
    issues=[],
)


def build_turn(text: str, tool_calls: list[ToolCall]) -> ModelTurn:
    """Return a model reply with the given text and tool calls (WRITE, ACT or OBSERVE)."""
    return ModelTurn(
        text=text,
        reasoning_summary="",
        tool_calls=tool_calls,
        stop_reason="tool_use" if tool_calls else "end_turn",
        provider_content=[],
    )


async def run(adapter: FakeChatModelAdapter, max_steps: int) -> AgentState:
    """Run the agent for employee E001's monitor request with the given adapter and step limit."""
    state = AgentState(
        requester_type=RequesterType.EMPLOYEE,
        employee_id="E001",
        request="my monitor is old",
        today=date(2026, 11, 27),
        tool_specs=[],
        max_steps=max_steps,
    )
    tool_gateway = FakeToolGateway({"get_employee_info": '{"employee_id": "E001"}'})
    template_gateway = FakeTemplateGateway({})
    return await run_agent(state, adapter, tool_gateway, template_gateway)


@pytest.mark.anyio
async def test_run_agent_with_a_decision_reflects_on_it():
    """Plan, then THINK finishes at once: reflection runs and records the critique."""
    adapter = FakeChatModelAdapter(
        [build_turn("- Call get_employee_info.", [])],
        [NO_TEMPLATE_SELECTION, FINISH_THOUGHT, SATISFIED_CRITIQUE],
    )

    final_state = await run(adapter, max_steps=5)

    assert final_state.reflection.critique == SATISFIED_CRITIQUE


@pytest.mark.anyio
async def test_run_agent_stopped_at_step_limit_skips_reflection():
    """THINK never finishes and the step limit (1) ends the run: no decision, no reflection."""
    employee_lookup = ToolCall(
        id="toolu_1", name="get_employee_info", arguments={"employee_id": "E001"}
    )
    adapter = FakeChatModelAdapter(
        [
            build_turn("- Call get_employee_info.", []),
            build_turn("", [employee_lookup]),
            build_turn("E001 exists.", []),
        ],
        [NO_TEMPLATE_SELECTION, CONTINUE_THOUGHT],
    )

    final_state = await run(adapter, max_steps=1)

    assert final_state.stop_reason == AgentStopReason.STEP_LIMIT
    assert final_state.reflection is None
