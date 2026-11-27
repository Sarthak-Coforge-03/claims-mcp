"""MCP server for the IT equipment request handler: exposes backend services as MCP tools.

Tools only translate between MCP and the backend; all business logic lives in claims_mcp.backend.
Run over stdio with: python -m claims_mcp.mcp_server.server
"""

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from claims_mcp.backend.models.eligibility_result import EligibilityResult
from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.escalation import Escalation
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.service_provider import (
    get_eligibility_service,
    get_employee_service,
    get_escalation_service,
    get_policy_service,
)

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


@mcp.tool()
def check_request_eligibility(employee_id: str, item: str) -> EligibilityResult:
    """Check whether an employee may get an item now under their role's policy, and why.

    Call this after get_employee_info; cite the returned rule_id in the decision.

    Args:
        employee_id: The employee's ID, e.g. "E001".
        item: The requested item, e.g. "laptop" (anything outside the catalog gives ESC-2).

    Returns:
        is_eligible, rule_id (ELG-1/2/3, DEN-2 or ESC-2), held_count, max_held,
        refresh_interval_months, newest_issued_date and eligible_from_date.

    Raises:
        ToolError: If no employee has that ID; the agent receives this as an error result.
    """
    eligibility = get_eligibility_service().check_request_eligibility(employee_id, item)
    if eligibility is None:
        raise ToolError(f"No employee with ID {employee_id}")
    return eligibility


@mcp.tool()
def flag_for_human_review(employee_id: str, request: str, reason: str) -> Escalation:
    """Escalate a request to a human reviewer instead of deciding it; saves an escalation record.

    Call this whenever an escalation rule (ESC-1..ESC-6) applies; put the rule ID in reason.

    Args:
        employee_id: The requesting employee's ID (an unknown ID is still escalated, ESC-1).
        request: What was asked for, e.g. "monitor".
        reason: Why a human must decide, starting with the rule ID, e.g. "ESC-4: in probation".

    Returns:
        The saved escalation: escalation_id, employee_id, request, reason, created_at, status.

    Raises:
        ToolError: If request or reason is empty; nothing is saved in that case.
    """
    try:
        return get_escalation_service().flag_for_human_review(employee_id, request, reason)
    except ValidationError as validation_error:
        raise ToolError(
            "Cannot escalate: request and reason must not be empty"
        ) from validation_error


if __name__ == "__main__":
    mcp.run()
