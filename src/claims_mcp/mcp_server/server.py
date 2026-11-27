"""MCP server for the IT equipment request handler: exposes backend services as MCP tools.

Tools only translate between MCP and the backend; all business logic lives in claims_mcp.backend.
Run over stdio with: python -m claims_mcp.mcp_server.server
"""

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.service_provider import get_employee_service, get_policy_service

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


@mcp.tool()
def get_policy_limits(role: str) -> RolePolicy:
    """List the items a role may hold, how many at once, and how often each can be replaced.

    Call this after get_employee_info, with the employee's role, before judging a request.

    Args:
        role: The employee's role, e.g. "standard", "manager" or "contractor".

    Returns:
        The role and its item policies (item, max_held, refresh_interval_months);
        an empty list means the role has no entitlements.

    Raises:
        ToolError: If the role has no policy; the agent receives this as an error result.
    """
    role_policy = get_policy_service().get_policy_limits(role)
    if role_policy is None:
        raise ToolError(f"No policy for role {role}")
    return role_policy


if __name__ == "__main__":
    mcp.run()
