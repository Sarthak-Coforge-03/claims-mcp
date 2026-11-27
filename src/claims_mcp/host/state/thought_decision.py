"""ThoughtDecision: THINK's choice to run another action or to finish the request."""

from enum import StrEnum


class ThoughtDecision(StrEnum):
    """continue = one more tool call is needed; finish = the request is decided."""

    CONTINUE = "continue"
    FINISH = "finish"
