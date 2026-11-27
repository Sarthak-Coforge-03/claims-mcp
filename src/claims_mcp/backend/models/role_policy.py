"""RolePolicy: everything one role is eligible for; what get_policy_limits returns."""

from pydantic import BaseModel

from claims_mcp.backend.models.employee_info import EmployeeRole
from claims_mcp.backend.models.item_policy import ItemPolicy


class RolePolicy(BaseModel):
    """The item policies for one role; an empty list (contractors) means no entitlements."""

    role: EmployeeRole
    item_policies: list[ItemPolicy]

    def get_item_policy(self, item: str) -> ItemPolicy | None:
        """Return this role's policy for one item, looked up by name rather than list position.

        Args:
            item: The catalog item name, e.g. "laptop".

        Returns:
            The ItemPolicy for that item, or None if the role isn't entitled to it.
        """
        for item_policy in self.item_policies:
            if item_policy.item == item:
                return item_policy
        return None
