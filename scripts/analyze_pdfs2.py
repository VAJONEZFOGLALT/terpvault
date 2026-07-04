"""
Deeper analysis: compare image-per-page counts and look at what's on each page.
The legacy PDF had 338 images, current has 646. That's nearly double.
337 products with 1 image each = 337 images expected. 
Cover might have 1 image = 338 for legacy.
646 for current means ~309 extra images — likely page backgrounds, chapter backgrounds, etc.
"""
import json, sys
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
legacy_path = PROJECT / "prod" / "terpenes-uk" / "catalogue.pdf"
current_path = PROJECT / "prod" / "terpenes-uk" / "catalogue-print.pdf"

if not legacy_path.exists():
    legacy_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-44.pdf"
if not current_path.exists():
    current_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-337.pdf"

print("=== Per-page image count comparison ===")
print()

for label, path in [("Legacy (44p)", legacy_path), ("Current (73p)", current_path)]:
    reader = PdfReader(str(path))
    print(f"{label}:")
    counts = []
    for pn, page in enumerate(reader.pages):
        n = len(list(page.images))
        counts.append(n)
    
    # Show every page's image count
    print(f"  Page-by-page: {', '.join(str(c) for c in counts)}")
    
    # Show image name summary per page for first 10 pages
    print(f"  First 10 pages image details:")
    for pn in range(min(10, len(reader.pages))):
        page = reader.pages[pn]
        imgs = list(page.images)
        names = [img.name for img in imgs]
        print(f"    Page {pn+1}: {len(imgs)} images: {names}")
    print()

# Also check: are there any non-product images in the current PDF?
# Chapter opener backgrounds use CSS gradients (not images), but text blocks etc.
# The 646 vs 338 is suspicious - check if duplicate images exist.

print("=== Duplicate image detection ===")
for label, path in [("Legacy (44p)", legacy_path), ("Current (73p)", current_path)]:
    reader = PdfReader(str(path))
    all_names = []
    for page in reader.pages:
        for img in page.images:
            all_names.append(img.name)
    unique = len(set(all_names))
    total = len(all_names)
    print(f"{label}: {total} total, {unique} unique ({total - unique} duplicates)")
