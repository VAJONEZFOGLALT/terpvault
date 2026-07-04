from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.config.settings import settings
from terpvault.web.template_config import render_string
from terpvault.web.routes.common import load_catalog

router = APIRouter()


@router.get("/catalogs/{slug}", response_class=HTMLResponse)
def supplier_portal(request: Request, slug: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Supplier not found", status_code=404)
    html = render_string("supplier.html", slug=slug, catalog=catalog)
    return HTMLResponse(html)


@router.get("/catalogs/{slug}/downloads", response_class=HTMLResponse)
def downloads_page(request: Request, slug: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Supplier not found", status_code=404)

    html = render_string("downloads.html", slug=slug, catalog=catalog)
    return HTMLResponse(html)
