"""InMemoryEscalationRepository: keeps escalations in a list in memory (test double)."""

from claims_mcp.backend.models.escalation import Escalation
from claims_mcp.backend.repositories.base.escalation_repository_base import (
    EscalationRepositoryBase,
)


class InMemoryEscalationRepository(EscalationRepositoryBase):
    """Stores escalations in a plain list; no files involved."""

    def __init__(self) -> None:
        """Start with no stored escalations."""
        self.escalations: list[Escalation] = []

    def add(self, escalation: Escalation) -> None:
        """Append the escalation to the in-memory list.

        Args:
            escalation: The escalation to store.
        """
        self.escalations.append(escalation)

    def list_all(self) -> list[Escalation]:
        """Return a copy of every stored escalation, oldest first.

        Returns:
            All escalations added so far.
        """
        return list(self.escalations)
