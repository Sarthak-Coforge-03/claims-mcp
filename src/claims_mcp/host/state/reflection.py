"""Reflection: the record of CRITIQUE and the optional REVISE, kept in the state as evidence."""

from pydantic import BaseModel

from claims_mcp.host.state.critique import Critique
from claims_mcp.host.state.request_decision import RequestDecision


class Reflection(BaseModel):
    """The code-check issues, the critique, THINK's draft and, if REVISE ran, its revision.

    revised_decision is None when the critique passed; state.request_decision is always final.
    """

    code_issues: list[str]
    critique: Critique
    draft_decision: RequestDecision
    revised_decision: RequestDecision | None
