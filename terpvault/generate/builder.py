from collections import OrderedDict
from typing import Optional

from terpvault.domain.catalog_document import (
    CatalogDocument, CatalogProduct, CatalogStats, CoverInfo,
    SectionInfo, SectionType, TocEntry,
)
from terpvault.domain.models import ProductData


class CatalogBuilder:
    def __init__(self, supplier_slug: str, supplier_name: str = ""):
        self.supplier_slug = supplier_slug
        self.supplier_name = supplier_name

    def build(self, products: list[ProductData], catalog_label: str = "") -> CatalogDocument:
        sorted_products = sorted(products, key=lambda p: (p.collection or "", p.brand or "", p.name or ""))

        product_map: dict[str, CatalogProduct] = {}
        section_map: dict[str, SectionInfo] = OrderedDict()
        brands: set[str] = set()

        section_index = 0
        for p in sorted_products:
            cp = self._to_catalog_product(p)
            product_map[p.external_id] = cp

            if p.brand:
                brands.add(p.brand)

            section_key = p.collection or p.brand or "General"
            if section_key not in section_map:
                section_type = SectionType.collection
                if p.collection:
                    section_type = SectionType.collection
                elif p.brand:
                    section_type = SectionType.brand
                section_map[section_key] = SectionInfo(
                    index=section_index,
                    type=section_type,
                    label=section_key,
                    subtitle=p.brand or "",
                    product_ids=[],
                )
                section_index += 1
            section_map[section_key].product_ids.append(p.external_id)

        sections = list(section_map.values())
        toc = [
            TocEntry(label=s.label, section_index=s.index)
            for s in sections
        ]

        cover = CoverInfo(
            supplier_name=self.supplier_name or self.supplier_slug,
            catalog_label=catalog_label or "Catalog",
            product_count=len(products),
            brand_count=len(brands),
        )

        stats = CatalogStats(
            product_count=len(product_map),
            brand_count=len(brands),
            section_count=len(sections),
            variant_count=sum(len(p.variants) for p in product_map.values()),
            image_count=sum(len(p.images) for p in product_map.values()),
        )

        return CatalogDocument(
            supplier_slug=self.supplier_slug,
            supplier_name=self.supplier_name,
            cover=cover,
            toc=toc,
            sections=sections,
            products=product_map,
            stats=stats,
        )

    @staticmethod
    def _to_catalog_product(p: ProductData) -> CatalogProduct:
        return CatalogProduct(
            external_id=p.external_id,
            name=p.name,
            description=p.description,
            brand=p.brand,
            category=p.category,
            collection=p.collection,
            available=p.available,
            price=float(p.price) if p.price is not None else None,
            compare_at_price=float(p.compare_at_price) if p.compare_at_price is not None else None,
            unit=p.unit,
            size=p.size,
            options=p.options,
            variants=p.variants,
            images=[img.model_dump() for img in p.images] if p.images else [],
        )
