import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from terpvault.domain.models import ProductData, VariantData, ImageData, SupplierData, SnapshotData
from terpvault.storage.tables import SupplierRow, ProductRow, VariantRow, ImageRow, SnapshotRow


class SupplierRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create(self, data: SupplierData) -> SupplierRow:
        row = self.session.query(SupplierRow).filter_by(slug=data.slug).first()
        if row:
            row.name = data.name
            row.config = json.dumps(data.config)
            return row
        row = SupplierRow(
            id=str(uuid.uuid4()),
            slug=data.slug,
            name=data.name,
            config=json.dumps(data.config),
        )
        self.session.add(row)
        return row

    def get_by_slug(self, slug: str) -> Optional[SupplierRow]:
        return self.session.query(SupplierRow).filter_by(slug=slug).first()


class ProductRepo:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, supplier_id: str, data: ProductData) -> ProductRow:
        row = self.session.query(ProductRow).filter_by(
            supplier_id=supplier_id, external_id=data.external_id
        ).first()
        if row:
            row.name = data.name
            row.description = data.description
            row.brand = data.brand
            row.category = data.category
            row.collection = data.collection
            row.available = data.available
            row.price = data.price
            row.compare_at_price = data.compare_at_price
            row.unit = data.unit
            row.size = data.size
            row.options = json.dumps(data.options)
            row.extra_metadata = json.dumps(data.metadata)
            row.raw = json.dumps(data.raw)
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = ProductRow(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                external_id=data.external_id,
                name=data.name,
                description=data.description,
                brand=data.brand,
                category=data.category,
                collection=data.collection,
                available=data.available,
                price=data.price,
                compare_at_price=data.compare_at_price,
                unit=data.unit,
                size=data.size,
                options=json.dumps(data.options),
                extra_metadata=json.dumps(data.metadata),
                raw=json.dumps(data.raw),
            )
            self.session.add(row)
        self.session.flush()
        return row

    def all_by_supplier(self, supplier_id: str) -> list[ProductRow]:
        return self.session.query(ProductRow).filter_by(supplier_id=supplier_id).all()

    def count_by_supplier(self, supplier_id: str) -> int:
        return self.session.query(ProductRow).filter_by(supplier_id=supplier_id).count()


class VariantRepo:
    def __init__(self, session: Session):
        self.session = session

    def upsert_batch(self, product_id: str, variants: list[VariantData]) -> list[VariantRow]:
        self.session.query(VariantRow).filter_by(product_id=product_id).delete()
        rows = []
        for v in variants:
            row = VariantRow(
                id=str(uuid.uuid4()),
                product_id=product_id,
                sku=v.sku,
                price=v.price,
                available=v.available,
                options=json.dumps(v.options),
                position=v.position,
            )
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows


class ImageRepo:
    def __init__(self, session: Session):
        self.session = session

    def upsert_batch(self, product_id: str, images: list[ImageData]) -> list[ImageRow]:
        self.session.query(ImageRow).filter_by(product_id=product_id).delete()
        rows = []
        for img in images:
            row = ImageRow(
                id=str(uuid.uuid4()),
                product_id=product_id,
                url=img.url,
                position=img.position,
                alt_text=img.alt_text,
            )
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows


class SnapshotRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: SnapshotData) -> SnapshotRow:
        products_json = json.dumps(
            [p.model_dump(mode="json") for p in data.products],
            default=str,
        )
        row = SnapshotRow(
            id=str(uuid.uuid4()),
            supplier_slug=data.supplier_slug,
            products=products_json,
            product_count=data.product_count,
            importer_version=data.importer_version,
            checksum="",
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def count_by_supplier(self, supplier_slug: str) -> int:
        return self.session.query(SnapshotRow).filter_by(supplier_slug=supplier_slug).count()

    def get_previous(self, supplier_slug: str, before_id: str) -> Optional[SnapshotRow]:
        return self.session.query(SnapshotRow).filter(
            SnapshotRow.supplier_slug == supplier_slug,
            SnapshotRow.id != before_id,
        ).order_by(SnapshotRow.created_at.desc()).first()

    def get_by_id(self, snapshot_id: str) -> Optional[SnapshotRow]:
        return self.session.query(SnapshotRow).filter_by(id=snapshot_id).first()


class ChangeRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, supplier_slug: str, source_snapshot_id: str | None, target_snapshot_id: str,
               changes_json: str, report_json: str, report_text: str,
               total_changes: int, major_count: int, normal_count: int, minor_count: int) -> "ChangeSetRow":
        from terpvault.storage.tables import ChangeSetRow
        row = ChangeSetRow(
            id=str(uuid.uuid4()),
            supplier_slug=supplier_slug,
            source_snapshot_id=source_snapshot_id,
            target_snapshot_id=target_snapshot_id,
            changes_json=changes_json,
            report_json=report_json,
            report_text=report_text,
            total_changes=total_changes,
            major_count=major_count,
            normal_count=normal_count,
            minor_count=minor_count,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def latest_by_supplier(self, supplier_slug: str) -> Optional["ChangeSetRow"]:
        from terpvault.storage.tables import ChangeSetRow
        return self.session.query(ChangeSetRow).filter_by(
            supplier_slug=supplier_slug
        ).order_by(ChangeSetRow.created_at.desc()).first()

    def count_by_supplier(self, supplier_slug: str) -> int:
        from terpvault.storage.tables import ChangeSetRow
        return self.session.query(ChangeSetRow).filter_by(supplier_slug=supplier_slug).count()
