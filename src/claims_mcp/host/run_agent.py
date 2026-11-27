"""run_agent: the whole agent on one shared state, the plan node first, then the ReAct loop.

Reflection will run here after the loop; each stage reads and writes the same AgentState.
"""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.plan.plan_node import run_plan_node
from claims_mcp.host.react.react_loop import run_react_loop
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.templates.template_gateway_base import TemplateGatewayBase
from claims_mcp.host.tools.tool_gateway_base import ToolGatewayBase


async def run_agent(
    state: AgentState,
    adapter: ChatModelAdapterBase,
    tool_gateway: ToolGatewayBase,
    template_gateway: TemplateGatewayBase,
) -> AgentState:
    """Make the plan once, then run THINK / ACT / OBSERVE until THINK finishes or the limit hits.

    Args:
        state: A fresh run state (no plan, no steps); it is changed in place.
        adapter: The chat model every stage calls.
        tool_gateway: Runs ACT's tool calls.
        template_gateway: Lists and fills the scenario templates for the plan node.

    Returns:
        The same state, with plan, steps, stop_reason and (on a finish) final_answer set.
    """
    await run_plan_node(state, adapter, template_gateway)
    return await run_react_loop(state, adapter, tool_gateway)
