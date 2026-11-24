"""Unit tests for JsonEmployeeRepository, the temporary JSON-file employee storage."""

import json
from datetime import date

import pytest

from claims_mcp.backend.repositories.json_employee_repository import (
    DEFAULT_EMPLOYEES_FILE,
    JsonEmployeeRepository,
)


@pytest.fixture
def single_employee_file(tmp_path):
    """Write a temporary employees JSON file holding only E100 (hired 2020-06-15, no equipment)."""
    employees_file = tmp_path / "employees.json"
    employees_file.write_text(
        json.dumps(
            {
                "employees": [
                    {
                        "employee_id": "E100",
                        "name": "Test Person",
                        "role": "standard",
                        "hire_date": "2020-06-15",
                        "equipment": [],
                    }
                ]
            }
        )
    )
    return employees_file


def test_json_repository_get_by_id_returns_validated_employee(single_employee_file):
    """A record read from JSON comes back validated: hire_date "2020-06-15" becomes a date."""
    employee_repository = JsonEmployeeRepository(single_employee_file)

    employee = employee_repository.get_by_id("E100")

    assert employee.hire_date == date(2020, 6, 15)


def test_json_repository_get_by_id_unknown_id_returns_none(single_employee_file):
    """An ID that isn't in the file (E999) returns None instead of raising."""
    employee_repository = JsonEmployeeRepository(single_employee_file)

    employee = employee_repository.get_by_id("E999")

    assert employee is None


def test_json_repository_reads_real_mock_data():
    """The default file (data/employees.json) is found and its E001 record is valid."""
    employee_repository = JsonEmployeeRepository(DEFAULT_EMPLOYEES_FILE)

    employee = employee_repository.get_by_id("E001")

    assert employee.name == "Priya Sharma"
