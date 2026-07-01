from pathlib import Path
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.config.settings import settings
from terpvault.web.template_config import render_string

router = APIRouter()


@router.get("/supplier/{slug}/search", response_class=HTMLResponse)
def search_page(request: Request, slug: str, q: str = ""):
    search_path = settings.catalogs_dir / slug / "search_index.json"
    if not search_path.exists():
        return HTMLResponse("Search index not found. Run `terpvault export` first.", status_code=404)

    data = json.loads(search_path.read_text(encoding="utf-8"))
    results = []
    query = q.strip().lower()
    if query:
        for entry in data["entries"]:
            if query in entry["searchable"]:
                results.append(entry)

    html = render_string("search.html", slug=slug, query=query, results=results, total=data["count"])
    return HTMLResponse(html)
