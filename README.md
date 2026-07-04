# TerpVault

Supplier synchronization and catalog publishing platform.

It imports supplier product data, preserves every version as a snapshot, and generates premium wholesale catalogs as reusable publishing artifacts.

## Live Demo

Browse the live catalogue at **[https://terpvault.space](https://terpvault.space)** — no setup required.

-   **Terpenes UK catalogue** — 337 products, 16 sections
-   **Downloadable PDF** — optimized for mobile (17 MB) and print master (130 MB)
-   **Full-text search**, brand pages, product timeline, changelog

## Quick Start

```bash
pip install -e ".[dev]"
alembic upgrade head
terpvault sync terpenes-uk
```

## Architecture

```
Supplier
  ↓
Raw Snapshot (exact supplier response, never modified)
  ↓
Normalized Catalog (Product, Variant, Image tables)
  ↓
Categorizer (rules-based classifier → canonical section)
  ↓
CatalogDocument (in-memory renderer-agnostic model)
  ↓
Integrity check (100% coverage, 0 duplicates = required)
  ↓
Artifacts (PDF, HTML, search index, manifest, ...)
```

### Key Design Decisions

- **Canonical sections, not Shopify collections**: Shopify collections are a merchandising tool, not a publication structure. Every product is classified into exactly one editorial section by the categorizer (`terpvault/generate/categorizer.py`). The manifest (`terpvault/generate/sections.py`) defines the canonical section order.
- **Build fails on coverage errors**: No product may appear in zero sections or more than one section. The integrity check enforces this.
- **Supplier-agnostic**: Adding a supplier requires a config file and an importer — no core engine changes.
- **Raw data preserved**: Every product's `raw` column stores the exact supplier JSON, enabling re-normalization without re-fetching.
- **Snapshot-first publishing**: Catalogs are generated from historical snapshots, not the current database.
- **Atomic sync**: Each synchronization runs in a single database transaction. If anything fails, no partial data is written.
- **Config-driven branding**: All visual supplier information (colors, fonts, logo) comes from YAML config, not code.

## Usage

```bash
# Synchronize supplier data
terpvault sync <supplier-slug>

# Export catalog from latest snapshot
terpvault export <supplier-slug>

# Show help
terpvault --help
```

## Adding a New Supplier

1. Create `terpvault/config/suppliers/<slug>.yaml` with branding and connection details.
2. Create `terpvault/sync/importer/<slug>.py` with a class implementing `fetch_products()` and the normalizer.
3. Optionally extend `terpvault/generate/categorizer.py` with supplier-specific classification rules.
4. Run `terpvault sync <slug>`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

All schema changes must go through Alembic migrations:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Milestones

| Milestone | Status |
|-----------|--------|
| M1 — Sync Pipeline | ✅ Complete |
| M2 — Diff & Changelog | ✅ Complete |
| M3 — Catalog Foundation (categorizer, sections, integrity) | ✅ Complete |
| M4 — PDF Publishing | ✅ Complete |
| M5 — Editorial Design (typography, grids, visual hierarchy) | 📅 Next |
| M6 — Second Supplier | 📅 Planned |
