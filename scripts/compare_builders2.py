"""
Fix: The snapshot has 684 rows, 337 unique products.
Run both builders on 337 unique products only (deduplicate by external_id).
"""
import json, sys
from pathlib import Path
from collections import OrderedDict, Counter

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.domain.catalog_document import (
    CatalogDocument, CatalogProduct, CatalogStats, CoverInfo,
    SectionInfo, SectionType, TocEntry,
)
from terpvault.domain.models import ProductData

# Load pure unique product data from the exported catalog JSON
with open(PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json", encoding="utf-8") as f:
    catalog_data = json.load(f)

# Build ProductData from the catalog JSON's products dict
unique_products = []
for pid, pdata in catalog_data['products'].items():
    unique_products.append(ProductData(
        external_id=pdata['external_id'],
        name=pdata['name'],
        description=pdata.get('description', ''),
        brand=pdata.get('brand'),
        category=pdata.get('category'),
        collection=pdata.get('collection'),
        available=pdata.get('available', True),
        price=pdata.get('price'),
        compare_at_price=pdata.get('compare_at_price'),
        unit=pdata.get('unit'),
        size=pdata.get('size'),
        options=pdata.get('options', []),
        variants=pdata.get('variants', []),
        images=pdata.get('images', []),
    ))

print(f"Unique products from catalog JSON: {len(unique_products)}")

# Also has 'sections' in the catalog JSON - these are from the CURRENT builder
current_sections_json = catalog_data.get('sections', [])
print(f"Current sections (from JSON): {len(current_sections_json)}")

# ============================================================
# CURRENT BUILDER - reconstruct from JSON directly
# ============================================================
print()
print("=== CURRENT builder (from catalog JSON sections) ===")
current_appearances = Counter()
for section in current_sections_json:
    for pid in section['product_ids']:
        current_appearances[pid] += 1

current_multi = {pid: c for pid, c in current_appearances.items() if c > 1}
current_single = {pid: c for pid, c in current_appearances.items() if c == 1}

print(f"  Sections: {len(current_sections_json)}")
print(f"  Products in 1 section: {len(current_single)}")
print(f"  Products in 2+ sections: {len(current_multi)}")
print(f"  Total appearances: {sum(current_appearances.values())}")
if current_multi:
    print(f"\n  Duplicated products ({len(current_multi)}):")
    for pid, count in sorted(current_multi.items(), key=lambda x: -x[1])[:20]:
        p = catalog_data['products'].get(pid, {})
        name = p.get('name', '?')
        secs = [s['label'] for s in current_sections_json if pid in s['product_ids']]
        print(f"    {name:40s} x{count}: {', '.join(secs)}")

# ============================================================
# LEGACY BUILDER - deduplicate then dynamic group
# ============================================================
print()
print("=== LEGACY builder (deduplicated, dynamic grouping) ===")

sorted_products = sorted(unique_products, key=lambda p: (p.collection or "", p.brand or "", p.name or ""))

product_map_legacy = {}
section_map_legacy = OrderedDict()
section_index = 0

for p in sorted_products:
    cp = CatalogProduct(
        external_id=p.external_id, name=p.name, description=p.description,
        brand=p.brand, category=p.category, collection=p.collection,
        available=p.available, price=float(p.price) if p.price is not None else None,
        compare_at_price=float(p.compare_at_price) if p.compare_at_price is not None else None,
        unit=p.unit, size=p.size, options=p.options,
        variants=p.variants,
        images=[img.model_dump() for img in p.images] if p.images else [],
    )
    product_map_legacy[p.external_id] = cp
    
    section_key = p.collection or p.brand or "General"
    if section_key not in section_map_legacy:
        section_type = SectionType.collection if p.collection else SectionType.brand
        section_map_legacy[section_key] = SectionInfo(
            index=section_index, type=section_type,
            label=section_key, subtitle=p.brand or "", product_ids=[],
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

print(f"  Sections: {len(legacy_sections)}")
print(f"  Products in 1 section: {len(legacy_single)}")
print(f"  Products in 2+ sections: {len(legacy_multi)}")
print(f"  Total appearances: {sum(legacy_appearances.values())}")
if legacy_multi:
    print(f"\n  Duplicated products ({len(legacy_multi)}):")
    for pid, count in sorted(legacy_multi.items(), key=lambda x: -x[1])[:20]:
        p = product_map_legacy.get(pid)
        name = p.name if p else '?'
        secs = [s.label for s in legacy_sections if pid in s.product_ids]
        print(f"    {name:40s} x{count}: {', '.join(secs)}")
else:
    print("\n  No duplication — each product appears in exactly one section.")

# ============================================================
# COMPARISON
# ============================================================
print()
print("=" * 70)
print("COMPARISON (deduplicated inputs)")
print("=" * 70)
print(f"{'Metric':40s} {'LEGACY':>15s} {'CURRENT':>15s}")
print("-" * 70)
print(f"{'Unique products':40s} {len(unique_products):>15d} {len(unique_products):>15d}")
print(f"{'Sections':40s} {len(legacy_sections):>15d} {len(current_sections_json):>15d}")
print(f"{'Total appearances':40s} {sum(legacy_appearances.values()):>15d} {sum(current_appearances.values()):>15d}")
print(f"{'Duplicated products':40s} {len(legacy_multi):>15d} {len(current_multi):>15d}")
print(f"{'Single-appearance products':40s} {len(legacy_single):>15d} {len(current_single):>15d}")

print()
print("Sections:")
print(f"  Legacy  ({len(legacy_sections)}): {', '.join(s.label for s in legacy_sections)}")
print(f"  Current ({len(current_sections_json)}): {', '.join(s['label'] for s in current_sections_json)}")
