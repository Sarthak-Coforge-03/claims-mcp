"""The parts every scenario template shares: the request block and the opening checks.

The opening checks exist because no tool result flags a contractor (ESC-3) or a probation hire
(ESC-4); the agent must read role and hire_date itself, whichever scenario it picked.
"""

from datetime import date

PROBATION_DAYS = 90

# The template was picked from the request's wording, so the tool results can still disagree.
UNMATCHED_RESULT_STEP = """If a tool result fits none of the steps above, this template doesn't fit
the request: decide from the tool results instead, and escalate if unsure."""


def build_request_block(
    employee_id: str, item: str, reason: str, quantity: str, today: date
) -> str:
    """Return the request the template was filled in for, plus today's date for the ESC-4 check.

    Args:
        employee_id: The requesting employee's ID, e.g. "E001".
        item: The requested item, e.g. "monitor".
        reason: The employee's reason, quoted as given.
        quantity: How many units are requested, as text, e.g. "1".
        today: The date the request is handled, written as YYYY-MM-DD.

    Returns:
        Plain text: a "Request" block with one line per field.
    """
    return f"""Request
- Employee ID: {employee_id}
- Item: {item}
- Quantity: {quantity}
- Reason given: {reason}
- Today: {today.isoformat()}"""


def build_opening_checks(employee_id: str, today: date) -> str:
    """Return the checks that run first in every template: ESC-1, ESC-3 and ESC-4.

    Args:
        employee_id: The requesting employee's ID, e.g. "E001".
        today: The date the request is handled, used for the probation check.

    Returns:
        Plain text: the opening checks as bullets, ending with how to escalate.
    """
    return f"""First, for every request:
- Call get_employee_info("{employee_id}"). If it returns an error, escalate with ESC-1.
- If role is contractor, escalate with ESC-3.
- If hire_date is less than {PROBATION_DAYS} days before {today.isoformat()}, escalate with ESC-4.

To escalate, call flag_for_human_review(employee_id, request, reason) once, with the rule ID first
in reason (e.g. "ESC-3: contractor"), then stop."""


def build_template(
    scenario_steps: str, employee_id: str, item: str, reason: str, quantity: str, today: date
) -> str:
    """Return a full template: the request, the opening checks, the scenario's steps, a fallback.

    Args:
        scenario_steps: The scenario's title and steps, placed after the opening checks.
        employee_id: The requesting employee's ID, e.g. "E001".
        item: The requested item, e.g. "monitor".
        reason: The employee's reason for the request.
        quantity: How many units are requested, as text, e.g. "1".
        today: The date the request is handled.

    Returns:
        The four blocks joined by blank lines, as one string.
    """
    request_block = build_request_block(employee_id, item, reason, quantity, today)
    opening_checks = build_opening_checks(employee_id, today)
    return f"{request_block}\n\n{opening_checks}\n\n{scenario_steps}\n\n{UNMATCHED_RESULT_STEP}"
