"""ModelTurn: one model response in provider-neutral fields, plus its raw blocks."""

from typing import Literal

from pydantic import BaseModel

from claims_mcp.host.llm.models.message_role import MessageRole
from claims_mcp.host.llm.models.tool_call import ToolCall


class ModelTurn(BaseModel):
    """One model reply, reported as returned; callers decide what it means, the adapter doesn't.

    text is every text block joined; reasoning_summary is the thinking summaries joined.
    stop_reason is the provider's raw value, e.g. "end_turn". provider_content is the reply exactly
    as the provider returned it (JSON dicts), kept so an adapter can replay it unchanged.
    """

    role: Literal[MessageRole.ASSISTANT] = MessageRole.ASSISTANT
    text: str
    reasoning_summary: str
    tool_calls: list[ToolCall]
    stop_reason: str
    provider_content: list[dict]
