from collections import OrderedDict
from typing import Optional

from terpvault.domain.catalog_document import (
    CatalogDocument, CatalogProduct, CatalogStats, CoverInfo,
    SectionInfo, SectionType, TocEntry,
)
from terpvault.domain.models import ProductData
from terpvault.generate.categorizer import classify
from terpvault.generate.sections import CANONICAL_SECTIONS, SECTION_BY_KEY


class CatalogBuilder:
    def __init__(self, supplier_slug: str, supplier_name: str = ""):
        self.supplier_slug = supplier_slug
        self.supplier_name = supplier_name

    def build(self, products: list[ProductData], catalog_label: str = "") -> CatalogDocument:
        product_map: dict[str, CatalogProduct] = {}
        section_buckets: dict[str, list[str]] = OrderedDict()

        for cs in CANONICAL_SECTIONS:
            section_buckets[cs.key] = []

        seen: set[str] = set()
        for p in products:
            if p.external_id in seen:
                continue
            seen.add(p.external_id)
            cp = self._to_catalog_product(p)
            product_map[p.external_id] = cp
            section_key = classify(p)
            if section_key in section_buckets:
                section_buckets[section_key].append(p.external_id)
            else:
                section_buckets[section_key] = [p.external_id]

        total_cards = sum(len(ids) for ids in section_buckets.values())
        if total_cards != len(seen):
            dupe_ids = [eid for ids in section_buckets.values() for eid in ids]
            from collections import Counter
            counts = Counter(dupe_ids)
            repeated = {eid: c for eid, c in counts.items() if c > 1}
            import warnings
            warnings.warn(
                f"PRODUCT DUPLICATION DETECTED: {len(seen)} unique products "
                f"produced {total_cards} cards ({total_cards - len(seen)} extra). "
                f"Offending IDs: {dict(list(repeated.items())[:20])}"
            )

        sections = []
        toc = []
        section_index = 0
        brands: set[str] = set()

        for cs in CANONICAL_SECTIONS:
            pids = section_buckets.get(cs.key, [])
            if not pids:
                continue
            sections.append(SectionInfo(
                index=section_index,
                type=SectionType.collection,
                label=cs.label,
                subtitle=cs.subtitle,
                product_ids=pids,
            ))
            toc.append(TocEntry(label=cs.label, section_index=section_index))
            section_index += 1

        for p in product_map.values():
            if p.brand:
                brands.add(p.brand)

        cover = CoverInfo(
            supplier_name=self.supplier_name or self.supplier_slug,
            catalog_label=catalog_label or "Catalog",
            product_count=len(product_map),
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
