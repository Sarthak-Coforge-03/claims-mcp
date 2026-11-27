"""Tests for the check_request_eligibility MCP tool, called through the MCP protocol in-process.

The backend eligibility service is swapped for one over in-memory data, so no test reads data/.
"""

from datetime import date

import pytest
from mcp import Client

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.item_policy import ItemPolicy
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.services.eligibility_service import EligibilityService
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.backend.services.policy_service import PolicyService
from claims_mcp.mcp_server import server
from claims_mcp.mcp_server.server import mcp
from fakes.in_memory_employee_repository import InMemoryEmployeeRepository
from fakes.in_memory_policy_repository import InMemoryPolicyRepository


@pytest.fixture
def in_memory_eligibility_service(monkeypatch):
    """Make the tool use in-memory data: E100 (standard, no equipment), standard laptop 1/48.

    monkeypatch puts the real get_eligibility_service back after each test.
    """
    test_employee = EmployeeInfo(
        employee_id="E100",
        name="Test Person",
        role="standard",
        hire_date=date(2015, 1, 5),
        equipment=[],
    )
    standard_policy = RolePolicy(
        role="standard",
        item_policies=[
            ItemPolicy(
                policy_rule_id="POL-STD-LAPTOP",
                item="laptop",
                max_held=1,
                refresh_interval_months=48,
            )
        ],
    )
    eligibility_service = EligibilityService(
        EmployeeService(InMemoryEmployeeRepository([test_employee])),
        PolicyService(InMemoryPolicyRepository([standard_policy])),
    )

    # The tool calls get_eligibility_service() through the name imported into the server
    # module, so that is the name to replace (patching backend.service_provider would not
    # affect the tool). monkeypatch restores the original after each test, keeping tests isolated.
    monkeypatch.setattr(server, "get_eligibility_service", lambda: eligibility_service)
    return eligibility_service


@pytest.mark.anyio
async def test_check_eligibility_tool_holds_none_returns_elg_1(in_memory_eligibility_service):
    """E100 holds no laptop and may hold 1, so the tool reports rule ELG-1 (eligible)."""
    tool_arguments = {"employee_id": "E100", "item": "laptop"}

    async with Client(mcp) as client:
        result = await client.call_tool("check_request_eligibility", tool_arguments)

    assert result.structured_content["rule_id"] == "ELG-1"


@pytest.mark.anyio
async def test_check_eligibility_tool_not_entitled_is_answer_not_error(
    in_memory_eligibility_service,
):
    """A phone for a standard employee is DEN-2, returned as a normal result, not an error."""
    tool_arguments = {"employee_id": "E100", "item": "phone"}

    async with Client(mcp) as client:
        result = await client.call_tool("check_request_eligibility", tool_arguments)

    assert (result.is_error, result.structured_content["rule_id"]) == (False, "DEN-2")


@pytest.mark.anyio
async def test_check_eligibility_tool_unknown_employee_returns_error_result(
    in_memory_eligibility_service,
):
    """An unknown employee ID (E999) returns a result with is_error True."""
    tool_arguments = {"employee_id": "E999", "item": "laptop"}

    async with Client(mcp) as client:
        result = await client.call_tool("check_request_eligibility", tool_arguments)

    assert result.is_error is True
