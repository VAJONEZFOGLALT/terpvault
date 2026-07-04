"""
Full catalog refresh: sync → export → generate PDFs → copy to prod/.
"""
import asyncio, json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from terpvault.sync.engine import SyncEngine
from terpvault.config.settings import settings
from terpvault.config.supplier_config import SupplierConfig
from terpvault.storage.database import get_session
from terpvault.storage.repository import SupplierRepo
from terpvault.storage.tables import SnapshotRow
from terpvault.domain.models import ProductData
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.export import export_json
from terpvault.generate.search_index import write_search_index
from terpvault.generate.artifacts.base import BuildContext
from terpvault.generate.artifacts.playwright_pdf import PlaywrightPDFGenerator

SUPPLIER = "terpenes-uk"
LOG_FILE = settings.catalogs_dir / SUPPLIER / "refresh.log"


def log(msg):
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


def main():
    log("=== Refresh started ===")

    # Step 1: Sync
    try:
        log("Syncing...")
        engine = SyncEngine(SUPPLIER)
        result = asyncio.run(engine.run())
        snapshot_id = result["snapshot_id"]
        log(f"  Synced {result['products']} products, snapshot={snapshot_id[:8]}")
    except Exception as e:
        log(f"  Sync failed: {e}")
        return

    # Step 2: Build catalogue document
    try:
        log("Building catalogue...")
        session = get_session()
        supplier_row = SupplierRepo(session).get_by_slug(SUPPLIER)
        snap = session.query(SnapshotRow).filter_by(
            supplier_slug=SUPPLIER
        ).order_by(SnapshotRow.created_at.desc()).first()
        products_data = json.loads(snap.products)
        products = [ProductData(**p) for p in products_data]
        builder = CatalogBuilder(SUPPLIER, supplier_row.name)
        doc = builder.build(products)
        session.close()
    except Exception as e:
        log(f"  Build failed: {e}")
        return

    # Step 3: Export JSON + search index
    try:
        slug = SUPPLIER
        output_path = settings.catalogs_dir / slug / f"catalog-{snap.id[:8]}.json"
        export_json(doc, output_path)
        write_search_index(doc, settings.catalogs_dir / slug)
        log(f"  Exported {doc.stats.product_count} products")
    except Exception as e:
        log(f"  Export failed: {e}")
        return

    # Step 4: Compose once, render print + digital from the same HTML
    try:
        config = SupplierConfig.load(SUPPLIER)

        version = doc.stats.product_count
        ctx = BuildContext(
            snapshot_id=snap.id,
            catalog_version=version,
            supplier_config=config,
            output_dir=settings.catalogs_dir,
            edition="print",
        )

        print_artifact, digital_artifact = PlaywrightPDFGenerator.generate_both(doc, ctx)
        log(f"  PDF (print):   {print_artifact.path.name} ({print_artifact.size_bytes/1024/1024:.0f} MB)")
        log(f"  PDF (digital): {digital_artifact.path.name} ({digital_artifact.size_bytes/1024/1024:.0f} MB)")
    except Exception as e:
        log(f"  PDF generation failed: {e}")
        return

    # Step 5: Copy to prod/
    try:
        prod_dir = settings.prod_dir / SUPPLIER
        prod_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_path, prod_dir / "catalog.json")
        shutil.copy2(settings.catalogs_dir / SUPPLIER / "search_index.json", prod_dir / "search_index.json")
        shutil.copy2(print_artifact.path, prod_dir / "catalogue-print.pdf")
        shutil.copy2(digital_artifact.path, prod_dir / "catalogue.pdf")
        # Remove legacy filename if it still exists
        legacy_digital = prod_dir / "catalogue-digital.pdf"
        if legacy_digital.exists():
            legacy_digital.unlink()

        log(f"  Copied to prod/")
    except Exception as e:
        log(f"  Copy to prod failed: {e}")
        return

    log("=== Refresh complete ===")


if __name__ == "__main__":
    main()
