import hashlib
import json
from datetime import datetime, timezone
from importlib import import_module

from sqlalchemy.orm import Session

from terpvault.config.supplier_config import SupplierConfig
from terpvault.domain.models import SupplierData, ProductData, VariantData, ImageData, SnapshotData
from terpvault.domain.raw_product import RawProduct
from terpvault.storage.database import get_session
from terpvault.storage.repository import (
    SupplierRepo, ProductRepo, VariantRepo, ImageRepo, SnapshotRepo,
)
from terpvault.sync.importer.client import SupplierClient


class SyncEngine:
    def __init__(self, supplier_slug: str):
        self.supplier_slug = supplier_slug
        self.config = SupplierConfig.load(supplier_slug)

    async def run(self) -> dict:
        module_path, class_name = self.config.importer_module.rsplit(".", 1)
        module = import_module(module_path)
        importer_class = getattr(module, class_name)
        importer = importer_class(self.config)

        try:
            raw_products = await importer.fetch_products()
            return self._store(raw_products)
        finally:
            await importer.close()

    def _store(self, raw_products: list[RawProduct]) -> dict:
        session = get_session()
        try:
            supplier_repo = SupplierRepo(session)
            product_repo = ProductRepo(session)
            variant_repo = VariantRepo(session)
            image_repo = ImageRepo(session)
            snapshot_repo = SnapshotRepo(session)

            supplier_row = supplier_repo.get_or_create(
                SupplierData(slug=self.config.slug, name=self.config.name, config=self.config.model_dump(mode="json"))
            )
            session.flush()

            product_count = 0
            variant_count = 0
            image_count = 0
            products_for_snapshot = []

            for rp in raw_products:
                product_data = ProductData(
                    external_id=rp.external_id,
                    name=rp.name,
                    description=rp.description,
                    brand=rp.brand,
                    category=rp.category,
                    collection=rp.collection,
                    available=rp.available,
                    price=rp.price,
                    compare_at_price=rp.compare_at_price,
                    unit=rp.unit,
                    size=rp.size,
                    options=rp.options,
                    metadata=rp.metadata,
                    raw=rp.raw,
                )
                product_row = product_repo.upsert(supplier_row.id, product_data)

                variant_data_list = [
                    VariantData(
                        sku=v["sku"],
                        price=v.get("price"),
                        available=v.get("available", True),
                        options=v.get("options", {}),
                        position=v.get("position", idx),
                    )
                    for idx, v in enumerate(rp.variants)
                ]
                if variant_data_list:
                    variant_repo.upsert_batch(product_row.id, variant_data_list)
                variant_count += len(variant_data_list)

                image_data_list = [
                    ImageData(
                        url=img["url"],
                        position=img.get("position", idx),
                        alt_text=img.get("alt_text"),
                    )
                    for idx, img in enumerate(rp.images)
                ]
                if image_data_list:
                    image_repo.upsert_batch(product_row.id, image_data_list)
                image_count += len(image_data_list)

                product_count += 1
                products_for_snapshot.append(product_data)

            snapshot_data = SnapshotData(
                supplier_slug=self.config.slug,
                products=products_for_snapshot,
                product_count=product_count,
                importer_version="1.0.0",
            )
            snapshot_row = snapshot_repo.create(snapshot_data)

            checksum_input = f"{self.config.slug}:{product_count}:{snapshot_row.created_at.isoformat()}"
            snapshot_row.checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

            session.commit()

            return {
                "supplier": self.config.slug,
                "products": product_count,
                "variants": variant_count,
                "images": image_count,
                "snapshot_id": snapshot_row.id,
                "checksum": snapshot_row.checksum,
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
