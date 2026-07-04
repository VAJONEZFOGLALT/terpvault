"""
Generate Digital and Print Master PDFs.
Digital: compressed for screens/sharing.
Print Master: full resolution for commercial printing.

Usage:
    python scripts/generate_pdfs.py [--quality 60]

Both editions are derived from the SAME source PDF (the Print Master).
The layout is pixel-identical between editions; only image compression differs.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pypdf", "-q"])
    from pypdf import PdfReader, PdfWriter

SUPPLIER = "terpenes-uk"
PROD = Path(__file__).resolve().parent.parent / "prod" / SUPPLIER
PRINT_MASTER = PROD / "catalogue-print.pdf"
DIGITAL = PROD / "catalogue.pdf"


def compress_digital(quality: int = 60):
    if not PRINT_MASTER.exists():
        print(f"Print Master not found: {PRINT_MASTER}")
        print("Run refresh_catalog.py first to generate a Print Master.")
        return

    src_mb = PRINT_MASTER.stat().st_size / (1024 * 1024)
    reader = PdfReader(str(PRINT_MASTER))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        writer.add_page(page)

    for page in writer.pages:
        for img in page.images:
            from PIL import Image
            pil_img = img.image
            if pil_img.mode == "RGBA":
                white = Image.new("RGB", pil_img.size, (255, 255, 255))
                white.paste(pil_img, mask=pil_img.split()[3])
                pil_img = white
            img.replace(pil_img, quality=quality)

    writer.write(str(DIGITAL))
    dig_mb = DIGITAL.stat().st_size / (1024 * 1024)

    pages = len(reader.pages)
    print(f"Print Master:  {PRINT_MASTER.name}  ({pages} pages, {src_mb:.0f} MB)")
    print(f"Digital:       {DIGITAL.name}             ({pages} pages, {dig_mb:.0f} MB)")
    print(f"Compression:   {src_mb:.0f} MB -> {dig_mb:.0f} MB  (saved {src_mb - dig_mb:.0f} MB, quality={quality})")


def main():
    parser = argparse.ArgumentParser(description="Generate digital and print master PDFs")
    parser.add_argument("--quality", type=int, default=60, help="JPEG quality for digital edition (default: 60)")
    args = parser.parse_args()
    compress_digital(quality=args.quality)


if __name__ == "__main__":
    main()
