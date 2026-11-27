"""FakeChatModelAdapter: a scripted ChatModelAdapterBase for tests; no network, no API key."""

from pydantic import BaseModel

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.model_turn import ModelTurn


class FakeChatModelAdapter(ChatModelAdapterBase):
    """Replays scripted replies in order and records every conversation it was sent.

    complete() replays scripted_turns (ACT, OBSERVE); complete_structured() replays
    scripted_structured_outputs (THINK). Each script repeats its last entry once used up.
    """

    def __init__(
        self, scripted_turns: list[ModelTurn], scripted_structured_outputs: list[BaseModel]
    ) -> None:
        """Keep both scripts and start with no recorded calls.

        Args:
            scripted_turns: Replies for complete(), in call order.
            scripted_structured_outputs: Replies for complete_structured(), in call order.
        """
        self.scripted_turns = scripted_turns
        self.scripted_structured_outputs = scripted_structured_outputs
        self.received_calls = []

    def complete(self, conversation: Conversation) -> ModelTurn:
        """Record the call and return the next scripted turn.

        Args:
            conversation: What the node sent; kept in received_calls.

        Returns:
            The next ModelTurn from scripted_turns (the last one again once used up).
        """
        turn_index = self.count_calls("complete")
        self.received_calls.append({"method": "complete", "conversation": conversation})
        return pick_scripted_reply(self.scripted_turns, turn_index)

    def complete_structured(self, conversation: Conversation, output_model: type) -> BaseModel:
        """Record the call and return the next scripted structured output.

        Args:
            conversation: What the node sent; kept in received_calls.
            output_model: Ignored; the script already holds instances of it.

        Returns:
            The next object from scripted_structured_outputs (the last one once used up).
        """
        output_index = self.count_calls("complete_structured")
        self.received_calls.append({"method": "complete_structured", "conversation": conversation})
        return pick_scripted_reply(self.scripted_structured_outputs, output_index)

    def count_calls(self, method: str) -> int:
        """Return how many calls of the given method were recorded so far.

        Args:
            method: "complete" or "complete_structured".

        Returns:
            The number of recorded calls to that method.
        """
        return len([call for call in self.received_calls if call["method"] == method])


def pick_scripted_reply(script: list, call_index: int):
    """Return the script entry for this call, or the last entry once the script is used up.

    Args:
        script: The scripted replies, in call order.
        call_index: How many earlier calls used this script.

    Returns:
        script[call_index], or script's last entry when call_index is past the end.
    """
    last_index = len(script) - 1
    return script[min(call_index, last_index)]
