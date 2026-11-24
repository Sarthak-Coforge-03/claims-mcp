"""Smoke check: start the MCP server over stdio, list its tools and call get_employee_info once.

Proves the client → server plumbing works end to end. Run with:
    uv run python -m claims_mcp.client.smoke_client
"""

import json
import sys

import anyio
from mcp import Client, StdioServerParameters

KNOWN_EMPLOYEE_ID = "E001"

# Start the server as a subprocess with the same Python (and so the same venv) as this client,
# so this works the same on the host and inside the Docker container.
SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "claims_mcp.mcp_server.server"],
)


async def run_smoke_check(employee_id: str) -> None:
    """Connect to the server over stdio, print its registered tools, then one tool result.

    Args:
        employee_id: The ID passed to get_employee_info, e.g. "E001".
    """
    async with Client(SERVER_PARAMETERS) as client:
        tools_result = await client.list_tools()
        tool_names = [tool.name for tool in tools_result.tools]
        print(f"Tools registered: {tool_names}")

        tool_result = await client.call_tool("get_employee_info", {"employee_id": employee_id})
        print(f"get_employee_info({employee_id!r}) is_error={tool_result.is_error}:")
        print(json.dumps(tool_result.structured_content, indent=2))


def main() -> None:
    """Run the smoke check for a known employee in data/employees.json."""
    anyio.run(run_smoke_check, KNOWN_EMPLOYEE_ID)


if __name__ == "__main__":
    main()
