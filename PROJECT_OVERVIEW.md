# TerpVault v2.0 — Complete Project Overview

## What is TerpVault?

A digital wholesale catalogue platform. It ingests product data from supplier APIs, normalises it, generates a structured catalogue document, and exports it as a website, PDF, and JSON.

---

## Project Structure

```
TerpVault/
├── prod/                     # Production artifacts (served by website)
│   └── terpenes-uk/
│       ├── catalog.json      # Full catalogue data (337 products, 13 brands, 16 sections)
│       ├── catalogue.pdf     # Editorial PDF (136MB, A4, full branding)
│       ├── search_index.json # Client-side search index
│       └── build.json        # Build metadata
├── terpvault/
│   ├── web/                  # FastAPI website
│   │   ├── assets/           # CSS, JS, logos, favicons
│   │   ├── routes/           # Route handlers
│   │   └── templates/        # Jinja2 templates (base + 8 page templates)
│   ├── config/               # Settings + supplier YAML configs
│   ├── domain/               # Pydantic data models
│   ├── generate/             # Catalogue building, PDF/HTML generation, search indexing
│   ├── storage/              # SQLite database access
│   └── sync/                 # Supplier import pipeline (Shopify → normalised data)
├── scripts/
│   ├── refresh_catalog.py    # Auto-refresh (called every 6h by scheduler)
│   ├── generate_mockups.py   # Concept PNG generation
│   └── generate_logo_concepts.py  # SVG logo generator
├── tests/
├── docs/
│   └── ARCHITECTURE.md
├── VERSION                   # Single source of truth (2.0.0)
├── pyproject.toml
└── README.md
```

---

## Key Numbers

- **337 products** — normalised, categorised, integrity-checked
- **13 brands** — each with dedicated brand pages
- **16 canonical sections** — across 8 chapters
- **1,815 variants** — with pricing and availability
- **48 PDF versions** — cleaned to single latest
- **0 duplicates** — engine enforces uniqueness
- **0 integrity errors** — build gate prevents publishing bad data

---

## Architecture

```
Supplier API (Shopify)
     │
     ▼
Sync Engine (fetch → normalise → store → diff)
     │
     ▼
CatalogBuilder (classify → build CatalogueDocument → integrity check)
     │
     ▼
Export → prod/catalog.json, prod/search_index.json
     │
     ▼
PDF Generator → prod/catalogue.pdf
     │
     ▼
Website (FastAPI + Jinja2) → serves everything from prod/
     │
     ▼
Cloudflare Tunnel → terpvault.space
```

---

## Website Pages

| Page | Route | Description |
|---|---|---|
| Portal | `/` | Supplier selector with stats |
| Dashboard | `/catalogs/{slug}` | Latest build, quick actions, highlights, featured products |
| Catalogue | `/catalogs/{slug}/catalogue` | Chapter/section filtered product browser |
| Brands | `/catalogs/{slug}/brands` | Brand cards with product counts |
| Brand Detail | `/catalogs/{slug}/brands/{brand}` | Products by section per brand |
| Product | `/catalogs/{slug}/products/{id}` | Gallery, variants, related products |
| Search | `/catalogs/{slug}/search` | Full-text product search |
| Downloads | `/catalogs/{slug}/downloads` | Latest PDF + JSON downloads |
| Timeline | `/catalogs/{slug}/timeline` | Change history |
| Health | `/health` | Scheduler status |

---

## Key Features

- **Dark/light theme** with system detection
- **Auto-refresh** every 6 hours (inline scheduler)
- **Instant search** with keyboard navigation
- **Responsive** desktop, tablet, mobile
- **PDF export** — editorial layout, brand colours, 337 products
- **JSON export** — full catalogue data for developers
- **Theme system** — CSS custom properties, not hardcoded colours
- **Supplier abstraction** — add new suppliers via YAML config

---

## To add a new supplier

1. Create `terpvault/config/suppliers/{slug}.yaml`
2. Implement an importer class
3. Run `python scripts/refresh_catalog.py` (with slug changed)
4. The website automatically picks it up at `/catalogs/{slug}/`

No architecture changes needed.

---

## Running the project

```bash
# Install
pip install -e .

# Sync + export
python scripts/refresh_catalog.py

# Start website
uvicorn terpvault.web.app:app --host 127.0.0.1 --port 9199

# Or via CLI
terpvault serve
```

The inline scheduler runs sync + export automatically every 6 hours.

---

## Live Site

https://terpvault.space
