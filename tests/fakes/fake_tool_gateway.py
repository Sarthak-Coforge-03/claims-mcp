"""FakeToolGateway: a ToolGatewayBase with canned results per tool name; no MCP server."""

from claims_mcp.host.gateways.tools.tool_gateway_base import ToolGatewayBase
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_spec import ToolSpec


class FakeToolGateway(ToolGatewayBase):
    """Returns a fixed content string per tool name and records every call it ran."""

    def __init__(self, content_by_tool_name: dict[str, str]) -> None:
        """Keep the canned results and start with no recorded calls.

        Args:
            content_by_tool_name: The content each tool returns, keyed by tool name.
        """
        self.content_by_tool_name = content_by_tool_name
        self.received_tool_calls = []

    async def list_tool_specs(self) -> list[ToolSpec]:
        """Return one minimal ToolSpec per canned tool name.

        Returns:
            ToolSpecs with an empty object schema.
        """
        return [
            ToolSpec(name=tool_name, description="", input_schema={"type": "object"})
            for tool_name in self.content_by_tool_name
        ]

    async def call_tool(self, tool_call: ToolCall) -> ToolResult:
        """Record the call and return the canned content for its tool, never an error.

        Args:
            tool_call: The call to "run".

        Returns:
            A ToolResult paired by tool_call.id with the canned content.
        """
        self.received_tool_calls.append(tool_call)
        return ToolResult(
            tool_call_id=tool_call.id,
            content=self.content_by_tool_name[tool_call.name],
            is_error=False,
        )
