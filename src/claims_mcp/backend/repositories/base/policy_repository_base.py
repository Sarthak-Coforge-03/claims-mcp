"""PolicyRepositoryBase: the interface every role-policy data source implements."""

from abc import ABC, abstractmethod

from claims_mcp.backend.models.role_policy import RolePolicy


class PolicyRepositoryBase(ABC):
    """Base for every role-policy data source (JSON file today, optionally SQL later).

    Services depend only on this class, so swapping storage never changes business logic.
    """

    @abstractmethod
    def get_by_role(self, role: str) -> RolePolicy | None:
        """Return the policy for this role, or None if the role has no policy.

        Args:
            role: The role name, e.g. "manager".

        Returns:
            The matching RolePolicy, or None.
        """
        ...
