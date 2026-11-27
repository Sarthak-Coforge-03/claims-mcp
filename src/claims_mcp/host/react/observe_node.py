"""OBSERVE node: have the model read the current tool result; THINK always follows."""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.react.prompts.observe_system_prompt import OBSERVE_SYSTEM_PROMPT
from claims_mcp.host.react.views import build_observe_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import ReactPhase


async def run_observe_node(state: AgentState, adapter: ChatModelAdapterBase) -> None:
    """Ask the model what the current result (or action error) establishes, and record it.

    Args:
        state: The run state; its current step gets the observation.
        adapter: The chat model; called once with no tools.

    Side effects:
        Sets state.next_phase to THINK.
    """
    conversation = Conversation.start(
        OBSERVE_SYSTEM_PROMPT, build_observe_view(state), tool_specs=[]
    )
    observe_turn = adapter.complete(conversation)
    state.current_step.observation = observe_turn.text
    state.next_phase = ReactPhase.THINK
