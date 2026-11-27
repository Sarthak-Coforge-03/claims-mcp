"""ToolCall: the model asking to run one tool, in a provider-neutral shape."""

from pydantic import BaseModel


class ToolCall(BaseModel):
    """One tool call the model made: the provider's call ID, the tool name and its arguments.

    The id is echoed back in the matching ToolResult so the provider can pair them.
    """

    id: str
    name: str
    arguments: dict
