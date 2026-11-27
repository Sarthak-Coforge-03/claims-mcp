"""Views: the slice of AgentState each phase is shown, rendered as its one user message.

What a view leaves out is as deliberate as what it shows:
- THINK sees the plan and every step's interpretation (observation), never raw tool results.
- ACT sees only the request and the action THINK chose, so it can't decide anything else.
- OBSERVE sees only the current call and its raw result, so it reads that result alone.
"""

import json

from claims_mcp.host.llm.models.tool_call import ToolCall
from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.state.agent_state import AgentState
from claims_mcp.host.state.plan import Plan
from claims_mcp.host.state.plan_source import PlanSource
from claims_mcp.host.state.react_step import ReActStep

NO_STEPS_YET = "Steps so far: none yet."


def build_think_view(state: AgentState) -> str:
    """Return THINK's view: request, today, tool catalog, the plan, every earlier step's reading.

    Args:
        state: The run state.

    Returns:
        Text sections: request, today's date, available tools, the plan if one was made, then
        the steps so far (thought, action, action error, observation; no raw tool results).
    """
    sections = [
        f"Request: {state.request}",
        f"Today: {state.today.isoformat()}",
        render_tool_catalog(state.tool_specs),
    ]
    if state.plan is not None:
        sections.append(render_plan(state.plan))
    sections.append(render_steps_for_think(state.steps))
    return "\n\n".join(sections)


def render_plan(plan: Plan) -> str:
    """Return the plan under a heading that says where it came from.

    Args:
        plan: The plan the plan node wrote before the loop.

    Returns:
        "Plan (from MCP template <name>):" or "Plan (from tool descriptions):", then its text.
    """
    if plan.source == PlanSource.MCP_TEMPLATE:
        plan_origin = f"MCP template {plan.template_name}"
    else:
        plan_origin = "tool descriptions"
    return f"Plan (from {plan_origin}):\n{plan.text}"


def build_act_view(state: AgentState) -> str:
    """Return ACT's view: the request and the current thought's next action, nothing else.

    Args:
        state: The run state; its current step holds THINK's chosen next action.

    Returns:
        Two lines: "Request: ..." and "Next action: ...".
    """
    next_action = state.current_step.thought.next_action
    return f"Request: {state.request}\nNext action: {next_action}"


def build_observe_view(state: AgentState) -> str:
    """Return OBSERVE's view: the request, why the call was made, the call and its raw outcome.

    Args:
        state: The run state; its current step holds ACT's call and result (or action_error).

    Returns:
        Lines for the request and the intended action, then either the action and its tool
        result (marked [error] if the tool failed) or the action error when no tool ran.
    """
    current_step = state.current_step
    lines = [
        f"Request: {state.request}",
        f"Intended action: {current_step.thought.next_action}",
    ]
    if current_step.action_error is not None:
        lines.append(f"Action error: {current_step.action_error}")
    else:
        lines.append(render_action(current_step.action))
        error_marker = " [error]" if current_step.tool_result.is_error else ""
        lines.append(f"Tool result{error_marker}: {current_step.tool_result.content}")
    return "\n".join(lines)


def render_tool_catalog(tool_specs: list[ToolSpec]) -> str:
    """Return one line per tool, name and description; THINK plans from it without tools.

    Args:
        tool_specs: The tools the agent may use.

    Returns:
        An "Available tools:" block.
    """
    tool_lines = [f"- {tool_spec.name}: {tool_spec.description}" for tool_spec in tool_specs]
    return "Available tools:\n" + "\n".join(tool_lines)


def render_steps_for_think(steps: list[ReActStep]) -> str:
    """Return the finished steps for THINK, oldest first, without raw tool results.

    Args:
        steps: Every step so far.

    Returns:
        A "Steps so far:" block, one paragraph per step, or a note that there are none.
    """
    if not steps:
        return NO_STEPS_YET
    rendered_steps = [render_step_for_think(step) for step in steps]
    return "Steps so far:\n\n" + "\n\n".join(rendered_steps)


def render_step_for_think(step: ReActStep) -> str:
    """Return one step's thought, action, action error and observation as lines.

    Args:
        step: A recorded step.

    Returns:
        "Thought: ..." and "Next: ..." first, then whichever of the other fields are set.
    """
    lines = [
        f"Thought: {step.thought.established_facts}",
        f"Next: {step.thought.next_action}",
    ]
    if step.action is not None:
        lines.append(render_action(step.action))
    if step.action_error is not None:
        lines.append(f"Action error: {step.action_error}")
    if step.observation is not None:
        lines.append(f"Observation: {step.observation}")
    return "\n".join(lines)


def render_action(action: ToolCall) -> str:
    """Return a tool call as one line, "Action: name({arguments as JSON})".

    Args:
        action: The tool call ACT made.

    Returns:
        The action line.
    """
    return f"Action: {action.name}({json.dumps(action.arguments)})"
