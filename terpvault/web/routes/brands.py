from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.web.template_config import render_string
from terpvault.web.routes.common import load_catalog, slugify, get_brands

router = APIRouter()


@router.get("/catalogs/{slug}/brands", response_class=HTMLResponse)
def brands_page(request: Request, slug: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Catalog not found", status_code=404)
    brands = get_brands(catalog)
    html = render_string("brands.html", slug=slug, catalog=catalog, brands=brands)
    return HTMLResponse(html)


@router.get("/catalogs/{slug}/brands/{brand_slug}", response_class=HTMLResponse)
def brand_page(request: Request, slug: str, brand_slug: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Catalog not found", status_code=404)

    brand = None
    for b in get_brands(catalog):
        if b["slug"] == brand_slug:
            brand = b
            break
    if brand is None:
        return HTMLResponse("Brand not found", status_code=404)

    brand_colors = {
        "eybna": "#2ecc71", "true terpenes": "#2c6b9e",
        "terp belt farms": "#c4883a", "terpenes uk": "#2C5F2D",
        "prestige": "#d4a85c", "dft": "#b8863a",
        "duty free terpenes": "#b8863a", "hardware": "#666",
        "live resin": "#6a3f8a",
    }

    sections = []
    for sec in catalog.get("sections", []):
        matching = [p for p in brand["products"] if p.get("external_id") in sec.get("product_ids", [])]
        if matching:
            sections.append({"section": sec, "products": matching})

    html = render_string("brand.html", slug=slug, catalog=catalog, brand=brand,
                         brand_colors=brand_colors, sections=sections)
    return HTMLResponse(html)
