"""Unit tests for the RolePolicy / ItemPolicy models and the by-item policy lookup."""

import pytest
from pydantic import ValidationError

from claims_mcp.backend.models.role_policy import RolePolicy


def build_standard_role_policy_record() -> dict:
    """Return a raw standard-role policy: laptop (max 1, every 48 months), monitor (1, 36)."""
    return {
        "role": "standard",
        "item_policies": [
            {
                "policy_rule_id": "POL-STD-LAPTOP",
                "item": "laptop",
                "max_held": 1,
                "refresh_interval_months": 48,
            },
            {
                "policy_rule_id": "POL-STD-MONITOR",
                "item": "monitor",
                "max_held": 1,
                "refresh_interval_months": 36,
            },
        ],
    }


def test_role_policy_valid_record_parses_role():
    """A valid standard-role record parses, keeping role "standard"."""
    raw_role_policy = build_standard_role_policy_record()

    role_policy = RolePolicy.model_validate(raw_role_policy)

    assert role_policy.role == "standard"


def test_role_policy_zero_max_held_is_rejected():
    """An item policy with max_held=0 is invalid; "not entitled" means leaving the item out."""
    raw_role_policy = {
        "role": "standard",
        "item_policies": [
            {
                "policy_rule_id": "POL-STD-LAPTOP",
                "item": "laptop",
                "max_held": 0,
                "refresh_interval_months": 48,
            }
        ],
    }

    with pytest.raises(ValidationError):
        RolePolicy.model_validate(raw_role_policy)


def test_get_item_policy_entitled_item_returns_its_policy():
    """Looking up "monitor" on the standard policy returns the monitor rule (every 36 months)."""
    role_policy = RolePolicy.model_validate(build_standard_role_policy_record())

    monitor_policy = role_policy.get_item_policy("monitor")

    assert monitor_policy.refresh_interval_months == 36


def test_get_item_policy_item_not_entitled_returns_none():
    """Looking up "phone" on the standard policy returns None: the role isn't entitled to it."""
    role_policy = RolePolicy.model_validate(build_standard_role_policy_record())

    phone_policy = role_policy.get_item_policy("phone")

    assert phone_policy is None
