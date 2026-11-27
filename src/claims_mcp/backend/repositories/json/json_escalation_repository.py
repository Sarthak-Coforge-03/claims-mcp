"""JsonEscalationRepository: stores escalations in a JSON file (path set in claims_mcp.settings)."""

import json
from pathlib import Path

from claims_mcp.backend.models.escalation import Escalation
from claims_mcp.backend.repositories.base.escalation_repository_base import (
    EscalationRepositoryBase,
)


class JsonEscalationRepository(EscalationRepositoryBase):
    """Keeps escalations in a JSON file of the form {"escalations": [record, ...]}.

    The file is created on the first add; every add reads it, appends and writes it back.
    """

    def __init__(self, escalations_file: Path) -> None:
        """Remember which file escalations are stored in.

        Args:
            escalations_file: Path to the JSON file; it doesn't need to exist yet.
        """
        self.escalations_file = escalations_file

    def add(self, escalation: Escalation) -> None:
        """Append one escalation to the file, keeping every escalation already stored.

        Args:
            escalation: The escalation to store.
        """
        escalation_records = [
            stored_escalation.model_dump(mode="json") for stored_escalation in self.list_all()
        ]
        escalation_records.append(escalation.model_dump(mode="json"))

        self.escalations_file.parent.mkdir(parents=True, exist_ok=True)
        self.escalations_file.write_text(
            json.dumps({"escalations": escalation_records}, indent=2), encoding="utf-8"
        )

    def list_all(self) -> list[Escalation]:
        """Return every escalation in the file, oldest first.

        Returns:
            All stored escalations as validated models; empty if the file doesn't exist yet.
        """
        if not self.escalations_file.exists():
            return []
        escalation_data = json.loads(self.escalations_file.read_text(encoding="utf-8"))
        return [
            Escalation.model_validate(escalation_record)
            for escalation_record in escalation_data["escalations"]
        ]
