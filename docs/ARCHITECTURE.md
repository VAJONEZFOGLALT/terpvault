# TerpVault Architecture

## Overview

TerpVault is a digital wholesale catalogue platform. It ingests product data from supplier APIs, normalizes it into a canonical schema, generates a structured catalogue document, and exports it as a website, PDF, and JSON.

```
Supplier API (Shopify)
     │
     ▼
Sync Engine
     │
     ├── Normalize
     ├── Store (SQLite)
     └── Diff (Change Tracking)
     │
     ▼
CatalogBuilder
     │
     ├── Classify (canonical sections)
     ├── Build CatalogDocument
     └── Integrity check
     │
     ▼
Export
     │
     ├── catalog.json (full CatalogueDocument)
     ├── search_index.json
     └── prod/ (production artifacts)
```

## Directory layout

```
TerpVault/
├── alembic/              # DB migrations
├── data/
│   ├── catalogs/         # Raw engine output per supplier
│   └── db/               # SQLite database
├── prod/                 # Production artifacts (served by website)
│   └── {supplier}/
│       ├── catalog.json
│       ├── catalogue.pdf
│       └── search_index.json
├── scripts/              # Utility scripts
│   ├── refresh_catalog.py
│   ├── generate_mockups.py
│   └── generate_logo_concepts.py
├── terpvault/            # Python package
│   ├── config/           # Settings + supplier configs
│   ├── domain/           # Data models
│   ├── generate/         # Catalogue building + artifact generation
│   ├── storage/          # DB access
│   ├── sync/             # Supplier import pipeline
│   └── web/              # FastAPI website
│       ├── assets/       # CSS, JS, logos, favicons
│       ├── routes/       # Route handlers
│       └── templates/    # Jinja2 templates
├── tests/
├── VERSION
└── pyproject.toml
```

## Key concepts

### Supplier
A single source of product data. Configured via a YAML file in `terpvault/config/suppliers/`. Each supplier gets its own subdirectory in `prod/` and `data/catalogs/`.

### CatalogDocument
A frozen Pydantic model representing the complete catalogue: cover, table of contents, sections, products, and stats. This is the single source of truth for all exports.

### Build Pipeline
1. `SyncEngine.run()` — fetches, normalizes, and stores products; computes diffs
2. `CatalogBuilder.build()` — classifies products into canonical sections; produces CatalogDocument
3. `export_json()` — writes CatalogDocument + search index to disk
4. `scripts/refresh_catalog.py` — runs both steps and copies to `prod/`

### Auto-refresh
The FastAPI server runs a background task every 6 hours that triggers the build pipeline. Results are written to `data/catalogs/` and copied to `prod/`.

## Adding a new supplier

1. Add a YAML config in `terpvault/config/suppliers/`
2. Implement an importer class following the pattern in `terpvault/sync/importer/terpenes_uk.py`
3. The `SyncEngine` will discover it automatically via the config's `importer_module` field

## Versioning

The canonical version is stored in `VERSION` at the project root. It is read by `terpvault/config/settings.py` and displayed in the website footer and FastAPI metadata.
