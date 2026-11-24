"""Builds the backend services and decides which storage each one uses (JSON now, ORM later).

Callers such as the MCP tools ask this module for a service and never construct storage themselves.
"""

from functools import lru_cache

from claims_mcp.backend.repositories.json_employee_repository import (
    DEFAULT_EMPLOYEES_FILE,
    JsonEmployeeRepository,
)
from claims_mcp.backend.services.employee_service import EmployeeService


@lru_cache
def get_employee_service() -> EmployeeService:
    """Return the shared EmployeeService, created on the first call and reused afterwards.

    This is the one place that picks employee storage; switching to the ORM changes only this line.

    Returns:
        An EmployeeService reading employees from data/employees.json.
    """
    return EmployeeService(JsonEmployeeRepository(DEFAULT_EMPLOYEES_FILE))
