"""McpToolGateway: ToolGatewayBase over an open MCP client session (the claims MCP server)."""

import json

from mcp import Client
from mcp.types import CallToolResult

from claims_mcp.host.gateways.tools.tool_gateway_base import ToolGatewayBase
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.llm.models.tool_spec import ToolSpec


class McpToolGateway(ToolGatewayBase):
    """Lists and calls the MCP server's tools through a Client the caller opened and will close."""

    def __init__(self, client: Client) -> None:
        """Keep the connected client; this class doesn't open or close the connection.

        Args:
            client: An MCP Client inside its `async with` block.
        """
        self.client = client

    async def list_tool_specs(self) -> list[ToolSpec]:
        """Return the server's tools as ToolSpecs, with their agent-facing descriptions.

        Returns:
            One ToolSpec per tool from the server's list_tools.
        """
        tools_result = await self.client.list_tools()
        return [
            ToolSpec(
                name=tool.name, description=tool.description or "", input_schema=tool.input_schema
            )
            for tool in tools_result.tools
        ]

    async def call_tool(self, tool_call: ToolCall) -> ToolResult:
        """Run the call on the server and return its outcome as text for the model.

        Args:
            tool_call: The tool name, its arguments and the model's call id.

        Returns:
            A ToolResult paired by tool_call.id; is_error copied from the server's result.
        """
        call_tool_result = await self.client.call_tool(tool_call.name, tool_call.arguments)
        return build_tool_result(tool_call.id, call_tool_result)


def build_tool_result(tool_call_id: str, call_tool_result: CallToolResult) -> ToolResult:
    """Return the MCP result as a ToolResult: structured content as JSON, else the text blocks.

    Args:
        tool_call_id: The id of the call this result answers.
        call_tool_result: What the MCP server returned.

    Returns:
        content = json.dumps(structured_content) on success; on an error (no structured
        content) the text blocks joined, e.g. "Error executing tool ...: No employee with ID E999".
    """
    if call_tool_result.structured_content is not None:
        content = json.dumps(call_tool_result.structured_content)
    else:
        text_blocks = [block.text for block in call_tool_result.content if block.type == "text"]
        content = "\n".join(text_blocks)
    return ToolResult(
        tool_call_id=tool_call_id, content=content, is_error=call_tool_result.is_error
    )
