"""InMemoryPolicyRepository: serves role policies from a list in memory (tests, quick dev runs)."""

from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.repositories.base.policy_repository_base import PolicyRepositoryBase


class InMemoryPolicyRepository(PolicyRepositoryBase):
    """Holds role policies in a dict keyed by role; no files or database involved."""

    def __init__(self, role_policies: list[RolePolicy]) -> None:
        """Store the given role policies, keyed by role.

        Args:
            role_policies: The role policies this repository should serve.
        """
        self.role_policy_by_role = {role_policy.role: role_policy for role_policy in role_policies}

    def get_by_role(self, role: str) -> RolePolicy | None:
        """Return the stored policy for this role, or None if it isn't stored.

        Args:
            role: The role name, e.g. "manager".

        Returns:
            The matching RolePolicy, or None.
        """
        return self.role_policy_by_role.get(role)
