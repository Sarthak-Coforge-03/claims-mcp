"""Views for the plan node's two model calls: SELECT a template, or WRITE a plan."""

from claims_mcp.host.gateways.templates.template_spec import TemplateSpec
from claims_mcp.host.react.views import render_tool_catalog
from claims_mcp.host.state.agent_state import AgentState


def build_select_view(request: str, template_specs: list[TemplateSpec]) -> str:
    """Return SELECT's view: the request and one line per template with its description.

    Args:
        request: The employee's request.
        template_specs: The templates the server offers.

    Returns:
        "Request: ..." then an "Available templates:" block.
    """
    template_lines = [
        f"- {template_spec.name}: {template_spec.description}" for template_spec in template_specs
    ]
    return f"Request: {request}\n\nAvailable templates:\n" + "\n".join(template_lines)


def build_write_view(state: AgentState) -> str:
    """Return WRITE's view: the request, today's date and the tool catalog.

    Args:
        state: The run state, before the loop has started.

    Returns:
        The three sections separated by blank lines.
    """
    sections = [
        f"Request: {state.request}",
        f"Today: {state.today.isoformat()}",
        render_tool_catalog(state.tool_specs),
    ]
    return "\n\n".join(sections)
