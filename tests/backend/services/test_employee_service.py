"""Unit tests for EmployeeService, backed by an in-memory repository instead of real storage."""

from datetime import date

from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.equipment_item import EquipmentItem
from claims_mcp.backend.services.employee_service import EmployeeService
from fakes.in_memory_employee_repository import InMemoryEmployeeRepository


def build_test_employee() -> EmployeeInfo:
    """Return employee E100 (standard, hired 2020-06-15, one laptop) for service tests."""
    return EmployeeInfo(
        employee_id="E100",
        name="Test Person",
        role="standard",
        hire_date=date(2020, 6, 15),
        equipment=[EquipmentItem(item="laptop", issued_date=date(2021, 1, 10))],
    )


def test_get_employee_info_known_id_returns_that_employee():
    """A known ID (E100) returns exactly that employee's record from the repository."""
    test_employee = build_test_employee()
    employee_service = EmployeeService(InMemoryEmployeeRepository([test_employee]))

    employee = employee_service.get_employee_info("E100")

    assert employee == test_employee


def test_get_employee_info_unknown_id_returns_none():
    """An ID the repository doesn't have (E999) returns None instead of raising."""
    employee_service = EmployeeService(InMemoryEmployeeRepository([build_test_employee()]))

    employee = employee_service.get_employee_info("E999")

    assert employee is None
