"""run_agent: the whole agent on one shared state: plan, then the ReAct loop, then reflection.

Each stage reads and writes the same AgentState; reflection's result is final (no loop back).
"""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.plan.plan_node import run_plan_node
from claims_mcp.host.react.react_loop import run_react_loop
from claims_mcp.host.reflect.run_reflection import run_reflection
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.templates.template_gateway_base import TemplateGatewayBase
from claims_mcp.host.tools.tool_gateway_base import ToolGatewayBase


async def run_agent(
    state: AgentState,
    adapter: ChatModelAdapterBase,
    tool_gateway: ToolGatewayBase,
    template_gateway: TemplateGatewayBase,
) -> AgentState:
    """Plan once, run THINK / ACT / OBSERVE until a finish or the limit, then reflect on a finish.

    Args:
        state: A fresh run state (no plan, no steps); it is changed in place.
        adapter: The chat model every stage calls.
        tool_gateway: Runs ACT's tool calls.
        template_gateway: Lists and fills the scenario templates for the plan node.

    Returns:
        The same state, with plan, steps and stop_reason set; on a finish also reflection and
        the final request_decision (THINK's draft, or REVISE's revision).
    """
    await run_plan_node(state, adapter, template_gateway)
    await run_react_loop(state, adapter, tool_gateway)
    if state.request_decision is not None:
        await run_reflection(state, adapter)
    return state
