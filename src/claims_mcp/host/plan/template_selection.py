"""TemplateSelection: SELECT's structured output, the template that fits plus its arguments."""

from pydantic import BaseModel, Field


class TemplateSelection(BaseModel):
    """The one template whose description fits the request, and the request's details.

    The model fills this in through structured outputs, so field descriptions are its instructions.
    The code still checks template_name against the catalog before using it.
    """

    template_name: str | None = Field(
        description="The name of the one template whose description fits the request, "
        "exactly as listed. Null if no description fits."
    )
    employee_id: str | None = Field(
        description="The employee ID as written in the request, e.g. E001. Null if none is given."
    )
    item: str | None = Field(
        description="The requested item in the request's own words, e.g. monitor. Null if none."
    )
    reason: str = Field(description="The employee's reason, quoted. Empty if none is given.")
    quantity: str = Field(description='How many units, as digits, e.g. "3"; "1" if not stated.')
