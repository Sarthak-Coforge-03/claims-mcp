"""Unit tests for JsonEscalationRepository, the first repository that writes to its JSON file."""

from datetime import UTC, datetime

from claims_mcp.backend.models.escalation import Escalation
from claims_mcp.backend.models.escalation_status import EscalationStatus
from claims_mcp.backend.repositories.json.json_escalation_repository import (
    JsonEscalationRepository,
)


def build_escalation(escalation_id: str) -> Escalation:
    """Return a pending escalation for E100 (monitor, reason ESC-4) with the given ID.

    Args:
        escalation_id: The ID to give the escalation, e.g. "test-escalation-1".

    Returns:
        A valid Escalation record.
    """
    return Escalation(
        escalation_id=escalation_id,
        employee_id="E100",
        request="monitor",
        reason="ESC-4: hired less than 90 days ago",
        created_at=datetime(2026, 1, 5, 9, 0, tzinfo=UTC),
        status=EscalationStatus.PENDING_REVIEW,
    )


def test_json_escalation_repository_add_to_missing_file_saves_record(tmp_path):
    """Adding to a file that doesn't exist yet creates it, and the record can be read back."""
    escalations_file = tmp_path / "escalations.json"
    escalation_repository = JsonEscalationRepository(escalations_file)
    first_escalation = build_escalation("test-escalation-1")

    escalation_repository.add(first_escalation)

    assert escalation_repository.list_all() == [first_escalation]


def test_json_escalation_repository_second_add_appends_instead_of_overwriting(tmp_path):
    """Two adds keep both records in order: the second escalation must not replace the first."""
    escalation_repository = JsonEscalationRepository(tmp_path / "escalations.json")
    escalation_repository.add(build_escalation("test-escalation-1"))

    escalation_repository.add(build_escalation("test-escalation-2"))

    saved_escalation_ids = [
        escalation.escalation_id for escalation in escalation_repository.list_all()
    ]
    assert saved_escalation_ids == ["test-escalation-1", "test-escalation-2"]
