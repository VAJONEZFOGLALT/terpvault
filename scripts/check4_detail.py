"""
Check 4 detailed: identify exactly which 3 images are missing in the new print vs legacy.
Also compare product lists between the two.
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
new_print = prod / "catalogue-print.pdf"
legacy = prod / "catalogue.pdf"

r_legacy = PdfReader(str(legacy))
r_new = PdfReader(str(new_print))

# Get all unique image names from each PDF
legacy_imgs = set()
for p in r_legacy.pages:
    for img in p.images:
        legacy_imgs.add(img.name)

new_imgs = set()
for p in r_new.pages:
    for img in p.images:
        new_imgs.add(img.name)

only_legacy = legacy_imgs - new_imgs
only_new = new_imgs - legacy_imgs

print("=== Check 4: Image-level difference ===")
print(f"  Legacy unique images: {len(legacy_imgs)}")
print(f"  New print unique images: {len(new_imgs)}")
print(f"  Images only in legacy: {len(only_legacy)}")
print(f"  Images only in new:    {len(only_new)}")
print()

if only_legacy:
    print(f"  Images in legacy but NOT in new ({len(only_legacy)}):")
    for name in sorted(only_legacy):
        # Find which page it was on
        for pn, p in enumerate(r_legacy.pages):
            for img in p.images:
                if img.name == name:
                    print(f"    {name}: page {pn+1}")
                    break
if only_new:
    print(f"  Images in new but NOT in legacy ({len(only_new)}):")
    for name in sorted(only_new):
        for pn, p in enumerate(r_new.pages):
            for img in p.images:
                if img.name == name:
                    print(f"    {name}: page {pn+1}")
                    break

# Also check the page images don't have empty names or the legacy's X52.png is the cover logo
print()
# Check for legacy cover logo
legacy_cover_img = None
for img in r_legacy.pages[0].images:
    legacy_cover_img = img.name
    print(f"  Legacy cover (page 1) image: {img.name} ({img.image.size[0]}x{img.image.size[1]})")

new_cover_img = None
for img in r_new.pages[0].images:
    new_cover_img = img.name
    print(f"  New cover (page 1) image: {img.name} ({img.image.size[0]}x{img.image.size[1]})")

# The legacy has a different cover logo URL. Let's check if the new one is fetching a different image.
print()
print("  The 3-image difference is likely because the legacy was generated against")
print("  an older snapshot with 340 products (3 more than the current 337), or because")
print("  the cover logo image in the template vs the legacy are different.")
