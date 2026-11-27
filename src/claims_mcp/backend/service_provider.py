"""Builds the backend services and picks each one's storage (JSON now, optionally SQL later).

Callers such as the MCP tools ask this module for a service and never construct storage themselves.
File locations come from claims_mcp.settings, so they can be changed through environment variables.
"""

from functools import lru_cache

from claims_mcp.backend.repositories.json.json_employee_repository import JsonEmployeeRepository
from claims_mcp.backend.repositories.json.json_policy_repository import JsonPolicyRepository
from claims_mcp.backend.services.eligibility_service import EligibilityService
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.backend.services.policy_service import PolicyService
from claims_mcp.settings import get_settings


@lru_cache
def get_employee_service() -> EmployeeService:
    """Return the shared EmployeeService, created on the first call and reused afterwards.

    This is the one place that picks employee storage; adding SQL later changes only this line.

    Returns:
        An EmployeeService reading employees from settings.employees_file.
    """
    return EmployeeService(JsonEmployeeRepository(get_settings().employees_file))


@lru_cache
def get_policy_service() -> PolicyService:
    """Return the shared PolicyService, created on the first call and reused afterwards.

    This is the one place that picks policy storage; adding SQL later changes only this line.

    Returns:
        A PolicyService reading role policies from settings.policies_file.
    """
    return PolicyService(JsonPolicyRepository(get_settings().policies_file))


@lru_cache
def get_eligibility_service() -> EligibilityService:
    """Return the shared EligibilityService, built on top of the shared employee/policy services.

    It has no storage of its own, so changing storage never touches it.

    Returns:
        An EligibilityService using get_employee_service() and get_policy_service().
    """
    return EligibilityService(get_employee_service(), get_policy_service())
