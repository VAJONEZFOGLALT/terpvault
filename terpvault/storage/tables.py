from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import String, Boolean, Numeric, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from terpvault.storage.database import Base


def _now():
    return datetime.now(timezone.utc)


class SupplierRow(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    config: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    brand: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category: Mapped[str | None] = mapped_column(String(512), nullable=True)
    collection: Mapped[str | None] = mapped_column(String(256), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    options: Mapped[str] = mapped_column(Text, default="[]")
    extra_metadata: Mapped[str] = mapped_column("metadata", Text, default="{}")
    raw: Mapped[str] = mapped_column(Text, default="{}")
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    variants: Mapped[list["VariantRow"]] = relationship("VariantRow", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[list["ImageRow"]] = relationship("ImageRow", back_populates="product", cascade="all, delete-orphan")


class VariantRow(Base):
    __tablename__ = "variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(256), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    options: Mapped[str] = mapped_column(Text, default="{}")
    position: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["ProductRow"] = relationship("ProductRow", back_populates="variants")


class ImageRow(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    alt_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    product: Mapped["ProductRow"] = relationship("ProductRow", back_populates="images")


class SnapshotRow(Base):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    products: Mapped[str] = mapped_column(Text, nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, nullable=False)
    importer_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
