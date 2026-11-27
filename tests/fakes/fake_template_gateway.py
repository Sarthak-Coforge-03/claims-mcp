"""FakeTemplateGateway: a TemplateGatewayBase with canned template text per name; no MCP server."""

from claims_mcp.host.gateways.templates.template_gateway_base import TemplateGatewayBase
from claims_mcp.host.gateways.templates.template_spec import TemplateSpec


class FakeTemplateGateway(TemplateGatewayBase):
    """Returns fixed text per template name and records every template request it got."""

    def __init__(self, text_by_template_name: dict[str, str]) -> None:
        """Keep the canned templates and start with no recorded requests.

        Args:
            text_by_template_name: The text each template returns, keyed by template name.
        """
        self.text_by_template_name = text_by_template_name
        self.received_template_requests = []

    async def list_template_specs(self) -> list[TemplateSpec]:
        """Return one TemplateSpec per canned template name.

        Returns:
            TemplateSpecs with a placeholder description.
        """
        return [
            TemplateSpec(name=template_name, description=f"Use for {template_name}.")
            for template_name in self.text_by_template_name
        ]

    async def get_template_text(self, template_name: str, arguments: dict[str, str]) -> str:
        """Record the request and return the canned text for that template.

        Args:
            template_name: The template asked for.
            arguments: The arguments it was asked with; kept in received_template_requests.

        Returns:
            The canned text for template_name.
        """
        self.received_template_requests.append(
            {"template_name": template_name, "arguments": arguments}
        )
        return self.text_by_template_name[template_name]
