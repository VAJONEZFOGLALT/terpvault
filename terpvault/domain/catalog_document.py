from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SectionType(str, Enum):
    brand = "brand"
    collection = "collection"
    category = "category"


class CoverInfo(BaseModel):
    supplier_name: str
    catalog_label: str
    generated_at: str = ""
    product_count: int = 0
    brand_count: int = 0


class TocEntry(BaseModel):
    label: str
    section_index: int = 0
    page_number: int = 0


class SectionInfo(BaseModel):
    index: int = 0
    type: SectionType = SectionType.collection
    label: str = ""
    subtitle: str = ""
    product_ids: list[str] = Field(default_factory=list)


class CatalogProduct(BaseModel):
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


class CatalogStats(BaseModel):
    model_config = {"frozen": True}
    product_count: int = 0
    brand_count: int = 0
    section_count: int = 0
    variant_count: int = 0
    image_count: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CatalogDocument(BaseModel):
    model_config = {"frozen": True}

    supplier_slug: str
    supplier_name: str = ""
    cover: CoverInfo = Field(default_factory=CoverInfo)
    toc: list[TocEntry] = Field(default_factory=list)
    sections: list[SectionInfo] = Field(default_factory=list)
    products: dict[str, CatalogProduct] = Field(default_factory=dict)
    stats: CatalogStats = Field(default_factory=CatalogStats)
