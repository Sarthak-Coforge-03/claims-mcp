"""CRITIQUE node: review THINK's draft once, and record the reflection in the state."""

from claims_mcp.host.llm.adapters.chat_model_adapter_base import ChatModelAdapterBase
from claims_mcp.host.llm.models.conversation import Conversation
from claims_mcp.host.reflect.decision_checks import find_decision_issues
from claims_mcp.host.reflect.reflect_views import build_critique_view
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.reflection import Reflection
from claims_mcp.host.system_prompts.critique_system_prompt import CRITIQUE_SYSTEM_PROMPT


async def run_critique_node(state: AgentState, adapter: ChatModelAdapterBase) -> Critique:
    """Run the code checks, ask the model to critique the draft, and record both.

    Args:
        state: A finished run state with request_decision set (the draft); gets reflection.
        adapter: The chat model; called once, structured, with no tools.

    Returns:
        The critique, so the caller can decide whether REVISE runs.
    """
    code_issues = find_decision_issues(state)
    conversation = Conversation.start(
        CRITIQUE_SYSTEM_PROMPT, build_critique_view(state, code_issues), tool_specs=[]
    )
    critique = adapter.complete_structured(conversation, Critique)
    state.reflection = Reflection(
        code_issues=code_issues,
        critique=critique,
        draft_decision=state.request_decision,
        revised_decision=None,
    )
    return critique
