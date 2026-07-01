from pathlib import Path
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig

router = APIRouter()

from terpvault.web.template_config import render_string


def _get_supplier_data(slug: str) -> dict | None:
    catalogs_dir = settings.catalogs_dir / slug
    if not catalogs_dir.exists():
        return None

    catalogs = []
    for cat_file in sorted(catalogs_dir.glob("catalog-*.json"), reverse=True):
        try:
            data = json.loads(cat_file.read_text(encoding="utf-8"))
            sections = data.get("sections", [])
            products = data.get("products", {})
            snapshot_id = cat_file.stem.replace("catalog-", "")
            catalogs.append({
                "filename": cat_file.name,
                "snapshot_id": snapshot_id,
                "timestamp": data.get("stats", {}).get("generated_at", ""),
                "product_count": len(products),
                "brand_count": data.get("stats", {}).get("brand_count", 0),
                "section_count": len(sections),
                "variant_count": data.get("stats", {}).get("variant_count", 0),
                "image_count": data.get("stats", {}).get("image_count", 0),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    name = slug.replace("-", " ").title()
    try:
        cfg = SupplierConfig.load(slug)
        name = cfg.name
    except (FileNotFoundError, Exception):
        pass
    return {
        "slug": slug,
        "name": name,
        "catalogs": catalogs,
    }


@router.get("/supplier/{slug}", response_class=HTMLResponse)
def supplier_page(request: Request, slug: str):
    data = _get_supplier_data(slug)
    if data is None:
        return HTMLResponse("Supplier not found", status_code=404)
    html = render_string("supplier.html", supplier=data)
    return HTMLResponse(html)
