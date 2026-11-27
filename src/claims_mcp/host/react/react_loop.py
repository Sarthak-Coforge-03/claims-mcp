"""The ReAct loop driver: run whichever node state.next_phase names until DONE.

The driver holds no domain logic and makes no routing decisions; the nodes set next_phase.
Its only rule is the step limit, checked before each THINK.
"""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.react.act_node import run_act_node
from claims_mcp.host.react.observe_node import run_observe_node
from claims_mcp.host.react.think_node import run_think_node
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.agent_stop_reason import AgentStopReason
from claims_mcp.host.state.react_phase import ReactPhase
from claims_mcp.host.tools.tool_gateway_base import ToolGatewayBase


async def run_react_loop(
    state: AgentState, adapter: ChatModelAdapterBase, tool_gateway: ToolGatewayBase
) -> AgentState:
    """Run THINK / ACT / OBSERVE as state.next_phase directs, until a node or the limit stops it.

    Args:
        state: The run state to advance; it is changed in place.
        adapter: The chat model every node calls.
        tool_gateway: Runs ACT's tool calls.

    Returns:
        The same state, finished: stop_reason FINAL_ANSWER (with final_answer) or STEP_LIMIT.
    """
    while state.next_phase != ReactPhase.DONE:
        if state.next_phase == ReactPhase.THINK and is_step_limit_reached(state):
            state.stop_reason = AgentStopReason.STEP_LIMIT
            state.next_phase = ReactPhase.DONE
        elif state.next_phase == ReactPhase.THINK:
            await run_think_node(state, adapter)
        elif state.next_phase == ReactPhase.ACT:
            await run_act_node(state, adapter, tool_gateway)
        elif state.next_phase == ReactPhase.OBSERVE:
            await run_observe_node(state, adapter)
    return state


def is_step_limit_reached(state: AgentState) -> bool:
    """Return whether max_steps cycles have already run, so no new THINK may start.

    Args:
        state: The run state.

    Returns:
        True when len(state.steps) is at least state.max_steps.
    """
    return len(state.steps) >= state.max_steps
