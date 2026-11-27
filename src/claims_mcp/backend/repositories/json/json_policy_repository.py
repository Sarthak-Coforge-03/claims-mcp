"""JsonPolicyRepository: reads role policies from a JSON file (path set in claims_mcp.settings)."""

import json
from pathlib import Path

from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.repositories.base.policy_repository_base import PolicyRepositoryBase


class JsonPolicyRepository(PolicyRepositoryBase):
    """Reads role policies from a JSON file shaped like data/policies.json."""

    def __init__(self, policies_file: Path) -> None:
        """Remember which file to read; it is read again on every lookup.

        Args:
            policies_file: Path to a JSON file of the form {"role_policies": [record, ...]}.
        """
        self.policies_file = policies_file

    def get_by_role(self, role: str) -> RolePolicy | None:
        """Find the policy record for this role in the file and return it as a validated model.

        Args:
            role: The role name, e.g. "manager".

        Returns:
            The matching record as a RolePolicy, or None if no record has that role.
        """
        policy_data = json.loads(self.policies_file.read_text(encoding="utf-8"))
        for role_policy_record in policy_data["role_policies"]:
            if role_policy_record["role"] == role:
                return RolePolicy.model_validate(role_policy_record)
        return None
