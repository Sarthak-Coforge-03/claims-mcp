"""EmployeeRepositoryBase: the interface every employee data source implements."""

from abc import ABC, abstractmethod

from claims_mcp.backend.models.employee_info import EmployeeInfo


class EmployeeRepositoryBase(ABC):
    """Base for every employee data source (JSON file today, an ORM later).

    Services depend only on this class, so swapping storage never changes business logic.
    """

    @abstractmethod
    def get_by_id(self, employee_id: str) -> EmployeeInfo | None:
        """Return the employee with this ID, or None if there isn't one.

        Args:
            employee_id: The ID to look up, e.g. "E001".

        Returns:
            The matching EmployeeInfo, or None.
        """
        ...
