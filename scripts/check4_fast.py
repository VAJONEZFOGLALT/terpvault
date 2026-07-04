"""
Fast check: identify the 3 missing images by comparing image name sets.
"""
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
new_print = prod / "catalogue-print.pdf"
legacy = prod / "catalogue.pdf"

from pypdf import PdfReader

# Legacy - just get unique names
r = PdfReader(str(legacy))
legacy_names = set()
for pg in r.pages:
    for img in pg.images:
        legacy_names.add(img.name)
del r

# New - just get unique names
r = PdfReader(str(new_print))
new_names = set()
for pg in r.pages:
    for img in pg.images:
        new_names.add(img.name)
del r

only_legacy = legacy_names - new_names
only_new = new_names - legacy_names

print("Legacy unique images:", len(legacy_names))
print("New print unique images:", len(new_names))
print("Only in legacy:", len(only_legacy))
print("Only in new:", len(only_new))
print()
if only_legacy:
    print("Legacy-only images:")
    for n in sorted(only_legacy):
        print(f"  {n}")
if only_new:
    print("New-only images:")
    for n in sorted(only_new):
        print(f"  {n}")
