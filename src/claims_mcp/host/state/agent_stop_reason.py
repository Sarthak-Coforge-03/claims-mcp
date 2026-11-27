"""AgentStopReason: why a run ended."""

from enum import StrEnum


class AgentStopReason(StrEnum):
    """final_answer = THINK finished with a request decision; step_limit = no finish in time."""

    FINAL_ANSWER = "final_answer"
    STEP_LIMIT = "step_limit"
