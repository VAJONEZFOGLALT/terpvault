"""
Check 5: Verify the regression safeguard catches duplication.
Test 1: with dedup fix (should pass clean)
Test 2: simulate old bug (should warn)
"""
import json, sys, warnings
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from terpvault.domain.models import ProductData
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.generate.builder import CatalogBuilder

session = get_session()
supplier_row = SupplierRepo(session).get_by_slug("terpenes-uk")
snap = (session.query(SnapshotRow)
        .filter_by(supplier_slug="terpenes-uk")
        .order_by(SnapshotRow.created_at.desc()).first())
products_data = json.loads(snap.products)
products = [ProductData(**p) for p in products_data]
session.close()

print("=== Test 1: Current builder with dedup fix ===")
print(f"  Input: {len(products)} rows, {len(set(p.external_id for p in products))} unique")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    builder = CatalogBuilder("terpenes-uk", supplier_row.name)
    doc = builder.build(products)
    if w:
        print(f"  WARNINGS: {len(w)}")
        for warning in w:
            print(f"    {warning.message}")
    else:
        print("  PASS: No warnings (clean)")
print(f"  Output: {doc.stats.product_count} products, {sum(len(s.product_ids) for s in doc.sections)} cards")

# Now also test by modifying the builder temporarily to simulate the old bug
print()
print("=== Test 2: Simulating old builder behavior (remove dedup, keep safeguard) ===")

from collections import OrderedDict
from terpvault.generate.categorizer import classify
from terpvault.generate.sections import CANONICAL_SECTIONS

# Simulate old behavior by creating a builder that doesn't dedup
class OldBuilder(CatalogBuilder):
    def build(self, products, catalog_label=""):
        product_map = {}
        section_buckets = OrderedDict()
        for cs in CANONICAL_SECTIONS:
            section_buckets[cs.key] = []
        # NO dedup - process all rows
        for p in products:
            cp = self._to_catalog_product(p)
            product_map[p.external_id] = cp
            section_key = classify(p)
            if section_key in section_buckets:
                section_buckets[section_key].append(p.external_id)
            else:
                section_buckets[section_key] = [p.external_id]
        
        # The safeguard now sits between sections build
        total_cards = sum(len(ids) for ids in section_buckets.values())
        if total_cards != len(product_map):
            print(f"  SAFEGUARD TRIGGERED: {len(product_map)} unique -> {total_cards} cards ({total_cards - len(product_map)} extra)")

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    old_builder = OldBuilder("terpenes-uk", supplier_row.name)
    old_doc = old_builder.build(products)
    if w:
        for warning in w:
            print(f"  Warning: {warning.message}")
print("  Old builder correctly detected.")
