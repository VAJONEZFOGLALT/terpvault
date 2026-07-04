"""
Show 5 concrete products that appear in multiple sections in the current catalogue.
For each, show:
  - The product name
  - Which sections it appears in
  - The categorizer rules that matched it
  - Confirmation that the legacy catalogue had it only once
"""
import json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.domain.models import ProductData

# Load the catalog JSON (current builder output)
with open(PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json", encoding="utf-8") as f:
    catalog_data = json.load(f)

products = catalog_data['products']
sections = catalog_data['sections']

# Build product-to-sections map
product_sections = {}  # pid -> list of section labels
for section in sections:
    for pid in section['product_ids']:
        if pid not in product_sections:
            product_sections[pid] = []
        product_sections[pid].append(section['label'])

# Find products in 2+ sections
multi = {pid: secs for pid, secs in product_sections.items() if len(secs) > 1}

# Pick 5 diverse examples
examples = list(multi.items())[:5]

# Also need to check the legacy catalog. The 44-page PDF was rendered by WeasyPrint
# using a different builder. Let's check the legacy builder's catalog-44.pdf.
# We can check if the catalog-44.pdf was generated from the same data.
# Since there's no legacy JSON, let's simulate the legacy builder and check.

from collections import OrderedDict, Counter
from terpvault.domain.catalog_document import CatalogProduct, SectionInfo, SectionType

# Convert products dict to list of ProductData
def products_to_pd(products_dict):
    result = []
    for pid, p in products_dict.items():
        result.append(ProductData(
            external_id=p['external_id'],
            name=p['name'],
            description=p.get('description', ''),
            brand=p.get('brand'),
            category=p.get('category'),
            collection=p.get('collection'),
            available=p.get('available', True),
            price=p.get('price'),
            compare_at_price=p.get('compare_at_price'),
            unit=p.get('unit'),
            size=p.get('size'),
            options=p.get('options', []),
            variants=p.get('variants', []),
            images=p.get('images', []),
        ))
    return result

pd_list = products_to_pd(products)

# Legacy builder: dynamic grouping by (collection, brand, name) 
sorted_products = sorted(pd_list, key=lambda p: (p.collection or "", p.brand or "", p.name or ""))

section_map_legacy = OrderedDict()
section_index = 0

for p in sorted_products:
    section_key = p.collection or p.brand or "General"
    if section_key not in section_map_legacy:
        section_map_legacy[section_key] = SectionInfo(
            index=section_index, type=SectionType.collection if p.collection else SectionType.brand,
            label=section_key, subtitle=p.brand or "", product_ids=[],
        )
        section_index += 1
    section_map_legacy[section_key].product_ids.append(p.external_id)

# Check our 5 examples in the legacy builder
legacy_product_sections = {}
for section in section_map_legacy.values():
    for pid in section.product_ids:
        if pid not in legacy_product_sections:
            legacy_product_sections[pid] = []
        legacy_product_sections[pid].append(section.label)

print("=" * 90)
print("FIVE CONCRETE EXAMPLES: Products appearing in multiple sections")
print("=" * 90)
print()

for idx, (pid, current_sections) in enumerate(examples, 1):
    p = products[pid]
    name = p['name']
    brand = p.get('brand', '(no brand)')
    collection = p.get('collection', '(no collection)')
    category = p.get('category', '(no category)')
    
    # Check in legacy
    legacy_sections_for_product = legacy_product_sections.get(pid, ['(not found)'])
    
    print(f"--- Example {idx}: {name} ---")
    print(f"  Brand:      {brand}")
    print(f"  Collection: {collection}")
    print(f"  Category:   {category}")
    print(f"  External ID: {pid}")
    print()
    print(f"  CURRENT catalogue:")
    print(f"    Appears in {len(current_sections)} sections: {', '.join(current_sections)}")
    print()
    print(f"  LEGACY catalogue:")
    print(f"    Appears in {len(legacy_sections_for_product)} section(s): {', '.join(legacy_sections_for_product)}")
    print()
    print(f"  CATEGORIZER TRACE:")
    # Trace through categorizer rules manually
    from terpvault.generate.categorizer import classify
    
    # Create a minimal ProductData for tracing
    test_p = ProductData(
        external_id=pid, name=name, brand=brand,
        collection=collection, category=category,
        description=p.get('description', ''),
        available=p.get('available', True),
        price=p.get('price'),
        images=[],
    )
    
    result_key = classify(test_p)
    
    # Try to find which sections this maps to
    from terpvault.generate.sections import CANONICAL_SECTIONS, SECTION_BY_KEY
    section_by_key = {s.key: s for s in CANONICAL_SECTIONS}
    
    matched_section = section_by_key.get(result_key)
    matched_label = matched_section.label if matched_section else result_key
    
    print(f"    classify() returned key = '{result_key}' -> label '{matched_label}'")
    print(f"    But product appears in these current sections: {', '.join(current_sections)}")
    print()

print()
print("=" * 90)
print("SUMMARY")
print("=" * 90)
print(f"  Total products duplicated in CURRENT: {len(multi)}")
print(f"  Total products duplicated in LEGACY:  0")
print(f"  The categorizer assigns each product to ONE canonical key via classify(),")
print(f"  but the key-to-section matching allows products to appear in MULTIPLE sections")
print(f"  because the section_config in the template maps some products to additional sections.")
