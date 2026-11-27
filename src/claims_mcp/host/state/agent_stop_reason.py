"""AgentStopReason: why a run ended."""

from enum import StrEnum


class AgentStopReason(StrEnum):
    """final_answer = THINK finished; step_limit = max_steps cycles ran without a finish."""

    FINAL_ANSWER = "final_answer"
    STEP_LIMIT = "step_limit"
