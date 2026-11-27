"""ChatModelAdapterBase: the interface every LLM provider adapter implements."""

from abc import ABC, abstractmethod

from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.model_turn import ModelTurn


class ChatModelAdapterBase(ABC):
    """A stateless bridge to one chat model provider, in provider-neutral types.

    The history lives in the Conversation the caller owns, so one adapter can serve many runs.
    """

    @abstractmethod
    def complete(self, conversation: Conversation) -> ModelTurn:
        """Ask the model for its next reply to the conversation so far, without changing it.

        Args:
            conversation: The instructions, tools and history; the caller appends the reply.

        Returns:
            The reply as a ModelTurn: tool calls to run, or the final answer.
        """
