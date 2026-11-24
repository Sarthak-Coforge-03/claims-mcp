"""Tests for the MCP server's tools, called through the real MCP protocol in-process.

mcp.Client(mcp) runs the full request/response cycle a real agent would, without a subprocess.
"""

import pytest
from mcp import Client

from claims_mcp.mcp_server.server import mcp


@pytest.mark.anyio
async def test_get_employee_info_tool_known_id_returns_employee():
    """Calling get_employee_info with E001 returns her record, so name is "Priya Sharma".

    Proves the whole path works: MCP call → tool → EmployeeService → JSON repository → data/.
    """
    tool_arguments = {"employee_id": "E001"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_employee_info", tool_arguments)

    assert result.structured_content["name"] == "Priya Sharma"


@pytest.mark.anyio
async def test_get_employee_info_tool_unknown_id_returns_error_result():
    """Calling get_employee_info with an unknown ID (E999) returns a result with is_error True.

    The agent must get a readable error it can escalate on, not a crashed server or empty data.
    """
    tool_arguments = {"employee_id": "E999"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_employee_info", tool_arguments)

    assert result.is_error is True
