"""AgentState: the one object the ReAct loop passes between phases."""

from datetime import date

from pydantic import BaseModel

from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.state.agent_stop_reason import AgentStopReason
from claims_mcp.host.state.react_phase import ReactPhase
from claims_mcp.host.state.react_step import ReActStep


class AgentState(BaseModel):
    """Inputs, progress and outcome of one run; each phase reads a view of it and writes back.

    Later steps add plan, draft and reflection fields here rather than a second object.
    """

    request: str
    today: date
    tool_specs: list[ToolSpec]
    max_steps: int
    steps: list[ReActStep] = []
    next_phase: ReactPhase = ReactPhase.THINK
    final_answer: str | None = None
    stop_reason: AgentStopReason | None = None

    @property
    def current_step(self) -> ReActStep:
        """Return the step being filled in: the last one THINK started.

        Returns:
            The newest ReActStep. Only called after THINK has added one (ACT, OBSERVE).
        """
        return self.steps[-1]
