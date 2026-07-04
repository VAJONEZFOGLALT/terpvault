from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from terpvault.config.settings import settings
from terpvault.web.template_config import render_string
from terpvault.web.routes.common import load_catalog, slugify, get_brands

router = APIRouter()


def _get_chapters(catalog: dict) -> list[str]:
    seen = set()
    chapters = []
    chapter_map = {
        "Strain Profiles": ["Eybna", "True Terpenes", "Terpene Belt Farms", "Terpenes UK - Botanical", "Prestige", "Duty Free Terpenes", "Strain Profiles", "Terpenes UK", "True Terpenes"],
        "Live Resin": ["Live Resin"],
        "Infusion": ["Concentrated Flavours", "Oil Soluble Flavours", "NEU Bag Infusion Packs"],
        "Isolates": ["Terpene Isolates"],
        "Hardware & Ingredients": ["Extract Liquidisers", "Diluents", "Vape Hardware"],
        "Sample Packs": ["Sample Packs"],
        "New Releases": ["New Releases"],
        "Clearance": ["Clearance"],
    }
    for section in catalog.get("sections", []):
        for ch, labels in chapter_map.items():
            if section["label"] in labels and ch not in seen:
                seen.add(ch)
                chapters.append(ch)
                break
    return chapters


@router.get("/catalogs/{slug}/catalogue", response_class=HTMLResponse)
def catalogue_page(request: Request, slug: str, chapter: str = "", section: str = ""):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Catalog not found", status_code=404)

    chapters = _get_chapters(catalog)
    brands = get_brands(catalog)

    filtered_sections = catalog.get("sections", [])
    if chapter:
        chapter_labels = {
            "strain-profiles": ["Eybna", "True Terpenes", "Terpene Belt Farms", "Terpenes UK - Botanical", "Prestige", "Duty Free Terpenes", "Strain Profiles", "Terpenes UK", "True Terpenes"],
            "live-resin": ["Live Resin"],
            "infusion": ["Concentrated Flavours", "Oil Soluble Flavours", "NEU Bag Infusion Packs"],
            "isolates": ["Terpene Isolates"],
            "hardware-ingredients": ["Extract Liquidisers", "Diluents", "Vape Hardware"],
            "sample-packs": ["Sample Packs"],
            "new-releases": ["New Releases"],
            "clearance": ["Clearance"],
        }
        allowed = chapter_labels.get(chapter, [])
        filtered_sections = [s for s in filtered_sections if s["label"] in allowed]

    html = render_string("catalog.html",
        slug=slug, catalog=catalog, sections=filtered_sections,
        chapters=chapters, brands=brands,
        active_chapter=chapter, active_section=section,
    )
    return HTMLResponse(html)


@router.get("/catalogs/{slug}/search-data")
def search_data(slug: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return JSONResponse({"entries": [], "count": 0})
    entries = []
    for pid, p in catalog.get("products", {}).items():
        name = p.get("name", "")
        brand = p.get("brand") or ""
        cat = p.get("category") or ""
        coll = p.get("collection") or ""
        searchable = " ".join(filter(None, [name, brand, cat, coll, pid])).lower()
        entries.append({"id": pid, "name": name, "brand": brand or None, "price": p.get("price"), "searchable": searchable})
    return JSONResponse({"entries": entries, "count": len(entries)})
