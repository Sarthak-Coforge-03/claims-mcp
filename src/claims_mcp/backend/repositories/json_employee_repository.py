"""JsonEmployeeRepository: reads employees from data/employees.json (temporary until the ORM)."""

import json
from pathlib import Path

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.repositories.employee_repository_base import EmployeeRepositoryBase

# data/ sits at the repository root. Going up from this file:
#   parents[0] repositories/ → [1] backend/ → [2] claims_mcp/ → [3] src/ → [4] repository root
DEFAULT_EMPLOYEES_FILE = Path(__file__).resolve().parents[4] / "data" / "employees.json"


class JsonEmployeeRepository(EmployeeRepositoryBase):
    """Reads employees from a JSON file shaped like data/employees.json."""

    def __init__(self, employees_file: Path) -> None:
        """Remember which file to read; it is read again on every lookup.

        Args:
            employees_file: Path to a JSON file of the form {"employees": [record, ...]}.
        """
        self.employees_file = employees_file

    def get_by_id(self, employee_id: str) -> EmployeeInfo | None:
        """Find the record with this ID in the file and return it as a validated model.

        Args:
            employee_id: The ID to look up, e.g. "E001".

        Returns:
            The matching record as an EmployeeInfo, or None if no record has that ID.
        """
        employee_data = json.loads(self.employees_file.read_text(encoding="utf-8"))
        for employee_record in employee_data["employees"]:
            if employee_record["employee_id"] == employee_id:
                return EmployeeInfo.model_validate(employee_record)
        return None
