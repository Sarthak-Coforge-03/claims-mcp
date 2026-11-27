"""AgentState: the one object the ReAct loop passes between phases."""

from datetime import date

from pydantic import BaseModel

from claims_mcp.host.llm.models.tool_spec import ToolSpec
from claims_mcp.host.state.enums import AgentStopReason, ReactPhase, RequesterType
from claims_mcp.host.state.plan import Plan
from claims_mcp.host.state.react_step import ReActStep
from claims_mcp.host.state.reflection import Reflection
from claims_mcp.host.state.request_decision import RequestDecision


class AgentState(BaseModel):
    """Inputs, progress and outcome of one run; each phase reads a view of it and writes back.

    The plan node writes plan before the loop; reflection is written after it, once.
    requester_name is given by a contractor; for an employee, ACT copies it from the record.
    """

    requester_type: RequesterType
    employee_id: str | None
    requester_name: str | None = None
    request: str
    today: date
    tool_specs: list[ToolSpec]
    max_steps: int
    plan: Plan | None = None
    steps: list[ReActStep] = []
    next_phase: ReactPhase = ReactPhase.THINK
    request_decision: RequestDecision | None = None
    reflection: Reflection | None = None
    stop_reason: AgentStopReason | None = None

    @property
    def current_step(self) -> ReActStep:
        """Return the step being filled in: the last one THINK started.

        Returns:
            The newest ReActStep. Only called after THINK has added one (ACT, OBSERVE).
        """
        return self.steps[-1]
