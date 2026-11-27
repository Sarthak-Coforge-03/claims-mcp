"""Unit tests for EscalationService, backed by an in-memory escalation repository."""

from claims_mcp.backend.models.escalation_status import EscalationStatus
from claims_mcp.backend.services.escalation_service import EscalationService
from fakes.in_memory_escalation_repository import InMemoryEscalationRepository


def test_flag_for_human_review_returns_pending_escalation():
    """Flagging E100's monitor request (ESC-4) returns an escalation waiting for review."""
    escalation_service = EscalationService(InMemoryEscalationRepository())

    escalation = escalation_service.flag_for_human_review(
        "E100", "monitor", "ESC-4: hired less than 90 days ago"
    )

    assert escalation.status == EscalationStatus.PENDING_REVIEW


def test_flag_for_human_review_saves_escalation_for_reviewers():
    """The side effect: the flagged escalation is stored, so the repository now lists its ID."""
    escalation_repository = InMemoryEscalationRepository()
    escalation_service = EscalationService(escalation_repository)

    escalation = escalation_service.flag_for_human_review(
        "E100", "monitor", "ESC-4: hired less than 90 days ago"
    )

    saved_escalation_ids = [
        saved_escalation.escalation_id for saved_escalation in escalation_repository.list_all()
    ]
    assert saved_escalation_ids == [escalation.escalation_id]
