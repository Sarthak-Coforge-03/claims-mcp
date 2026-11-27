"""EligibilityService: decides whether a request is within policy (docs/requirements.md section 5).

It combines the employee's equipment on file with their role's item policy and today's date.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

from claims_mcp.backend.models.catalog_item import CatalogItem
from claims_mcp.backend.models.eligibility_result import EligibilityResult
from claims_mcp.backend.models.eligibility_rule import EligibilityRule
from claims_mcp.backend.models.employee_info import EmployeeInfo
from claims_mcp.backend.models.item_policy import ItemPolicy
from claims_mcp.backend.services.employee_service import EmployeeService
from claims_mcp.backend.services.policy_service import PolicyService

CATALOG_ITEM_NAMES = {catalog_item.value for catalog_item in CatalogItem}


class EligibilityService:
    """Checks one employee's request for one item against their role's policy.

    Built once at server startup and reused; it holds no per-request state.
    """

    def __init__(self, employee_service: EmployeeService, policy_service: PolicyService) -> None:
        """Keep the services this check reads employees and role policies from.

        Args:
            employee_service: Looks up the employee's role and equipment on file.
            policy_service: Looks up what the employee's role may hold and how often.
        """
        self.employee_service = employee_service
        self.policy_service = policy_service

    def check_request_eligibility(self, employee_id: str, item: str) -> EligibilityResult | None:
        """Return whether the employee may get the item now, and which rule decided it.

        Args:
            employee_id: The employee's ID, e.g. "E001".
            item: The requested item, e.g. "laptop"; may be something outside the catalog.

        Returns:
            An EligibilityResult (rule ELG-1/2/3, DEN-2 or ESC-2), or None for an unknown employee.
        """
        employee = self.employee_service.get_employee_info(employee_id)
        if employee is None:
            return None

        if item not in CATALOG_ITEM_NAMES:
            return build_unassessable_result(employee, item, EligibilityRule.ESC_2)

        item_policy = self.find_item_policy(employee, item)
        if item_policy is None:
            return build_unassessable_result(employee, item, EligibilityRule.DEN_2)

        return check_against_item_policy(employee, item, item_policy)

    def find_item_policy(self, employee: EmployeeInfo, item: str) -> ItemPolicy | None:
        """Return the employee's role policy for the item, or None if the role isn't entitled.

        Args:
            employee: The employee whose role is looked up.
            item: A catalog item name, e.g. "laptop".

        Returns:
            The matching ItemPolicy, or None.
        """
        role_policy = self.policy_service.get_policy_limits(employee.role)
        if role_policy is None:
            return None
        return role_policy.get_item_policy(item)


def build_unassessable_result(
    employee: EmployeeInfo, item: str, rule_id: EligibilityRule
) -> EligibilityResult:
    """Return a not-eligible result for an item that has no policy to apply (ESC-2 or DEN-2).

    Args:
        employee: The requesting employee.
        item: The requested item.
        rule_id: EligibilityRule.ESC_2 (not in catalog) or EligibilityRule.DEN_2 (not entitled).

    Returns:
        An EligibilityResult with is_eligible False and all policy fields (incl. POL ID) None.
    """
    return EligibilityResult(
        employee_id=employee.employee_id,
        item=item,
        is_eligible=False,
        rule_id=rule_id,
        policy_rule_id=None,
        held_count=count_items_held(employee, item),
        max_held=None,
        refresh_interval_months=None,
        newest_issued_date=None,
        eligible_from_date=None,
    )


def check_against_item_policy(
    employee: EmployeeInfo, item: str, item_policy: ItemPolicy
) -> EligibilityResult:
    """Apply ELG-1, ELG-2 and ELG-3 for an item the employee's role is entitled to.

    Args:
        employee: The requesting employee.
        item: The requested catalog item.
        item_policy: The role's limit and refresh interval for that item.

    Returns:
        An EligibilityResult: ELG-1 (below max), ELG-2 (replacement due) or ELG-3 (too soon).
    """
    held_count = count_items_held(employee, item)
    newest_issued_date = find_newest_issued_date(employee, item)

    if held_count < item_policy.max_held:
        return EligibilityResult(
            employee_id=employee.employee_id,
            item=item,
            is_eligible=True,
            rule_id=EligibilityRule.ELG_1,
            policy_rule_id=item_policy.policy_rule_id,
            held_count=held_count,
            max_held=item_policy.max_held,
            refresh_interval_months=item_policy.refresh_interval_months,
            newest_issued_date=newest_issued_date,
            eligible_from_date=None,
        )

    eligible_from_date = newest_issued_date + relativedelta(
        months=item_policy.refresh_interval_months
    )
    replacement_is_due = date.today() >= eligible_from_date
    return EligibilityResult(
        employee_id=employee.employee_id,
        item=item,
        is_eligible=replacement_is_due,
        rule_id=EligibilityRule.ELG_2 if replacement_is_due else EligibilityRule.ELG_3,
        policy_rule_id=item_policy.policy_rule_id,
        held_count=held_count,
        max_held=item_policy.max_held,
        refresh_interval_months=item_policy.refresh_interval_months,
        newest_issued_date=newest_issued_date,
        eligible_from_date=eligible_from_date,
    )


def count_items_held(employee: EmployeeInfo, item: str) -> int:
    """Return how many units of the item the employee currently has on file.

    Args:
        employee: The employee whose equipment is counted.
        item: The item name to count, e.g. "monitor".

    Returns:
        The number of matching equipment entries (0 if none).
    """
    matching_equipment = [equipment for equipment in employee.equipment if equipment.item == item]
    return len(matching_equipment)


def find_newest_issued_date(employee: EmployeeInfo, item: str) -> date | None:
    """Return the most recent issue date among the employee's units of the item.

    Args:
        employee: The employee whose equipment is searched.
        item: The item name, e.g. "laptop".

    Returns:
        The latest issued_date for that item, or None if the employee holds none.
    """
    issued_dates = [
        equipment.issued_date for equipment in employee.equipment if equipment.item == item
    ]
    if not issued_dates:
        return None
    return max(issued_dates)
