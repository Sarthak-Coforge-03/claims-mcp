"""UserMessage: plain text from the user, e.g. the equipment request."""

from typing import Literal

from pydantic import BaseModel

from claims_mcp.host.llm.models.message_role import MessageRole


class UserMessage(BaseModel):
    """A text message from the user; the fixed role tells it apart from other message types."""

    role: Literal[MessageRole.USER] = MessageRole.USER
    text: str
