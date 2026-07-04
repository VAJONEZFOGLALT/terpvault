import pytest
from terpvault.domain.models import ProductData, ImageData
from terpvault.domain.catalog_document import CatalogDocument, SectionType
from terpvault.generate.builder import CatalogBuilder
from terpvault.generate.categorizer import classify


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


def test_eybna_products_group_under_eybna_section():
    products = [
        ProductData(external_id="A", name="Strain A", brand="Eybna", collection="Eybna Palate & Live Line™"),
        ProductData(external_id="B", name="Strain B", brand="Eybna", collection="Eybna Live Plus+ Line™"),
        ProductData(external_id="C", name="Strain C", brand="Eybna", collection="Eybna Enhancer Line"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.section_count == 1
    assert doc.sections[0].label == "Eybna"
    assert len(doc.sections[0].product_ids) == 3


def test_brands_collected():
    products = [
        ProductData(external_id="A", name="A", brand="Eybna"),
        ProductData(external_id="B", name="B", brand="True Terpenes - Strain Profiles"),
        ProductData(external_id="C", name="C", brand="Terpenes UK - Strain Profiles"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.brand_count == 3


def test_toc_in_canonical_order():
    products = [
        ProductData(external_id="A", name="A", brand="Eybna"),
        ProductData(external_id="B", name="B", brand="Terpenes UK - Strain Profiles"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert len(doc.toc) == 2
    assert doc.toc[0].label == "Eybna"
    assert doc.toc[1].label == "Terpenes UK - Botanical"


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


def test_unknown_product_routed_to_new_releases():
    products = [
        ProductData(external_id="A", name="Mystery Product", collection="Unknown Collection"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.section_count == 1
    assert doc.sections[0].label == "New Releases"
    assert len(doc.sections[0].product_ids) == 1


def test_stats_counts():
    products = [
        ProductData(external_id="A", name="A", brand="Eybna", variants=[{"sku": "V1"}], images=[ImageData(url="https://ex.com/a.jpg")]),
        ProductData(external_id="B", name="B", brand="Eybna", variants=[{"sku": "V2"}, {"sku": "V3"}], images=[ImageData(url="https://ex.com/b.jpg")]),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    assert doc.stats.product_count == 2
    assert doc.stats.section_count == 1
    assert doc.stats.variant_count == 3
    assert doc.stats.image_count == 2


def test_sample_pack_goes_to_sample_packs_section():
    products = [
        ProductData(external_id="A", name="Eybna Sample Pack", brand="Eybna"),
        ProductData(external_id="B", name="True Terpenes Sample Pack", brand="True Terpenes - Strain Profiles"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    sample_section = [s for s in doc.sections if s.label == "Sample Packs"]
    assert len(sample_section) == 1
    assert len(sample_section[0].product_ids) == 2


def test_hardware_goes_to_vape_hardware_section():
    products = [
        ProductData(external_id="A", name="CCELL Battery", brand="Hardware", collection="Vape Hardware"),
        ProductData(external_id="B", name="Mixing Kit", brand="Hardware", collection="Vape Hardware"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    hw_section = [s for s in doc.sections if s.label == "Vape Hardware"]
    assert len(hw_section) == 1
    assert len(hw_section[0].product_ids) == 2


def test_all_products_covered_exactly_once():
    products = [
        ProductData(external_id="A", name="Strain", brand="Eybna"),
        ProductData(external_id="B", name="Hardware", brand="Hardware", collection="Vape Hardware"),
        ProductData(external_id="C", name="Sample Pack", brand="Eybna"),
        ProductData(external_id="D", name="Isolate", collection="Terpene Isolates", brand="Terpenes UK - Isolates"),
    ]
    builder = CatalogBuilder("test")
    doc = builder.build(products)
    total_section_ids = sum(len(s.product_ids) for s in doc.sections)
    assert total_section_ids == 4
    assert total_section_ids == len(doc.products)
