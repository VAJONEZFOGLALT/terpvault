"""
Verify the dedup fix: run the CURRENT builder (with fix) on raw 684-entry data,
and confirm each product appears exactly once.
"""
import json, sys
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

session = get_session()
supplier_row = SupplierRepo(session).get_by_slug("terpenes-uk")
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc()).first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()

print(f"Raw input: {len(products)} entries")
print(f"Unique external IDs: {len(set(p.external_id for p in products))}")

builder = CatalogBuilder("terpenes-uk", supplier_row.name)
doc = builder.build(products)

print(f"\nAfter fix: {doc.stats.product_count} products")
print(f"Sections: {len(doc.sections)}")

# Count appearances per product
appearances = Counter()
for section in doc.sections:
    for pid in section.product_ids:
        appearances[pid] += 1

multi = {pid: c for pid, c in appearances.items() if c > 1}
single = {pid: c for pid, c in appearances.items() if c == 1}
total = sum(appearances.values())

print(f"Products in 1 section: {len(single)}")
print(f"Products in 2+ sections: {len(multi)}")
print(f"Total appearances: {total}")
print(f"Ratio: {total / len(appearances):.1f}x")

if multi:
    print(f"\nREMAINING DUPLICATIONS ({len(multi)}):")
    for pid, count in sorted(multi.items(), key=lambda x: -x[1])[:10]:
        p = doc.products.get(pid)
        name = p.name if p else '?'
        secs = [s.label for s in doc.sections if pid in s.product_ids]
        print(f"  {name:40s} x{count}: {', '.join(secs)}")
else:
    print("\nAll products appear exactly once. Fix confirmed!")
