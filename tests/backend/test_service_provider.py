"""Unit tests for backend/service_provider.py, the one place that wires services to storage.

The MCP tools get their services only through this provider, so it must hand out shared instances.
"""

from claims_mcp.backend.service_provider import (
    get_eligibility_service,
    get_employee_service,
    get_escalation_service,
    get_policy_service,
)


def test_get_employee_service_returns_same_instance_each_call():
    """Two calls to get_employee_service() return the very same EmployeeService object.

    The service (and later an ORM connection pool) must be built once, not on every tool call.
    """
    first_employee_service = get_employee_service()

    second_employee_service = get_employee_service()

    assert second_employee_service is first_employee_service


def test_get_policy_service_returns_same_instance_each_call():
    """Two calls to get_policy_service() return the very same PolicyService object.

    Like the employee service, it is built once per server process and shared by every tool call.
    """
    first_policy_service = get_policy_service()

    second_policy_service = get_policy_service()

    assert second_policy_service is first_policy_service


def test_get_eligibility_service_returns_same_instance_each_call():
    """Two calls to get_eligibility_service() return the very same EligibilityService object.

    It reuses the shared employee and policy services instead of building its own copies.
    """
    first_eligibility_service = get_eligibility_service()

    second_eligibility_service = get_eligibility_service()

    assert second_eligibility_service is first_eligibility_service


def test_get_escalation_service_returns_same_instance_each_call():
    """Two calls to get_escalation_service() return the very same EscalationService object.

    Every escalation in a server process goes through one service and so one escalations file.
    """
    first_escalation_service = get_escalation_service()

    second_escalation_service = get_escalation_service()

    assert second_escalation_service is first_escalation_service
