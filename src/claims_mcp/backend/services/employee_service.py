"""EmployeeService: employee lookups, independent of where employee data is stored."""

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.repositories.employee_repository_base import EmployeeRepositoryBase


class EmployeeService:
    """Answers employee questions using whatever repository it is given.

    Built once at server startup and reused; it holds no per-request state.
    """

    def __init__(self, employee_repository: EmployeeRepositoryBase) -> None:
        """Keep the repository this service reads employees from.

        Args:
            employee_repository: Any employee repository (JSON now, ORM later, in-memory in tests).
        """
        self.employee_repository = employee_repository

    def get_employee_info(self, employee_id: str) -> EmployeeInfo | None:
        """Return an employee's role, hire date and equipment on file, or None if unknown.

        Args:
            employee_id: The ID to look up, e.g. "E001".

        Returns:
            The employee's EmployeeInfo, or None if no employee has that ID.
        """
        return self.employee_repository.get_by_id(employee_id)
