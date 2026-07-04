"""
Fast page-count audit via Playwright.
Trick: Use page.js to count pages via CSS paged-media polyfill, or route-block images to avoid network.
Or: generate PDF quickly by blocking image loads.
"""
import json, re, sys, time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from jinja2 import Environment, BaseLoader
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
# 1. Build document once
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
# 2. Render and count
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

# Pre-render all HTML to avoid redundant work
print("  Pre-rendering HTML variants...")

def test(label: str, template_text: str, prev_html: str = None) -> int:
    """Render HTML and count PDF pages via Playwright.
    
    Key optimization: block all image requests (route interception) to avoid network.
    """
    html = render_html(template_text) if template_text != prev_html else prev_html
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Block image loads to dramatically speed up rendering
        def route_handler(route):
            if route.request.resource_type in ("image", "font", "stylesheet"):
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", route_handler)
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(0.5)  # brief settle for layout
        
        pdf_bytes = page.pdf(
            format="A4", print_background=True,
            margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"},
            scale=1.0,
        )
        browser.close()
    
    reader = PdfReader(BytesIO(pdf_bytes))
    count = len(reader.pages)
    size_mb = len(pdf_bytes) / (1024 * 1024)
    print(f"  [{label:50s}] {count:2d} pages  ({size_mb:.0f} MB)")
    return count, html

# ---------------------------------------------------------------------------
# 3. Template mutations
# ---------------------------------------------------------------------------
ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")

def remove_quick_guide(html: str) -> str:
    return re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', html, count=1, flags=re.DOTALL)

def remove_chapter_openers(html: str) -> str:
    return re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', html, flags=re.DOTALL)

def remove_section_pagebreaks(html: str) -> str:
    html = html.replace(
        '.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
        '.section-header.section-break {\n    padding-top: 0.5cm;\n  }',
    )
    html = html.replace(
        '.section-header.section-break.brand-section { page-break-before: always; }',
        '',
    )
    html = html.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
    # Also remove page-break-before from the section-header base class
    return html

def only_section_breaks(html: str) -> str:
    """Remove EVERYTHING except section-break pagebreaks - to isolate their effect."""
    # Keep section break CSS but remove other pagebreaks
    # Remove chapter opener page-break-before
    html = html.replace('  .chapter-opener {\n    page-break-before: always;', '  .chapter-opener {\n    /* removed */')
    # Remove quick-guide page-break-after
    html = html.replace('.quick-guide { page-break-after: always;', '.quick-guide { /* removed */')
    # Remove TOC page-break-after
    html = html.replace('.toc { page-break-after: always;', '.toc { /* removed */')
    # Remove cover page-break-after
    html = html.replace('.cover {\n    page-break-after: always;', '.cover {\n    /* removed */')
    return html

def no_toc_break(html: str) -> str:
    return html.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')

def original_margins(html: str) -> str:
    return html.replace('margin: 1.5cm 1.4cm 1.8cm;', 'margin: 2cm 1.8cm;')

# ---------------------------------------------------------------------------
# 4. Run tests
# ---------------------------------------------------------------------------
print()
print("=== Page Count Audit ===")
print()

results = []
prev_html = None

# Baseline
label = "Baseline (current)"
count, prev_html = test(label, ORIG, None)
results.append((label, count))

# We want to measure the effect of EACH feature in isolation.
# Strategy: create a stripped version with NO pagebreaks, then add each feature back.

# Create a minimal breaks version: only cover + TOC page breaks
stripped = ORIG
stripped = remove_quick_guide(stripped)
stripped = remove_chapter_openers(stripped)
stripped = remove_section_pagebreaks(stripped)
# Keep cover break, keep TOC break (original also had TOC)
# Remove QG break was already done above

label = "No QG, no ch openers, no section breaks"
count, prev_html = test(label, stripped, prev_html)
results.append((label, count))

# Now add each feature back one at a time to isolate its contribution

# Feature: Quick Guide (add QG back)
with_qg = stripped.replace(
    '<section class="toc"',  # text before QG normally comes
    '<section class="quick-guide" id="quick-guide"><h2>Quick Guide</h2><div class="qg-grid"><div class="qg-card"><div class="label">TEST</div><div class="def">Test</div></div></div></section><section class="toc"'
)
# Actually, easier to use the original and selectively enable one thing:
# Let me use a different approach: start from ORIG and remove only ONE thing at a time

print()
print("--- Individual feature contributions (remove one at a time from baseline) ---")
print()

# Baseline
results2 = []
count2, _ = test("Baseline (current)", ORIG, None)
results2.append(("Baseline (current)", count2))

# Remove only Quick Guide
v = remove_quick_guide(ORIG)
count2, _ = test("Remove Quick Guide only", v, None)
results2.append(("Remove Quick Guide only", count2))

# Remove only chapter openers
v = remove_chapter_openers(ORIG)
count2, _ = test("Remove chapter openers only", v, None)
results2.append(("Remove chapter openers only", count2))

# Remove only section breaks
v = remove_section_pagebreaks(ORIG)
count2, _ = test("Remove section breaks only", v, None)
results2.append(("Remove section breaks only", count2))

# Remove only TOC break
v = no_toc_break(ORIG)
count2, _ = test("Remove TOC break only", v, None)
results2.append(("Remove TOC break only", count2))

# Original margins only
v = original_margins(ORIG)
count2, _ = test("Original margins only", v, None)
results2.append(("Original margins only", count2))

# Combine all removals
v = ORIG
v = remove_quick_guide(v)
v = remove_chapter_openers(v)
v = remove_section_pagebreaks(v)
v = no_toc_break(v)
count2, _ = test("All content removals combined", v, None)
results2.append(("All content removals combined", count2))

# All removals + original margins
v = original_margins(v)
count2, _ = test("ALL removals + orig margins", v, None)
results2.append(("ALL removals + orig margins", count2))

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
base = results2[0][1]
print(f"{'Test':52s} {'Pages':>5s}  {'Delta':>5s}")
print("-" * 70)
for label, count in results2:
    delta = count - base
    sign = "+" if delta > 0 else " "
    print(f"{label:52s} {count:5d}  {sign}{delta: 4d}")
print(f"\nTarget: 44 pages ({base - 44} pages to eliminate)")
