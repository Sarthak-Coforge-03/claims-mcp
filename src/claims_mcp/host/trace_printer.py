"""Prints a finished run's Thought / Action / Observation trace, read from the AgentState alone."""

from claims_mcp.host.react.views import render_action, render_plan
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.request_decision import RequestDecision

NO_DECISION = "No decision (step limit reached)"


def print_trace(state: AgentState) -> None:
    """Print the request, the plan and where it came from, every step numbered, then the outcome.

    Args:
        state: The state run_react_loop returned.
    """
    print(f"Request: {state.request}\n")
    if state.plan is not None:
        print(render_plan(state.plan))
        print()
    for step_number, step in enumerate(state.steps, start=1):
        print(f"--- Step {step_number} ---")
        print(render_step_for_trace(step))
        print()
    print(f"Stop reason: {state.stop_reason}")
    if state.request_decision is None:
        print(NO_DECISION)
    else:
        print(render_request_decision(state.request_decision))


def render_request_decision(request_decision: RequestDecision) -> str:
    """Return the decision as lines: outcome and rule, the supporting IDs that are set, the reply.

    Args:
        request_decision: THINK's decision on the request.

    Returns:
        "Outcome: approve (ELG-2)", then policy_rule_id / eligible_from_date / escalation_id lines
        for the ones set, then "Response: ...".
    """
    lines = [f"Outcome: {request_decision.outcome} ({request_decision.rule_id})"]
    if request_decision.policy_rule_id is not None:
        lines.append(f"policy_rule_id: {request_decision.policy_rule_id}")
    if request_decision.eligible_from_date is not None:
        lines.append(f"eligible_from_date: {request_decision.eligible_from_date}")
    if request_decision.escalation_id is not None:
        lines.append(f"escalation_id: {request_decision.escalation_id}")
    lines.append(f"Response: {request_decision.response}")
    return "\n".join(lines)


def render_step_for_trace(step: ReActStep) -> str:
    """Return one step's lines: thought, next or finish, action, raw result, observation.

    Args:
        step: A recorded step; a FINISH step has only its thought.

    Returns:
        The step's lines joined by newlines; fields that are None are left out.
    """
    thought = step.thought
    lines = [f"Thought: {thought.established_facts}"]
    if thought.next_action is not None:
        lines.append(f"Next: {thought.next_action}")
    if thought.request_decision is not None:
        request_decision = thought.request_decision
        lines.append(f"Finish: {request_decision.outcome} under {request_decision.rule_id}")
    if step.action is not None:
        lines.append(render_action(step.action))
    if step.tool_result is not None:
        error_marker = " [error]" if step.tool_result.is_error else ""
        lines.append(f"Tool result{error_marker}: {step.tool_result.content}")
    if step.action_error is not None:
        lines.append(f"Action error: {step.action_error}")
    if step.observation is not None:
        lines.append(f"Observation: {step.observation}")
    return "\n".join(lines)
