"""Tests for the get_policy_limits MCP tool, called through the real MCP protocol in-process.

The backend policy service is swapped for an in-memory one, so no test reads the real data files.
"""

import pytest
from mcp import Client

from claims_mcp.backend.models.item_policy import ItemPolicy
from claims_mcp.backend.models.role_policy import RolePolicy
from claims_mcp.backend.services.policy_service import PolicyService
from claims_mcp.mcp_server import server
from claims_mcp.mcp_server.server import mcp
from fakes.in_memory_policy_repository import InMemoryPolicyRepository


@pytest.fixture
def in_memory_policy_service(monkeypatch):
    """Make the tools use an in-memory service: manager (laptop 1/24, phone 1/24), contractor [].

    monkeypatch puts the real get_policy_service back after each test.
    """
    manager_policy = RolePolicy(
        role="manager",
        item_policies=[
            ItemPolicy(
                policy_rule_id="POL-MGR-LAPTOP",
                item="laptop",
                max_held=1,
                refresh_interval_months=24,
            ),
            ItemPolicy(
                policy_rule_id="POL-MGR-PHONE",
                item="phone",
                max_held=1,
                refresh_interval_months=24,
            ),
        ],
    )
    contractor_policy = RolePolicy(role="contractor", item_policies=[])
    policy_service = PolicyService(InMemoryPolicyRepository([manager_policy, contractor_policy]))

    # The tool calls get_policy_service() through the name imported into the server module, so
    # that is the name to replace (patching backend.service_provider would not affect the tool).
    # The replacement returns the in-memory service above instead of the JSON-backed one, and
    # pytest's monkeypatch restores the original function after each test, keeping tests isolated.
    monkeypatch.setattr(server, "get_policy_service", lambda: policy_service)
    return policy_service


@pytest.mark.anyio
async def test_get_policy_limits_tool_manager_includes_phone_policy(in_memory_policy_service):
    """Calling get_policy_limits for "manager" returns a phone rule: max 1, every 24 months."""
    tool_arguments = {"role": "manager"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_policy_limits", tool_arguments)

    item_policies = result.structured_content["item_policies"]
    phone_policies = [policy for policy in item_policies if policy["item"] == "phone"]
    assert phone_policies == [
        {
            "policy_rule_id": "POL-MGR-PHONE",
            "item": "phone",
            "max_held": 1,
            "refresh_interval_months": 24,
        }
    ]


@pytest.mark.anyio
async def test_get_policy_limits_tool_contractor_returns_empty_list(in_memory_policy_service):
    """Calling it for "contractor" returns an empty item list: a valid answer, not an error."""
    tool_arguments = {"role": "contractor"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_policy_limits", tool_arguments)

    assert result.structured_content["item_policies"] == []


@pytest.mark.anyio
async def test_get_policy_limits_tool_unknown_role_returns_error_result(in_memory_policy_service):
    """Calling it for a role with no policy ("intern") returns a result with is_error True."""
    tool_arguments = {"role": "intern"}

    async with Client(mcp) as client:
        result = await client.call_tool("get_policy_limits", tool_arguments)

    assert result.is_error is True
