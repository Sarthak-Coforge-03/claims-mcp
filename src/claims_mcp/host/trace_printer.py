"""Prints a finished run's Thought / Action / Observation trace, read from the AgentState alone."""

from claims_mcp.host.react.views import render_action, render_plan
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.react_step import ReActStep

NO_ANSWER = "no answer (step limit reached)"


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
    print(f"Final answer: {state.final_answer or NO_ANSWER}")


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
    if thought.final_answer is not None:
        lines.append(f"Finish: {thought.final_answer}")
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
