"""Plan: the steps generated once, before the ReAct loop, that THINK follows."""

from pydantic import BaseModel

from claims_mcp.host.state.plan_source import PlanSource


class Plan(BaseModel):
    """The plan's text, where it came from, and the template's name when one was used.

    template_name is None when source is TOOL_DESCRIPTIONS.
    """

    source: PlanSource
    template_name: str | None
    text: str
