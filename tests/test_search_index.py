import json
import pytest
from pathlib import Path
from terpvault.domain.catalog_document import CatalogDocument, CatalogProduct, CatalogStats, CoverInfo, SectionInfo, SectionType, TocEntry
from terpvault.generate.search_index import build_search_index, write_search_index


def _make_doc() -> CatalogDocument:
    return CatalogDocument(
        supplier_slug="test",
        cover=CoverInfo(supplier_name="Test", catalog_label="Catalog"),
        toc=[TocEntry(label="A", section_index=0)],
        sections=[SectionInfo(index=0, label="Citrus", product_ids=["P1", "P2"])],
        products={
            "P1": CatalogProduct(
                external_id="P1", name="Limonene", brand="Terpenes UK",
                collection="Citrus", description="Premium citrus terpene",
                price=14.99, variants=[{"sku": "LIM-10ML", "price": 14.99}],
            ),
            "P2": CatalogProduct(
                external_id="P2", name="Orange Bliss", brand="Terpenes UK",
                collection="Citrus", description="Sweet orange profile",
                price=12.99, variants=[{"sku": "ORA-10ML", "price": 12.99}],
            ),
        },
        stats=CatalogStats(product_count=2, section_count=1, brand_count=1),
    )


def test_build_search_index_count():
    doc = _make_doc()
    index = build_search_index(doc)
    assert index["count"] == 2


def test_build_search_index_entries():
    doc = _make_doc()
    index = build_search_index(doc)
    names = {e["name"] for e in index["entries"]}
    assert "Limonene" in names
    assert "Orange Bliss" in names


def test_search_index_searchable_text():
    doc = _make_doc()
    index = build_search_index(doc)
    limonene = [e for e in index["entries"] if e["name"] == "Limonene"][0]
    assert "limonene" in limonene["searchable"]
    assert "terpenes uk" in limonene["searchable"]
    assert "citrus" in limonene["searchable"]
    assert "citrus" in limonene["searchable"]
    assert "lim-10ml" in limonene["searchable"]
    assert "premium" in limonene["searchable"]


def test_search_index_round_trip(tmp_path):
    doc = _make_doc()
    path = write_search_index(doc, tmp_path / "supplier")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["count"] == 2
