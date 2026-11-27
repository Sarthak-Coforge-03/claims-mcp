"""Demo: run the agent (plan, ReAct, reflection) on one request against the live server and Claude.

Needs the Foundry settings in .env and a running server. Run:
    docker compose up -d --wait mcp_server
    uv run python -m claims_mcp.host.agent.run_demo                                # scenario 1
    uv run python -m claims_mcp.host.agent.run_demo employee E004 "three monitors"
    uv run python -m claims_mcp.host.agent.run_demo contractor "Alex Doe" "a laptop"
"""

import sys

import anyio
from mcp import Client

from claims_mcp.host.agent.build_state import build_state
from claims_mcp.host.agent.run_agent import run_agent
from claims_mcp.host.agent.trace_printer import print_trace
from claims_mcp.host.gateways.templates.mcp_template_gateway import McpTemplateGateway
from claims_mcp.host.gateways.tools.mcp_tool_gateway import McpToolGateway
from claims_mcp.host.llm.adapter_provider import create_chat_model_adapter
from claims_mcp.host.state.enums import RequesterType
from claims_mcp.settings import get_settings

# Scenario 1 in docs/requirements.md: expected approve under ELG-2 (POL-STD-MONITOR).
DEMO_REQUESTER_TYPE = RequesterType.EMPLOYEE
DEMO_REQUESTER = "E001"
DEMO_REQUEST = "my monitor is old, I'd like a new one."
# requester type, ID or name, request
DEMO_ARGUMENT_COUNT = 3


async def run_demo(requester_type: RequesterType, requester: str, request: str) -> None:
    """Connect to the server, run the agent on one request, and print the finished trace.

    Args:
        requester_type: Employee or contractor.
        requester: An employee's ID, or a contractor's full name.
        request: The request in the requester's own words.
    """
    settings = get_settings()
    adapter = create_chat_model_adapter()
    async with Client(settings.server_url) as client:
        tool_gateway = McpToolGateway(client)
        template_gateway = McpTemplateGateway(client)
        tool_specs = await tool_gateway.list_tool_specs()
        state = build_state(requester_type, requester, request, tool_specs, settings)
        final_state = await run_agent(state, adapter, tool_gateway, template_gateway)
    print_trace(final_state)


def main() -> None:
    """Run the demo for the type, ID or name and request on the command line, else scenario 1."""
    command_line_arguments = sys.argv[1:]
    if len(command_line_arguments) == DEMO_ARGUMENT_COUNT:
        requester_type = RequesterType(command_line_arguments[0])
        requester = command_line_arguments[1]
        request = command_line_arguments[2]
    else:
        requester_type = DEMO_REQUESTER_TYPE
        requester = DEMO_REQUESTER
        request = DEMO_REQUEST
    anyio.run(run_demo, requester_type, requester, request)


if __name__ == "__main__":
    main()
