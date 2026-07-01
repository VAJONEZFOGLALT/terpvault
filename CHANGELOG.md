# Changelog

## 0.1.0 — 2026-06-30

### Milestone 1 — Sync Pipeline (Complete)

- Project skeleton with pyproject.toml, CLI, and settings
- Domain models: Supplier, Product, Variant, Image, Snapshot
- SQLite storage with SQLAlchemy 2.x and Alembic migrations
- Supplier configuration system (YAML-based)
- SupplierClient with HTTP, rate limiting, and retries
- ShopifyNormalizer for converting Shopify JSON → RawProduct
- Terpenes UK importer (crawls collections/products)
- SyncEngine: atomic fetch → normalize → store → snapshot pipeline
- 29 tests covering normalization, storage, sync engine, CLI, and rollback

### Key Features

- Raw supplier JSON preserved exactly on every product
- Atomic sync transactions (all-or-nothing)
- Idempotent re-sync (no duplicate records)
- Snapshot created per sync with checksum
- CLI: `terpvault sync <supplier>`
