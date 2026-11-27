"""Unit tests for the Escalation model: what a saved escalation record accepts and rejects."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from claims_mcp.backend.models.escalation import Escalation


def test_escalation_blank_reason_is_rejected():
    """An escalation with an empty reason ("") is invalid: a reviewer must always see why."""
    raw_escalation = {
        "escalation_id": "test-escalation-1",
        "employee_id": "E100",
        "request": "monitor",
        "reason": "",
        "created_at": datetime(2026, 1, 5, 9, 0, tzinfo=UTC),
        "status": "pending_review",
    }

    with pytest.raises(ValidationError):
        Escalation.model_validate(raw_escalation)
