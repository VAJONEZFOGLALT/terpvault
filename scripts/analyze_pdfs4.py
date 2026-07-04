"""
Test image duplication with images BLOCKED.
We know from earlier that baseline with blocked images = same page count.
Let's check if duplication still happens (it shouldn't, since images blocked).
Then test with images loaded but blocking route for specific patterns.
"""
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
import re, sys, time, json

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
from playwright.sync_api import sync_playwright

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

def render(template_text: str) -> str:
    env = Environment(loader=StringLoader(template_text))
    return env.get_template("catalog_pdf.html").render(doc=doc, supplier=config, version=ctx.catalog_version)

ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")

def block_all(route):
    route.abort()

def block_images(route):
    if route.request.resource_type in ("image", "font", "stylesheet", "media"):
        route.abort()
    else:
        route.continue_()

def allow_images(route):
    route.continue_()

def test(label, template_text, route_handler, wait=1.0):
    html = render(template_text)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route("**/*", route_handler)
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(wait)
        pdf_bytes = page.pdf(format="A4", print_background=True,
                             margin={"top":"1.5cm","bottom":"1.8cm","left":"1.4cm","right":"1.4cm"}, scale=1.0)
        page.close()
        browser.close()
    reader = PdfReader(BytesIO(pdf_bytes))
    all_names = []
    for pg in reader.pages:
        for img in pg.images:
            all_names.append(img.name)
    unique = len(set(all_names))
    total = len(all_names)
    pages = len(reader.pages)
    print(f"  {label:50s} {pages:2d} pages, {total:3d} images ({unique:3d} unique, {total-unique:3d} dupes)")
    return pages, total, unique, total-unique

print("=== Image Duplication Root Cause ===")
print()

# Test 1: baseline with IMAGES ALLOWED
test("Baseline (images allowed)", ORIG, allow_images)

# Test 2: baseline with IMAGES BLOCKED
test("Baseline (images blocked)", ORIG, block_images)

# Test 3: no page-break-inside (images blocked)
v = ORIG.replace('page-break-inside: avoid;', '/* r */')
test("No PB-inside (images blocked)", v, block_images)

# Test 4: no page breaks at all (images blocked)
v = ORIG
v = v.replace('page-break-inside: avoid;', '/* r */')
v = v.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('  .chapter-opener {\n    page-break-before: always;', '  .chapter-opener {\n    /* r */')
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = v.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
test("All breaks removed (blocked)", v, block_images)

# Test 5: Current template with images allowed but rendering same HTML multiple times
# Let's verify: are there exactly 337 <img> tags in the rendered HTML?
print()
html = render(ORIG)
img_tags = len(re.findall(r'<img\s', html))
print(f"<img> tags in rendered HTML: {img_tags}")
product_cards = len(re.findall(r'class="product-card', html))
print(f"product-card divs in rendered HTML: {product_cards}")

# Check if any product appears more than once in the HTML
product_ids_in_html = re.findall(r'data-product-id="([^"]+)"', html)
print(f"data-product-id attributes: {len(product_ids_in_html)}")

# Let's verify: for each section, how many products?
print()
print("Product count per section in HTML:")
section_pattern = re.compile(r'<div class="section-header.*?data-label="([^"]+)".*?<div class="product-grid')
# Count products per section by looking at card divs between section headers
sections = re.split(r'<div class="section-header', html)
for i, sec_html in enumerate(sections[1:], 1):
    label_match = re.search(r'data-label="([^"]+)"', sec_html)
    cards = len(re.findall(r'<div class="product-card', sec_html))
    label = label_match.group(1) if label_match else "?"
    print(f"  Section {i}: {label} = {cards} product cards")
