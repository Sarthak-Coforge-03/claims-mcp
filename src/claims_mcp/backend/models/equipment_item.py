"""The EquipmentItem model: one piece of equipment held by an employee."""

from datetime import date

from pydantic import BaseModel


class EquipmentItem(BaseModel):
    """One piece of equipment on an employee's record and the date it was issued."""

    item: str
    issued_date: date
