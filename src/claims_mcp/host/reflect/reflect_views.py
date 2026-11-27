"""Views for reflection: CRITIQUE and REVISE see the draft next to the raw tool results.

Unlike THINK, reflection reads the raw results, so it can catch what OBSERVE's readings lost.
"""

from claims_mcp.host.react.views import render_action
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.request_decision import RequestDecision

NO_ISSUES = "none"


def build_critique_view(state: AgentState, code_issues: list[str]) -> str:
    """Return CRITIQUE's view: request, today, the draft, every call's raw result, code issues.

    Args:
        state: A finished run state with request_decision set (the draft).
        code_issues: The issues find_decision_issues reported.

    Returns:
        Text sections separated by blank lines, ending with "Code checks found:".
    """
    sections = [
        f"Request: {state.request}",
        f"Today: {state.today.isoformat()}",
        render_draft_decision(state.request_decision),
        render_tool_calls(state),
        "Code checks found:\n" + render_bullets(code_issues),
    ]
    return "\n\n".join(sections)


def build_revise_view(state: AgentState, critique: Critique) -> str:
    """Return REVISE's view: request, today, the draft, every call's raw result, the critique.

    Args:
        state: A finished run state with request_decision set (the draft).
        critique: CRITIQUE's review, which did not pass.

    Returns:
        Text sections separated by blank lines, ending with the critique's answers and issues.
    """
    sections = [
        f"Request: {state.request}",
        f"Today: {state.today.isoformat()}",
        render_draft_decision(state.request_decision),
        render_tool_calls(state),
        render_critique(critique),
    ]
    return "\n\n".join(sections)


def render_draft_decision(request_decision: RequestDecision) -> str:
    """Return the draft decision's fields, one per line.

    Args:
        request_decision: THINK's draft.

    Returns:
        A "Draft decision:" block with outcome, rule_id, the three IDs and the response.
    """
    return (
        "Draft decision:\n"
        f"- outcome: {request_decision.outcome}\n"
        f"- rule_id: {request_decision.rule_id}\n"
        f"- policy_rule_id: {request_decision.policy_rule_id}\n"
        f"- eligible_from_date: {request_decision.eligible_from_date}\n"
        f"- escalation_id: {request_decision.escalation_id}\n"
        f"- response: {request_decision.response}"
    )


def render_tool_calls(state: AgentState) -> str:
    """Return each call made, oldest first, with its raw result or its action error.

    Args:
        state: The run state.

    Returns:
        A "Tool calls and raw results:" block; "none" if no call was made.
    """
    call_blocks = []
    for step in state.steps:
        if step.action is not None:
            error_marker = " [error]" if step.tool_result.is_error else ""
            call_blocks.append(
                f"{render_action(step.action)}\nResult{error_marker}: {step.tool_result.content}"
            )
        elif step.action_error is not None:
            call_blocks.append(f"Action error: {step.action_error}")
    if not call_blocks:
        return "Tool calls and raw results: " + NO_ISSUES
    return "Tool calls and raw results:\n" + "\n\n".join(call_blocks)


def render_critique(critique: Critique) -> str:
    """Return the critique's four answers and its issues.

    Args:
        critique: CRITIQUE's review.

    Returns:
        A "Critique:" block, then "Issues:" with one bullet per issue.
    """
    return (
        "Critique:\n"
        f"- addresses_request: {critique.addresses_request}\n"
        f"- follows_policy: {critique.follows_policy}\n"
        f"- avoids_unconfirmed_promises: {critique.avoids_unconfirmed_promises}\n"
        f"- matches_tool_results: {critique.matches_tool_results}\n"
        "Issues:\n" + render_bullets(critique.issues)
    )


def render_bullets(lines: list[str]) -> str:
    """Return the lines as "- " bullets, or "none" when there are none.

    Args:
        lines: The items to list.

    Returns:
        One bullet per line, joined by newlines.
    """
    if not lines:
        return NO_ISSUES
    return "\n".join(f"- {line}" for line in lines)
