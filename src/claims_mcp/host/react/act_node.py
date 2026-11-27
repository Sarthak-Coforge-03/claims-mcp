"""ACT node: turn THINK's next action into one tool call and run it; OBSERVE always follows."""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.react.views import build_act_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.react_phase import ReactPhase
from claims_mcp.host.system_prompts.act_system_prompt import ACT_SYSTEM_PROMPT
from claims_mcp.host.tools.tool_gateway_base import ToolGatewayBase

EXPECTED_TOOL_CALL_COUNT = 1


async def run_act_node(
    state: AgentState, adapter: ChatModelAdapterBase, tool_gateway: ToolGatewayBase
) -> None:
    """Ask the model for the tool call, run it, and record the call and its result.

    A reply with no tool call, or several, is recorded as action_error and no tool runs:
    the run never ends here, THINK sees the error after OBSERVE and chooses again.

    Args:
        state: The run state; its current step gets action and tool_result, or action_error.
        adapter: The chat model; called once with all of state.tool_specs.
        tool_gateway: Runs the chosen tool.

    Side effects:
        Sets state.next_phase to OBSERVE.
    """
    conversation = Conversation.start(
        ACT_SYSTEM_PROMPT, build_act_view(state), tool_specs=state.tool_specs
    )
    act_turn = adapter.complete(conversation)
    current_step = state.current_step

    if len(act_turn.tool_calls) == EXPECTED_TOOL_CALL_COUNT:
        tool_call = act_turn.tool_calls[0]
        current_step.action = tool_call
        current_step.tool_result = await tool_gateway.call_tool(tool_call)
    else:
        current_step.action_error = (
            f"ACT made {len(act_turn.tool_calls)} tool calls; it replied: {act_turn.text}"
        )
    state.next_phase = ReactPhase.OBSERVE
