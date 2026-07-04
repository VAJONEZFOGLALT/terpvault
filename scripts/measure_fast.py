"""
Fast measurement - use pypdf with no image extraction, just metadata.
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
data = PROJECT / "data" / "catalogs" / "terpenes-uk"

# New files are in prod/ (refresh_catalog copied them)
# Legacy catalogue.pdf
legacy_path = prod / "catalogue.pdf"
# Old pre-fix (might have been overwritten by the refresh)
# Check data dir for the old one
old_path = data / "catalog-337.pdf"  # this one was overwritten
# Actually refresh creates a NEW snapshot, so old was at data/catalogs too but got overwritten
# Let's check prod for the newly generated ones
new_print = prod / "catalogue-print.pdf"
new_digital = prod / "catalogue-digital.pdf"

paths = {
    "Legacy (44p)": legacy_path,
    "New Print": new_print,
    "New Digital": new_digital,
}

for label, path in paths.items():
    if not path.exists():
        print(f"{label}: NOT FOUND at {path}")
        continue
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    size_mb = path.stat().st_size / (1024 * 1024)
    
    # Quick image count via pypdf
    total = 0
    names = []
    for pg in reader.pages:
        for img in pg.images:
            total += 1
            names.append(img.name)
    
    unique = len(set(names))
    dupes = total - unique
    
    print(f"=== {label} ===")
    print(f"  Size:     {size_mb:.0f} MB")
    print(f"  Pages:    {pages}")
    print(f"  Images:   {total}")
    print(f"  Unique:   {unique}")
    print(f"  Dupes:    {dupes}")
    print()
