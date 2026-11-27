"""Template for an item the employee doesn't hold yet, or several of one (scenarios 3, 5, 9, 10)."""

from datetime import date

from claims_mcp.mcp_server.prompts.shared_steps import build_template

NEW_ITEM_STEPS = """Then, for a new item:
4. Call check_request_eligibility(employee_id, item).
5. rule_id ESC-2 (not in the catalog): escalate with ESC-2.
6. Quantity above max_held: escalate with ESC-6.
7. rule_id DEN-2 (role not entitled): call get_policy_limits for the other roles, then deny with
   DEN-2 and name the role the item is limited to.
8. rule_id ELG-1 (below the limit): approve, citing ELG-1 and policy_rule_id."""


def build_new_item_request_prompt(
    employee_id: str, item: str, reason: str, quantity: str, today: date
) -> str:
    """Return the new-item template filled in for one request.

    Args:
        employee_id: The requesting employee's ID, e.g. "E003".
        item: The requested item, e.g. "phone".
        reason: The employee's reason, e.g. "I travel for client visits".
        quantity: How many units are requested, as text, e.g. "3".
        today: The date the request is handled.

    Returns:
        The template text: the request, the opening checks and the new-item steps.
    """
    return build_template(NEW_ITEM_STEPS, employee_id, item, reason, quantity, today)
