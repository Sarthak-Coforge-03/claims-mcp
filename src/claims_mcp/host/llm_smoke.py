"""Smoke check: one real model call through the adapter, no tools, to prove the LLM wiring works.

Confirms the Foundry resource, API key and deployment before the ReAct loop depends on them. Run:
    uv run python -m claims_mcp.host.llm_smoke
"""

from claims_mcp.host.llm.adapter_provider import create_chat_model_adapter
from claims_mcp.host.llm.models.conversation import Conversation

SMOKE_SYSTEM_PROMPT = "You are a terse assistant."
SMOKE_USER_MESSAGE = "Reply with exactly: adapter ok"


def main() -> None:
    """Send one message with no tools and print the model's reply and stop reason."""
    adapter = create_chat_model_adapter()
    conversation = Conversation.start(SMOKE_SYSTEM_PROMPT, SMOKE_USER_MESSAGE, tool_specs=[])

    model_turn = adapter.complete(conversation)

    print(f"stop_reason={model_turn.stop_reason}")
    print(f"final_text={model_turn.final_text!r}")


if __name__ == "__main__":
    main()
