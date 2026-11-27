"""EscalationService: flags requests for human review and records them for reviewers."""

from datetime import UTC, datetime
from uuid import uuid4

from claims_mcp.backend.models.escalation import Escalation
from claims_mcp.backend.models.escalation_status import EscalationStatus
from claims_mcp.backend.repositories.base.escalation_repository_base import (
    EscalationRepositoryBase,
)


class EscalationService:
    """Creates escalation records; the side effect behind flag_for_human_review.

    It deliberately doesn't check that the employee exists: an unknown ID is itself a reason to
    escalate (rule ESC-1), so that case must still reach a human.
    """

    def __init__(self, escalation_repository: EscalationRepositoryBase) -> None:
        """Keep the repository escalations are saved to.

        Args:
            escalation_repository: Any escalation store (JSON now, in-memory in tests).
        """
        self.escalation_repository = escalation_repository

    def flag_for_human_review(self, employee_id: str, request: str, reason: str) -> Escalation:
        """Create a pending escalation for a request, save it, and return the saved record.

        Args:
            employee_id: The requesting employee's ID, e.g. "E005" (may be unknown, see ESC-1).
            request: What was asked for, e.g. "monitor".
            reason: Why a human must decide, citing the rule, e.g. "ESC-4: in probation".

        Returns:
            The stored Escalation with a new escalation_id, created_at (UTC) and pending status.

        Raises:
            pydantic.ValidationError: If request or reason is empty.
        """
        escalation = Escalation(
            escalation_id=str(uuid4()),
            employee_id=employee_id,
            request=request,
            reason=reason,
            created_at=datetime.now(UTC),
            status=EscalationStatus.PENDING_REVIEW,
        )
        self.escalation_repository.add(escalation)
        return escalation
