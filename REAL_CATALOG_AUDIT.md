# Real Catalog Audit

## Summary

- Supplier: Terpenes UK (https://terpenes-uk.co.uk)
- Snapshot ID: 818c19f8
- Products imported (raw): 684
- Unique products (catalog): 337
- Variants: 1,815
- Images: 348
- Brands: 13
- Sections: 22
- Integrity: 0 errors, 0 warnings → **Ready to publish**

---

## 1. Why 684 imported → 337 catalog products

**Cause: Multi-collection membership (benign).**

Shopify allows a single product to appear in multiple collections.
The importer crawls every collection, so the same product is fetched
once per collection it belongs to.

Example:

```
Product "Kush Cake"
  → Clearance collection
  → Eybna collection
  → Eybna Palate & Live Line collection
  → Home page collection
  → 4 raw entries, 1 unique product
```

Of the 230 duplicated external_ids:

- **4x each**: products in 4 collections (Home page + New Releases + brand collection + sub-line)
- **3x each**: products in 3 collections (Bundle + brand + sub-line, or Clearance + brand + sub-line)
- **2x each**: products in 2 collections

**No data loss.** All products with matching external_ids carry identical
name, price, and variant data. The dedup is correct.

**Action:** None required. The CatalogDocument correctly stores one canonical
product per external_id, referenced from multiple sections.

---

## 2. Variant/Image count discrepancy (FIXED)

**Root cause:** `CatalogBuilder` was counting variants/images from the raw
(684-item) input list, but `product_count` used the deduplicated (337-item)
map. Stats disagreed with reality.

**Fix:** Count variants and images from the final `product_map.values()`
instead of the raw products list.

**Result:** Integrity checker now reports 0 errors, 0 warnings.
- actual variants: 1,815
- actual images: 348
- stats match these values.

---

## 3. Section hierarchy vs real website

The generated sections match the Shopify collections:

| Section | Products |
|---------|----------|
| Home page | 178 |
| Strain Profiles | 64 |
| Terpenes UK | 64 |
| True Terpenes | 47 |
| Eybna | 46 |
| New Releases | 42 |
| Concentrated Flavours | 36 |
| Terpene Isolates | 36 |
| Oil Soluble Flavours | 30 |
| Terpene Belt Farms | 29 |
| Eybna Palate & Live Line | 25 |
| Live Resin | 15 |
| Bundle | 14 |
| Eybna Live Plus+ Line | 14 |
| Duty Free Terpenes | 7 |
| Extract Liquidisers | 7 |
| Eybna Enhancer Line | 7 |
| Vape Hardware | 7 |
| NEU Bag Infusion Packs | 5 |
| Prestige | 5 |
| Clearance | 3 |
| Diluents | 3 |

The "Home page" section (178 products) is a Shopify artifact — products
visible on the home page aren't a meaningful editorial grouping. This
could be filtered or merged in a future pass.

---

## 4. Brand analysis

13 brand values from Shopify's `vendor` field. Some are not commercial
brands but editorial labels:

| Vendor | Classification |
|--------|---------------|
| Terpenes UK | ✅ Brand |
| Terpenes UK - Strain Profiles | ⚠️ Editorial sub-label |
| Terpenes UK - Prestige | ⚠️ Editorial sub-label |
| Terpenes UK - Flavour Concentrates | ⚠️ Editorial sub-label |
| Terpenes UK - Isolates | ⚠️ Editorial sub-label |
| Terpenes UK - Oil Soluble Flavours | ⚠️ Editorial sub-label |
| Terpenes UK - Diluents | ⚠️ Editorial sub-label |
| terpenes uk - Liquidisers | ⚠️ Editorial sub-label |
| True Terpenes - Strain Profiles | ⚠️ Editorial sub-label |
| True Terpenes - Live Resin | ⚠️ Editorial sub-label |
| Eybna | ✅ Brand |
| DFT | ✅ Brand |
| Hardware | ✅ Brand |

The vendor field is being used faithfully. Editorial normalization
(e.g., grouping all "Terpenes UK - *" under "Terpenes UK") is a
future publishing concern, not an importer issue.

---

## 5. Discrepancy classification

| Issue | Type | Severity | Status |
|-------|------|----------|--------|
| 684→337 dedup | Multi-collection membership | ✅ Not a bug | Documented |
| Variant count mismatch | Builder counting from wrong list | ✅ Fixed | Resolved |
| Image count mismatch | Same as above | ✅ Fixed | Resolved |
| "Home page" section | Shopify artifact | ⚠️ Editorial | Future |
| Brand sub-labels | Shopify vendor field granularity | ⚠️ Editorial | Future |

---

## Confidence score

**95%** — The generated catalog faithfully represents the supplier.
The remaining 5% is editorial refinement (brand grouping, section filtering)
that doesn't affect correctness.

```
REAL_CATALOG_AUDIT
```
