from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    product_added = "product_added"
    product_removed = "product_removed"
    product_updated = "product_updated"
    variant_added = "variant_added"
    variant_removed = "variant_removed"
    variant_updated = "variant_updated"
    image_added = "image_added"
    image_removed = "image_removed"
    image_updated = "image_updated"


class FieldChange(BaseModel):
    field: str
    old_value: Any = None
    new_value: Any = None


class ChangeEntry(BaseModel):
    change_type: ChangeType
    product_external_id: str
    product_name: str
    fields_changed: list[FieldChange] = Field(default_factory=list)
    old_values: dict[str, Any] = Field(default_factory=dict)
    new_values: dict[str, Any] = Field(default_factory=dict)


class ChangeSet(BaseModel):
    source_snapshot_id: str = ""
    target_snapshot_id: str = ""
    entries: list[ChangeEntry] = Field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.entries)

    @property
    def has_changes(self) -> bool:
        return len(self.entries) > 0
