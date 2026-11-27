"""The small enums the shared AgentState uses, grouped in one file (alphabetical)."""

from enum import StrEnum


class AgentStopReason(StrEnum):
    """final_answer = THINK finished with a request decision; step_limit = no finish in time."""

    FINAL_ANSWER = "final_answer"
    STEP_LIMIT = "step_limit"


class PlanSource(StrEnum):
    """mcp_template = a server scenario template fit the request; tool_descriptions = written."""

    MCP_TEMPLATE = "mcp_template"
    TOOL_DESCRIPTIONS = "tool_descriptions"


class ReactPhase(StrEnum):
    """The loop's next phase; THINK picks ACT or DONE, code forces ACT → OBSERVE → THINK."""

    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    DONE = "done"


class RequesterType(StrEnum):
    """Who is asking: an employee (standard or manager, from the record) or a contractor."""

    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"


class RequestOutcome(StrEnum):
    """approve or deny under the rules, or escalate to a human reviewer."""

    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"


class ThoughtDecision(StrEnum):
    """continue = one more tool call is needed; finish = the request is decided."""

    CONTINUE = "continue"
    FINISH = "finish"
