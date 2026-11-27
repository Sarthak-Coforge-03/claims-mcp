"""Unit tests for PolicyService, backed by an in-memory policy repository instead of files."""

from claims_mcp.backend.models.item_policy import ItemPolicy
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.repositories.in_memory_policy_repository import InMemoryPolicyRepository
from claims_mcp.backend.services.policy_service import PolicyService


def build_manager_role_policy() -> RolePolicy:
    """Return a manager policy with one rule: a phone, max 1, every 24 months."""
    return RolePolicy(
        role="manager",
        item_policies=[ItemPolicy(item="phone", max_held=1, refresh_interval_months=24)],
    )


def test_get_policy_limits_known_role_returns_that_policy():
    """Asking for "manager" returns exactly the manager policy stored in the repository."""
    manager_policy = build_manager_role_policy()
    policy_service = PolicyService(InMemoryPolicyRepository([manager_policy]))

    role_policy = policy_service.get_policy_limits("manager")

    assert role_policy == manager_policy


def test_get_policy_limits_unknown_role_returns_none():
    """Asking for a role with no policy ("intern") returns None instead of raising."""
    policy_service = PolicyService(InMemoryPolicyRepository([build_manager_role_policy()]))

    role_policy = policy_service.get_policy_limits("intern")

    assert role_policy is None
