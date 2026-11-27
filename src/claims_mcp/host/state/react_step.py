"""ReActStep: one THINK → ACT → OBSERVE cycle, filled in phase by phase."""

from pydantic import BaseModel

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.state.thought import Thought


class ReActStep(BaseModel):
    """One cycle; each field is written by one phase, the rest stay None until it runs.

    THINK writes thought. ACT writes action and tool_result, or action_error when the model made
    zero or several tool calls (no tool runs then). OBSERVE writes observation.
    """

    thought: Thought
    action: ToolCall | None = None
    tool_result: ToolResult | None = None
    action_error: str | None = None
    observation: str | None = None
