"""
The template's section_config is missing 'Clearance' and 'New Releases'.
Clearance has 3 products — they're classified but never rendered.
That accounts for the 3 fewer images in the new PDF vs legacy.
"""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

catalog_json = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json"
with open(catalog_json, encoding="utf-8") as f:
    data = json.load(f)

# Find Clearance section
for s in data["sections"]:
    if s["label"] == "Clearance":
        print(f"=== Clearance Section ({len(s['product_ids'])} products) ===")
        for pid in s["product_ids"]:
            p = data["products"].get(pid, {})
            print(f"  {p.get('name','?'):40s} (id: {pid})  brand={p.get('brand')}")
    elif s["label"] == "New Releases":
        print(f"=== New Releases Section ({len(s['product_ids'])} products) ===")
        for pid in s["product_ids"]:
            p = data["products"].get(pid, {})
            print(f"  {p.get('name','?'):40s} (id: {pid})  brand={p.get('brand')}")
