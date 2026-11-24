"""Unit tests for the EmployeeInfo model: what it accepts and what it rejects."""

from datetime import date

import pytest
from pydantic import ValidationError

from claims_mcp.backend.models.employee_info import EmployeeInfo


def build_valid_employee_record() -> dict:
    """Return a fresh raw employee record, shaped like the JSON data, that passes validation."""
    return {
        "employee_id": "E100",
        "name": "Test Person",
        "role": "standard",
        "hire_date": "2020-06-15",
        "equipment": [{"item": "laptop", "issued_date": "2021-01-10"}],
    }


def test_employee_info_valid_record_parses_hire_date():
    """A valid record parses, and the ISO hire_date "2020-06-15" becomes a real date."""
    raw_employee_record = build_valid_employee_record()

    employee = EmployeeInfo.model_validate(raw_employee_record)

    assert employee.hire_date == date(2020, 6, 15)


def test_employee_info_unknown_role_is_rejected():
    """A role outside standard/manager/contractor ("intern") fails validation."""
    raw_employee_record = build_valid_employee_record()
    raw_employee_record["role"] = "intern"

    with pytest.raises(ValidationError):
        EmployeeInfo.model_validate(raw_employee_record)


def test_employee_info_missing_hire_date_is_rejected():
    """A record without hire_date fails validation instead of loading half-filled."""
    raw_employee_record = build_valid_employee_record()
    del raw_employee_record["hire_date"]

    with pytest.raises(ValidationError):
        EmployeeInfo.model_validate(raw_employee_record)
