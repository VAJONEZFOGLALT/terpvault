from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SupplierData(BaseModel):
    slug: str
    name: str
    config: dict = Field(default_factory=dict)


class ProductData(BaseModel):
    external_id: str
    name: str
    description: str = ""
    brand: Optional[str] = None
    category: Optional[str] = None
    collection: Optional[str] = None
    available: bool = True
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    unit: Optional[str] = None
    size: Optional[str] = None
    options: list[dict] = Field(default_factory=list)
    variants: list[dict] = Field(default_factory=list)
    images: list["ImageData"] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    raw: dict = Field(default_factory=dict)


class VariantData(BaseModel):
    sku: str
    price: Optional[Decimal] = None
    available: bool = True
    options: dict = Field(default_factory=dict)
    position: int = 0


class ImageData(BaseModel):
    url: str
    position: int = 0
    alt_text: Optional[str] = None


class SnapshotData(BaseModel):
    supplier_slug: str
    products: list[ProductData]
    product_count: int
    importer_version: str = "1.0.0"
