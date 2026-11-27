"""Tests for the MCP server's tools, called through the real MCP protocol in-process.

mcp.Client(mcp) runs the full request/response cycle a real agent would, without a subprocess.
The backend service is swapped for an in-memory one, so no test reads the real data files.
"""

from datetime import date

import pytest
from mcp import Client

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.equipment_item import EquipmentItem
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.mcp_server import server
from claims_mcp.mcp_server.server import mcp
from fakes.in_memory_employee_repository import InMemoryEmployeeRepository


@pytest.fixture
def in_memory_employee_service(monkeypatch):
    """Make the server's tools use an in-memory service holding only E100 (standard, 1 laptop).

    monkeypatch puts the real get_employee_service back after each test.
    """
    test_employee = EmployeeInfo(
        employee_id="E100",
        name="Test Person",
        role="standard",
        hire_date=date(2020, 6, 15),
        equipment=[EquipmentItem(item="laptop", issued_date=date(2021, 1, 10))],
    )
    employee_service = EmployeeService(InMemoryEmployeeRepository([test_employee]))
    monkeypatch.setattr(server, "get_employee_service", lambda: employee_service)
    return employee_service


@pytest.mark.anyio
async def test_get_employee_info_tool_known_id_returns_employee(in_memory_employee_service):
    """Calling get_employee_info with E100 returns that record, so name is "Test Person".

    Proves the MCP path works: client call → tool → EmployeeService → repository → result.
    """
    tool_arguments = {"employee_id": "E100"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_employee_info", tool_arguments)

    assert result.structured_content["name"] == "Test Person"


@pytest.mark.anyio
async def test_get_employee_info_tool_unknown_id_returns_error_result(in_memory_employee_service):
    """Calling get_employee_info with an unknown ID (E999) returns a result with is_error True.

    The agent must get a readable error it can escalate on, not a crashed server or empty data.
    """
    tool_arguments = {"employee_id": "E999"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_employee_info", tool_arguments)

    assert result.is_error is True
