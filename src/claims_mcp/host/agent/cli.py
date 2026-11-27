"""Interactive CLI: ask who is asking and what they need, run the agent, print the run.

Asks employee or contractor first: an employee then gives their ID (role and name come from
the employee record), a contractor their name (they have no ID). Needs a running server. Run:
    uv run claims-mcp                # or: docker compose run --rm cli
"""

from typing import Any

import anyio
import questionary
from mcp import Client

from claims_mcp.host.agent.build_state import build_state
from claims_mcp.host.agent.run_agent import run_agent
from claims_mcp.host.agent.trace_printer import print_run
from claims_mcp.host.gateways.templates.mcp_template_gateway import McpTemplateGateway
from claims_mcp.host.gateways.tools.mcp_tool_gateway import McpToolGateway
from claims_mcp.host.llm.adapter_provider import create_chat_model_adapter
from claims_mcp.host.state.enums import RequesterType
from claims_mcp.settings import get_settings

EMPTY_ANSWER_MESSAGE = "Please type an answer."


async def run_cli() -> None:
    """Connect once, then handle requests one after another until the user stops."""
    settings = get_settings()
    adapter = create_chat_model_adapter()
    async with Client(settings.server_url) as client:
        tool_gateway = McpToolGateway(client)
        template_gateway = McpTemplateGateway(client)
        tool_specs = await tool_gateway.list_tool_specs()
        print(f"Connected to {settings.server_url}.\n")

        is_running = True
        while is_running:
            requester_type = await ask_requester_type()
            requester = await ask_requester(requester_type) if requester_type else None
            request = await ask_request() if requester else None
            if request is None:
                break

            print("\nRunning the agent…\n")
            state = build_state(requester_type, requester, request, tool_specs, settings)
            final_state = await run_agent(state, adapter, tool_gateway, template_gateway)
            print_run(final_state, settings.show_trace)
            print()
            is_running = bool(await ask(questionary.confirm("Handle another request?")))
    print("Bye.")


async def ask(question: questionary.Question) -> Any:
    """Show one prompt and return the answer; a cancel or a closed input returns None.

    Args:
        question: A questionary prompt (select, text or confirm).

    Returns:
        The answer, or None on Ctrl+C or when there is no terminal input (EOF).
    """
    try:
        return await question.ask_async()
    except EOFError:
        return None


async def ask_requester_type() -> RequesterType | None:
    """Ask whether an employee or a contractor is asking.

    Returns:
        The chosen RequesterType, or None if the user cancelled (Ctrl+C).
    """
    answer = await ask(
        questionary.select(
            "Are you an employee or a contractor?",
            choices=[requester_type.value for requester_type in RequesterType],
        )
    )
    if answer is None:
        return None
    return RequesterType(answer)


async def ask_requester(requester_type: RequesterType) -> str | None:
    """Ask an employee for their ID, or a contractor for their full name.

    Args:
        requester_type: Who is asking.

    Returns:
        The trimmed answer, or None if the user cancelled.
    """
    if requester_type == RequesterType.CONTRACTOR:
        message = "Your full name:"
    else:
        message = "Your employee ID (e.g. E001):"
    answer = await ask(questionary.text(message, validate=validate_not_empty))
    return answer.strip() if answer is not None else None


async def ask_request() -> str | None:
    """Ask what the requester needs, in their own words.

    Returns:
        The trimmed request, or None if the user cancelled.
    """
    answer = await ask(questionary.text("What do you need?", validate=validate_not_empty))
    return answer.strip() if answer is not None else None


def validate_not_empty(answer: str) -> bool | str:
    """Return True for a non-blank answer, else the message questionary shows under the prompt.

    Args:
        answer: What the user typed so far.

    Returns:
        True when the answer has text, else EMPTY_ANSWER_MESSAGE.
    """
    if answer.strip():
        return True
    return EMPTY_ANSWER_MESSAGE


def main() -> None:
    """Run the interactive CLI (the claims-mcp entry point)."""
    anyio.run(run_cli)


if __name__ == "__main__":
    main()
