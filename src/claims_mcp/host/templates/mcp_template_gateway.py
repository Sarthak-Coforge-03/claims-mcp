"""McpTemplateGateway: TemplateGatewayBase over an open MCP client session's prompts."""

from mcp import Client

from claims_mcp.host.templates.template_gateway_base import TemplateGatewayBase
from claims_mcp.host.templates.template_spec import TemplateSpec


class McpTemplateGateway(TemplateGatewayBase):
    """Lists and fills the server's MCP prompts through a Client the caller opened and closes."""

    def __init__(self, client: Client) -> None:
        """Keep the connected client; this class doesn't open or close the connection.

        Args:
            client: An MCP Client inside its `async with` block.
        """
        self.client = client

    async def list_template_specs(self) -> list[TemplateSpec]:
        """Return the server's prompts as TemplateSpecs.

        Returns:
            One TemplateSpec per prompt from list_prompts; a missing description becomes "".
        """
        prompts_result = await self.client.list_prompts()
        return [
            TemplateSpec(name=prompt.name, description=prompt.description or "")
            for prompt in prompts_result.prompts
        ]

    async def get_template_text(self, template_name: str, arguments: dict[str, str]) -> str:
        """Fill in one prompt on the server and return its text.

        Args:
            template_name: The prompt name, e.g. "replacement_request".
            arguments: Its arguments as text (MCP prompt arguments are always strings).

        Returns:
            The text of every text message the prompt returned, joined by blank lines.
        """
        prompt_result = await self.client.get_prompt(template_name, arguments)
        message_texts = [
            message.content.text
            for message in prompt_result.messages
            if message.content.type == "text"
        ]
        return "\n\n".join(message_texts)
