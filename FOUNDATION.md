# TerpVault Foundation

## Status

Engine frozen at v1.0.0-engine.

## Permanent architectural decisions

These decisions are considered permanent unless a real production issue
requires changing them. They should not be revisited for aesthetic or
architectural preference.

### Engine → Artifacts → Portal

The engine generates artifacts onto disk. The portal consumes artifacts
from disk. The portal never reads the database. This makes artifacts
self-contained, portable, and versionable — a catalog can be zipped,
emailed, hosted on S3, or browsed fully offline.

### Immutable snapshots

Every sync creates an immutable point-in-time snapshot. Nothing
overwrites history. Snapshots enable catalog regeneration from any
past state without depending on the current database.

### CatalogDocument as canonical model

The CatalogDocument is the single source of truth for all publishing
outputs. It is immutable once built. Every artifact (PDF, HTML, JSON,
search index, manifest) consumes the same document. No renderer
modifies it.

### Artifact-only portal

The web portal reads only pre-generated artifacts from disk. It
performs no database queries, no regeneration, and no business logic.
This keeps the portal deployable as static files or behind any
web server.

### Supplier-agnostic pipeline

Adding a supplier requires a config YAML and an importer file.
Nothing in the core engine, CatalogDocument, artifact generators,
or portal knows about any specific supplier.

### Frozen engine

All engine code is considered stable and complete after v1.0.0-engine.
Changes should only be made for verified bugs, not for architectural
preference. The design-lab branch is where visual and editorial
improvements happen.
