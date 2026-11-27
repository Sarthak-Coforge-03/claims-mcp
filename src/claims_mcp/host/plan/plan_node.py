"""Plan node: write state.plan once, from a fitting MCP template or from the tool descriptions."""

from claims_mcp.host.gateways.templates.template_gateway_base import TemplateGatewayBase
from claims_mcp.host.gateways.templates.template_spec import TemplateSpec
from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.plan.plan_views import build_select_view, build_write_view
from claims_mcp.host.plan.prompts.select_template_system_prompt import (
    SELECT_TEMPLATE_SYSTEM_PROMPT,
)
from claims_mcp.host.plan.prompts.write_plan_system_prompt import WRITE_PLAN_SYSTEM_PROMPT
from claims_mcp.host.plan.template_selection import TemplateSelection
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import PlanSource
from claims_mcp.host.state.plan import Plan


async def run_plan_node(
    state: AgentState, adapter: ChatModelAdapterBase, template_gateway: TemplateGatewayBase
) -> None:
    """Pick a fitting template and fill it in; if none can be used, have the model write a plan.

    Args:
        state: The run state before the loop; gets state.plan.
        adapter: The chat model; SELECT is one structured call, WRITE (fallback) one text call.
        template_gateway: Lists and fills the server's scenario templates.

    Side effects:
        Sets state.plan: source MCP_TEMPLATE with the template's text, or TOOL_DESCRIPTIONS
        with the written plan.
    """
    template_specs = await template_gateway.list_template_specs()
    select_conversation = Conversation.start(
        SELECT_TEMPLATE_SYSTEM_PROMPT,
        build_select_view(state.request, template_specs),
        tool_specs=[],
    )
    selection = adapter.complete_structured(select_conversation, TemplateSelection)

    if is_usable_selection(selection, template_specs):
        template_text = await template_gateway.get_template_text(
            selection.template_name, build_template_arguments(selection)
        )
        state.plan = Plan(
            source=PlanSource.MCP_TEMPLATE,
            template_name=selection.template_name,
            text=template_text,
        )
    else:
        write_conversation = Conversation.start(
            WRITE_PLAN_SYSTEM_PROMPT, build_write_view(state), tool_specs=[]
        )
        write_turn = adapter.complete(write_conversation)
        state.plan = Plan(
            source=PlanSource.TOOL_DESCRIPTIONS, template_name=None, text=write_turn.text
        )


def is_usable_selection(selection: TemplateSelection, template_specs: list[TemplateSpec]) -> bool:
    """Return whether the selected template exists and can be filled in.

    Args:
        selection: SELECT's reply.
        template_specs: The templates the server offers.

    Returns:
        True when template_name is one of the server's templates and employee_id and item are
        set; the model's choice is never trusted without this check.
    """
    template_names = [template_spec.name for template_spec in template_specs]
    is_known_template = selection.template_name in template_names
    has_required_arguments = selection.employee_id is not None and selection.item is not None
    return is_known_template and has_required_arguments


def build_template_arguments(selection: TemplateSelection) -> dict[str, str]:
    """Return the template arguments from SELECT's reply, all as text (MCP prompt arguments).

    Args:
        selection: A usable selection (employee_id and item are set).

    Returns:
        {"employee_id", "item", "reason", "quantity"} mapped to the selection's values.
    """
    return {
        "employee_id": selection.employee_id,
        "item": selection.item,
        "reason": selection.reason,
        "quantity": selection.quantity,
    }
