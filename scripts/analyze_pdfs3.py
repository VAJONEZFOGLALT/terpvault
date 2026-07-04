"""
Investigate image duplication in the current PDF.
The legacy PDF has 338 unique images (337 products + 1 cover).
The current has 646 total but only 338 unique = 308 duplicates.
This means some images are embedded 2+ times in the PDF.

Let's find which images are duplicated and on which pages.
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
current_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-337.pdf"
if not current_path.exists():
    current_path = PROJECT / "prod" / "terpenes-uk" / "catalogue-print.pdf"

reader = PdfReader(str(current_path))

# Track which images appear on which pages
image_pages = {}  # name -> [page_numbers]

for pn, page in enumerate(reader.pages):
    for img in page.images:
        name = img.name
        if name not in image_pages:
            image_pages[name] = []
        image_pages[name].append(pn + 1)

# Find duplicates: images appearing on >1 page
duplicates = {name: pages for name, pages in image_pages.items() if len(pages) > 1}
singletons = {name: pages for name, pages in image_pages.items() if len(pages) == 1}

print("=== Image Duplication Analysis (Current 73-page PDF) ===")
print(f"Total unique images: {len(image_pages)}")
print(f"Images on 1 page only: {len(singletons)}")
print(f"Images on 2+ pages: {len(duplicates)}")
print()

# Show duplication frequency
freq_dist = {}
for name, pages in duplicates.items():
    n = len(pages)
    freq_dist[n] = freq_dist.get(n, 0) + 1

print("Duplication frequency:")
for n in sorted(freq_dist.keys()):
    print(f"  {n} pages: {freq_dist[n]} images")

print()
print("First 20 duplicated images and their pages:")
for i, (name, pages) in enumerate(sorted(duplicates.items())[:20]):
    print(f"  {name}: pages {pages}")

print()
print("=== Compare with Legacy 44-page PDF ===")
legacy_path = PROJECT / "prod" / "terpenes-uk" / "catalogue.pdf"
if not legacy_path.exists():
    legacy_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-44.pdf"

reader2 = PdfReader(str(legacy_path))
image_pages2 = {}
for pn, page in enumerate(reader2.pages):
    for img in page.images:
        name2 = img.name
        if name2 not in image_pages2:
            image_pages2[name2] = []
        image_pages2[name2].append(pn + 1)

dups2 = {name: pages for name, pages in image_pages2.items() if len(pages) > 1}
print(f"Total unique images: {len(image_pages2)}")
print(f"Images on 2+ pages: {len(dups2)}")
if dups2:
    for name, pages in list(dups2.items())[:10]:
        print(f"  {name}: pages {pages}")
else:
    print("  No duplicate images - each image appears exactly once")
