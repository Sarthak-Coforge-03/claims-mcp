"""InMemoryEmployeeRepository: serves employees from a list in memory (tests and quick dev runs)."""

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.repositories.base.employee_repository_base import EmployeeRepositoryBase


class InMemoryEmployeeRepository(EmployeeRepositoryBase):
    """Holds employees in a dict keyed by ID; no files or database involved."""

    def __init__(self, employees: list[EmployeeInfo]) -> None:
        """Store the given employees, keyed by employee_id.

        Args:
            employees: The employees this repository should serve.
        """
        self.employee_by_id = {employee.employee_id: employee for employee in employees}

    def get_by_id(self, employee_id: str) -> EmployeeInfo | None:
        """Return the stored employee with this ID, or None if it isn't stored.

        Args:
            employee_id: The ID to look up, e.g. "E001".

        Returns:
            The matching EmployeeInfo, or None.
        """
        return self.employee_by_id.get(employee_id)
