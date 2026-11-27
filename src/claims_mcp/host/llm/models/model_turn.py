"""ModelTurn: one model response, reduced to what the ReAct loop needs, plus its raw blocks."""

from typing import Literal

from pydantic import BaseModel

from claims_mcp.host.llm.models.message_role import MessageRole
from claims_mcp.host.llm.models.tool_call import ToolCall


class ModelTurn(BaseModel):
    """One model reply: its reasoning, the tools it wants to call, or its final answer.

    A turn with tool_calls is a Thought + Action step (final_text None); a turn without is the
    final answer (final_text set). stop_reason is the provider's raw value, e.g. "end_turn".
    provider_content is the reply exactly as the provider returned it (JSON dicts). The loop never
    reads it; the adapter replays it, because Claude requires its thinking blocks back unchanged.
    """

    role: Literal[MessageRole.ASSISTANT] = MessageRole.ASSISTANT
    thought_text: str
    tool_calls: list[ToolCall]
    final_text: str | None
    stop_reason: str
    provider_content: list[dict]
