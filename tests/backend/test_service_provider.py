"""Unit tests for backend/service_provider.py, the one place that wires services to storage.

The MCP tools get their services only through this provider, so it must hand out shared instances.
"""

from claims_mcp.backend.service_provider import get_employee_service


def test_get_employee_service_returns_same_instance_each_call():
    """Two calls to get_employee_service() return the very same EmployeeService object.

    The service (and later an ORM connection pool) must be built once, not on every tool call.
    """
    first_employee_service = get_employee_service()

    second_employee_service = get_employee_service()

    assert second_employee_service is first_employee_service
