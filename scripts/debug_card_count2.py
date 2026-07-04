"""
Verify product card count more precisely.
The regex-based section split might be inaccurate.
Count the actual product_card macro invocations.
"""
import json, re, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from jinja2 import Environment, BaseLoader

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.domain.models import ProductData
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.artifacts.base import BuildContext

ORIGINAL_PATH = PROJECT / "terpvault" / "generate" / "templates" / "catalog_pdf.html"

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
config = SupplierConfig.load("terpenes-uk")
ctx = BuildContext(snapshot_id=snap.id, catalog_version=doc.stats.product_count,
                   supplier_config=config, output_dir=Path("data/catalogs"), edition="print")

class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

env = Environment(loader=StringLoader(ORIGINAL_PATH.read_text(encoding="utf-8")))
template = env.get_template("catalog_pdf.html")
html = template.render(doc=doc, supplier=config, version=ctx.catalog_version)

# Count actual <img> tags in the rendered HTML
img_tags = html.count('<img ')
print(f"<img> tags in rendered HTML: {img_tags}")

# Count product-card divs
card_divs = html.count('class="product-card')
print(f"product-card class occurrences: {card_divs}")

# Count data-brand attributes on cards
brand_attrs = len(re.findall(r'data-brand="([^"]+)"', html))
print(f"data-brand attributes: {brand_attrs}")

# Check: how many macro invocations? Count {{ product_card( 
invocations = html.count('product_card(')
print(f"product_card( invocations: {invocations}")

# Let's look for the actual pattern: {{ product_card(p, 
macro_calls = len(re.findall(r'product_card\(p,\s*', html))
print(f"product_card(p, calls: {macro_calls}")

# Let's find all unique product names in the HTML by looking at 
# the text inside .product-card-name divs
names = re.findall(r'<div class="product-card-name">([^<]+)</div>', html)
print(f"product-card-name divs: {len(names)}")

# Count unique names
unique_names = len(set(names))
print(f"Unique product names: {unique_names}")

# Show a sample of names and their frequency
from collections import Counter
name_counts = Counter(names)
print(f"\nTop 10 most frequent product names:")
for name, count in name_counts.most_common(10):
    print(f"  '{name}': {count}x")
