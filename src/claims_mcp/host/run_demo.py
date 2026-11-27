"""Demo: run the ReAct loop on scenario 1 against the live MCP server and Claude, print the trace.

Needs the Foundry settings in .env and a running server. Run:
    docker compose up -d --wait mcp_server
    uv run python -m claims_mcp.host.run_demo
"""

from datetime import date

import anyio
from mcp import Client

from claims_mcp.host.llm.adapter_provider import create_chat_model_adapter
from claims_mcp.host.react.react_loop import run_react_loop
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.tools.mcp_tool_gateway import McpToolGateway
from claims_mcp.host.trace_printer import print_trace
from claims_mcp.settings import get_settings

# Scenario 1 in docs/requirements.md: expected approve under ELG-2 (POL-STD-MONITOR).
DEMO_REQUEST = "Employee E001: my monitor is old, I'd like a new one."


async def run_demo(request: str) -> None:
    """Connect to the server, run the loop on one request, and print the finished trace.

    Args:
        request: The employee's request in natural language.
    """
    settings = get_settings()
    adapter = create_chat_model_adapter()
    async with Client(settings.server_url) as client:
        tool_gateway = McpToolGateway(client)
        state = AgentState(
            request=request,
            today=date.today(),
            tool_specs=await tool_gateway.list_tool_specs(),
            max_steps=settings.max_react_steps,
        )
        final_state = await run_react_loop(state, adapter, tool_gateway)
    print_trace(final_state)


def main() -> None:
    """Run the demo for scenario 1."""
    anyio.run(run_demo, DEMO_REQUEST)


if __name__ == "__main__":
    main()
