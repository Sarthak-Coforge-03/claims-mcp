"""Tests for the MCP server's prompts, fetched through the real MCP protocol in-process.

Prompts only build text from their arguments, so no backend service needs replacing here.
"""

import pytest
from mcp import Client

from claims_mcp.mcp_server.server import mcp


@pytest.mark.anyio
async def test_list_prompts_returns_the_three_playbooks():
    """list_prompts offers exactly replacement_request, new_item_request and exception_request."""
    async with Client(mcp) as client:
        result = await client.list_prompts()

    prompt_names = {prompt.name for prompt in result.prompts}
    assert prompt_names == {"replacement_request", "new_item_request", "exception_request"}


@pytest.mark.anyio
async def test_get_prompt_exception_request_tells_agent_to_escalate():
    """exception_request for E002 / laptop / "screen cracked" mentions flag_for_human_review."""
    prompt_arguments = {"employee_id": "E002", "item": "laptop", "reason": "screen cracked"}

    async with Client(mcp) as client:
        result = await client.get_prompt("exception_request", prompt_arguments)

    prompt_text = result.messages[0].content.text
    assert "flag_for_human_review" in prompt_text
