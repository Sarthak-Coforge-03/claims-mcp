"""EligibilityRule: the rule IDs an eligibility check can report (docs/requirements.md §5–6)."""

from enum import StrEnum


class EligibilityRule(StrEnum):
    """Which rule decided an eligibility check; the agent cites this ID in its decision."""

    ELG_1 = "ELG-1"  # holds fewer than the max → eligible (new allocation)
    ELG_2 = "ELG-2"  # at the max, newest unit old enough → eligible (replacement)
    ELG_3 = "ELG-3"  # at the max, newest unit too recent → not eligible yet
    DEN_2 = "DEN-2"  # catalog item the role isn't entitled to
    ESC_2 = "ESC-2"  # item not in the catalog, so it can't be assessed
