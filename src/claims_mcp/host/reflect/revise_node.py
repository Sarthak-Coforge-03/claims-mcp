"""REVISE node: rewrite the draft to fix the critique; the revision becomes the final decision."""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.reflect.prompts.revise_system_prompt import REVISE_SYSTEM_PROMPT
from claims_mcp.host.reflect.reflect_views import build_revise_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.request_decision import RequestDecision


async def run_revise_node(
    state: AgentState, adapter: ChatModelAdapterBase, critique: Critique
) -> None:
    """Ask the model for a corrected decision and make it final, keeping the draft on record.

    Args:
        state: The run state after CRITIQUE; state.reflection holds the draft.
        adapter: The chat model; called once, structured, with no tools.
        critique: CRITIQUE's review that did not pass.

    Side effects:
        Sets state.reflection.revised_decision and replaces state.request_decision.
    """
    conversation = Conversation.start(
        REVISE_SYSTEM_PROMPT, build_revise_view(state, critique), tool_specs=[]
    )
    revised_decision = adapter.complete_structured(conversation, RequestDecision)
    state.reflection.revised_decision = revised_decision
    state.request_decision = revised_decision
