"""Thought: THINK's structured output, the only place the run is declared finished."""

from pydantic import BaseModel, Field

from claims_mcp.host.state.thought_decision import ThoughtDecision


class Thought(BaseModel):
    """THINK's established facts, its decision, and either the next action or the final answer.

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
    final_answer: str | None = Field(
        description="When finishing: the reply to the employee with the decision and rule ID, "
        "plus the policy_rule_id, eligible-from date or escalation_id that applies. Else null."
    )
