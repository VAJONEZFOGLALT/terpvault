from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from terpvault.web.template_config import render_string
from terpvault.web.routes.common import load_catalog

router = APIRouter()


@router.get("/catalogs/{slug}/products/{product_id}", response_class=HTMLResponse)
def product_page(request: Request, slug: str, product_id: str):
    catalog = load_catalog(slug)
    if catalog is None:
        return HTMLResponse("Catalog not found", status_code=404)

    product = catalog.get("products", {}).get(product_id)
    if product is None:
        return HTMLResponse("Product not found", status_code=404)

    related = []
    for pid, p in catalog.get("products", {}).items():
        if pid == product_id:
            continue
        if p.get("brand") == product.get("brand") or p.get("collection") == product.get("collection"):
            if len(related) < 6:
                related.append({"id": pid, **p})

    section_name = None
    for sec in catalog.get("sections", []):
        if product_id in sec.get("product_ids", []):
            section_name = sec["label"]
            break

    html = render_string("product.html", slug=slug, catalog=catalog,
                         product=product, product_id=product_id,
                         section_name=section_name, related=related)
    return HTMLResponse(html)
