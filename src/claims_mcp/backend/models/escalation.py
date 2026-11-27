"""Escalation: a request flagged for a human reviewer; what flag_for_human_review returns."""

from datetime import datetime

from pydantic import BaseModel, Field

from claims_mcp.backend.models.escalation_status import EscalationStatus


class Escalation(BaseModel):
    """One escalated equipment request, saved so a human reviewer can decide it.

    request and reason must be non-empty: a reviewer always needs to know what and why.
    """

    escalation_id: str
    employee_id: str
    request: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    created_at: datetime
    status: EscalationStatus
