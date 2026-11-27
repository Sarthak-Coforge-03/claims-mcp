"""ReactPhase: which phase of the ReAct loop runs next."""

from enum import StrEnum


class ReactPhase(StrEnum):
    """The loop's next phase; THINK picks ACT or DONE, code forces ACT → OBSERVE → THINK."""

    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    DONE = "done"
