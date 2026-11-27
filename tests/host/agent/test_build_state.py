"""Unit tests for build_state: the requester lands in employee_id or requester_name by type."""

from claims_mcp.host.agent.build_state import build_state
from claims_mcp.host.state.enums import RequesterType
from claims_mcp.settings import Settings


def test_build_state_employee_requester_is_the_employee_id():
    """An employee's answer (E001) is their employee ID; the name waits for the record."""
    state = build_state(RequesterType.EMPLOYEE, "E001", "a monitor", [], Settings())

    assert state.employee_id == "E001"
    assert state.requester_name is None


def test_build_state_contractor_requester_is_the_name_with_no_employee_id():
    """A contractor's answer (Alex Doe) is their name, and they have no employee ID."""
    state = build_state(RequesterType.CONTRACTOR, "Alex Doe", "a laptop", [], Settings())

    assert state.requester_name == "Alex Doe"
    assert state.employee_id is None
