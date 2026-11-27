"""Tests for the flag_for_human_review MCP tool, called through the MCP protocol in-process.

The escalation service is swapped for one over an in-memory store, so no escalation is written
to data/ and the saved records can be inspected directly.
"""

import pytest
from mcp import Client

from claims_mcp.backend.services.escalation_service import EscalationService
from claims_mcp.mcp_server import server
from claims_mcp.mcp_server.server import mcp
from fakes.in_memory_escalation_repository import InMemoryEscalationRepository


@pytest.fixture
def in_memory_escalation_repository(monkeypatch):
    """Make the tool save escalations to an empty in-memory store, and return that store.

    monkeypatch puts the real get_escalation_service back after each test.
    """
    escalation_repository = InMemoryEscalationRepository()
    escalation_service = EscalationService(escalation_repository)

    # The tool calls get_escalation_service() through the name imported into the server
    # module, so that is the name to replace (patching backend.service_provider would not
    # affect the tool). monkeypatch restores the original after each test, keeping tests isolated.
    monkeypatch.setattr(server, "get_escalation_service", lambda: escalation_service)
    return escalation_repository


@pytest.mark.anyio
async def test_flag_tool_returns_pending_escalation(in_memory_escalation_repository):
    """Flagging E005's monitor request (ESC-4) returns an escalation with status pending_review."""
    tool_arguments = {
        "employee_id": "E005",
        "request": "monitor",
        "reason": "ESC-4: hired less than 90 days ago",
    }

    async with Client(mcp) as client:
        result = await client.call_tool("flag_for_human_review", tool_arguments)

    assert result.structured_content["status"] == "pending_review"


@pytest.mark.anyio
async def test_flag_tool_saves_escalation_for_reviewers(in_memory_escalation_repository):
    """The side effect: after the call, the store holds exactly the escalation the tool returned."""
    tool_arguments = {
        "employee_id": "E005",
        "request": "monitor",
        "reason": "ESC-4: hired less than 90 days ago",
    }

    async with Client(mcp) as client:
        result = await client.call_tool("flag_for_human_review", tool_arguments)

    saved_escalation_ids = [
        escalation.escalation_id for escalation in in_memory_escalation_repository.list_all()
    ]
    assert saved_escalation_ids == [result.structured_content["escalation_id"]]


@pytest.mark.anyio
async def test_flag_tool_empty_reason_returns_error_result(in_memory_escalation_repository):
    """Escalating with an empty reason ("") is rejected as an error result: reviewers need a why."""
    tool_arguments = {"employee_id": "E005", "request": "monitor", "reason": ""}

    async with Client(mcp) as client:
        result = await client.call_tool("flag_for_human_review", tool_arguments)

    assert result.is_error is True
