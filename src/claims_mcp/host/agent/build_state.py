"""build_state: turn who is asking and what they asked into a fresh AgentState."""

from datetime import date

from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import RequesterType
from claims_mcp.settings import Settings


def build_state(
    requester_type: RequesterType,
    requester: str,
    request: str,
    tool_specs: list[ToolSpec],
    settings: Settings,
) -> AgentState:
    """Return a new run state for one request, dated today.

    Args:
        requester_type: Employee or contractor.
        requester: An employee's ID (e.g. "E001"), or a contractor's full name.
        request: The request in the requester's own words.
        tool_specs: The server's tools.
        settings: Supplies max_react_steps.

    Returns:
        An AgentState with employee_id set for an employee, or requester_name set for a
        contractor (an employee's name comes from the record during the run).
    """
    is_contractor = requester_type == RequesterType.CONTRACTOR
    return AgentState(
        requester_type=requester_type,
        employee_id=None if is_contractor else requester,
        requester_name=requester if is_contractor else None,
        request=request,
        today=date.today(),
        tool_specs=tool_specs,
        max_steps=settings.max_react_steps,
    )
