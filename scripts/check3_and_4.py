"""
Check 3: Verify print & digital are identical except image compression.
- Same page count? 
- Compare page-by-page image names to see if they match
- Check if SHA256 of page content matches (they shouldn't for compressed images)
- Check if the text content is identical (extract text per page)

Check 4: Compare new print against legacy 44-page catalogue.
- Identify missing/extra products
- Compare page-level image counts
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"
data = PROJECT / "data" / "catalogs" / "terpenes-uk"

new_print = prod / "catalogue-print.pdf"
new_digital = prod / "catalogue-digital.pdf"
legacy = prod / "catalogue.pdf"

print("=== Check 3: Print vs Digital Comparison ===")
print()

r_print = PdfReader(str(new_print))
r_digital = PdfReader(str(new_digital))

print(f"  Print pages:   {len(r_print.pages)}")
print(f"  Digital pages: {len(r_digital.pages)}")
print(f"  Same page count? {'YES' if len(r_print.pages) == len(r_digital.pages) else 'NO - MISMATCH!'}")

# Compare image names per page
page_mismatches = 0
for pn in range(min(len(r_print.pages), len(r_digital.pages))):
    p_print = list(r_print.pages[pn].images)
    p_digital = list(r_digital.pages[pn].images)
    p_names = sorted([img.name for img in p_print])
    d_names = sorted([img.name for img in p_digital])
    if p_names != d_names:
        page_mismatches += 1
        if page_mismatches <= 3:
            print(f"  Page {pn+1} image mismatch:")
            print(f"    Print:   {p_names}")
            print(f"    Digital: {d_names}")

print(f"  Pages with different images: {page_mismatches} / {len(r_print.pages)}")

# Check sizes
print(f"  Print size:   {new_print.stat().st_size/1024/1024:.0f} MB")
print(f"  Digital size: {new_digital.stat().st_size/1024/1024:.0f} MB")
print(f"  Compression ratio: {new_print.stat().st_size / new_digital.stat().st_size:.0f}x")

# Check total image counts
print_total = sum(len(list(p.images)) for p in r_print.pages)
digital_total = sum(len(list(p.images)) for p in r_digital.pages)
print_print_unique = len(set(img.name for p in r_print.pages for img in p.images))
print_digital_unique = len(set(img.name for p in r_digital.pages for img in p.images))
print(f"  Print images:   {print_total} total, {print_print_unique} unique")
print(f"  Digital images: {digital_total} total, {print_digital_unique} unique")

print()
print("=== Check 4: New Print vs Legacy Comparison ===")
print()

r_legacy = PdfReader(str(legacy))

print(f"  Legacy pages:  {len(r_legacy.pages)}")
print(f"  New print pages: {len(r_print.pages)}")
print(f"  Difference:    {len(r_print.pages) - len(r_legacy.pages)} pages ({'shorter' if len(r_print.pages) < len(r_legacy.pages) else 'longer'})")
print()

# Compare image counts per page, side by side
legacy_counts = [len(list(p.images)) for p in r_legacy.pages]
new_counts = [len(list(p.images)) for p in r_print.pages]

print("Page-by-page image count comparison:")
print(f"{'Pg':>4s}  {'Legacy':>8s}  {'New':>8s}  {'Diff':>8s}")
print("-" * 35)
page_diffs = []
for i in range(max(len(legacy_counts), len(new_counts))):
    lc = legacy_counts[i] if i < len(legacy_counts) else 0
    nc = new_counts[i] if i < len(new_counts) else 0
    diff = nc - lc
    page_diffs.append((i+1, lc, nc, diff))
    if diff != 0:
        print(f"  {i+1:2d}  {lc:8d}  {nc:8d}  {diff:+8d}")

print()
# Summarize differences
diff_pages = [(p, l, n) for p, l, n, d in page_diffs if d != 0]
zero_pages = [(p, l, n) for p, l, n, d in page_diffs if d == 0]
print(f"  Pages with same image count: {len(zero_pages)}")
print(f"  Pages with different image count: {len(diff_pages)}")
print(f"  Total image diff: {sum(n - l for (p, l, n) in diff_pages)}")
print()

# Identify which section boundaries differ
# Compare the section patterns: pages with 0-1 images are section/chapter breaks
print("Pages with 0-1 images (section/chapter/cover):")
for label, counts, pgnums in [
    ("Legacy", legacy_counts, range(1, len(legacy_counts)+1)),
    ("New", new_counts, range(1, len(new_counts)+1)),
]:
    zero_or_one = [pn for pn, c in zip(pgnums, counts) if c <= 1]
    print(f"  {label}: pages {', '.join(str(p) for p in zero_or_one)}")
