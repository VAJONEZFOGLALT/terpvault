import json
from pathlib import Path

from terpvault.domain.catalog_document import CatalogDocument


def build_search_index(doc: CatalogDocument) -> dict:
    entries = []
    for pid, p in doc.products.items():
        searchable = " ".join(filter(None, [
            p.name,
            p.brand or "",
            p.collection or "",
            p.category or "",
            pid,
            p.description or "",
        ]))
        variants_text = " ".join(
            str(v.get("sku", "")) for v in p.variants
        )
        searchable += " " + variants_text
        entries.append({
            "id": pid,
            "name": p.name,
            "brand": p.brand,
            "collection": p.collection,
            "category": p.category,
            "price": p.price,
            "searchable": searchable.lower(),
        })
    return {"entries": entries, "count": len(entries)}


def write_search_index(doc: CatalogDocument, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = build_search_index(doc)
    path = output_dir / "search_index.json"
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path
