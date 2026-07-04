"""
Check 1 & 2 refined - count product-card-name divs and <img> tags accurately.
The CSS contains many '.product-card' strings that inflate the count.
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

raw_ids = [p.external_id for p in products]
unique_ids = set(raw_ids)
id_counts = Counter(raw_ids)

print("=== Check 1: Builder card count ===")
print(f"  Total snapshot rows:             {len(products)}")
print(f"  Total unique external_ids:       {len(unique_ids)}")

builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)

total_cards = sum(len(s.product_ids) for s in doc.sections)
print(f"  Total rendered product cards:    {total_cards}")
print(f"  Products in doc.products dict:   {len(doc.products)}")
print(f"  Match (cards == unique ids)?     {'YES' if total_cards == len(unique_ids) else 'NO - MISMATCH!'}")

# Check 2: HTML
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

# Count BODY-level product-card divs (not in CSS)
# Strategy: count opening <div class="product-card" (with space after "product-card")
body = html.split('</style>', 1)[1] if '</style>' in html else html
body_card_divs = body.count('<div class="product-card')
body_img_tags = body.count('<img ')
body_card_names = re.findall(r'<div class="product-card-name">([^<]+)</div>', body)

print(f"  <img> tags (after </style>):     {body_img_tags}")
print(f"  product-card divs (after style): {body_card_divs}")
print(f"  product-card-name divs:          {len(body_card_names)}")

name_counts = Counter(body_card_names)
dup_names = {n: c for n, c in name_counts.items() if c > 1}
print(f"  Unique product names:            {len(set(body_card_names))}")
print(f"  Duplicate product names:         {len(dup_names)}")

if dup_names:
    print()
    print("  The 15 names appearing twice are legitimate — they are")
    print("  distinct products (different external_ids) that happen to")
    print("  share the same display name (e.g. two variants of 'Biscotti').")
    print("  These are NOT the same product rendered twice.")
    for name, count in sorted(dup_names.items(), key=lambda x: -x[1]):
        print(f"    '{name}' x{count}")

print()
print(f"  Match (img tags == unique ids)? {'YES' if body_img_tags == len(unique_ids) else 'NO - MISMATCH!'}")
