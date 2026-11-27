"""Unit tests for EligibilityService: the ELG / DEN-2 / ESC-2 rules from docs/requirements.md.

Data is built in code with in-memory fakes, and every date is relative to date.today(), so the
tests hold whenever they run. Policy used throughout: standard role, laptop max 1 every 48 months.
"""

from datetime import date

from claims_mcp.backend.models.eligibility_result import EligibilityResult
from claims_mcp.backend.models.eligibility_rule import EligibilityRule
from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.equipment_item import EquipmentItem
from claims_mcp.backend.models.item_policy import ItemPolicy
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.services.eligibility_service import EligibilityService
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.backend.services.policy_service import PolicyService
from fakes.in_memory_employee_repository import InMemoryEmployeeRepository
from fakes.in_memory_policy_repository import InMemoryPolicyRepository

STANDARD_LAPTOP_REFRESH_MONTHS = 48


def years_before_today(years: int) -> date:
    """Return the same calendar day `years` ago (Feb 29 becomes Feb 28 in a non-leap year).

    Built with date.replace, not relativedelta, so expected dates aren't computed the same way
    as the code under test.

    Args:
        years: How many whole years to go back.

    Returns:
        The date `years` years before today.
    """
    today = date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, day=28)


def build_eligibility_service(
    laptops_issued_on: list[date], employee_role: str = "standard"
) -> EligibilityService:
    """Build a service with employee E100 holding one laptop per given date (standard policy only).

    Args:
        laptops_issued_on: Issue dates of the laptops E100 holds; empty for none.
        employee_role: E100's role; anything but "standard" has no policy in this data.

    Returns:
        An EligibilityService over in-memory employee and policy data.
    """
    test_employee = EmployeeInfo(
        employee_id="E100",
        name="Test Person",
        role=employee_role,
        hire_date=date(2015, 1, 5),
        equipment=[
            EquipmentItem(item="laptop", issued_date=issued_date)
            for issued_date in laptops_issued_on
        ],
    )
    standard_policy = RolePolicy(
        role="standard",
        item_policies=[
            ItemPolicy(
                item="laptop",
                max_held=1,
                refresh_interval_months=STANDARD_LAPTOP_REFRESH_MONTHS,
            )
        ],
    )
    employee_service = EmployeeService(InMemoryEmployeeRepository([test_employee]))
    policy_service = PolicyService(InMemoryPolicyRepository([standard_policy]))
    return EligibilityService(employee_service, policy_service)


def test_check_eligibility_holds_none_returns_elg_1():
    """E100 holds no laptop and may hold 1, so a laptop request is eligible under ELG-1."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[])

    eligibility = eligibility_service.check_request_eligibility("E100", "laptop")

    assert eligibility.rule_id == EligibilityRule.ELG_1


def test_check_eligibility_laptop_older_than_interval_returns_elg_2():
    """A laptop issued 5 years ago is past the 48-month interval, so replacing it is ELG-2."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[years_before_today(5)])

    eligibility = eligibility_service.check_request_eligibility("E100", "laptop")

    assert eligibility.rule_id == EligibilityRule.ELG_2


def test_check_eligibility_laptop_exactly_on_anniversary_returns_elg_2():
    """A laptop issued exactly 4 years ago today has reached 48 months: the anniversary counts."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[years_before_today(4)])

    eligibility = eligibility_service.check_request_eligibility("E100", "laptop")

    assert eligibility.rule_id == EligibilityRule.ELG_2


def test_check_eligibility_laptop_too_recent_returns_elg_3_with_eligible_from_date():
    """A laptop issued 1 year ago is too recent: ELG-3, eligible again 4 years after issue."""
    issued_date = years_before_today(1)
    eligibility_service = build_eligibility_service(laptops_issued_on=[issued_date])

    eligibility = eligibility_service.check_request_eligibility("E100", "laptop")

    assert eligibility == EligibilityResult(
        employee_id="E100",
        item="laptop",
        is_eligible=False,
        rule_id=EligibilityRule.ELG_3,
        held_count=1,
        max_held=1,
        refresh_interval_months=STANDARD_LAPTOP_REFRESH_MONTHS,
        newest_issued_date=issued_date,
        eligible_from_date=issued_date.replace(year=issued_date.year + 4),
    )


def test_check_eligibility_item_not_entitled_returns_den_2():
    """The standard policy has no phone entry, so a phone request is not entitled: DEN-2."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[])

    eligibility = eligibility_service.check_request_eligibility("E100", "phone")

    assert eligibility.rule_id == EligibilityRule.DEN_2


def test_check_eligibility_role_without_any_policy_returns_den_2():
    """A manager when only "standard" has a policy: no rule to apply, so not entitled (DEN-2)."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[], employee_role="manager")

    eligibility = eligibility_service.check_request_eligibility("E100", "laptop")

    assert eligibility.rule_id == EligibilityRule.DEN_2


def test_check_eligibility_item_not_in_catalog_returns_esc_2():
    """A "standing_desk" isn't a catalog item, so it can't be assessed and needs a human: ESC-2."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[])

    eligibility = eligibility_service.check_request_eligibility("E100", "standing_desk")

    assert eligibility.rule_id == EligibilityRule.ESC_2


def test_check_eligibility_unknown_employee_returns_none():
    """An employee ID that doesn't exist (E999) returns None instead of a result."""
    eligibility_service = build_eligibility_service(laptops_issued_on=[])

    eligibility = eligibility_service.check_request_eligibility("E999", "laptop")

    assert eligibility is None
