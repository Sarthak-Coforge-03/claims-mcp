"""EligibilityResult: what check_request_eligibility returns (docs/requirements.md section 7)."""

from datetime import date

from pydantic import BaseModel

from claims_mcp.backend.models.eligibility_rule import EligibilityRule


class EligibilityResult(BaseModel):
    """Whether an employee may get an item now, which rule decided it, and the facts behind it.

    Policy fields are None when no policy applies (ESC-2 not in catalog, DEN-2 not entitled).
    """

    employee_id: str
    item: str
    is_eligible: bool
    rule_id: EligibilityRule
    policy_rule_id: str | None  # the POL-* row applied (cited on approval), None if no policy
    held_count: int
    max_held: int | None
    refresh_interval_months: int | None
    newest_issued_date: date | None
    eligible_from_date: date | None
