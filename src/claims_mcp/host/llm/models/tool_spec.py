"""ToolSpec: a tool the model may call, in a provider-neutral shape."""

from pydantic import BaseModel


class ToolSpec(BaseModel):
    """One tool offered to the model: its name, when to use it, and its argument JSON schema.

    Built from MCP's list_tools; each adapter turns it into its provider's tool format.
    """

    name: str
    description: str
    input_schema: dict
