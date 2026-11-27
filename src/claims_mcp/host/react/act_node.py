"""ACT node: turn THINK's next action into one tool call and run it; OBSERVE always follows."""

import json

from claims_mcp.host.gateways.tools.tool_gateway_base import ToolGatewayBase
from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_result import ToolResult
from claims_mcp.host.react.prompts.act_system_prompt import ACT_SYSTEM_PROMPT
from claims_mcp.host.react.views import build_act_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import ReactPhase

EXPECTED_TOOL_CALL_COUNT = 1
EMPLOYEE_LOOKUP_TOOL_NAME = "get_employee_info"


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
        record_requester_name(state, tool_call, current_step.tool_result)
    else:
        current_step.action_error = (
            f"ACT made {len(act_turn.tool_calls)} tool calls; it replied: {act_turn.text}"
        )
    state.next_phase = ReactPhase.OBSERVE


def record_requester_name(state: AgentState, tool_call: ToolCall, tool_result: ToolResult) -> None:
    """Copy the employee's name from a successful employee lookup into the state.

    The name then comes from the record, not from the model, and every later view shows it.

    Args:
        state: The run state; gets requester_name.
        tool_call: The call ACT just ran.
        tool_result: What it returned.

    Side effects:
        Sets state.requester_name when tool_call is get_employee_info, the result is not an
        error, and its JSON has a "name"; otherwise leaves the state as it is.
    """
    if tool_call.name != EMPLOYEE_LOOKUP_TOOL_NAME or tool_result.is_error:
        return
    employee_record = json.loads(tool_result.content)
    if employee_record.get("name"):
        state.requester_name = employee_record["name"]
