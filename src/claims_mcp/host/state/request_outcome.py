"""RequestOutcome: what was decided for the employee's request."""

from enum import StrEnum


class RequestOutcome(StrEnum):
    """approve or deny under the rules, or escalate to a human reviewer."""

    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"
