"""Two code checks on THINK's decision, passed to the reflection model review as hints.

The model review does the full comparison against the tool results; these catch the two
mistakes that are certain from the state alone, without asking a model.
"""

from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.enums import RequestOutcome

ESCALATION_TOOL_NAME = "flag_for_human_review"
# Mirrors the rule tables in docs/requirements.md (sections 5 and 6).
KNOWN_RULE_IDS = {
    "ELG-1",
    "ELG-2",
    "ELG-3",
    "DEN-1",
    "DEN-2",
    "ESC-1",
    "ESC-2",
    "ESC-3",
    "ESC-4",
    "ESC-5",
    "ESC-6",
    "ESC-7",
}


def find_decision_issues(state: AgentState) -> list[str]:
    """Return the certain issues with the decision: an unknown rule, or an escalation not filed.

    Args:
        state: A finished run state with request_decision set.

    Returns:
        One sentence per issue; empty when both checks pass.
    """
    request_decision = state.request_decision
    decision_issues = []
    if request_decision.rule_id not in KNOWN_RULE_IDS:
        decision_issues.append(
            f"rule_id {request_decision.rule_id} is not a rule in docs/requirements.md."
        )
    if request_decision.outcome == RequestOutcome.ESCALATE and not has_filed_escalation(state):
        decision_issues.append(
            f"Outcome is escalate, but {ESCALATION_TOOL_NAME} never returned a result."
        )
    return decision_issues


def has_filed_escalation(state: AgentState) -> bool:
    """Return whether any step called flag_for_human_review and got a non-error result.

    Args:
        state: The run state.

    Returns:
        True when an escalation was actually saved.
    """
    for step in state.steps:
        is_escalation_call = step.action is not None and step.action.name == ESCALATION_TOOL_NAME
        if is_escalation_call and step.tool_result is not None and not step.tool_result.is_error:
            return True
    return False
