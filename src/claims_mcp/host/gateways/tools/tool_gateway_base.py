"""ToolGatewayBase: the interface the agent uses to list and run tools, in neutral types."""

from abc import ABC, abstractmethod

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_spec import ToolSpec


class ToolGatewayBase(ABC):
    """Where the agent's tools live; the agent never knows whether they come from MCP or a fake."""

    @abstractmethod
    async def list_tool_specs(self) -> list[ToolSpec]:
        """Return every tool the agent may call.

        Returns:
            One ToolSpec (name, description, argument JSON schema) per tool.
        """

    @abstractmethod
    async def call_tool(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its outcome; tool errors are results, not exceptions.

        Args:
            tool_call: The tool name, its arguments and the model's call id.

        Returns:
            A ToolResult with the same call id, the content as text, and is_error.
        """
