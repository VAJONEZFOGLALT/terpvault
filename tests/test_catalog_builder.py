import pytest
from terpvault.domain.models import ProductData, ImageData
from terpvault.domain.catalog_document import CatalogDocument, SectionType
from terpvault.generate.builder import CatalogBuilder


def test_empty_products():
    builder = CatalogBuilder("test-supplier", "Test Supplier")
    doc = builder.build([], "Test Catalog")
    assert doc.supplier_slug == "test-supplier"
    assert doc.stats.product_count == 0
    assert doc.stats.section_count == 0
    assert doc.cover.catalog_label == "Test Catalog"
    assert len(doc.products) == 0


def test_single_product():
    products = [ProductData(external_id="SKU-001", name="Product A", brand="Brand X")]
    builder = CatalogBuilder("test-supplier")
    doc = builder.build(products)
    assert doc.stats.product_count == 1
    assert doc.stats.brand_count == 1
    assert "SKU-001" in doc.products
    assert doc.products["SKU-001"].name == "Product A"


def test_products_grouped_by_collection():
    products = [
        ProductData(external_id="A", name="A", collection="Citrus"),
        ProductData(external_id="B", name="B", collection="Citrus"),
        ProductData(external_id="C", name="C", collection="Herbal"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.section_count == 2
    citrus_section = [s for s in doc.sections if s.label == "Citrus"]
    herbal_section = [s for s in doc.sections if s.label == "Herbal"]
    assert len(citrus_section) == 1
    assert len(herbal_section) == 1
    assert citrus_section[0].product_ids == ["A", "B"]
    assert herbal_section[0].product_ids == ["C"]


def test_brands_collected():
    products = [
        ProductData(external_id="A", name="A", brand="Brand X"),
        ProductData(external_id="B", name="B", brand="Brand Y"),
        ProductData(external_id="C", name="C", brand="Brand X"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.brand_count == 2


def test_toc_generated():
    products = [
        ProductData(external_id="A", name="A", collection="Citrus"),
        ProductData(external_id="B", name="B", collection="Herbal"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert len(doc.toc) == 2
    assert doc.toc[0].label == "Citrus"
    assert doc.toc[1].label == "Herbal"


def test_product_details_preserved():
    products = [ProductData(
        external_id="SKU-001", name="Product", description="Desc",
        brand="B", category="Cat", price=10.0, unit="ml", size="30ml",
        variants=[{"sku": "V1", "price": 10.0, "available": True}],
        images=[ImageData(url="https://ex.com/img.jpg", position=0, alt_text="Alt")],
    )]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    cp = doc.products["SKU-001"]
    assert cp.description == "Desc"
    assert cp.price == 10.0
    assert cp.unit == "ml"
    assert len(cp.variants) == 1
    assert len(cp.images) == 1
    assert cp.images[0]["url"] == "https://ex.com/img.jpg"


def test_no_duplicate_products():
    products = [
        ProductData(external_id="A", name="A"),
        ProductData(external_id="A", name="A"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.product_count == 1
    assert len(doc.products) == 1


def test_document_immutable():
    products = [ProductData(external_id="A", name="A")]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    with pytest.raises((TypeError, ValueError)):
        doc.products = {}
    with pytest.raises((TypeError, ValueError)):
        doc.supplier_slug = "changed"
    with pytest.raises((TypeError, ValueError)):
        doc.stats.product_count = 999


def test_json_serializable():
    products = [ProductData(external_id="A", name="A", price=10.0)]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    json_str = doc.model_dump_json()
    import json
    parsed = json.loads(json_str)
    assert parsed["supplier_slug"] == "test"
    assert parsed["stats"]["product_count"] == 1


def test_cover_metadata():
    products = [
        ProductData(external_id="A", name="A", brand="X"),
        ProductData(external_id="B", name="B", brand="Y"),
    ]
    builder = CatalogBuilder("test-supplier", "Test Supplier")
    doc = builder.build(products, "June 2026")
    assert doc.cover.supplier_name == "Test Supplier"
    assert doc.cover.catalog_label == "June 2026"
    assert doc.cover.product_count == 2
    assert doc.cover.brand_count == 2


def test_no_collection_uses_brand_as_section():
    products = [
        ProductData(external_id="A", name="A", brand="Brand X"),
        ProductData(external_id="B", name="B", brand="Brand Y"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.section_count >= 2
    labels = [s.label for s in doc.sections]
    assert "Brand X" in labels
    assert "Brand Y" in labels


def test_products_empty_collection_and_no_brand_general():
    products = [
        ProductData(external_id="A", name="A"),
        ProductData(external_id="B", name="B"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.section_count == 1
    assert doc.sections[0].label == "General"
    assert len(doc.sections[0].product_ids) == 2


def test_stats_counts():
    products = [
        ProductData(external_id="A", name="A", collection="C1", variants=[{"sku": "V1"}], images=[ImageData(url="https://ex.com/a.jpg")]),
        ProductData(external_id="B", name="B", collection="C2", variants=[{"sku": "V2"}, {"sku": "V3"}], images=[ImageData(url="https://ex.com/b.jpg")]),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.product_count == 2
    assert doc.stats.section_count == 2
    assert doc.stats.variant_count == 3
    assert doc.stats.image_count == 2
