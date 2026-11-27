"""Smoke check: connect to the running MCP server over HTTP, list its tools, call one once.

Proves the client → server plumbing works end to end. Start the server first, then run:
    uv run python -m claims_mcp.mcp_server.server              (terminal 1)
    uv run python -m claims_mcp.host.gateways.smoke_client     (terminal 2)
The server URL comes from CLAIMS_MCP_SERVER_URL (default http://localhost:8000/mcp).
"""

import json

import anyio
from mcp import Client

from claims_mcp.settings import get_settings

KNOWN_EMPLOYEE_ID = "E001"


async def run_smoke_check(server_url: str, employee_id: str) -> None:
    """Connect to the server by URL, print its registered tools, then one tool result.

    Args:
        server_url: The server's Streamable HTTP endpoint, e.g. "http://localhost:8000/mcp".
        employee_id: The ID passed to get_employee_info, e.g. "E001".
    """
    async with Client(server_url) as client:
        tools_result = await client.list_tools()
        tool_names = [tool.name for tool in tools_result.tools]
        print(f"Connected to {server_url}")
        print(f"Tools registered: {tool_names}")

        tool_result = await client.call_tool("get_employee_info", {"employee_id": employee_id})
        print(f"get_employee_info({employee_id!r}) is_error={tool_result.is_error}:")
        print(json.dumps(tool_result.structured_content, indent=2))


def main() -> None:
    """Run the smoke check for a known employee in data/employees.json."""
    anyio.run(run_smoke_check, get_settings().server_url, KNOWN_EMPLOYEE_ID)


if __name__ == "__main__":
    main()
