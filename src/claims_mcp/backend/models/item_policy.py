"""ItemPolicy: one role's limit for one catalog item (docs/requirements.md §4)."""

from pydantic import BaseModel, Field

from claims_mcp.backend.models.catalog_item import CatalogItem


class ItemPolicy(BaseModel):
    """How many of one item a role may hold at once, and how often the newest may be replaced.

    An item a role isn't entitled to has no ItemPolicy at all, so max_held is always at least 1.
    """

    item: CatalogItem
    max_held: int = Field(ge=1)
    refresh_interval_months: int = Field(ge=1)
