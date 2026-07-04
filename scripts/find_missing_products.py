"""
Find the 3 legacy-only images and map them to product names.
Strategy: the legacy PDF uses X{N}.png naming where N increments per image.
We need to map image names to product names. Since pypdf assigns sequential names
in document order, we can correlate image insertion order with product iteration order.
"""
import json
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
legacy = prod / "catalogue.pdf"
new_print = prod / "catalogue-print.pdf"
catalog_json = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json"

# Load current products
with open(catalog_json, encoding="utf-8") as f:
    data = json.load(f)
current_products = data["products"]

# Get all unique image names from each PDF
r_legacy = PdfReader(str(legacy))
legacy_img_names = set()
for pg in r_legacy.pages:
    for img in pg.images:
        legacy_img_names.add(img.name)

r_new = PdfReader(str(new_print))
new_img_names = set()
for pg in r_new.pages:
    for img in pg.images:
        new_img_names.add(img.name)

only_in_legacy = legacy_img_names - new_img_names
only_in_new = new_img_names - legacy_img_names

print(f"Images only in legacy: {len(only_in_legacy)}")
print(f"Images only in new:    {len(only_in_new)}")
print()

# The legacy has 338 images, current has 335. But the naming is sequential and 
# non-overlapping (different renderer runs assign different X{N} numbers).
# The real difference is in the COUNT (338 vs 335 = 3 images).
# Let's find which 3 product images are in legacy but not in new by comparing
# the page-by-page image count distribution.

# Build legacy image-position map: pypdf assigns X1, X2, X3... in order of encounter
# We can map the Nth image to the Nth unique product in document order.
# The cover image is X52.png (the first image in the PDF). After that, product images
# appear in document order.

# Let's read all products from legacy by their appearance order
print("=== Legacy image order ===")
r_legacy = PdfReader(str(legacy))
img_order = []
for pg in r_legacy.pages:
    for img in pg.images:
        img_order.append(img.name)

# The first image after the cover (X52.png) should correspond to the first product
# Let's check what X52 is
print(f"  First image: {img_order[0]} (cover logo)")
print(f"  Images 2-338: product images in document order")

# Now match with current products - but since the renderers are different,
# we can't map directly. Instead, let's check which products are in the 
# current catalog JSON that have images, vs the legacy PDF's 338 total.

# Number of products with images currently
products_with_images = sum(1 for p in current_products.values() if p.get("images"))
products_without_images = sum(1 for p in current_products.values() if not p.get("images"))
print(f"\nCurrent products with images:    {products_with_images}")
print(f"Current products without images: {products_without_images}")
print(f"Current unique products total:   {len(current_products)}")

# Legacy: 338 images = 1 cover + 337 product images = 337 products with images
# Current: 335 images = 1 cover + 334 product images = 334 products with images
# Difference: 3 products that had images in legacy but don't exist in current

print(f"\nExpected legacy products with images: 337 (338 - 1 cover)")
print(f"Current products with images:         {products_with_images}")
print(f"Difference:                           {337 - products_with_images} products")

# Find which current products have no image
print(f"\nProducts currently without images:")
for pid, p in sorted(current_products.items()):
    if not p.get("images"):
        print(f"  {p['name']:40s} (id: {pid})")

# Also find which sections have fewer products than legacy
print(f"\n=== Section-level comparison ===")
r_new = PdfReader(str(new_print))
new_counts = [len(list(p.images)) for p in r_new.pages]
legacy_counts_actual = [len(list(p.images)) for p in r_legacy.pages]

# Show pages where new has fewer images than legacy
for pg in range(max(len(legacy_counts_actual), len(new_counts))):
    lc = legacy_counts_actual[pg] if pg < len(legacy_counts_actual) else 0
    nc = new_counts[pg] if pg < len(new_counts) else 0
    if lc > nc:
        missing = lc - nc
        print(f"  Page {pg+1}: legacy has {lc} images, new has {nc} ({missing} fewer)")
