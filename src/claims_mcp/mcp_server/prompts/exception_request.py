"""Template for a request that claims damage, loss or a need (requirements scenario 7)."""

from datetime import date

from claims_mcp.mcp_server.prompts.shared_steps import build_template

EXCEPTION_STEPS = """Then, for a claimed exception:
- Call check_request_eligibility(employee_id, item).
- rule_id ELG-3 (too soon): escalate with ESC-5, quoting the claim from the reason.
- rule_id ELG-1 or ELG-2: approve, citing the rule and policy_rule_id; the claim doesn't matter."""


def build_exception_request_prompt(
    employee_id: str, item: str, reason: str, quantity: str, today: date
) -> str:
    """Return the exception template filled in for one request.

    Args:
        employee_id: The requesting employee's ID, e.g. "E002".
        item: The requested item, e.g. "laptop".
        reason: The claimed exception, e.g. "screen cracked".
        quantity: How many units are requested, as text, e.g. "1".
        today: The date the request is handled.

    Returns:
        The template text: the request, the opening checks and the exception steps.
    """
    return build_template(EXCEPTION_STEPS, employee_id, item, reason, quantity, today)
