"""Unit tests for JsonPolicyRepository, the temporary JSON-file storage for role policies."""

import json

import pytest

from claims_mcp.backend.repositories.json.json_policy_repository import JsonPolicyRepository


@pytest.fixture
def two_role_policies_file(tmp_path):
    """Write a temporary policies file: standard (monitor 1/36) and manager (laptop 1/24)."""
    policies_file = tmp_path / "policies.json"
    policies_file.write_text(
        json.dumps(
            {
                "role_policies": [
                    {
                        "role": "standard",
                        "item_policies": [
                            {
                                "policy_rule_id": "POL-STD-MONITOR",
                                "item": "monitor",
                                "max_held": 1,
                                "refresh_interval_months": 36,
                            }
                        ],
                    },
                    {
                        "role": "manager",
                        "item_policies": [
                            {
                                "policy_rule_id": "POL-MGR-LAPTOP",
                                "item": "laptop",
                                "max_held": 1,
                                "refresh_interval_months": 24,
                            }
                        ],
                    },
                ]
            }
        )
    )
    return policies_file


def test_json_policy_repository_known_role_returns_its_policy(two_role_policies_file):
    """Looking up "standard" returns its policy, whose monitor rule is every 36 months."""
    policy_repository = JsonPolicyRepository(two_role_policies_file)

    role_policy = policy_repository.get_by_role("standard")

    assert role_policy.get_item_policy("monitor").refresh_interval_months == 36


def test_json_policy_repository_unknown_role_returns_none(two_role_policies_file):
    """A role that isn't in the file ("intern") returns None instead of raising."""
    policy_repository = JsonPolicyRepository(two_role_policies_file)

    role_policy = policy_repository.get_by_role("intern")

    assert role_policy is None
