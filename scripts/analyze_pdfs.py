"""
Analyze images in legacy (44-page) vs current (73-page) PDFs.
Extract sample images, measure dimensions, and compare container sizes.
"""
import json, sys
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO

PROJECT = Path(__file__).resolve().parent.parent

legacy_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-44.pdf"
current_path = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-337.pdf"

if not legacy_path.exists():
    # Try prod/
    legacy_path = PROJECT / "prod" / "terpenes-uk" / "catalogue.pdf"
if not current_path.exists():
    current_path = PROJECT / "prod" / "terpenes-uk" / "catalogue-print.pdf"

print("=== PDF Image Analysis ===")
print()

for label, path in [("Legacy (44-page)", legacy_path), ("Current (73-page)", current_path)]:
    if not path.exists():
        print(f"{label}: NOT FOUND at {path}")
        continue
    reader = PdfReader(str(path))
    print(f"{label}: {len(reader.pages)} pages")
    
    total_images = 0
    img_sizes = []
    sample_imgs = 0
    
    for page_num, page in enumerate(reader.pages):
        images = list(page.images)
        total_images += len(images)
        for img in images:
            w, h = img.image.size
            img_sizes.append((w, h))
            if sample_imgs < 10:
                print(f"  Page {page_num+1}: img '{img.name}' = {w}x{h} px")
                sample_imgs += 1
    
    if img_sizes:
        widths = [s[0] for s in img_sizes]
        heights = [s[1] for s in img_sizes]
        print(f"  Total images: {total_images}")
        print(f"  Width range:  {min(widths)}-{max(widths)} px")
        print(f"  Height range: {min(heights)}-{max(heights)} px")
        print(f"  Avg width:    {sum(widths)//len(widths)} px")
        print(f"  Avg height:   {sum(heights)//len(heights)} px")
    
    # Check page size
    page = reader.pages[0]
    mb = page.mediabox
    print(f"  Page size: {float(mb.width):.0f} x {float(mb.height):.0f} pts ({float(mb.width)/72*2.54:.1f} x {float(mb.height)/72*2.54:.1f} cm)")
    print()

# Now let's also check how the original builder grouped sections
print()
print("=== Legacy PDF page-by-page analysis ===")
print()

# Count number of product images per page in legacy vs current
for label, path in [("Legacy (44-page)", legacy_path), ("Current (73-page)", current_path)]:
    if not path.exists():
        continue
    reader = PdfReader(str(path))
    print(f"{label} - images per page:")
    img_counts = []
    for page_num, page in enumerate(reader.pages):
        n = len(list(page.images))
        img_counts.append(n)
    # Show distribution
    print(f"  Pages with 0 images: {img_counts.count(0)}")
    print(f"  Pages with 1-3 images: {sum(1 for c in img_counts if 1 <= c <= 3)}")
    print(f"  Pages with 4-6 images: {sum(1 for c in img_counts if 4 <= c <= 6)}")
    print(f"  Pages with 7-9 images: {sum(1 for c in img_counts if 7 <= c <= 9)}")
    print(f"  Pages with 10+ images: {sum(1 for c in img_counts if c >= 10)}")
    print(f"  Max images on a page: {max(img_counts)}")
    print()
