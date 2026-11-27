"""EscalationRepositoryBase: the interface every escalation store implements."""

from abc import ABC, abstractmethod

from claims_mcp.backend.models.escalation import Escalation


class EscalationRepositoryBase(ABC):
    """Base for every escalation store (JSON file today, optionally SQL later).

    Unlike the employee and policy repositories, this one is written to: escalations are added.
    """

    @abstractmethod
    def add(self, escalation: Escalation) -> None:
        """Save a new escalation so human reviewers can see it.

        Args:
            escalation: The escalation to store.
        """
        ...

    @abstractmethod
    def list_all(self) -> list[Escalation]:
        """Return every stored escalation, oldest first (the reviewers' queue).

        Returns:
            All escalations, in the order they were added; empty if there are none.
        """
        ...
