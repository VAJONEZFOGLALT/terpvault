import json
import re
from pathlib import Path

from terpvault.config.settings import settings


def load_catalog(slug: str) -> dict | None:
    # Prefer production artifact, fall back to data/catalogs
    prod = settings.prod_dir / slug / "catalog.json"
    if prod.exists():
        try:
            return json.loads(prod.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    cat_dir = settings.catalogs_dir / slug
    if not cat_dir.exists():
        return None
    files = sorted(cat_dir.glob("catalog-*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def get_brands(catalog: dict) -> list[dict]:
    brands = {}
    for p in catalog.get("products", {}).values():
        b = p.get("brand")
        if b:
            b_slug = slugify(b)
            if b not in brands:
                brands[b] = {"name": b, "slug": b_slug, "count": 0, "products": [], "sections": set()}
            brands[b]["count"] += 1
            brands[b]["products"].append(p)
            if p.get("collection"):
                brands[b]["sections"].add(p["collection"])
    result = []
    for b in brands.values():
        b["sections"] = sorted(b["sections"])
        result.append(b)
    return sorted(result, key=lambda x: x["name"].lower())
