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

## 1.0.0 — 2026-07-01

### V9 Design Toolkit

- `scripts/export_pages.py` — Export PDF pages as 200 DPI PNGs via PyMuPDF
- `scripts/catalog_metrics.py` — Per-page whitespace, utilization, and text density analysis
- `scripts/catalog_review.py` — Automated per-page review generating `review/NNN-review.md` + `PAGE_AUDIT.md`
- Workflow: Generate PDF → export_pages → review → iterate

### V9 Catalog Template Fixes

- Removed duplicate Flavours and Oil Soluble Flavours chapters (products already rendered under Infusion)
- Removed nested `<div class="product-grid">` from render_section macro to prevent double-wrapping
- Fixed gen_pdf.py to output to `data/catalogs/terpenes-uk/` directory

### V10 Design Improvements

- **Tighter card layout**: Reduced card width gap (0.18→0.12cm), increased card width (31.8%→32.5%), reduced padding, smaller margins (2cm→1.5cm top), card image height (3.5→3.2cm)
- **Typography refinement**: Product name 8.5pt→8pt, price 10pt→8.5pt, description 6pt→5.5pt, badges 5pt→4.5pt
- **Running header infrastructure**: Added `string-set` on chapter openers and brand openers for `@top-left` running header; added `@top-right` for section name
- **Chapter accent colors**: Infusion (brown), Isolates (blue), Hardware (graphite), Sample Packs (purple) with matching background gradients
- **Editorial inserts**: Added callout card grid with styled cards (white bg, green top border) for CDT/BDT comparison and Choosing a Profile
- **2-column grids**: Sparse sections (Liquidisers, Diluents, Hardware, Bundle, Concentrated Flavours, Oil Soluble Flavours) now use `.grid-2col` for larger cards
- **Page count**: V8=57 → V9=49 → V10=55 pages (337 unique products, 0 duplicates)
- **CSS image container**: Changed from white to `var(--canvas)` for consistent background fill

### V11 Blocking Fixes

- **TOC page numbers**: JavaScript computes page positions at render time, fills `.toc-page` cells via `data-target` ID references. Chapters 1-8 now show real page numbers.
- **Badge system**: Replaced hardcoded "PREMIUM CDT" with data-driven badges reading from product name, collection, and brand keywords. Assigns CDT/BDT/Live Resin/Oil Soluble/Isolate/Prestige badges correctly per product.
- **Sample packs dedup**: `reserved_ids` namespace pre-loads all Bundle product IDs before brand section rendering. Brand sections skip reserved IDs. Sample packs render only in the Sample Packs chapter.
- **Prestige page break**: Added `.collection-hero` CSS class with `page-break-before: always` applied to Prestige, Live Resin, and Eybna Enhancer Line subsections.
- **Page count**: V10=55 → V11=56 (Prestige page break added 1 page).

### V12 Visual Redesign

- **Cover**: Replaced emoji placeholder with typographic wordmark ("Terpenes UK" + "Est. 2018"). Cleaner, no placeholder assets.
- **Chapter-specific card layouts**: Isolate cards (`.isolate-card`) render without images, with compact text and specs. Hardware cards (`.hardware-card`) get larger image containers with grey backgrounds. Sample cards (`.sample-card`) render as full-width horizontal rows with image + text side by side.
- **Distinct visual treatments per chapter**: Hardware chapter uses grey-toned containers. Isolates chapter uses dense text layout. Sample Packs uses list-style cards. Each chapter now feels visually different.
- **Badge system expanded**: Added `badge-sample` for sample pack products, `product-card-stock` for hero card availability indicator.
- **Hero card infrastructure**: `.hero-card` class with larger image (5cm), larger name (10pt), larger price (10pt), and in-stock indicator. Ready for use when Jinja2 namespace mutation is resolved.
- **Page count**: V11=56 → V12=48 pages (denser isolate layout, compact sample list, tighter overall).
- **All 337 products render exactly once** — verified by dedup tracking.

### V13 — Hero Products

- **Jinja2 namespace mutation solved**: Used list-as-mutable-flag pattern (`hero_flag.append(1)`) to track whether hero cards have been rendered, avoiding `namespace.attr = value` limitation.
- **Hero cards active**: First 2 products in each major brand section render as `.hero-card` with larger image (5cm), larger name (10pt), larger price (10pt), and in-stock badge.
- **Page 6, 13, 24**: Larger rendered file sizes confirm hero cards are carrying more visual content.

### V14 — Curated Heroes

- **Replaced algorithmic hero selection** (`loop.index <= 2`) with curated name-based system. `render_brand_sections` now accepts `hero_names` parameter — a list of product names that should get hero treatment.
- **Curated hero products**: Permanent Marker, Lemon Cherry Gelato, Blue Zushi (Eybna); Wedding Cake (True Terpenes); Rainbow Belts, Honey Banana (Terpenes UK); Permanent Marker, White Truffle, Wedding Cake (Live Resin).
- **CURATION.md** documents editorial identity for every chapter with buyer's question, pacing, hero justifications, and comparison content.
- **Live Resin section separated** from True Terpenes with its own `render_brand_sections` call and dedicated hero list.
- **Page count**: V13=48 → V14=48 pages.

### V15 — Editorial Selling (RC1 / Print Candidate)

- **4 new editorial sell-spreads** interspersed between product chapters:
  - "How to choose the right profile" — buyer guide with decision scales (botanical vs CDT, sweet vs gassy, modern vs classic) before Strain Profiles
  - "Why Live Resin costs more" — dark-themed value proposition explaining fresh-frozen extraction, full-spectrum, and yield economics
  - "Build your vape formulation" — industrial-themed four-step pipeline (Base → Liquidiser → Diluent → Hardware) before Hardware chapter
  - "Not sure where to start?" — purple-themed gateway spread positioning Sample Packs as lowest-risk evaluation tool
- **Brand personality treatments**: Eybna (light grey minimal), True Terpenes (dark/black background), Terp Belt Farms (warm beige), Terpenes UK (green), Hardware (industrial grey), Samples (purple).
- **No two consecutive spreads are identical** — the template now alternates between product grids, editorial spreads, brand openers, comparison tables, and sell-spreads.
- **Page count**: V14=48 → V15=52 pages (4 editorial spreads added).
- **Engine unchanged** throughout all versions. All 337 products render exactly once.
- **Feature-complete**. Declared RC1. Further changes should be driven by visual inspection of the printed PDF.

## 2.0.0-editorial-foundation — 2026-07-02

### Architectural rewrite: Data-first pipeline

**Problem**: The old builder grouped products by Shopify `collection` field, creating 22 sections with 684 total references for 337 unique products (products appeared in multiple collections). The template used `rendered_ids` hacks, `reserved_ids` filters, and a JavaScript page-number calculator just to work around duplicate rendering.

**Solution**: Moved editorial decisions out of the template and into a data-first categorization pipeline.

#### New: Canonical section manifest (`terpvault/generate/sections.py`)
- Defines 17 canonical sections across 6 chapters as a single source of truth
- Sections are ordered by editorial intent, not Shopify collection order
- Empty sections are automatically skipped during build

#### New: Rule-based categorizer (`terpvault/generate/categorizer.py`)
- Classifies every product into exactly one canonical section
- Rules are ordered by specificity: sample → hardware → liquidisers → diluents → isolates → oil soluble → flavours → infusion → live resin → clearance → duty free → prestige → brand → new releases (catchment)
- No product falls through to "unknown" — unknown products go to New Releases

#### Rewritten: CatalogBuilder (`terpvault/generate/builder.py`)
- `build()` iterates canonical sections in order, buckets products via categorizer
- Each product appears in exactly one section (verified by integrity check)
- Empty sections are omitted from output

#### Rewritten: Integrity checker (`terpvault/generate/integrity.py`)
- New `_check_coverage()`: fails build if any product appears in multiple sections or is missing from all sections
- Existing structural, statistical, serialization, and publishing checks preserved

#### Rewritten: PDF template (`terpvault/generate/templates/catalog_pdf.html`)
- Removed: `rendered_ids` namespace hack, `reserved_ids` pre-load, JS page-number calculator, `render_brand_sections` and `render_section` macros, recursive Jinja2 logic
- Added: clean chapter→section→product iteration based on `section_config` dictionary
- Template now describes layout only — no business logic

### Verification
- 337 products, 337 unique section references, 0 duplicates
- 0 integrity errors, 0 integrity warnings
- 132/132 tests passing
- 15 populated sections across 6 chapters (2 catchment sections empty — expected)

### Roadmap declaration
- Data model frozen
- Categorization frozen
- Integrity checks frozen
- Rendering pipeline frozen
- Future changes: typography, spacing, grids, visual hierarchy, editorial content, photography, print quality only
