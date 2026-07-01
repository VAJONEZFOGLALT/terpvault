import pytest
from terpvault.domain.catalog_document import CatalogDocument, CatalogProduct, CatalogStats, CoverInfo, SectionInfo, SectionType, TocEntry
from terpvault.generate.integrity import check_catalog, IntegrityResult, Severity


def _make_doc(**overrides) -> CatalogDocument:
    defaults = {
        "supplier_slug": "test",
        "cover": CoverInfo(supplier_name="Test Supplier", catalog_label="Catalog"),
        "toc": [TocEntry(label="Section A", section_index=0)],
        "sections": [SectionInfo(index=0, label="Section A", product_ids=["P1"])],
        "products": {"P1": CatalogProduct(external_id="P1", name="Product One", price=10.0)},
        "stats": CatalogStats(product_count=1, brand_count=0, section_count=1, variant_count=0, image_count=0),
    }
    defaults.update(overrides)
    return CatalogDocument(**defaults)


def test_clean_document_no_issues():
    doc = _make_doc()
    result = check_catalog(doc)
    assert result.is_ready
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_section_references_missing_product():
    doc = _make_doc(sections=[SectionInfo(index=0, label="A", product_ids=["NONEXISTENT"])])
    result = check_catalog(doc)
    assert not result.is_ready
    assert any("NONEXISTENT" in i.message for i in result.errors)


def test_toc_references_missing_section():
    doc = _make_doc(toc=[TocEntry(label="Ghost", section_index=99)])
    result = check_catalog(doc)
    assert not result.is_ready
    assert any("section index 99" in i.message for i in result.errors)


def test_stats_product_count_mismatch():
    doc = _make_doc(stats=CatalogStats(product_count=999, section_count=1))
    result = check_catalog(doc)
    assert any("product_count" in i.message for i in result.errors)


def test_stats_section_count_mismatch():
    doc = _make_doc(stats=CatalogStats(product_count=1, section_count=999))
    result = check_catalog(doc)
    assert any("section_count" in i.message for i in result.errors)


def test_stats_brand_count_mismatch():
    doc = _make_doc(
        products={"P1": CatalogProduct(external_id="P1", name="A", brand="X")},
        stats=CatalogStats(product_count=1, brand_count=999, section_count=1),
    )
    result = check_catalog(doc)
    assert any("brand_count" in i.message for i in result.issues)


def test_serialization_round_trip():
    doc = _make_doc()
    result = check_catalog(doc)
    assert not any(i.category == "serialization" for i in result.issues)


def test_product_without_name():
    doc = _make_doc(products={"P1": CatalogProduct(external_id="P1", name="")})
    result = check_catalog(doc)
    assert any("no name" in i.message for i in result.errors)


def test_section_without_label():
    doc = _make_doc(sections=[SectionInfo(index=0, label="", product_ids=["P1"])])
    result = check_catalog(doc)
    assert any("no label" in i.message for i in result.errors)


def test_available_product_no_price():
    doc = _make_doc(products={"P1": CatalogProduct(external_id="P1", name="A", available=True, price=None)})
    result = check_catalog(doc)
    assert any("no price" in i.message for i in result.warnings)


def test_duplicate_section_index():
    doc = _make_doc(sections=[
        SectionInfo(index=0, label="A", product_ids=["P1"]),
        SectionInfo(index=0, label="B", product_ids=["P1"]),
    ])
    result = check_catalog(doc)
    assert any("Duplicate section index" in i.message for i in result.errors)


def test_orphan_product():
    doc = _make_doc(
        sections=[SectionInfo(index=0, label="A", product_ids=[])],
        products={
            "P1": CatalogProduct(external_id="P1", name="A"),
            "P2": CatalogProduct(external_id="P2", name="B"),
        },
        stats=CatalogStats(product_count=2, section_count=1),
    )
    result = check_catalog(doc)
    assert any("not referenced" in i.message for i in result.warnings)


def test_empty_toc():
    doc = _make_doc(toc=[])
    result = check_catalog(doc)
    assert any("No table of contents" in i.message for i in result.warnings)


def test_summary_output():
    doc = _make_doc()
    result = check_catalog(doc)
    summary = result.summary()
    assert "Errors: 0" in summary
    assert "Ready to publish" in summary


def test_summary_with_errors():
    doc = _make_doc(sections=[SectionInfo(index=0, label="A", product_ids=["MISSING"])])
    result = check_catalog(doc)
    summary = result.summary()
    assert "Errors: 1" in summary
    assert "Cannot publish" in summary
