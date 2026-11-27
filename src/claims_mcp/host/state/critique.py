"""Critique: CRITIQUE's structured review of THINK's draft decision."""

from pydantic import BaseModel, Field


class Critique(BaseModel):
    """Four yes/no answers about the draft, plus each problem found; REVISE runs if any fail.

    The model fills this in through structured outputs, so field descriptions are its instructions.
    """

    addresses_request: bool = Field(
        description="True if the draft directly answers the employee's specific request."
    )
    follows_policy: bool = Field(
        description="True if the outcome and rule_id follow the equipment rules, given the "
        "tool results."
    )
    avoids_unconfirmed_promises: bool = Field(
        description="True if the response promises nothing the tool results don't confirm "
        "(no delivery dates, device models, costs or unapproved exceptions)."
    )
    matches_tool_results: bool = Field(
        description="True if every call the decision depends on was made and succeeded, and the "
        "outcome, rule_id, IDs and dates agree with what those calls returned."
    )
    issues: list[str] = Field(
        description="Each problem found, naming the tool result it conflicts with. Empty if none."
    )

    @property
    def is_satisfied(self) -> bool:
        """Return whether the draft passed: all four answers yes and no issues listed.

        Returns:
            True when no revision is needed.
        """
        all_answers_yes = (
            self.addresses_request
            and self.follows_policy
            and self.avoids_unconfirmed_promises
            and self.matches_tool_results
        )
        return all_answers_yes and not self.issues
