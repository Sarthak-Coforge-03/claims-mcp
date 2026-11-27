"""Reflection: CRITIQUE the draft once, then REVISE only if the critique didn't pass.

Whatever this produces is final; the run never loops back to the ReAct loop.
"""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.reflect.critique_node import run_critique_node
from claims_mcp.host.reflect.revise_node import run_revise_node
from claims_mcp.host.state.agent_state import AgentState


async def run_reflection(state: AgentState, adapter: ChatModelAdapterBase) -> None:
    """Critique THINK's draft and, if it falls short, replace it with a revision.

    Args:
        state: A finished run state with request_decision set (the draft).
        adapter: The chat model both nodes call.

    Side effects:
        Sets state.reflection; replaces state.request_decision when REVISE runs.
    """
    critique = await run_critique_node(state, adapter)
    if not critique.is_satisfied:
        await run_revise_node(state, adapter, critique)
