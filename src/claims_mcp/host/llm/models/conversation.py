"""Conversation: the full, provider-neutral history of one agent run with the model."""

from typing import Annotated

from pydantic import BaseModel, Field

from claims_mcp.host.llm.models.model_turn import ModelTurn
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_results_message import ToolResultsMessage
from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.llm.models.user_message import UserMessage

# Any message in the history; "role" tells pydantic which model each one is when loading JSON.
ConversationMessage = Annotated[
    UserMessage | ModelTurn | ToolResultsMessage, Field(discriminator="role")
]


class Conversation(BaseModel):
    """Everything an adapter needs to ask for the next turn: instructions, tools and history.

    Adapters only read it; the agent loop appends each model turn and each set of tool results.
    """

    system_prompt: str
    tool_specs: list[ToolSpec]
    messages: list[ConversationMessage]

    @classmethod
    def start(
        cls, system_prompt: str, user_message: str, tool_specs: list[ToolSpec]
    ) -> "Conversation":
        """Return a new conversation holding one user message.

        Args:
            system_prompt: The instructions that frame the whole conversation.
            user_message: The first user message, e.g. the equipment request.
            tool_specs: The tools the model may call.

        Returns:
            A Conversation whose messages are just that UserMessage.
        """
        return cls(
            system_prompt=system_prompt,
            tool_specs=tool_specs,
            messages=[UserMessage(text=user_message)],
        )

    def add_model_turn(self, model_turn: ModelTurn) -> None:
        """Append the model's reply to the history.

        Args:
            model_turn: The turn an adapter's complete() returned.
        """
        self.messages.append(model_turn)

    def add_tool_results(self, tool_results: list[ToolResult]) -> None:
        """Append the results of the last turn's tool calls as one message.

        Args:
            tool_results: One result per tool call of the last turn.
        """
        self.messages.append(ToolResultsMessage(tool_results=tool_results))
