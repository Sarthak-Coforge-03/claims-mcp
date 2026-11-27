"""CatalogItem: the kinds of equipment that can be requested (docs/requirements.md §3)."""

from enum import StrEnum


class CatalogItem(StrEnum):
    """Every requestable item kind; anything else is "not in the catalog" (rule ESC-2).

    A StrEnum member equals its string value (CatalogItem.LAPTOP == "laptop"), so JSON stays plain.
    Details such as brand or model would be extra fields on the equipment record, not new members.
    """

    LAPTOP = "laptop"
    MONITOR = "monitor"
    DOCKING_STATION = "docking_station"
    HEADSET = "headset"
    KEYBOARD = "keyboard"
    PHONE = "phone"
