"""
The product data has 684 entries, but refresh log says 337 products.
This means ProductData includes archived/old product versions, not just current.
We need to deduplicate by external_id or use the latest version of each.
"""
import json, sys
from pathlib import Path
from collections import OrderedDict, Counter

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.domain.models import ProductData

# Load raw data
with open(PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json", encoding="utf-8") as f:
    catalog_data = json.load(f)

# The catalog JSON has a 'products' dict keyed by external_id
products_dict = catalog_data.get('products', {})
print(f"Products in catalog JSON: {len(products_dict)} unique products")
print(f"Sections in catalog JSON: {len(catalog_data.get('sections', []))}")

# Load ProductData from the raw snapshot to see what's going on
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow

session = get_session()
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc()).first())

# Check the raw snapshot products string
raw_products = json.loads(snap.products)
print(f"\nRaw snapshot products list length: {len(raw_products)}")

# Check unique external IDs
unique_ids = set(p.get('external_id', p.get('id', '?')) for p in raw_products)
print(f"Unique external_ids in snapshot: {len(unique_ids)}")

# Check if there are products with duplicate external_ids
from collections import Counter
id_counts = Counter(p.get('external_id', p.get('id', '?')) for p in raw_products)
dupes = {k: v for k, v in id_counts.items() if v > 1}
print(f"Products with duplicate external_ids: {len(dupes)}")
if dupes:
    print("Sample duplicates:")
    for pid, count in list(dupes.items())[:5]:
        print(f"  {pid}: {count} entries")

session.close()
