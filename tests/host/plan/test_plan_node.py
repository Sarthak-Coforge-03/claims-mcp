"""Unit tests for the plan node: a fitting template becomes the plan, else the model writes one.

The model and the templates are fakes. SELECT uses complete_structured; WRITE uses complete.
"""

from datetime import date

import pytest

from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.plan.plan_node import run_plan_node
from claims_mcp.host.plan.template_selection import TemplateSelection
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.plan import Plan
from claims_mcp.host.state.plan_source import PlanSource
from fakes.fake_chat_model_adapter import FakeChatModelAdapter
from fakes.fake_template_gateway import FakeTemplateGateway

REPLACEMENT_TEMPLATE_TEXT = "- Call check_request_eligibility(employee_id, item)."
WRITTEN_PLAN_TEXT = "- Call get_employee_info.\n- Escalate if unsure."
WRITE_TURN = ModelTurn(
    text=WRITTEN_PLAN_TEXT,
    reasoning_summary="",
    tool_calls=[],
    stop_reason="end_turn",
    provider_content=[],
)


def build_selection(template_name: str | None, employee_id: str | None) -> TemplateSelection:
    """Return a SELECT reply for a monitor request with the given template name and employee ID."""
    return TemplateSelection(
        template_name=template_name,
        employee_id=employee_id,
        item="monitor",
        reason="my monitor is old",
        quantity="1",
    )


async def run_node(selection: TemplateSelection) -> dict:
    """Run the plan node with the given SELECT reply; return the state, adapter and gateway."""
    adapter = FakeChatModelAdapter([WRITE_TURN], [selection])
    template_gateway = FakeTemplateGateway({"replacement_request": REPLACEMENT_TEMPLATE_TEXT})
    state = AgentState(
        request="Employee E001: my monitor is old, I'd like a new one.",
        today=date(2026, 11, 27),
        tool_specs=[],
        max_steps=5,
    )
    await run_plan_node(state, adapter, template_gateway)
    return {"state": state, "adapter": adapter, "template_gateway": template_gateway}


@pytest.mark.anyio
async def test_plan_node_fitting_template_becomes_the_plan_without_writing():
    """SELECT picks replacement_request: its text is the plan, and no WRITE call is made."""
    run_result = await run_node(build_selection("replacement_request", "E001"))

    assert run_result["state"].plan == Plan(
        source=PlanSource.MCP_TEMPLATE,
        template_name="replacement_request",
        text=REPLACEMENT_TEMPLATE_TEXT,
    )
    assert [call["method"] for call in run_result["adapter"].received_calls] == [
        "complete_structured"
    ]


@pytest.mark.anyio
async def test_plan_node_fills_template_with_the_extracted_arguments():
    """The template is requested with SELECT's employee_id, item, reason and quantity, as text."""
    run_result = await run_node(build_selection("replacement_request", "E001"))

    assert run_result["template_gateway"].received_template_requests == [
        {
            "template_name": "replacement_request",
            "arguments": {
                "employee_id": "E001",
                "item": "monitor",
                "reason": "my monitor is old",
                "quantity": "1",
            },
        }
    ]


@pytest.mark.anyio
async def test_plan_node_no_fitting_template_writes_plan_from_tools():
    """SELECT returns no template: the plan is WRITE's reply, sourced from the tool descriptions."""
    run_result = await run_node(build_selection(None, "E001"))

    assert run_result["state"].plan == Plan(
        source=PlanSource.TOOL_DESCRIPTIONS, template_name=None, text=WRITTEN_PLAN_TEXT
    )


@pytest.mark.anyio
async def test_plan_node_unknown_template_name_falls_back_to_writing():
    """A template name the server doesn't have is ignored; the plan is written instead."""
    run_result = await run_node(build_selection("standing_desk_request", "E001"))

    assert run_result["state"].plan.source == PlanSource.TOOL_DESCRIPTIONS
    assert run_result["template_gateway"].received_template_requests == []


@pytest.mark.anyio
async def test_plan_node_missing_employee_id_falls_back_to_writing():
    """A template can't be filled without an employee ID, so the plan is written instead."""
    run_result = await run_node(build_selection("replacement_request", None))

    assert run_result["state"].plan.source == PlanSource.TOOL_DESCRIPTIONS
    assert run_result["template_gateway"].received_template_requests == []
