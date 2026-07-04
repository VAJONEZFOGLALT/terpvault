"""
Debug: why are we getting 6825 product cards for 337 products?
That's 20x. Let's trace the template logic.
"""
import json, sys
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

# Check: how many times does each product appear across all sections?
from collections import Counter
product_section_counts = Counter()
for section in doc.sections:
    for pid in section.product_ids:
        product_section_counts[pid] += 1

# How many products appear in multiple sections?
multi = {pid: c for pid, c in product_section_counts.items() if c > 1}
print(f"Products appearing in 1 section: {sum(1 for c in product_section_counts.values() if c == 1)}")
print(f"Products appearing in 2+ sections: {len(multi)}")
if multi:
    print("Products in multiple sections:")
    for pid, count in list(multi.items())[:10]:
        p = doc.products.get(pid)
        print(f"  {pid} ({p.name if p else '?'}): {count} sections")

# Now let's also check: what section_config entries exist vs what sections exist
section_config_keys = [
    'Eybna', 'True Terpenes', 'Terp Belt Farms', 'Terpenes UK - Botanical',
    'Prestige', 'Duty Free Terpenes', 'Live Resin', 'Concentrated Flavours',
    'Oil Soluble Flavours', 'NEU Bag Infusion Packs', 'Terpene Isolates',
    'Extract Liquidisers', 'Diluents', 'Vape Hardware', 'Sample Packs'
]

print("\nSections in document:")
for s in doc.sections:
    in_config = s.label in section_config_keys
    print(f"  {s.label}: {len(s.product_ids)} products {'[IN CONFIG]' if in_config else '[MISSING FROM CONFIG]'}")
    
# Check: any products with empty product_ids list?
print("\nEmpty sections in document:")
for s in doc.sections:
    if not s.product_ids:
        print(f"  {s.label}: EMPTY")
        
# Count total product appearances across sections
total_appearances = sum(len(s.product_ids) for s in doc.sections)
print(f"\nTotal product appearances across all sections: {total_appearances}")
print(f"Total unique products: {len(doc.products)}")
print(f"Ratio: {total_appearances / len(doc.products):.1f}x")
