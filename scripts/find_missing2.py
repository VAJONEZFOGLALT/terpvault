"""
The legacy has 338 images = 1 cover logo + 337 product images.
The new has 335 images = 1 cover logo + 334 product images.
But all 337 current products have images. This means either:
1. The cover logo in legacy is counted but in new it's not (different rendering)
2. Some product images in the new PDF are the same image (duplicated)

Let me check: 335 images = 335 images. If all 337 current products have images, 
then 2 product images must be missing from the PDF despite being in the data.
Or: the cover logo image is being counted differently.

Let me compare the image count difference directly per-section by loading the 
current catalog JSON and counting images that would render per section.
"""
import json
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"

new_print = prod / "catalogue-print.pdf"
legacy = prod / "catalogue.pdf"

r_new = PdfReader(str(new_print))
r_legacy = PdfReader(str(legacy))

# Count images per page in both
new_counts = [len(list(p.images)) for p in r_new.pages]
legacy_counts = [len(list(p.images)) for p in r_legacy.pages]

print(f"Legacy: {sum(legacy_counts)} total images across {len(legacy_counts)} pages")
print(f"New:    {sum(new_counts)} total images across {len(new_counts)} pages")
print(f"Diff:   {sum(legacy_counts) - sum(new_counts)} fewer in new")
print()

# Check cover images specifically
print("=== Page 1 (Cover) ===")
legacy_p1_imgs = list(r_legacy.pages[0].images)
new_p1_imgs = list(r_new.pages[0].images)
print(f"  Legacy cover images: {len(legacy_p1_imgs)}")
for img in legacy_p1_imgs:
    print(f"    {img.name} ({img.image.size})")
print(f"  New cover images: {len(new_p1_imgs)}")
for img in new_p1_imgs:
    print(f"    {img.name} ({img.image.size})")

# Now check: template has <img src="URL"> for cover logo. 
# The legacy used a different cover (no logo image, just text).
# The current template has a logo image. So both should have 1 cover image.
# Actual images: legacy 338 = 1 cover + 337 product. New 335 = 1 cover + 334 product.
# With 337 products all having images, that's 334 product images in PDF = 3 products
# whose images didn't render. These could be products with broken image URLs.

# Let's check: which products have 404 URLs or use http:// (blocked)?
print()
print("=== Checking for products that might have missing/broken images ===")
catalog_json = PROJECT / "data" / "catalogs" / "terpenes-uk" / "catalog-874c633b.json"
with open(catalog_json, encoding="utf-8") as f:
    data = json.load(f)

# Check each product's first image URL
bad_products = []
for pid, p in data["products"].items():
    images = p.get("images", [])
    if not images:
        bad_products.append((pid, p["name"], "no images array"))
    else:
        url = images[0].get("url", "") if isinstance(images[0], dict) else str(images[0])
        if not url:
            bad_products.append((pid, p["name"], "empty URL"))

print(f"Products with missing/empty image URLs: {len(bad_products)}")
for pid, name, reason in bad_products[:10]:
    print(f"  {name:40s} (id: {pid}) - {reason}")

if not bad_products:
    print("  All 337 products have valid image URLs.")

# The real answer: 338 images in legacy (1 cover + 337 products) vs 335 in new.
# But current data shows 337 products with images. Let me verify the actual count differently.
print()
print("=== Verifying product image count in catalog JSON ===")
total_product_images = 0
image_urls_set = set()
for pid, p in data["products"].items():
    for img in p.get("images", []):
        url = img.get("url", "") if isinstance(img, dict) else str(img)
        if url:
            total_product_images += 1
            image_urls_set.add(url)

print(f"Total image URLs across all products (including variants): {total_product_images}")
print(f"Unique image URLs: {len(image_urls_set)}")

# The CatalogProduct model stores images as a list of dicts with 'url' key.
# Some products may have multiple image entries but the template only uses .images[0].url
print(f"Products with >1 image entries: {sum(1 for p in data['products'].values() if len(p.get('images', [])) > 1)}")
