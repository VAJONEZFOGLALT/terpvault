"""
Phase 2: Investigate density differences.
Compare original builder section structure vs current.
Also test: repack 3-column grid, remove page-break-inside:avoid, 
and simulate original flat-section layout.
"""
import json, re, sys, time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from jinja2 import Environment, BaseLoader, FileSystemLoader
from pypdf import PdfReader
from io import BytesIO

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

# ---------------------------------------------------------------------------
# 1. Build document
# ---------------------------------------------------------------------------
print("=== Building CatalogDocument ===")
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
ctx = BuildContext(
    snapshot_id=snap.id,
    catalog_version=doc.stats.product_count,
    supplier_config=config,
    output_dir=settings.catalogs_dir,
    edition="print",
)
print(f"  Products: {doc.stats.product_count}, Sections: {len(doc.sections)}")

# ---------------------------------------------------------------------------
# 2. Helper: render + count
# ---------------------------------------------------------------------------
class StringLoader(BaseLoader):
    def __init__(self, source):
        self.source = source
    def get_source(self, environment, template_name):
        return self.source, template_name, True

def render_html(template_text: str) -> str:
    env = Environment(loader=StringLoader(template_text))
    template = env.get_template("catalog_pdf.html")
    return template.render(doc=doc, supplier=config, version=ctx.catalog_version)

def count_pdf(html: str) -> int:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(1.0)
        pdf_bytes = page.pdf(
            format="A4", print_background=True,
            margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"},
            scale=1.0,
        )
        browser.close()
    reader = PdfReader(BytesIO(pdf_bytes))
    return len(reader.pages)

def test(label: str, html: str) -> int:
    c = count_pdf(html)
    print(f"  [{label:55s}] {c:2d} pages")
    return c

ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# 3. Tests: card & density experiments
# ---------------------------------------------------------------------------
print()
print("=== Phase 2: Density & Card Layout Tests ===")
print()

results = []

# Baseline (use the template as-is)
html_base = render_html(ORIG)
baseline = test("Baseline (current)", html_base)
results.append(("Baseline (current)", baseline))

# Test A: Remove page-break-inside:avoid from all product cards
# This allows cards to split across pages, improving packing
v = ORIG.replace('page-break-inside: avoid;', '/* avoid removed */')
html_v = render_html(v)
results.append(("Remove card page-break-inside", test("Remove card page-break-inside", html_v)))

# Test B: Reduce card image height
v = ORIG.replace('height: 3.2cm;', 'height: 2.5cm;')
html_v = render_html(v)
results.append(("Card image 3.2->2.5cm", test("Card image 3.2->2.5cm", html_v)))

# Test C: Reduce card image height further
v = ORIG.replace('height: 3.2cm;', 'height: 2.0cm;')
html_v = render_html(v)
results.append(("Card image 3.2->2.0cm", test("Card image 3.2->2.0cm", html_v)))

# Test D: Remove description entirely from cards
v = ORIG.replace('{{ p.description|striptags|truncate(60) }}', '')
html_v = render_html(v)
results.append(("Remove card descriptions", test("Remove card descriptions", html_v)))

# Test E: Reduce grid gap to 0
v = ORIG.replace('gap: 0.16cm;', 'gap: 0.05cm;')
html_v = render_html(v)
results.append(("Grid gap 0.16->0.05cm", test("Grid gap 0.16->0.05cm", html_v)))

# Test F: Increase card width to pack tighter (33.3% for perfect 3-col)
v = ORIG.replace('width: 32.5%;', 'width: 33.1%;')
html_v = render_html(v)
results.append(("Card width 32.5->33.1%", test("Card width 32.5->33.1%", html_v)))

# Test G: Try 33.3%
v = ORIG.replace('width: 32.5%;', 'width: 33.3%;')
html_v = render_html(v)
results.append(("Card width 33.3%", test("Card width 33.3%", html_v)))

# Test H: All tweaks combined (aggressive)
v = ORIG
v = v.replace('page-break-inside: avoid;', '/* avoid removed */')
v = v.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('{{ p.description|striptags|truncate(60) }}', '')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;')
v = v.replace('width: 32.5%;', 'width: 33.3%;')
html_v = render_html(v)
results.append(("All density tweaks", test("All density tweaks", html_v)))

# Test I: All content fixes + all density tweaks
v = ORIG
# Content fixes
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', v, flags=re.DOTALL)
v = v.replace(
    '.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
    '.section-header.section-break {\n    padding-top: 0.5cm;\n  }',
)
v = v.replace(
    '.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
# Density tweaks
v = v.replace('page-break-inside: avoid;', '/* avoid removed */')
v = v.replace('height: 3.2cm;', 'height: 2.5cm;')
v = v.replace('{{ p.description|striptags|truncate(60) }}', '')
v = v.replace('gap: 0.16cm;', 'gap: 0.05cm;')
v = v.replace('width: 32.5%;', 'width: 33.3%;')
html_v = render_html(v)
results.append(("ALL content+density fixes", test("ALL content+density fixes", html_v)))

# Test J: Try with original section grouping (simulate by removing section breaks + 
# remove brand-section per-section page breaks — sections flow naturally)
v = ORIG
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = v.replace(
    '.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
    '.section-header.section-break {\n    padding-top: 0.5cm;\n  }',
)
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
# Remove brand-section page-break-before
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
# Keep chapter openers but without page-break
v = v.replace('  .chapter-opener {\n    page-break-before: always;', '  .chapter-opener {\n    /* removed */')
# Keep TOC break
html_v = render_html(v)
results.append(("Content fixes, ch openers no break", test("Content fixes, ch openers no break", html_v)))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
base = results[0][1]
print(f"{'Test':60s} {'Pages':>5s}  {'Delta':>5s}")
print("-" * 70)
for label, count in results:
    delta = count - base
    sign = "+" if delta > 0 else " "
    print(f"{label:60s} {count:5d}  {sign}{delta: 4d}")
print(f"\nTarget: 44 pages (need to eliminate {base - 44})")
