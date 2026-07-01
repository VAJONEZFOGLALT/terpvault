from pathlib import Path
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.config.settings import settings
from terpvault.web.template_config import render_string

router = APIRouter()


@router.get("/supplier/{slug}/timeline", response_class=HTMLResponse)
def timeline_page(request: Request, slug: str):
    changes_path = settings.catalogs_dir / slug / "changes.json"
    if not changes_path.exists():
        return HTMLResponse("No change history available.", status_code=404)

    try:
        data = json.loads(changes_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return HTMLResponse("Could not read change history.", status_code=500)

    html = render_string("timeline.html", slug=slug, changes=data)
    return HTMLResponse(html)
