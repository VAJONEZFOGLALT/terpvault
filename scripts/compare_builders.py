"""
Compare legacy builder vs current builder on the SAME product data.
Build the catalog twice:
1. Using the CURRENT builder (categorizer + canonical sections)
2. Simulating the LEGACY builder (dynamic grouping by collection/brand)

Then count how many times each product appears across sections.
"""
import json, sys
from pathlib import Path
from collections import OrderedDict, Counter

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.domain.models import ProductData
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.sections import CANONICAL_SECTIONS, SECTION_BY_KEY
from terpvault.generate.categorizer import classify
from terpvault.domain.catalog_document import (
    CatalogDocument, CatalogProduct, CatalogStats, CoverInfo,
    SectionInfo, SectionType, TocEntry,
)

# ---- Load product data ----
session = get_session()
supplier_row = SupplierRepo(session).get_by_slug("terpenes-uk")
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc()).first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()

print(f"Total unique products: {len(products)}")
print()

# =====================================================
# BUILDER 1: CURRENT (categorizer + canonical sections)
# =====================================================
builder = CatalogBuilder("terpenes-uk", supplier_row.name)
current_doc = builder.build(products)

current_appearances = Counter()
for section in current_doc.sections:
    for pid in section.product_ids:
        current_appearances[pid] += 1

current_multi = {pid: c for pid, c in current_appearances.items() if c > 1}
current_single = {pid: c for pid, c in current_appearances.items() if c == 1}

print("=== CURRENT builder (categorizer + canonical sections) ===")
print(f"  Sections produced: {len(current_doc.sections)}")
print(f"  Products in 1 section: {len(current_single)}")
print(f"  Products in 2+ sections: {len(current_multi)}")
print(f"  Total appearances: {sum(current_appearances.values())}")
print(f"  Ratio: {sum(current_appearances.values())/len(products):.1f}x")
if current_multi:
    print(f"\n  Products in 2+ sections ({len(current_multi)} total):")
    for pid, count in sorted(current_multi.items(), key=lambda x: -x[1])[:30]:
        p = current_doc.products.get(pid)
        name = p.name if p else "?"
        # Show which sections
        sections_for_product = [s.label for s in current_doc.sections if pid in s.product_ids]
        print(f"    {name:40s} appears in {count} sections: {', '.join(sections_for_product)}")

# =====================================================
# BUILDER 2: LEGACY (dynamic grouping, same code as c765810)
# =====================================================
print()
print("=== LEGACY builder (dynamic grouping by collection/brand) ===")

# Replicate the original builder logic from commit c765810
sorted_products = sorted(products, key=lambda p: (p.collection or "", p.brand or "", p.name or ""))

product_map_legacy = {}
section_map_legacy = OrderedDict()
section_index = 0

for p in sorted_products:
    cp = CatalogProduct(
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
    product_map_legacy[p.external_id] = cp
    
    section_key = p.collection or p.brand or "General"
    if section_key not in section_map_legacy:
        section_type = SectionType.collection
        if p.collection:
            section_type = SectionType.collection
        elif p.brand:
            section_type = SectionType.brand
        section_map_legacy[section_key] = SectionInfo(
            index=section_index,
            type=section_type,
            label=section_key,
            subtitle=p.brand or "",
            product_ids=[],
        )
        section_index += 1
    section_map_legacy[section_key].product_ids.append(p.external_id)

legacy_sections = list(section_map_legacy.values())

legacy_appearances = Counter()
for section in legacy_sections:
    for pid in section.product_ids:
        legacy_appearances[pid] += 1

legacy_multi = {pid: c for pid, c in legacy_appearances.items() if c > 1}
legacy_single = {pid: c for pid, c in legacy_appearances.items() if c == 1}

print(f"  Sections produced: {len(legacy_sections)}")
print(f"  Products in 1 section: {len(legacy_single)}")
print(f"  Products in 2+ sections: {len(legacy_multi)}")
print(f"  Total appearances: {sum(legacy_appearances.values())}")
print(f"  Ratio: {sum(legacy_appearances.values())/len(products):.1f}x")

if legacy_multi:
    print(f"\n  Products in 2+ sections ({len(legacy_multi)} total):")
    for pid, count in sorted(legacy_multi.items(), key=lambda x: -x[1])[:30]:
        p = product_map_legacy.get(pid)
        name = p.name if p else "?"
        sections_for_product = [s.label for s in legacy_sections if pid in s.product_ids]
        print(f"    {name:40s} appears in {count} sections: {', '.join(sections_for_product)}")
else:
    print("\n  No products duplicated — each product appears in exactly one section.")

# =====================================================
# SUMMARY COMPARISON
# =====================================================
print()
print("=" * 70)
print("COMPARISON")
print("=" * 70)
print(f"{'Metric':40s} {'LEGACY':>15s} {'CURRENT':>15s}")
print("-" * 70)
print(f"{'Products':40s} {len(products):>15d} {len(products):>15d}")
print(f"{'Sections':40s} {len(legacy_sections):>15d} {len(current_doc.sections):>15d}")
print(f"{'Total appearances':40s} {sum(legacy_appearances.values()):>15d} {sum(current_appearances.values()):>15d}")
print(f"{'Duplicated products':40s} {len(legacy_multi):>15d} {len(current_multi):>15d}")
print(f"{'Unique appearances only':40s} {len(legacy_single):>15d} {len(current_single):>15d}")
print(f"{'Ratio':40s} {sum(legacy_appearances.values())/len(products):>14.1f}x {sum(current_appearances.values())/len(products):>14.1f}x")

# Show section labels side by side
print()
print("Sections:")
legacy_labels = [s.label for s in legacy_sections]
current_labels = [s.label for s in current_doc.sections]
print(f"  Legacy  ({len(legacy_labels)}): {', '.join(legacy_labels)}")
print(f"  Current ({len(current_labels)}): {', '.join(current_labels)}")
