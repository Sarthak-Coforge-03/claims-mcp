"""ChatModelAdapterBase: the interface every LLM provider adapter implements."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.model_turn import ModelTurn

# The pydantic model a structured call must return; the caller passes the class.
OutputModelT = TypeVar("OutputModelT", bound=BaseModel)


class ChatModelAdapterBase(ABC):
    """A stateless bridge to one chat model provider, in provider-neutral types.

    The history lives in the Conversation the caller owns, so one adapter can serve many runs.
    """

    @abstractmethod
    def complete(self, conversation: Conversation) -> ModelTurn:
        """Ask the model for its next reply to the conversation, offering its tools.

        Args:
            conversation: The instructions, tools and history; it is not changed.

        Returns:
            The reply as a ModelTurn (text, reasoning summary, tool calls), not interpreted.
        """

    @abstractmethod
    def complete_structured(
        self, conversation: Conversation, output_model: type[OutputModelT]
    ) -> OutputModelT:
        """Ask the model for a reply that matches output_model; no tools are offered.

        Args:
            conversation: The instructions and history; its tool specs are ignored.
            output_model: The pydantic model class the reply must match.

        Returns:
            The reply validated as an output_model instance.

        Raises:
            ValueError: If the model returned no parseable output (e.g. it refused).
        """
