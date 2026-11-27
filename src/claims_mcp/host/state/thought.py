"""Thought: THINK's structured output, the only place the run is declared finished."""

from pydantic import BaseModel, Field

from claims_mcp.host.state.enums import ThoughtDecision
from claims_mcp.host.state.request_decision import RequestDecision


class Thought(BaseModel):
    """THINK's established facts, its choice, and either the next action or the request decision.

    The model fills this in through structured outputs, so field descriptions are its instructions.
    No field asks for the model's reasoning: Claude's safeguards refuse that
    (refusal category "reasoning_extraction"), so the first field asks for established facts.
    """

    established_facts: str = Field(
        description="The facts the observations so far have established about the request."
    )
    decision: ThoughtDecision = Field(
        description="continue to run one more action, or finish when the request is decided."
    )
    next_action: str | None = Field(
        description="When continuing: the one tool to call, its arguments, and why. Else null."
    )
    request_decision: RequestDecision | None = Field(
        description="When finishing: the decision on the request, its rule and the reply to the "
        "employee. Else null."
    )
