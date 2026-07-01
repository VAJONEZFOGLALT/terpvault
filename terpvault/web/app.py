from pathlib import Path
import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.web.template_config import render_string
from terpvault.web.routes.suppliers import router as suppliers_router
from terpvault.web.routes.timeline import router as timeline_router
from terpvault.web.routes.search import router as search_router

app = FastAPI(title="TerpVault", version="0.4.0")

app.include_router(suppliers_router)
app.include_router(timeline_router)
app.include_router(search_router)

catalogs_static = settings.catalogs_dir
if catalogs_static.exists():
    app.mount("/catalogs", StaticFiles(directory=str(catalogs_static)), name="catalogs")




def _find_suppliers() -> list[dict]:
    config_dir = settings.config_dir
    suppliers = []
    for f in sorted(config_dir.glob("*.yaml")):
        slug = f.stem
        catalogs_dir = settings.catalogs_dir / slug
        catalogs = []
        if catalogs_dir.exists():
            for cat_file in sorted(catalogs_dir.glob("catalog-*.json"), reverse=True):
                try:
                    data = json.loads(cat_file.read_text(encoding="utf-8"))
                    products = data.get("products", {})
                    catalogs.append({
                        "product_count": len(products),
                        "brand_count": data.get("stats", {}).get("brand_count", 0),
                        "section_count": len(data.get("sections", [])),
                        "timestamp": data.get("stats", {}).get("generated_at", ""),
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
        suppliers.append({
            "slug": slug,
            "name": _supplier_name(slug),
            "catalog_count": len(catalogs),
            "latest_catalog": catalogs[0] if catalogs else None,
        })
    return suppliers


def _supplier_name(slug: str) -> str:
    try:
        cfg = SupplierConfig.load(slug)
        return cfg.name
    except (FileNotFoundError, Exception):
        return slug.replace("-", " ").title()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    suppliers = _find_suppliers()
    html = render_string("portal.html", suppliers=suppliers, version="0.4.0")
    return HTMLResponse(html)
