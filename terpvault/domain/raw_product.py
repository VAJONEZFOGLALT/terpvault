from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class RawProduct(BaseModel):
    external_id: str
    name: str
    description: str = ""
    brand: Optional[str] = None
    category: Optional[str] = None
    collection: Optional[str] = None
    available: bool = True
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    unit: Optional[str] = None
    size: Optional[str] = None
    options: list[dict] = Field(default_factory=list)
    variants: list[dict] = Field(default_factory=list)
    images: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    raw: dict = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
