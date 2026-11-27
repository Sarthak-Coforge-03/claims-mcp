"""Builds the backend services and picks each one's storage (JSON now, optionally SQL later).

Callers such as the MCP tools ask this module for a service and never construct storage themselves.
"""

from functools import lru_cache

from claims_mcp.backend.repositories.json_employee_repository import (
    DEFAULT_EMPLOYEES_FILE,
    JsonEmployeeRepository,
)
from claims_mcp.backend.repositories.json_policy_repository import (
    DEFAULT_POLICIES_FILE,
    JsonPolicyRepository,
)
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.backend.services.policy_service import PolicyService


@lru_cache
def get_employee_service() -> EmployeeService:
    """Return the shared EmployeeService, created on the first call and reused afterwards.

    This is the one place that picks employee storage; adding SQL later changes only this line.

    Returns:
        An EmployeeService reading employees from data/employees.json.
    """
    return EmployeeService(JsonEmployeeRepository(DEFAULT_EMPLOYEES_FILE))


@lru_cache
def get_policy_service() -> PolicyService:
    """Return the shared PolicyService, created on the first call and reused afterwards.

    This is the one place that picks policy storage; adding SQL later changes only this line.

    Returns:
        A PolicyService reading role policies from data/policies.json.
    """
    return PolicyService(JsonPolicyRepository(DEFAULT_POLICIES_FILE))
