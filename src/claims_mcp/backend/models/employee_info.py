"""The EmployeeInfo model and the roles an employee can have."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from claims_mcp.backend.models.equipment_item import EquipmentItem

EmployeeRole = Literal["standard", "manager", "contractor"]


class EmployeeInfo(BaseModel):
    """An employee's role, hire date and equipment on file.

    Validation rejects unknown roles and missing fields, and parses ISO date strings into dates.
    """

    employee_id: str
    name: str
    role: EmployeeRole
    hire_date: date
    equipment: list[EquipmentItem]
