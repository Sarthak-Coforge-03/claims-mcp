"""FoundryClaudeAdapter: ChatModelAdapterBase for Claude on Microsoft Foundry (Azure).

Uses the anthropic SDK's AnthropicFoundry client on the native /anthropic/v1/messages path.
Claude-specific rules this adapter follows (Opus 5.5):
- thinking is always on; "adaptive" + display "summarized" returns readable reasoning summaries.
- each assistant reply goes back as returned (ModelTurn.provider_content), thinking included.
- tool_choice stays "auto" (forced "any"/"tool" is rejected on this model).
"""

from anthropic import AnthropicFoundry
from anthropic.types import Message

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_results_message import ToolResultsMessage
from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.llm.models.user_message import UserMessage

# Room for thinking plus the reply; stays under the SDK's non-streaming timeout.
MAX_OUTPUT_TOKENS = 16000
THINKING_CONFIG = {"type": "adaptive", "display": "summarized"}


class FoundryClaudeAdapter(ChatModelAdapterBase):
    """Stateless Claude-on-Foundry adapter: each call rebuilds the request from the Conversation."""

    def __init__(self, client: AnthropicFoundry, model_deployment: str, effort: str) -> None:
        """Keep the client and model settings; no conversation state is held here.

        Args:
            client: A configured AnthropicFoundry client (resource + API key).
            model_deployment: The Foundry deployment name, e.g. "claude-opus-5-5-fast".
            effort: How much the model thinks: "low", "medium", "high", "xhigh" or "max".
        """
        self.client = client
        self.model_deployment = model_deployment
        self.effort = effort

    def complete(self, conversation: Conversation) -> ModelTurn:
        """Send the conversation to Claude and return its reply, leaving the conversation as is.

        Args:
            conversation: The system prompt, tools and history to send.

        Returns:
            The reply as a ModelTurn, with its raw blocks kept for the next call.
        """
        tools = [build_anthropic_tool(tool_spec) for tool_spec in conversation.tool_specs]
        response = self.client.messages.create(
            model=self.model_deployment,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=conversation.system_prompt,
            messages=build_anthropic_messages(conversation),
            tools=tools,
            thinking=THINKING_CONFIG,
            output_config={"effort": self.effort},
        )
        return build_model_turn(response)


def build_anthropic_tool(tool_spec: ToolSpec) -> dict:
    """Return the Anthropic tool definition for a provider-neutral ToolSpec.

    Args:
        tool_spec: The tool's name, description and argument JSON schema.

    Returns:
        A dict with keys "name", "description" and "input_schema".
    """
    return {
        "name": tool_spec.name,
        "description": tool_spec.description,
        "input_schema": tool_spec.input_schema,
    }


def build_anthropic_messages(conversation: Conversation) -> list[dict]:
    """Return the conversation's history as Anthropic messages, in order.

    Args:
        conversation: The provider-neutral history.

    Returns:
        One dict per message ("role" + "content"): user text, assistant blocks replayed
        unchanged from provider_content, and tool results as a user message of tool_result blocks.
    """
    anthropic_messages = []
    for message in conversation.messages:
        if isinstance(message, UserMessage):
            anthropic_messages.append({"role": "user", "content": message.text})
        elif isinstance(message, ModelTurn):
            anthropic_messages.append({"role": "assistant", "content": message.provider_content})
        elif isinstance(message, ToolResultsMessage):
            anthropic_messages.append(build_tool_results_message(message))
    return anthropic_messages


def build_tool_results_message(tool_results_message: ToolResultsMessage) -> dict:
    """Return one Anthropic user message holding a tool_result block per result.

    Args:
        tool_results_message: The results of one turn's tool calls.

    Returns:
        {"role": "user", "content": [tool_result blocks keyed by tool_use_id]}.
    """
    tool_result_blocks = [
        {
            "type": "tool_result",
            "tool_use_id": tool_result.tool_call_id,
            "content": tool_result.content,
            "is_error": tool_result.is_error,
        }
        for tool_result in tool_results_message.tool_results
    ]
    return {"role": "user", "content": tool_result_blocks}


def build_model_turn(message: Message) -> ModelTurn:
    """Reduce a Claude response to a ModelTurn: thought, tool calls or final answer, raw blocks.

    Args:
        message: The assistant Message returned by messages.create.

    Returns:
        With tool_use blocks: thought_text = thinking summaries + text, final_text None.
        Without: thought_text = thinking summaries, final_text = the text blocks.
        provider_content always holds every block as a JSON dict, for replay.
    """
    thinking_texts = []
    reply_texts = []
    tool_calls = []
    for block in message.content:
        if block.type == "thinking" and block.thinking:
            thinking_texts.append(block.thinking)
        elif block.type == "text":
            reply_texts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input))
    provider_content = [
        block.model_dump(mode="json", exclude_none=True) for block in message.content
    ]

    if tool_calls:
        return ModelTurn(
            thought_text="\n".join(thinking_texts + reply_texts),
            tool_calls=tool_calls,
            final_text=None,
            stop_reason=message.stop_reason,
            provider_content=provider_content,
        )
    return ModelTurn(
        thought_text="\n".join(thinking_texts),
        tool_calls=[],
        final_text="\n".join(reply_texts),
        stop_reason=message.stop_reason,
        provider_content=provider_content,
    )
