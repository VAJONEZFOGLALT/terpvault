"""
Fast audit - block ALL images (images have fixed-size containers so layout is unaffected).
Single Playwright session.
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
TEMPLATE_DIR = PROJECT / "terpvault" / "generate" / "templates"
ORIGINAL_PATH = TEMPLATE_DIR / "catalog_pdf.html"

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
                   supplier_config=config, output_dir=settings.catalogs_dir, edition="print")
print(f"Products: {doc.stats.product_count}, Sections: {len(doc.sections)}")

class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

def render(template_text: str) -> str:
    env = Environment(loader=StringLoader(template_text))
    return env.get_template("catalog_pdf.html").render(doc=doc, supplier=config, version=ctx.catalog_version)

ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")

variants = []
variants.append(("01 Baseline", ORIG))
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', ORIG, count=1, flags=re.DOTALL)
variants.append(("02 Remove Quick Guide", v))
v = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', ORIG, flags=re.DOTALL)
variants.append(("03 Remove ch openers", v))
v = ORIG.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
                 '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
variants.append(("04 Remove section breaks", v))
v = ORIG.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
variants.append(("05 Remove TOC break", v))
v = ORIG.replace('margin: 1.5cm 1.4cm 1.8cm;', 'margin: 2cm 1.8cm;')
variants.append(("06 Original margins", v))
v = ORIG.replace('page-break-inside: avoid;', '/* r */')
variants.append(("07 Remove PB-inside", v))
v = ORIG.replace('height: 3.2cm;', 'height: 2.5cm;')
variants.append(("08 Image 3.2->2.5cm", v))
v = ORIG.replace('{{ p.description|striptags|truncate(60) }}', '')
variants.append(("09 Remove descriptions", v))
v = ORIG.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
variants.append(("10 Tighter gaps", v))
v = ORIG.replace('width: 32.5%;', 'width: 33.3%;')
variants.append(("11 Wider cards 33%", v))
# combined density
v = ORIG
v = v.replace('page-break-inside: avoid;', '/* r */')
v = v.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('{{ p.description|striptags|truncate(60) }}', '')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
v = v.replace('width: 32.5%;', 'width: 33.3%;')
variants.append(("12 All density", v))
# combined content
v = ORIG
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', v, flags=re.DOTALL)
v = v.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
variants.append(("13 All content", v))
# combined all
v = ORIG
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', v, flags=re.DOTALL)
v = v.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
v = v.replace('page-break-inside: avoid;', '/* r */')
v = v.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('{{ p.description|striptags|truncate(60) }}', '')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;').replace('gap: 0.2cm;', 'gap: 0.05cm;')
v = v.replace('width: 32.5%;', 'width: 33.3%;')
variants.append(("14 ALL content+density", v))
# content fixes + chapter openers no break
v = ORIG
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = v.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('  .chapter-opener {\n    page-break-before: always;', '  .chapter-opener {\n    /* r */')
variants.append(("15 Content + ch no break", v))

# Pre-render all
print(f"Pre-rendering {len(variants)} variants...")
htmls = [(label, render(t)) for label, t in variants]

print("Rendering PDFs (single Playwright session, images blocked)...")
print()

results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for label, html in htmls:
        page = browser.new_page()
        def block_reqs(route):
            if route.request.resource_type in ("image", "font", "stylesheet", "media"):
                route.abort()
            else:
                route.continue_()
        page.route("**/*", block_reqs)
        t0 = time.time()
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(0.3)
        pdf_bytes = page.pdf(
            format="A4", print_background=True,
            margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"},
            scale=1.0,
        )
        page.close()
        reader = PdfReader(BytesIO(pdf_bytes))
        count = len(reader.pages)
        elapsed = time.time() - t0
        print(f"  {label:35s} {count:2d} pages  ({elapsed:.0f}s)")
        results.append((label, count))
    browser.close()

print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
base = results[0][1]
print(f"{'Test':40s} {'Pages':>5s}  {'Delta':>5s}")
print("-" * 70)
for label, count in results:
    delta = count - base
    sign = "+" if delta > 0 else " "
    print(f"{label:40s} {count:5d}  {sign}{delta: 4d}")
print(f"\nTarget: 44 pages (eliminate {base - 44} pages)")
