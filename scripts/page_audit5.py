"""
Final verification: test with real images (or estimate their impact),
and check what the original catalog-44.pdf font/image settings were.
Also: the original was rendered via WeasyPrint, not Playwright. 
Test Playwright's default rendering vs the legacy playback.
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

ORIGINAL_PATH = PROJECT / "terpvault" / "generate" / "templates" / "catalog_pdf.html"

session = get_session()
supplier_row = SupplierRepo(session).get_by_slug("terpenes-uk")
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc())
        .first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()
builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)
config = SupplierConfig.load("terpenes-uk")
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

ORIG = ORIGINAL_PATH.read_text(encoding="utf-8")
TEMPLATE_DIR = PROJECT / "terpvault" / "generate" / "templates"

variants = []

# 1 Current baseline with images enabled
variants.append(("BL With images", ORIG, False))

# 2 Current baseline with images blocked
variants.append(("BL No images", ORIG, True))

# 3 Content fixes + images blocked
v = ORIG
v = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v, count=1, flags=re.DOTALL)
v = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', v, flags=re.DOTALL)
v = v.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v = v.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v = v.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v = v.replace('.toc { page-break-after: always; padding-top: 2.5cm;', '.toc { padding-top: 2.5cm;')
variants.append(("Content fixes", v, True))

# 4 Content fixes + img height 2.5
v4 = v.replace('height: 3.2cm;', 'height: 2.5cm;')
variants.append(("Content + img 2.5", v4, True))

# 5 Content fixes + img height 2.0
v5 = v.replace('height: 3.2cm;', 'height: 2.0cm;')
variants.append(("Content + img 2.0", v5, True))

# 6 Content fixes + img height 1.5
v6 = v.replace('height: 3.2cm;', 'height: 1.5cm;')
variants.append(("Content + img 1.5", v6, True))

# 7 Content fixes + section opener no break (keep visual but not forced page)
v7 = ORIG
v7 = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v7, count=1, flags=re.DOTALL)
v7 = v7.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v7 = v7.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v7 = v7.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
# Keep chapter openers but don't force page-break
v7 = v7.replace('  .chapter-opener {\n    page-break-before: always;', '  .chapter-opener {\n    /* r */')
v7 = v7.replace('height: 3.2cm;', 'height: 2.5cm;')
variants.append(("Content+ch no br+2.5", v7, True))

# 8 Also remove cover background (complex gradients can affect rendering)
v8 = ORIG
v8 = re.sub(r'<section class="quick-guide".*?</section>\s*\n', '', v8, count=1, flags=re.DOTALL)
v8 = re.sub(r'<section class="chapter-opener".*?</section>\s*\n', '', v8, flags=re.DOTALL)
v8 = v8.replace('.section-header.section-break {\n    page-break-before: always;\n    padding-top: 0.5cm;\n  }',
              '.section-header.section-break {\n    padding-top: 0.5cm;\n  }')
v8 = v8.replace('.section-header.section-break.brand-section { page-break-before: always; }', '')
v8 = v8.replace('{% if brand_key and not is_first %} section-break{% endif %}', '')
v8 = v8.replace('height: 3.2cm;', 'height: 2.5cm;')
# Remove cover page-break-after (cover content will flow into TOC)
v8 = v8.replace('.cover {\n    page-break-after: always;', '.cover {\n    /* r */')
variants.append(("All+2.5+no cover brk", v8, True))

htmls = [(label, render(t), block) for label, t, block in variants]

print(f"Rendering {len(variants)} variants...")
print()

results = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for label, html, block_imgs in htmls:
        page = browser.new_page()
        if block_imgs:
            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ("image","font","stylesheet","media") else route.continue_())
        page.set_content(html, wait_until="domcontentloaded")
        time.sleep(0.5)
        pdf_bytes = page.pdf(format="A4", print_background=True,
                             margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"}, scale=1.0)
        page.close()
        reader = PdfReader(BytesIO(pdf_bytes))
        count = len(reader.pages)
        size_mb = len(pdf_bytes) / (1024*1024)
        print(f"  {label:35s} {count:2d} pages  ({size_mb:.0f} MB)")
        results.append((label, count))
    browser.close()

print()
print("=" * 70)
base = results[0][1]
for label, count in results:
    delta = count - base
    print(f"{label:35s} {count:3d}  {delta:+3d}")
