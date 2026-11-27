"""TemplateGatewayBase: the interface the plan node uses to list and fill scenario templates."""

from abc import ABC, abstractmethod

from claims_mcp.host.gateways.templates.template_spec import TemplateSpec


class TemplateGatewayBase(ABC):
    """Where scenario templates live; the plan node never knows whether they come from MCP."""

    @abstractmethod
    async def list_template_specs(self) -> list[TemplateSpec]:
        """Return every template the plan node may pick.

        Returns:
            One TemplateSpec (name, description) per template.
        """

    @abstractmethod
    async def get_template_text(self, template_name: str, arguments: dict[str, str]) -> str:
        """Return one template filled in with the request's arguments.

        Args:
            template_name: The template to fill in, e.g. "replacement_request".
            arguments: Its arguments as text, e.g. {"employee_id": "E001", "item": "monitor"}.

        Returns:
            The filled-in template as plain text.
        """
