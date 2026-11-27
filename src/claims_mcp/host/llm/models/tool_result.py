"""ToolResult: what running one tool call returned, in a provider-neutral shape."""

from pydantic import BaseModel


class ToolResult(BaseModel):
    """The outcome of one ToolCall, sent back to the model as the Observation.

    is_error is True when the tool reported an error (e.g. unknown employee); the model still sees
    the content, so it can react to it (e.g. escalate with ESC-1).
    """

    tool_call_id: str
    content: str
    is_error: bool
