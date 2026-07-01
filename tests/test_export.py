import json
from pathlib import Path
import pytest
from terpvault.domain.catalog_document import CatalogDocument, CatalogProduct, CatalogStats, CoverInfo, SectionInfo, SectionType, TocEntry
from terpvault.generate.export import export_json
from terpvault.generate.integrity import check_catalog


def _make_doc() -> CatalogDocument:
    return CatalogDocument(
        supplier_slug="test",
        cover=CoverInfo(supplier_name="Test Supplier", catalog_label="Catalog"),
        toc=[TocEntry(label="A", section_index=0)],
        sections=[SectionInfo(index=0, label="A", product_ids=["P1"])],
        products={"P1": CatalogProduct(external_id="P1", name="Product", price=10.0)},
        stats=CatalogStats(product_count=1, section_count=1),
    )


def test_export_json(tmp_path):
    doc = _make_doc()
    out = tmp_path / "catalog.json"
    result = export_json(doc, out)
    assert result == out
    assert out.exists()
    content = json.loads(out.read_text(encoding="utf-8"))
    assert content["supplier_slug"] == "test"
    assert content["stats"]["product_count"] == 1


def test_export_directory_created(tmp_path):
    doc = _make_doc()
    out = tmp_path / "nested" / "dir" / "catalog.json"
    export_json(doc, out)
    assert out.exists()


def test_export_round_trip(tmp_path):
    doc = _make_doc()
    out = tmp_path / "catalog.json"
    export_json(doc, out)
    restored = CatalogDocument.model_validate_json(out.read_text(encoding="utf-8"))
    assert restored == doc


def test_export_passes_integrity(tmp_path):
    doc = _make_doc()
    out = tmp_path / "catalog.json"
    export_json(doc, out)
    restored = CatalogDocument.model_validate_json(out.read_text(encoding="utf-8"))
    result = check_catalog(restored)
    assert result.can_publish


def test_cli_export_help():
    from typer.testing import CliRunner
    from terpvault.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["export", "--help"])
    assert result.exit_code == 0
    assert "snapshot" in result.output
    assert "output" in result.output
