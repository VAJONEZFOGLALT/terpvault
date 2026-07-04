"""
Check 1: Builder product card count vs external_ids
Check 2: No duplicate cards in HTML
"""
import json, re, sys
from pathlib import Path
from collections import Counter

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

# Raw input stats
raw_ids = [p.external_id for p in products]
unique_ids = set(raw_ids)
id_counts = Counter(raw_ids)

print("=== Check 1: Builder card count ===")
print(f"  Total snapshot rows:            {len(products)}")
print(f"  Total unique external_ids:      {len(unique_ids)}")
print()

# Run builder
builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)

# Count total product IDs across all sections
total_cards = sum(len(s.product_ids) for s in doc.sections)
print(f"  Total rendered product cards:   {total_cards}")
print(f"  Products in doc.products dict:  {len(doc.products)}")
print(f"  Match (cards == unique ids)?    {'YES' if total_cards == len(unique_ids) else 'NO - MISMATCH!'}")
print()

if total_cards != len(unique_ids):
    print("  MISMATCH DETAIL:")
    # Find which IDs appear multiple times
    card_counts = Counter()
    for s in doc.sections:
        for pid in s.product_ids:
            card_counts[pid] += 1
    dupes = {pid: c for pid, c in card_counts.items() if c > 1}
    missing = unique_ids - set(card_counts.keys())
    print(f"    IDs with multiple cards: {len(dupes)}")
    for pid, count in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
        p = doc.products.get(pid)
        name = p.name if p else '?'
        print(f"      {name:40s} ({pid}) x{count}")
    if missing:
        print(f"    IDs with zero cards: {len(missing)}")
        for pid in list(missing)[:5]:
            print(f"      {pid}")

# Check 2: Verify HTML
print()
print("=== Check 2: HTML card count ===")
ORIGINAL_PATH = PROJECT / "terpvault" / "generate" / "templates" / "catalog_pdf.html"
template_text = ORIGINAL_PATH.read_text(encoding="utf-8")

class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

env = Environment(loader=StringLoader(template_text))
template = env.get_template("catalog_pdf.html")
config = SupplierConfig.load("terpenes-uk")
ctx = BuildContext(snapshot_id=snap.id, catalog_version=doc.stats.product_count,
                   supplier_config=config, output_dir=Path("data/catalogs"), edition="print")
html = template.render(doc=doc, supplier=config, version=ctx.catalog_version)

# Count product-card divs
card_divs = html.count('class="product-card')
img_tags = html.count('<img ')
product_names = re.findall(r'<div class="product-card-name">([^<]+)</div>', html)

print(f"  <img> tags in HTML:              {img_tags}")
print(f"  product-card divs in HTML:       {card_divs}")
print(f"  product-card-name divs in HTML:  {len(product_names)}")

# Check for duplicate names
name_counts = Counter(product_names)
dup_names = {n: c for n, c in name_counts.items() if c > 1}
print(f"  Unique product names in HTML:    {len(set(product_names))}")
print(f"  Duplicate product names in HTML: {len(dup_names)}")
if dup_names:
    print("  First 10 duplicated names:")
    for name, count in sorted(dup_names.items(), key=lambda x: -x[1])[:10]:
        print(f"    '{name}' x{count}")

print()
print(f"  Match (img tags == unique ids)? {'YES' if img_tags == len(unique_ids) else 'NO - MISMATCH!'}")
print(f"  Match (cards == unique ids)?    {'YES' if card_divs == len(unique_ids) else 'NO - MISMATCH!'}")
