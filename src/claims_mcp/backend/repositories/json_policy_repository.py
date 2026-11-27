"""JsonPolicyRepository: reads role policies from data/policies.json."""

import json
from pathlib import Path

from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.repositories.policy_repository_base import PolicyRepositoryBase

# data/ sits at the repository root. Going up from this file:
#   parents[0] repositories/ → [1] backend/ → [2] claims_mcp/ → [3] src/ → [4] repository root
DEFAULT_POLICIES_FILE = Path(__file__).resolve().parents[4] / "data" / "policies.json"


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
