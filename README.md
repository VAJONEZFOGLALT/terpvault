# TerpVault

Supplier synchronization and catalog publishing platform.

It imports supplier product data, preserves every version as a snapshot, and generates premium wholesale catalogs as reusable publishing artifacts.

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
CatalogDocument (in-memory renderer-agnostic model)
  ↓
Artifacts (PDF, HTML, search index, manifest, ...)
```

### Key Design Decisions

- **Supplier-agnostic**: Adding a supplier requires a config file and an importer — no core engine changes.
- **Raw data preserved**: Every product's `raw` column stores the exact supplier JSON, enabling re-normalization without re-fetching.
- **Snapshot-first publishing**: Catalogs are generated from historical snapshots, not the current database. `terpvault generate --from snapshot-2026-01-14` works forever.
- **Atomic sync**: Each synchronization runs in a single database transaction. If anything fails, no partial data is written.
- **Config-driven branding**: All visual supplier information (colors, fonts, logo) comes from YAML config, not code.

## Usage

```bash
# Synchronize supplier data
terpvault sync <supplier-slug>

# Show help
terpvault --help
```

## Adding a New Supplier

1. Create `terpvault/config/suppliers/<slug>.yaml` with branding and connection details.
2. Create `terpvault/sync/importer/<slug>.py` with a class implementing `fetch_products()` and the normalizer.
3. Run `terpvault sync <slug>`.

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
| M2 — Diff & Changelog | ⏳ Next |
| M3 — PDF Publishing | 📅 Planned |
| M4 — HTML + Web Interface | 📅 Planned |
| M5 — Second Supplier | 📅 Planned |
