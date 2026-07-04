from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.config.settings import settings
from terpvault.web.template_config import render_string
from terpvault.web.routes.common import load_catalog

router = APIRouter()


@router.get("/catalogs/{slug}/search", response_class=HTMLResponse)
def search_page(request: Request, slug: str, q: str = ""):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Supplier not found", status_code=404)

    entries = []
    for pid, p in catalog.get("products", {}).items():
        name = p.get("name", "")
        brand = p.get("brand") or ""
        cat = p.get("category") or ""
        coll = p.get("collection") or ""
        searchable = " ".join(filter(None, [name, brand, cat, coll, pid])).lower()
        entries.append({
            "id": pid,
            "name": name,
            "brand": brand or None,
            "collection": coll or None,
            "category": cat or None,
            "price": p.get("price"),
            "searchable": searchable,
        })

    results = []
    query = q.strip().lower()
    if query:
        for entry in entries:
            if query in entry["searchable"]:
                results.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "brand": entry["brand"],
                    "collection": entry["collection"],
                    "category": entry["category"],
                    "price": entry["price"],
                })

    html = render_string("search.html", slug=slug, query=query, results=results, total=len(entries))
    return HTMLResponse(html)
