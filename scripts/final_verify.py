"""
Final verification:
1. catalogue.pdf and catalogue-print.pdf: same pages, layout, ordering
2. No file size/compression artifacts other than intended
3. Website serves correct files
"""
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
prod = PROJECT / "prod" / "terpenes-uk"

digital = prod / "catalogue.pdf"
print_master = prod / "catalogue-print.pdf"

print("=== Final Verification ===")
print()

r_d = PdfReader(str(digital))
r_p = PdfReader(str(print_master))

print(f"catalogue.pdf:      {len(r_d.pages)} pages, {digital.stat().st_size/1024/1024:.0f} MB")
print(f"catalogue-print.pdf: {len(r_p.pages)} pages, {print_master.stat().st_size/1024/1024:.0f} MB")
print()

# Same page count
pages_match = len(r_d.pages) == len(r_p.pages)
print(f"Same page count?           {'YES' if pages_match else 'NO'}")

# Same image names per page (just extension)
img_mismatches = 0
for pn in range(min(len(r_d.pages), len(r_p.pages))):
    d_imgs = sorted([img.name for img in r_d.pages[pn].images])
    p_imgs = sorted([img.name for img in r_p.pages[pn].images])
    # Strip extension
    d_base = set(n.rsplit('.', 1)[0] for n in d_imgs)
    p_base = set(n.rsplit('.', 1)[0] for n in p_imgs)
    if d_base != p_base:
        img_mismatches += 1
        if img_mismatches <= 3:
            print(f"  Page {pn+1} image mismatch:")

print(f"Pages with matching images? {'YES' if img_mismatches == 0 else f'NO ({img_mismatches} mismatches)'}")
print()

# Verify no duplicates in either
for label, reader in [("catalogue.pdf", r_d), ("catalogue-print.pdf", r_p)]:
    all_names = []
    for pg in reader.pages:
        for img in pg.images:
            all_names.append(img.name)
    print(f"{label}: {len(set(all_names))} unique images, {len(all_names)-len(set(all_names))} duplicates")

# Verify all files in prod/
print()
print("=== Prod directory state ===")
for f in sorted(prod.glob("*")):
    if f.is_file() and f.suffix != ".py":
        mb = f.stat().st_size / (1024*1024)
        print(f"  {f.name:30s} {mb:7.1f} MB" if f.suffix == ".pdf" else f"  {f.name:30s} {f.stat().st_size/1024:7.0f} KB")

# Verify download links reference correct files
print()
print("=== Website references ===")
downloads_html = PROJECT / "terpvault" / "web" / "templates" / "downloads.html"
supplier_html = PROJECT / "terpvault" / "web" / "templates" / "supplier.html"
for label, path in [("downloads.html", downloads_html), ("supplier.html", supplier_html)]:
    text = path.read_text(encoding="utf-8")
    refs = []
    if "catalogue.pdf" in text:
        refs.append("catalogue.pdf")
    if "catalogue-print.pdf" in text:
        refs.append("catalogue-print.pdf")
    if "catalogue-digital.pdf" in text:
        refs.append("catalogue-digital.pdf (STALE!)")
    print(f"  {label}: references {', '.join(refs)}")
