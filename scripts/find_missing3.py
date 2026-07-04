"""
The new PDF has 335 images = 1 cover + 334 product images, but 337 products 
have valid image URLs. 3 product images didn't render in the PDF.

Check: do all 337 products appear in the rendered HTML as <img> tags?
If yes, the issue is Playwright failing to fetch 3 images during PDF generation.
If no, the issue is in the builder/template.
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

builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)
config = SupplierConfig.load("terpenes-uk")
ctx = BuildContext(snapshot_id=snap.id, catalog_version=doc.stats.product_count,
                   supplier_config=config, output_dir=Path("data/catalogs"), edition="print")

ORIGINAL_PATH = PROJECT / "terpvault" / "generate" / "templates" / "catalog_pdf.html"

class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

env = Environment(loader=StringLoader(ORIGINAL_PATH.read_text(encoding="utf-8")))
template = env.get_template("catalog_pdf.html")
html = template.render(doc=doc, supplier=config, version=ctx.catalog_version)

body = html.split('</style>', 1)[1]

# Extract image sources from the body
img_srcs = re.findall(r'<img\s+src="([^"]+)"', body)
print(f"<img> tags in rendered HTML body: {len(img_srcs)}")

# Also check: each product-card should have exactly one <img> 
# (except isolate cards which have none)
card_imgs = re.findall(r'<div class="product-card[^>]*">.*?<img\s', body, re.DOTALL)
print(f"Cards with <img> inside: {len(card_imgs)}")

# Check product cards without images
cards_without_img = re.findall(
    r'<div class="product-card(?!.*?<img\s)', 
    body, 
    re.DOTALL
)
# Better approach: split by product-card and check each
card_blocks = re.split(r'<div class="product-card[^>]*">', body)[1:]
cards_without = 0
cards_with = 0
for block in card_blocks:
    if '<img ' in block:
        cards_with += 1
    else:
        cards_without += 1
        # Get the product name from this block
        name_match = re.search(r'<div class="product-card-name">([^<]+)', block)
        if name_match:
            print(f"  Card without image: {name_match.group(1)}")

print(f"\nCards WITH image:    {cards_with}")
print(f"Cards WITHOUT image: {cards_without}")
print(f"Total product cards: {cards_with + cards_without}")
