"""Tests for McpToolGateway: MCP tools become ToolSpecs, and calls become ToolResults.

A test-only server with one known tool keeps these independent of the claims server's real tools
(those are tested in tests/mcp_server/). Client runs the full MCP protocol in-process.
"""

import json

import pytest
from mcp import Client
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from claims_mcp.host.gateways.tools.mcp_tool_gateway import McpToolGateway
from claims_mcp.host.llm.models.tool_call import ToolCall

KNOWN_EMPLOYEE_ID = "E001"

test_server = MCPServer("tool-gateway-test")


class Badge(BaseModel):
    """The test tool's structured result."""

    employee_id: str
    role: str


@test_server.tool(description="Look up an employee's badge.")
def get_badge(employee_id: str) -> Badge:
    """Return E001's badge; any other ID is a tool error, like an unknown employee."""
    if employee_id != KNOWN_EMPLOYEE_ID:
        raise ToolError(f"No badge for {employee_id}")
    return Badge(employee_id=employee_id, role="standard")


@pytest.mark.anyio
async def test_list_tool_specs_maps_each_tool_to_name_description_and_schema():
    """The server's one tool comes back as a ToolSpec with its description and argument schema."""
    async with Client(test_server) as client:
        tool_specs = await McpToolGateway(client).list_tool_specs()

    spec_summaries = [
        {
            "name": tool_spec.name,
            "description": tool_spec.description,
            "required": tool_spec.input_schema["required"],
        }
        for tool_spec in tool_specs
    ]
    assert spec_summaries == [
        {
            "name": "get_badge",
            "description": "Look up an employee's badge.",
            "required": ["employee_id"],
        }
    ]


@pytest.mark.anyio
async def test_call_tool_success_returns_structured_content_as_json():
    """A successful call returns the tool's structured content as JSON text, paired by call id."""
    tool_call = ToolCall(id="toolu_1", name="get_badge", arguments={"employee_id": "E001"})

    async with Client(test_server) as client:
        tool_result = await McpToolGateway(client).call_tool(tool_call)

    assert json.loads(tool_result.content) == {"employee_id": "E001", "role": "standard"}
    assert tool_result.tool_call_id == "toolu_1"
    assert tool_result.is_error is False


@pytest.mark.anyio
async def test_call_tool_tool_error_returns_error_result_with_message():
    """A ToolError comes back as a ToolResult with is_error True and the error text, no raise.

    The error has no structured content, so the gateway passes on the text message instead.
    """
    tool_call = ToolCall(id="toolu_2", name="get_badge", arguments={"employee_id": "E999"})

    async with Client(test_server) as client:
        tool_result = await McpToolGateway(client).call_tool(tool_call)

    assert tool_result.is_error is True
    assert tool_result.content == "Error executing tool get_badge: No badge for E999"
