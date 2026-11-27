"""Tests for McpTemplateGateway: MCP prompts become TemplateSpecs and filled-in template text.

A test-only server with one known prompt keeps these independent of the claims server's real
templates (those are tested in tests/mcp_server/test_prompts.py). Client runs MCP in-process.
"""

import pytest
from mcp import Client
from mcp.server import MCPServer

from claims_mcp.host.gateways.templates.mcp_template_gateway import McpTemplateGateway
from claims_mcp.host.gateways.templates.template_spec import TemplateSpec

test_server = MCPServer("template-gateway-test")


@test_server.prompt(name="greeting_template", description="Use when greeting someone.")
def greeting_template(employee_id: str) -> str:
    """Return a fixed one-line template that echoes the argument."""
    return f"Greet {employee_id}."


@pytest.mark.anyio
async def test_list_template_specs_maps_each_prompt_to_name_and_description():
    """The server's one prompt comes back as a TemplateSpec with its name and description."""
    async with Client(test_server) as client:
        template_specs = await McpTemplateGateway(client).list_template_specs()

    assert template_specs == [
        TemplateSpec(name="greeting_template", description="Use when greeting someone.")
    ]


@pytest.mark.anyio
async def test_get_template_text_returns_the_filled_in_template():
    """Getting greeting_template for E001 returns its text with the argument filled in."""
    async with Client(test_server) as client:
        template_text = await McpTemplateGateway(client).get_template_text(
            "greeting_template", {"employee_id": "E001"}
        )

    assert template_text == "Greet E001."
