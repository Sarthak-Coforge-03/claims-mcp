"""TemplateSpec: one scenario template the plan node can pick, in a provider-neutral shape."""

from pydantic import BaseModel


class TemplateSpec(BaseModel):
    """A template's name and its description of when to use it; the plan node picks by these."""

    name: str
    description: str
