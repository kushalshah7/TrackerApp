from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class EntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any]

    @field_validator("data")
    @classmethod
    def clean(cls, value):
        cleaned = {}
        for key, item in value.items():
            if isinstance(item, str):
                item = item.rstrip() if "Week " in key or key in {"Remarks", "Discussion Points", "Action Items"} else item.strip()
                item = item or None
            if key in {"Value (₹)", "Deal Value"} and item is not None:
                try: item = float(item)
                except (TypeError, ValueError): raise ValueError(f"{key} must be numeric")
                if item < 0: raise ValueError(f"{key} cannot be negative")
            if key in {"Date", "PO Date", "Expected Completion Date"} and item:
                try: item = date.fromisoformat(str(item))
                except ValueError: raise ValueError(f"{key} must be a valid ISO date")
            cleaned[key] = item
        return cleaned

class StatusPayload(BaseModel):
    status: Literal["Pending", "Completed"]
    up_to: str | None = Field(default=None, max_length=120)
