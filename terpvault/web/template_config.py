import json
import re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


_template_dir = Path(__file__).resolve().parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_template_dir)), enable_async=False)


def _slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _relative_time(iso_str: str) -> str:
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return "just now"
        if secs < 3600:
            m = secs // 60
            return f"{m} min ago"
        if secs < 86400:
            h = secs // 3600
            return f"{h} hour{'s' if h != 1 else ''} ago"
        if secs < 604800:
            d = secs // 86400
            return f"{d} day{'s' if d != 1 else ''} ago"
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        return iso_str[:10] if iso_str else "Unknown"


def render_string(name: str, **context) -> str:
    is_portal = context.pop("is_portal", False) if "is_portal" in context else False

    if not is_portal:
        if "slug" not in context:
            context["slug"] = "terpenes-uk"
        global_slug = context["slug"]
    else:
        global_slug = None

    _catalog_cache = {}

    def get_catalog():
        if global_slug is None:
            return None
        if global_slug in _catalog_cache:
            return _catalog_cache[global_slug]
        # Prefer prod/ catalog, fall back to data/catalogs/
        prod_path = Path(__file__).resolve().parent.parent.parent / "prod" / global_slug / "catalog.json"
        if prod_path.exists():
            try:
                data = json.loads(prod_path.read_text(encoding="utf-8"))
                _catalog_cache[global_slug] = data
                return data
            except (json.JSONDecodeError, OSError):
                pass
        cat_dir = Path(__file__).resolve().parent.parent.parent / "data" / "catalogs" / global_slug
        if not cat_dir.exists():
            return None
        files = sorted(cat_dir.glob("catalog-*.json"), reverse=True)
        if not files:
            return None
        try:
            data = json.loads(files[0].read_text(encoding="utf-8"))
            _catalog_cache[global_slug] = data
            return data
        except (json.JSONDecodeError, OSError):
            return None

    def catalog_chapters():
        return [
            "Strain Profiles", "Live Resin", "Infusion", "Isolates",
            "Hardware & Ingredients", "Sample Packs", "New Releases", "Clearance",
        ]

    def catalog_brands():
        catalog = get_catalog()
        if not catalog:
            return []
        brands = {}
        for p in catalog.get("products", {}).values():
            b = p.get("brand")
            if b:
                b_slug = _slugify(b)
                if b not in brands:
                    brands[b] = {"name": b, "slug": b_slug, "count": 0}
                brands[b]["count"] += 1
        return sorted(brands.values(), key=lambda x: x["name"].lower())

    def latest_pdf():
        prod_dir = Path(__file__).resolve().parent.parent.parent / "prod" / global_slug
        for name in ("catalogue.pdf", "catalogue-print.pdf"):
            path = prod_dir / name
            if path.exists():
                return path.name
        cat_dir = Path(__file__).resolve().parent.parent.parent / "data" / "catalogs" / global_slug
        if not cat_dir.exists():
            return None
        files = sorted(cat_dir.glob("catalog-*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0].name if files else None

    def pdf_info(name: str) -> dict:
        prod_dir = Path(__file__).resolve().parent.parent.parent / "prod" / global_slug
        path = prod_dir / name
        if not path.exists():
            cat_dir = Path(__file__).resolve().parent.parent.parent / "data" / "catalogs" / global_slug
            path = cat_dir / name
        if not path.exists():
            return {"pages": 0, "size_mb": 0}
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = len(reader.pages)
        except Exception:
            pages = 0
        size_mb = path.stat().st_size / (1024 * 1024)
        return {"pages": pages, "size_mb": round(size_mb, 1)}

    def latest_json():
        prod_path = Path(__file__).resolve().parent.parent.parent / "prod" / global_slug / "catalog.json"
        if prod_path.exists():
            return prod_path.name
        cat_dir = Path(__file__).resolve().parent.parent.parent / "data" / "catalogs" / global_slug
        if not cat_dir.exists():
            return None
        files = sorted(cat_dir.glob("catalog-*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0].name if files else None

    _env.globals["get_catalog"] = get_catalog
    _env.globals["catalog_chapters"] = catalog_chapters
    _env.globals["catalog_brands"] = catalog_brands
    _env.globals["latest_pdf"] = latest_pdf
    _env.globals["pdf_info"] = pdf_info
    _env.globals["latest_json"] = latest_json
    _env.globals["is_portal"] = is_portal
    _env.filters["slugify"] = _slugify
    _env.filters["relative_time"] = _relative_time
    _env.globals["slug"] = global_slug

    template = _env.get_template(name)
    return template.render(**context)
