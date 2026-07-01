import json
from terpvault.domain.models import ProductData, ImageData
from terpvault.domain.changes import ChangeType
from terpvault.sync.differ import diff_products, diff_snapshot_products


def test_same_snapshot_zero_changes():
    products = [
        ProductData(external_id="SKU-001", name="Product A", price=10.0),
        ProductData(external_id="SKU-002", name="Product B", price=20.0),
    ]
    result = diff_products(products, products)
    assert result.total_changes == 0
    assert result.has_changes is False


def test_product_added():
    old = [ProductData(external_id="SKU-001", name="Product A")]
    new = [
        ProductData(external_id="SKU-001", name="Product A"),
        ProductData(external_id="SKU-002", name="Product B", price=15.0),
    ]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert result.entries[0].change_type == ChangeType.product_added
    assert result.entries[0].product_external_id == "SKU-002"


def test_product_removed():
    old = [
        ProductData(external_id="SKU-001", name="Product A"),
        ProductData(external_id="SKU-002", name="Product B"),
    ]
    new = [ProductData(external_id="SKU-001", name="Product A")]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert result.entries[0].change_type == ChangeType.product_removed
    assert result.entries[0].product_external_id == "SKU-002"


def test_price_change():
    old = [ProductData(external_id="SKU-001", name="Product A", price=10.0)]
    new = [ProductData(external_id="SKU-001", name="Product A", price=15.0)]
    result = diff_products(old, new)
    assert result.total_changes == 1
    entry = result.entries[0]
    assert entry.change_type == ChangeType.product_updated
    assert len(entry.fields_changed) == 1
    assert entry.fields_changed[0].field == "price"
    assert entry.fields_changed[0].old_value == 10.0
    assert entry.fields_changed[0].new_value == 15.0


def test_name_change():
    old = [ProductData(external_id="SKU-001", name="Old Name")]
    new = [ProductData(external_id="SKU-001", name="New Name")]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert result.entries[0].fields_changed[0].field == "name"


def test_availability_change():
    old = [ProductData(external_id="SKU-001", name="P", available=True)]
    new = [ProductData(external_id="SKU-001", name="P", available=False)]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert result.entries[0].fields_changed[0].field == "available"


def test_compare_at_price_change():
    old = [ProductData(external_id="SKU-001", name="P", compare_at_price=20.0)]
    new = [ProductData(external_id="SKU-001", name="P", compare_at_price=25.0)]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert result.entries[0].fields_changed[0].field == "compare_at_price"


def test_variant_added():
    old_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[{"sku": "VAR-A", "price": 10.0, "available": True}],
    )]
    new_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[
            {"sku": "VAR-A", "price": 10.0, "available": True},
            {"sku": "VAR-B", "price": 20.0, "available": True},
        ],
    )]
    result = diff_products(old_products, new_products)
    variant_added = [e for e in result.entries if e.change_type == ChangeType.variant_added]
    assert len(variant_added) == 1
    assert variant_added[0].new_values["sku"] == "VAR-B"


def test_variant_removed():
    old_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[
            {"sku": "VAR-A", "price": 10.0, "available": True},
            {"sku": "VAR-B", "price": 20.0, "available": True},
        ],
    )]
    new_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[{"sku": "VAR-A", "price": 10.0, "available": True}],
    )]
    result = diff_products(old_products, new_products)
    removed = [e for e in result.entries if e.change_type == ChangeType.variant_removed]
    assert len(removed) == 1
    assert removed[0].old_values["sku"] == "VAR-B"


def test_variant_price_updated():
    old_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[{"sku": "VAR-A", "price": 10.0, "available": True}],
    )]
    new_products = [ProductData(
        external_id="SKU-001", name="P",
        variants=[{"sku": "VAR-A", "price": 15.0, "available": True}],
    )]
    result = diff_products(old_products, new_products)
    updated = [e for e in result.entries if e.change_type == ChangeType.variant_updated]
    assert len(updated) == 1
    assert updated[0].fields_changed[0].field == "price"


def test_image_added():
    old = [ProductData(
        external_id="SKU-001", name="P",
        images=[ImageData(url="https://example.com/img1.jpg", position=0)],
    )]
    new = [ProductData(
        external_id="SKU-001", name="P",
        images=[
            ImageData(url="https://example.com/img1.jpg", position=0),
            ImageData(url="https://example.com/img2.jpg", position=1),
        ],
    )]
    result = diff_products(old, new)
    added = [e for e in result.entries if e.change_type == ChangeType.image_added]
    assert len(added) == 1
    assert added[0].new_values["url"] == "https://example.com/img2.jpg"


def test_image_removed():
    old = [ProductData(
        external_id="SKU-001", name="P",
        images=[
            ImageData(url="https://example.com/img1.jpg", position=0),
            ImageData(url="https://example.com/img2.jpg", position=1),
        ],
    )]
    new = [ProductData(
        external_id="SKU-001", name="P",
        images=[ImageData(url="https://example.com/img1.jpg", position=0)],
    )]
    result = diff_products(old, new)
    removed = [e for e in result.entries if e.change_type == ChangeType.image_removed]
    assert len(removed) == 1


def test_multiple_changes_detected():
    old = [ProductData(external_id="SKU-001", name="Old", price=10.0, available=True)]
    new = [ProductData(external_id="SKU-001", name="New", price=15.0, available=False)]
    result = diff_products(old, new)
    assert result.total_changes == 1
    assert len(result.entries[0].fields_changed) == 3


def test_deterministic_ordering():
    old = [
        ProductData(external_id="SKU-B", name="B"),
        ProductData(external_id="SKU-A", name="A"),
    ]
    new = [
        ProductData(external_id="SKU-A", name="A"),
        ProductData(external_id="SKU-B", name="B"),
        ProductData(external_id="SKU-C", name="C"),
    ]
    result1 = diff_products(old, new)
    result2 = diff_products(old, new)
    assert result1.model_dump_json() == result2.model_dump_json()


def test_diff_from_snapshot_json():
    old_json = json.dumps([{"external_id": "SKU-001", "name": "Old", "description": "", "available": True, "price": 10.0}])
    new_json = json.dumps([{"external_id": "SKU-001", "name": "New", "description": "", "available": True, "price": 15.0}])
    result = diff_snapshot_products(old_json, new_json)
    assert result.total_changes == 1
    assert result.entries[0].change_type == ChangeType.product_updated
