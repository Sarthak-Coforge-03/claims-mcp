"""ToolResultsMessage: the results of one turn's tool calls, sent back to the model together."""

from typing import Literal

from pydantic import BaseModel

from claims_mcp.host.llm.models.message_role import MessageRole
from claims_mcp.host.llm.models.tool_result import ToolResult


class ToolResultsMessage(BaseModel):
    """All Observations of one turn as one message; splitting them discourages parallel calls."""

    role: Literal[MessageRole.TOOL_RESULTS] = MessageRole.TOOL_RESULTS
    tool_results: list[ToolResult]
