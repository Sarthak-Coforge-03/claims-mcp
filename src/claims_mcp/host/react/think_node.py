"""THINK node: the one phase that chooses where the run goes next (ACT, or DONE)."""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.react.prompts.think_system_prompt import THINK_SYSTEM_PROMPT
from claims_mcp.host.react.views import build_think_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.agent_stop_reason import AgentStopReason
from claims_mcp.host.state.react_phase import ReactPhase
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.thought import Thought
from claims_mcp.host.state.thought_decision import ThoughtDecision


async def run_think_node(state: AgentState, adapter: ChatModelAdapterBase) -> None:
    """Ask the model for a Thought, start a new step with it, and route on its decision.

    Args:
        state: The run state; gets a new step, and on FINISH the request decision and stop reason.
        adapter: The chat model; called once, structured, with no tools.

    Side effects:
        Sets state.next_phase to ACT (continue) or DONE (finish).
    """
    conversation = Conversation.start(THINK_SYSTEM_PROMPT, build_think_view(state), tool_specs=[])
    thought = adapter.complete_structured(conversation, Thought)
    state.steps.append(ReActStep(thought=thought))

    if thought.decision == ThoughtDecision.FINISH:
        state.request_decision = thought.request_decision
        state.stop_reason = AgentStopReason.FINAL_ANSWER
        state.next_phase = ReactPhase.DONE
    else:
        state.next_phase = ReactPhase.ACT
