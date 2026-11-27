"""Template for replacing an item the employee already holds (requirements scenarios 1, 2, 4)."""

from datetime import date

from claims_mcp.mcp_server.prompts.shared_steps import build_template

REPLACEMENT_STEPS = """Then, for a replacement:
4. Call check_request_eligibility(employee_id, item).
5. rule_id ELG-2 (replacement due): approve, citing ELG-2 and policy_rule_id.
6. rule_id ELG-3 (too soon): deny with DEN-1 and state eligible_from_date. "Old" or "slow" is not
   damage, so it is no reason to escalate."""


def build_replacement_request_prompt(
    employee_id: str, item: str, reason: str, quantity: str, today: date
) -> str:
    """Return the replacement template filled in for one request.

    Args:
        employee_id: The requesting employee's ID, e.g. "E001".
        item: The item to replace, e.g. "monitor".
        reason: The employee's reason, e.g. "my monitor is old".
        quantity: How many units are requested, as text, e.g. "1".
        today: The date the request is handled.

    Returns:
        The template text: the request, the opening checks and the replacement steps.
    """
    return build_template(REPLACEMENT_STEPS, employee_id, item, reason, quantity, today)
