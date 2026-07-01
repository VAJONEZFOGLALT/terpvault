import asyncio
import json
from pathlib import Path
import typer

from terpvault.config.settings import settings
from terpvault.sync.engine import SyncEngine
from terpvault.storage.database import get_session
from terpvault.storage.repository import ChangeRepo, SnapshotRepo, SupplierRepo
from terpvault.storage.tables import SupplierRow
from terpvault.domain.changes import ChangeSet
from terpvault.domain.models import ProductData
from terpvault.sync.differ import diff_snapshot_products
from terpvault.sync.report import ChangeReport
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.integrity import check_catalog
from terpvault.generate.export import export_json
from terpvault.generate.search_index import write_search_index

app = typer.Typer(
    name="terpvault",
    help="Supplier synchronization and catalog publishing platform.",
)


@app.callback()
def callback():
    pass


@app.command()
def sync(supplier: str):
    """Synchronize product data from a supplier."""
    try:
        engine = SyncEngine(supplier)
        result = asyncio.run(engine.run())
        typer.echo(f"Synced {result['products']} products from {result['supplier']}")
        typer.echo(f"  Variants: {result['variants']}")
        typer.echo(f"  Images:   {result['images']}")
        typer.echo(f"  Snapshot: {result['snapshot_id']}")
        typer.echo(f"  Checksum: {result['checksum']}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Sync failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def diff(supplier: str):
    """Show changes between the two most recent snapshots."""
    session = get_session()
    try:
        change_repo = ChangeRepo(session)
        latest = change_repo.latest_by_supplier(supplier)
        if latest is None:
            typer.echo("No changes detected.")
            return
        typer.echo(latest.report_text)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    finally:
        session.close()


@app.command()
def changes(
    supplier: str,
    latest: bool = typer.Option(False, "--latest", help="Show latest changes"),
    snapshot_a: str = typer.Option("", "--snapshot-a", help="First snapshot ID for comparison"),
    snapshot_b: str = typer.Option("", "--snapshot-b", help="Second snapshot ID for comparison"),
):
    """View synchronization changes."""
    session = get_session()
    try:
        if snapshot_a and snapshot_b:
            snap_repo = SnapshotRepo(session)
            snap_a = snap_repo.get_by_id(snapshot_a)
            snap_b = snap_repo.get_by_id(snapshot_b)
            if not snap_a:
                typer.echo(f"Snapshot not found: {snapshot_a}", err=True)
                raise typer.Exit(code=1)
            if not snap_b:
                typer.echo(f"Snapshot not found: {snapshot_b}", err=True)
                raise typer.Exit(code=1)
            change_set = diff_snapshot_products(snap_a.products, snap_b.products)
            change_set.source_snapshot_id = snap_a.id
            change_set.target_snapshot_id = snap_b.id
            report = ChangeReport(change_set)
            typer.echo(report.to_text())
            return

        if snapshot_a and not snapshot_b:
            typer.echo("Error: --snapshot-b is required when using --snapshot-a.", err=True)
            raise typer.Exit(code=1)

        if latest:
            change_repo = ChangeRepo(session)
            latest_row = change_repo.latest_by_supplier(supplier)
            if latest_row is None:
                typer.echo("No changes detected.")
                return
            typer.echo(latest_row.report_text)
            return

        from terpvault.storage.tables import SnapshotRow
        all_snaps = session.query(SnapshotRow).filter_by(supplier_slug=supplier).order_by(SnapshotRow.created_at.desc()).all()
        typer.echo(f"Available snapshots for '{supplier}':")
        for s in all_snaps:
            typer.echo(f"  {s.id}  {s.created_at}  ({s.product_count} products)")
        typer.echo("Use --latest or --snapshot-a / --snapshot-b to view changes.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    finally:
        session.close()


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
):
    """Start the TerpVault web portal."""
    import uvicorn
    typer.echo(f"Starting TerpVault portal at http://{host}:{port}")
    uvicorn.run("terpvault.web.app:app", host=host, port=port, log_level="info")


@app.command()
def export(
    supplier: str,
    snapshot_id: str = typer.Option("", "--snapshot", help="Snapshot ID (defaults to latest)"),
    output: str = typer.Option("", "--output", help="Output file path (defaults to data/catalogs/)"),
):
    """Export a catalog document from a snapshot."""
    session = get_session()
    try:
        snap_repo = SnapshotRepo(session)
        supplier_repo = SupplierRepo(session)

        supplier_row = supplier_repo.get_by_slug(supplier)
        if not supplier_row:
            typer.echo(f"Supplier not found: {supplier}", err=True)
            raise typer.Exit(code=1)

        snap = None
        if snapshot_id:
            snap = snap_repo.get_by_id(snapshot_id)
            if not snap:
                typer.echo(f"Snapshot not found: {snapshot_id}", err=True)
                raise typer.Exit(code=1)
        else:
            from terpvault.storage.tables import SnapshotRow
            snap = session.query(SnapshotRow).filter_by(
                supplier_slug=supplier
            ).order_by(SnapshotRow.created_at.desc()).first()
            if not snap:
                typer.echo(f"No snapshots found for supplier: {supplier}", err=True)
                raise typer.Exit(code=1)

        import json as _json
        products_data = _json.loads(snap.products)
        products = [ProductData(**p) for p in products_data]

        builder = CatalogBuilder(supplier, supplier_row.name)
        doc = builder.build(products)

        integrity = check_catalog(doc)
        if not integrity.can_publish:
            typer.echo("Catalog integrity check failed:", err=True)
            for issue in integrity.errors:
                typer.echo(f"  ERROR: {issue.message}", err=True)
            raise typer.Exit(code=1)

        if integrity.warnings:
            for issue in integrity.warnings:
                typer.echo(f"  WARNING: {issue.message}")

        output_path = Path(output) if output else settings.catalogs_dir / supplier / f"catalog-{snap.id[:8]}.json"
        export_json(doc, output_path)

        search_index_path = write_search_index(doc, settings.catalogs_dir / supplier)
        typer.echo(f"Exported: {output_path}")
        typer.echo(f"  Search index: {search_index_path}")
        typer.echo(f"  Products: {doc.stats.product_count}")
        typer.echo(f"  Sections: {doc.stats.section_count}")
        typer.echo(f"  Brands:   {doc.stats.brand_count}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    finally:
        session.close()
