"""RequestDecision: THINK's decision on a finish, as data rather than prose."""

from pydantic import BaseModel, Field

from claims_mcp.host.state.enums import RequestOutcome


class RequestDecision(BaseModel):
    """The outcome, the deciding rule, its supporting IDs or dates, and the reply to the employee.

    The model fills this in through structured outputs, so field descriptions are its instructions.
    These are THINK's claims; reflection checks them against the tool results in the steps.
    """

    outcome: RequestOutcome = Field(description="approve, deny or escalate.")
    rule_id: str = Field(
        description='The one rule that decided the request, e.g. "ELG-2", "DEN-1" or "ESC-4", '
        "copied from a tool result or the escalation reason."
    )
    policy_rule_id: str | None = Field(
        description="The policy_rule_id from check_request_eligibility, e.g. POL-STD-MONITOR, "
        "when it returned one. Else null."
    )
    eligible_from_date: str | None = Field(
        description="The eligible_from_date (YYYY-MM-DD) from check_request_eligibility, "
        "for a DEN-1 deny. Else null."
    )
    escalation_id: str | None = Field(
        description="The escalation_id from flag_for_human_review's result, for an escalation. "
        "Else null."
    )
    response: str = Field(
        description="The reply to the employee: the decision, the rule ID and the supporting "
        "facts, using only facts from the observations."
    )
