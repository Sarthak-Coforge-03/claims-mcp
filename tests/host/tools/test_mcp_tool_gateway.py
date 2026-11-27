"""Tests for McpToolGateway: the host's tool access, over the real MCP protocol in-process.

Client(mcp) talks to the real server object without HTTP. The fixture swaps only the employee
service the tools read from, so the real get_employee_info tool runs against a custom E100.
"""

import json
from datetime import date

import pytest
from mcp import Client

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.tools.mcp_tool_gateway import McpToolGateway
from claims_mcp.mcp_server import server
from claims_mcp.mcp_server.server import mcp
from fakes.in_memory_employee_repository import InMemoryEmployeeRepository


@pytest.fixture
def in_memory_employee_service(monkeypatch):
    """Make the server's tools use an in-memory service holding only E100 (standard, no items)."""
    test_employee = EmployeeInfo(
        employee_id="E100",
        name="Test Person",
        role="standard",
        hire_date=date(2020, 6, 15),
        equipment=[],
    )
    employee_service = EmployeeService(InMemoryEmployeeRepository([test_employee]))
    monkeypatch.setattr(server, "get_employee_service", lambda: employee_service)
    return employee_service


@pytest.mark.anyio
async def test_list_tool_specs_returns_every_server_tool_with_schema():
    """The four server tools come back as ToolSpecs; each has an object-typed argument schema."""
    async with Client(mcp) as client:
        tool_specs = await McpToolGateway(client).list_tool_specs()

    schema_type_by_tool_name = {
        tool_spec.name: tool_spec.input_schema["type"] for tool_spec in tool_specs
    }
    assert schema_type_by_tool_name == {
        "get_employee_info": "object",
        "get_policy_limits": "object",
        "check_request_eligibility": "object",
        "flag_for_human_review": "object",
    }


@pytest.mark.anyio
async def test_call_tool_known_employee_returns_structured_content_as_json(
    in_memory_employee_service,
):
    """A successful call returns the tool's structured content as JSON text, paired by call id."""
    tool_call = ToolCall(id="toolu_1", name="get_employee_info", arguments={"employee_id": "E100"})

    async with Client(mcp) as client:
        tool_result = await McpToolGateway(client).call_tool(tool_call)

    # The chain behind this value: the real tool returns the fixture's EmployeeInfo; MCP
    # serialises it into structured_content (dates become ISO strings); the gateway json.dumps
    # that dict for the model. json.loads undoes the last step, so key order and spacing don't
    # matter; the fields must match the fixture's E100.
    assert json.loads(tool_result.content) == {
        "employee_id": "E100",
        "name": "Test Person",
        "role": "standard",
        "hire_date": "2020-06-15",
        "equipment": [],
    }
    assert tool_result.tool_call_id == "toolu_1"
    assert tool_result.is_error is False


@pytest.mark.anyio
async def test_call_tool_unknown_employee_returns_error_result(in_memory_employee_service):
    """A tool error (unknown E999) comes back as a ToolResult with is_error True, not an exception.

    The error has no structured content, so the gateway passes on the text message instead.
    """
    tool_call = ToolCall(id="toolu_2", name="get_employee_info", arguments={"employee_id": "E999"})

    async with Client(mcp) as client:
        tool_result = await McpToolGateway(client).call_tool(tool_call)

    assert tool_result.is_error is True
    assert tool_result.content == (
        "Error executing tool get_employee_info: No employee with ID E999"
    )
