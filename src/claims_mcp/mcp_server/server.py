"""MCP server for the IT equipment request handler: exposes backend services as MCP tools.

Tools only translate between MCP and the backend; all business logic lives in claims_mcp.backend.
Run over stdio with: python -m claims_mcp.mcp_server.server
"""

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.service_provider import get_employee_service

mcp = MCPServer("it-equipment-requests")


@mcp.tool()
def get_employee_info(employee_id: str) -> EmployeeInfo:
    """Look up an employee's role, hire date and equipment on file by their employee ID.

    Call this first for any equipment request: the role decides the policy that applies.

    Args:
        employee_id: The employee's ID, e.g. "E001".

    Returns:
        The employee's ID, name, role, hire date and equipment list (item and issued date).

    Raises:
        ToolError: If no employee has that ID; the agent receives this as an error result.
    """
    employee = get_employee_service().get_employee_info(employee_id)
    if employee is None:
        raise ToolError(f"No employee with ID {employee_id}")
    return employee


if __name__ == "__main__":
    mcp.run()
