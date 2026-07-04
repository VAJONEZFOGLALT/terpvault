import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.web.template_config import render_string
from terpvault.web.routes.suppliers import router as suppliers_router
from terpvault.web.routes.timeline import router as timeline_router
from terpvault.web.routes.search import router as search_router
from terpvault.web.routes.catalog import router as catalog_router
from terpvault.web.routes.brands import router as brands_router
from terpvault.web.routes.products import router as products_router
from terpvault.web.routes.changes import router as changes_router

PDF_FILENAMES = {
    "catalogue.pdf": "TerpVault-Catalogue.pdf",
    "catalogue-print.pdf": "TerpVault-Catalogue-Print.pdf",
    "catalogue-digital.pdf": "TerpVault-Catalogue-Digital.pdf",
}

REFRESH_INTERVAL_HOURS = 6
SUPPLIER_SLUG = "terpenes-uk"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REFRESH_SCRIPT = PROJECT_ROOT / "scripts" / "refresh_catalog.py"


def _run_refresh():
    log = PROJECT_ROOT / "data" / "catalogs" / SUPPLIER_SLUG / "refresh.log"
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(log, "a") as f:
        f.write(f"[{ts}] Starting refresh\n")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(REFRESH_SCRIPT)],
            capture_output=True, text=True, timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        with open(log, "a") as f:
            f.write(result.stdout + "\n")
            if result.returncode != 0:
                f.write(f"[{ts}] FAIL: {result.stderr.strip()[:200]}\n")
    except Exception as e:
        with open(log, "a") as f:
            f.write(f"[{ts}] ERROR: {e}\n")


async def _refresh_loop():
    while True:
        await asyncio.sleep(REFRESH_INTERVAL_HOURS * 3600)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _run_refresh)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_refresh_loop())
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, _run_refresh)
    yield
    task.cancel()


APP_VERSION = settings.version
app = FastAPI(title="TerpVault", version=APP_VERSION, lifespan=lifespan)

app.include_router(suppliers_router)
app.include_router(timeline_router)
app.include_router(search_router)
app.include_router(catalog_router)
app.include_router(brands_router)
app.include_router(products_router)
app.include_router(changes_router)

catalogs_static = settings.catalogs_dir
if catalogs_static.exists():
    app.mount("/catalogs", StaticFiles(directory=str(catalogs_static)), name="catalogs")

prod_static = settings.prod_dir
if prod_static.exists():
    from fastapi import APIRouter
    prod_router = APIRouter()

    @prod_router.get("/{slug}/{filename:path}")
    def prod_file(slug: str, filename: str):
        file_path = prod_static / slug / filename
        if not file_path.exists() or not file_path.is_file():
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        download_name = PDF_FILENAMES.get(filename)
        if download_name:
            return FileResponse(
                path=str(file_path),
                media_type="application/pdf",
                filename=download_name,
                content_disposition_type="attachment",
            )
        return FileResponse(path=str(file_path))

    app.include_router(prod_router, prefix="/prod")

assets_dir = Path(__file__).resolve().parent / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


def _find_suppliers() -> list[dict]:
    config_dir = settings.config_dir
    suppliers = []
    for f in sorted(config_dir.glob("*.yaml")):
        slug = f.stem
        cat_dir = settings.catalogs_dir / slug
        stats = None
        if cat_dir.exists():
            for cat_file in sorted(cat_dir.glob("catalog-*.json"), reverse=True):
                try:
                    data = json.loads(cat_file.read_text(encoding="utf-8"))
                    products = data.get("products", {})
                    stats = {
                        "product_count": len(products),
                        "brand_count": data.get("stats", {}).get("brand_count", 0),
                        "section_count": len(data.get("sections", [])),
                        "variant_count": data.get("stats", {}).get("variant_count", 0),
                        "generated_at": data.get("stats", {}).get("generated_at", ""),
                    }
                    break
                except (json.JSONDecodeError, KeyError):
                    continue
        try:
            cfg = SupplierConfig.load(slug)
            name = cfg.name
        except (FileNotFoundError, Exception):
            name = slug.replace("-", " ").title()
        suppliers.append({"slug": slug, "name": name, "stats": stats})
    return suppliers


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    suppliers = _find_suppliers()
    html = render_string("portal.html", suppliers=suppliers, is_portal=True, app_version=APP_VERSION)
    return HTMLResponse(html)


@app.get("/health")
def health():
    from datetime import timezone
    return {
        "status": "ok",
        "refresh_interval_hours": REFRESH_INTERVAL_HOURS,
        "supplier": SUPPLIER_SLUG,
    }
