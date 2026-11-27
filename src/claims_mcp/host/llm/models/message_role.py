"""MessageRole: who a conversation message is from, used to tell message types apart."""

from enum import StrEnum


class MessageRole(StrEnum):
    """The kind of message in a Conversation; each message model fixes its own value."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULTS = "tool_results"
