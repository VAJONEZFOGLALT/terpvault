import asyncio
import typer

from terpvault.sync.engine import SyncEngine

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
