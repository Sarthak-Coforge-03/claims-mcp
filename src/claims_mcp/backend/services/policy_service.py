"""PolicyService: role policy lookups, independent of where policies are stored."""

from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.repositories.base.policy_repository_base import PolicyRepositoryBase


class PolicyService:
    """Answers "what is this role eligible for, and how often?" using whatever repository it gets.

    Built once at server startup and reused; it holds no per-request state.
    """

    def __init__(self, policy_repository: PolicyRepositoryBase) -> None:
        """Keep the repository this service reads role policies from.

        Args:
            policy_repository: Any policy repository (JSON now, SQL later, in-memory in tests).
        """
        self.policy_repository = policy_repository

    def get_policy_limits(self, role: str) -> RolePolicy | None:
        """Return the items a role may hold, how many, and their refresh intervals, or None.

        Args:
            role: The role name, e.g. "manager".

        Returns:
            The role's RolePolicy (an empty item list means no entitlements), or None if unknown.
        """
        return self.policy_repository.get_by_role(role)
