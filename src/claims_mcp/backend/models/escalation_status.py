"""EscalationStatus: where an escalated request is in the human review process."""

from enum import StrEnum


class EscalationStatus(StrEnum):
    """Review state of an escalation; every new escalation starts as pending_review.

    Reviewer outcomes (e.g. approved, rejected) can be added later as new members.
    """

    PENDING_REVIEW = "pending_review"
