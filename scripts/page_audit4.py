"""
Focused test: Combine the winning strategies + try more aggressive tweaks.
Key finding so far: image height matters hugely (-9 pages).
Content fixes total: -7 pages.
Combined should be -16 pages from baseline 73 = 57.
Need to reach 44 = 13 more pages.
"""
import json, re, sys, time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from jinja2 import Environment, BaseLoader
from pypdf import PdfReader
from io import BytesIO
from playwright.sync_api import sync_playwright

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.domain.models import ProductData
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.artifacts.base import BuildContext

SUPPLIER = "terpenes-uk"
ORIGINAL_PATH = Path(__file__).resolve().parent.parent / "terpvault" / "generate" / "templates" / "catalog_pdf.html"

session = get_session()
supplier_row = SupplierRepo(session).get_by_slug(SUPPLIER)
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug=SUPPLIER)
        .order_by(SnapshotRow.created_at.desc())
        .first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()
builder = CatalogBuilder(SUPPLIER, supplier_row.name)
doc = builder.build(products)
config = SupplierConfig.load(SUPPLIER)
ctx = BuildContext(snapshot_id=snap.id, catalog_version=doc.stats.product_count,
                   supplier_config=config, output_dir=Path("data/catalogs"), edition="print")
print(f"Products: {doc.stats.product_count}, Sections: {len(doc.sections)}")

class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

def render(template_text: str) -> str:
    env = Environment(loader=StringLoader(template_text))
    return env.get_template("catalog_pdf.html").render(doc=doc, supplier=config, version=ctx.catalog_version)

def block_reqs(route):
    if route.request.resource_type in ("image", "font", "stylesheet", "media"):
        route.abort()
    else:
        route.continue_()

ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")

variants = []

# Baseline
variants.append(("Baseline", ORIG))

# Content fixes baseline
base_content = ORIG
base_content = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', base_content, count=1, flags=re.DOTALL)
base_content = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', base_content, flags=re.DOTALL)
base_content = base_content.replace(
    '.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
    '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
base_content = base_content.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
base_content = base_content.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
variants.append(("Content fixes only", base_content))

# Content + image height experiments
variants.append(("Content + img 3.0cm", base_content.replace('height: 3.2cm;', 'height: 3.0cm;')))
variants.append(("Content + img 2.8cm", base_content.replace('height: 3.2cm;', 'height: 2.8cm;')))
variants.append(("Content + img 2.5cm", base_content.replace('height: 3.2cm;', 'height: 2.5cm;')))
variants.append(("Content + img 2.0cm", base_content.replace('height: 3.2cm;', 'height: 2.0cm;')))
variants.append(("Content + img 1.5cm", base_content.replace('height: 3.2cm;', 'height: 1.5cm;')))

# Content + original section approach: no section breaks, no chapter openers, continuous flow
# Same as content fixes above

# Try: content fixes + original margins 
# (original margins were 2cm 1.8cm which uses LESS area, so it increased pages - skip)

# Try: content fixes + tighter spacing
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('margin-bottom: 0.16cm;', 'margin-bottom: 0.05cm;')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
variants.append(("Content+2.5cm+tighter", v))

# Try: remove product card border
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('border: 0.5px solid var(--card-border);', '')
variants.append(("Content+2.5cm+no border", v))

# Try: reduce card body padding
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('padding: 0.07cm 0.1cm 0.1cm;', 'padding: 0.02cm 0.05cm 0.05cm;')
variants.append(("Content+2.5cm+less pad", v))

# Try: smaller fonts across the board
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('font-size: 7.5pt;', 'font-size: 7pt;')
v = v.replace('font-size: 8pt;', 'font-size: 7.5pt;')
variants.append(("Content+2.5cm+smaller f", v))

# Try: combine all spacing tweaks
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('margin-bottom: 0.16cm;', 'margin-bottom: 0.05cm;')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
v = v.replace('padding: 0.07cm 0.1cm 0.1cm;', 'padding: 0.02cm 0.05cm 0.05cm;')
v = v.replace('padding: 0.25cm 0 0.1cm 0;', 'padding: 0.1cm 0 0.05cm 0;')
v = v.replace('margin-bottom: 0.1cm;', 'margin-bottom: 0.05cm;')
variants.append(("Content+2.5cm+all s pc", v))

# Try: combine all spacing + smaller fonts
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('margin-bottom: 0.16cm;', 'margin-bottom: 0.05cm;')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
v = v.replace('padding: 0.07cm 0.1cm 0.1cm;', 'padding: 0.02cm 0.05cm 0.05cm;')
v = v.replace('padding: 0.25cm 0 0.1cm 0;', 'padding: 0.1cm 0 0.05cm 0;')
v = v.replace('margin-bottom: 0.1cm;', 'margin-bottom: 0.05cm;')
v = v.replace('font-size: 7.5pt;', 'font-size: 7pt;')
v = v.replace('font-size: 8pt;', 'font-size: 7.5pt;')
v = v.replace('font-size: 5.5pt;', 'font-size: 5pt;')
variants.append(("Content+2.5+all sp+sm", v))

# Try: ALL tweaks + remove card descriptions
v = base_content.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('margin-bottom: 0.16cm;', 'margin-bottom: 0.05cm;')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
v = v.replace('padding: 0.07cm 0.1cm 0.1cm;', 'padding: 0.02cm 0.05cm 0.05cm;')
v = v.replace('padding: 0.25cm 0 0.1cm 0;', 'padding: 0.1cm 0 0.05cm 0;')
v = v.replace('margin-bottom: 0.1cm;', 'margin-bottom: 0.05cm;')
v = v.replace('font-size: 7.5pt;', 'font-size: 7pt;')
v = v.replace('font-size: 8pt;', 'font-size: 7.5pt;')
v = v.replace('font-size: 5.5pt;', 'font-size: 5pt;')
v = v.replace('{{ p.description|striptags|truncate(60) }}', '')
variants.append(("ALL content+dense+no desc", v))

# Try: Try width: 100% cards (single column) - probably bad but let's see
v = base_content.replace('width: 32.5%;', 'width: 100%;')
v = v.replace('width: 48.8%;', 'width: 100%;')
variants.append(("Content + single column", v))

htmls = [(label, render(t)) for label, t in variants]
print(f"Rendering {len(variants)} variants...")
print()

results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for label, html in htmls:
        page = browser.new_page()
        page.route("**/*", block_reqs)
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(0.3)
        pdf_bytes = page.pdf(format="A4", print_background=True,
                             margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"}, scale=1.0)
        page.close()
        reader = PdfReader(BytesIO(pdf_bytes))
        results.append((label, len(reader.pages)))
        print(f"  {label:40s} {len(reader.pages):2d} pages")
    browser.close()

print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
base = results[0][1]
for label, count in results:
    delta = count - base
    sign = "+" if delta > 0 else " "
    print(f"{label:40s} {count:5d}  {sign}{delta: 4d}")
print(f"\nTarget: 44 pages (need {base - 44})")
