"""
Comprehensive measurement of all four PDFs:
- Legacy:  catalogue.pdf (44-page) from prod/
- Old:    catalog-337.pdf (73-page, before fix) from data/catalogs/
- New Print:  catalogue-print.pdf (after fix) from prod/
- New Digital: catalogue-digital.pdf (after fix) from prod/
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
data = PROJECT / "data" / "catalogs" / "terpenes-uk"

pdfs = {
    "Legacy (44p)":     prod / "catalogue.pdf",
    "Old (73p, pre-fix)": data / "catalog-337.pdf",
    "New Print":        prod / "catalogue-print.pdf",
    "New Digital":      prod / "catalogue-digital.pdf",
}

for label, path in pdfs.items():
    if not path.exists():
        print(f"{label}: NOT FOUND at {path}")
        continue
    
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    
    # Count images
    all_imgs = []
    for pg in reader.pages:
        for img in pg.images:
            all_imgs.append(img.name)
    
    total_imgs = len(all_imgs)
    unique_imgs = len(set(all_imgs))
    dupes = total_imgs - unique_imgs
    
    # Count images per page
    imgs_per_page = []
    for pg in reader.pages:
        imgs_per_page.append(len(list(pg.images)))
    
    max_pp = max(imgs_per_page) if imgs_per_page else 0
    size_mb = path.stat().st_size / (1024 * 1024)
    
    print(f"=== {label} ===")
    print(f"  File size:      {size_mb:.0f} MB")
    print(f"  Pages:          {pages}")
    print(f"  Total images:   {total_imgs}")
    print(f"  Unique images:  {unique_imgs}")
    print(f"  Duplicate imgs: {dupes}")
    print(f"  Max images/page:{max_pp}")
    print(f"  Images per page: {', '.join(str(c) for c in imgs_per_page[:15])}{'...' if len(imgs_per_page) > 15 else ''}")
    print()

# Legacy images per page full (for reference)
print("=== Legacy full page image breakdown ===")
reader = PdfReader(str(pdfs["Legacy (44p)"]))
for pn, page in enumerate(reader.pages):
    n = len(list(page.images))
    print(f"  Page {pn+1}: {n} images")
