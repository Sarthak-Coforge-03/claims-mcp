"""Builds the chat model adapter the host uses, from settings (the one place a provider is chosen).

Swapping providers means returning a different ChatModelAdapterBase here; callers don't change.
"""

from anthropic import AnthropicFoundry

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.adapters.foundry_claude_adapter import FoundryClaudeAdapter
from claims_mcp.settings import get_settings


def create_chat_model_adapter() -> ChatModelAdapterBase:
    """Return a new adapter for one conversation, configured from CLAIMS_MCP_* settings.

    Returns:
        A FoundryClaudeAdapter for the configured Foundry resource and deployment.

    Raises:
        ValueError: If CLAIMS_MCP_FOUNDRY_RESOURCE or CLAIMS_MCP_FOUNDRY_API_KEY is not set.
    """
    settings = get_settings()
    if not settings.foundry_resource or settings.foundry_api_key is None:
        raise ValueError(
            "Set CLAIMS_MCP_FOUNDRY_RESOURCE and CLAIMS_MCP_FOUNDRY_API_KEY (e.g. in .env)"
        )
    client = AnthropicFoundry(
        resource=settings.foundry_resource,
        api_key=settings.foundry_api_key.get_secret_value(),
    )
    return FoundryClaudeAdapter(client, settings.model_deployment, settings.model_effort)
