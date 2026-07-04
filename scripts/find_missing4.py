"""
337 products, 335 <img> tags, 1 cover logo.
336 expected product images. 334 actual product images (335 - 1 cover).
2 product images are hidden by design (isolate cards).
Plus isolate cards have {% if not is_isolate %} before the <img> tag.

Let me verify: count isolate-card products and confirm 335 = 337 - 2 (isolates) = correct.

Also: the earlier count said 335 images in the PDF, with 337 products + 1 cover = 338 expected.
338 - 335 = 3. So we expect 3 products without images in the PDF.
- 2 are isolate cards (no image by design)
- 1 is... let's find it.
"""
import json, re, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.domain.models import ProductData
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.artifacts.base import BuildContext
from jinja2 import Environment, BaseLoader

session = get_session()
supplier_row = SupplierRepo(session).get_by_slug("terpenes-uk")
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc()).first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()

builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)

# Find the Terpene Isolates section (uses isolate-card = no image)
isolates_section = None
for s in doc.sections:
    if s.label == "Terpene Isolates":
        isolates_section = s
        break

print("=== Isolate products (no image by design) ===")
if isolates_section:
    print(f"  {len(isolates_section.product_ids)} products in Terpene Isolates section")
    for pid in isolates_section.product_ids:
        p = doc.products.get(pid)
        if p:
            print(f"    {p.name:40s} (id: {pid})")
else:
    print("  No Terpene Isolates section found")

# Now find products with NO images in their data
print()
print("=== Products with empty images list ===")
no_img_products = []
for pid, p in doc.products.items():
    if not p.images:
        no_img_products.append(p)
        print(f"  {p.name:40s} (id: {pid})")

print(f"  Total: {len(no_img_products)} products")

# Expected images = 337 products + 1 cover - 64 isolates (no img) = 274
# But the template shows isolate cards with "if not is_isolate" guard
# so 337 products - 64 isolates = 273 product images + 1 cover = 274
# But actual is 335. That doesn't match either.

# Wait - let me re-read the template. The isolate-card removes the image div:
# {% if not is_isolate %}
#   <div class="product-card-image">...<img ...></div>
# {% endif %}
# And isolate cards only occur in grid == 'isolate' which is NOT used in section_config.
# The Terpene Isolates section uses grid: '3col' not 'isolate'!
# So ALL products get images. Let me check what grid each section uses.

print()
print("=== Grid configuration per section ===")
section_config = {
    'Eybna': '3col', 'True Terpenes': '3col', 'Terp Belt Farms': '3col',
    'Terpenes UK - Botanical': '3col', 'Prestige': '3col', 'Duty Free Terpenes': '3col',
    'Live Resin': '3col', 'Concentrated Flavours': '2col',
    'Oil Soluble Flavours': '2col', 'NEU Bag Infusion Packs': '3col',
    'Terpene Isolates': '3col', 'Extract Liquidisers': '3col',
    'Diluents': '2col', 'Vape Hardware': '3col', 'Sample Packs': 'sample',
}

for s in doc.sections:
    grid = section_config.get(s.label, '?')
    print(f"  {s.label:35s} grid={grid:10s} products={len(s.product_ids)}")

# Count: total products in non-isolate cards
total_3col = sum(len(s.product_ids) for s in doc.sections if section_config.get(s.label) == '3col')
total_2col = sum(len(s.product_ids) for s in doc.sections if section_config.get(s.label) == '2col')
total_sample = sum(len(s.product_ids) for s in doc.sections if section_config.get(s.label) == 'sample')
total_unknown = sum(len(s.product_ids) for s in doc.sections if section_config.get(s.label) not in ('3col','2col','sample'))
print(f"\nTotal 3-col cards:   {total_3col}")
print(f"Total 2-col cards:   {total_2col}")
print(f"Total sample cards:  {total_sample}")
print(f"Total unknown cards: {total_unknown}")
print(f"Grand total:         {total_3col + total_2col + total_sample + total_unknown}")

# All card types show an <img> tag. So all 337 products should have an image in the HTML.
# 335 <img> tags = 1 cover + 334 product. 3 product images missing = 337 - 334.
# Let me find which 3 product URLs didn't render by checking the HTML vs data.
