import json
from terpvault.sync.importer.normalizer import ShopifyNormalizer
from terpvault.domain.raw_product import RawProduct


SAMPLE_PRODUCT = {
    "id": 123456789,
    "title": "Limonene Terpene",
    "body_html": "<p>A premium Limonene terpene.</p>",
    "vendor": "Terpenes UK",
    "product_type": "Cannabis Terpenes",
    "handle": "limonene-terpene",
    "tags": "terpene, premium",
    "published_at": "2025-01-15T10:00:00Z",
    "created_at": "2025-01-10T08:00:00Z",
    "updated_at": "2025-06-01T12:00:00Z",
    "options": [
        {"name": "Size", "values": ["10ml", "30ml", "100ml"]}
    ],
    "variants": [
        {
            "id": 1001,
            "sku": "LIM-10ML",
            "price": "14.99",
            "compare_at_price": "19.99",
            "available": True,
            "option1": "10ml",
            "option2": None,
            "option3": None,
        },
        {
            "id": 1002,
            "sku": "LIM-30ML",
            "price": "29.99",
            "compare_at_price": None,
            "available": True,
            "option1": "30ml",
            "option2": None,
            "option3": None,
        },
    ],
    "images": [
        {"src": "https://example.com/img1.jpg", "alt": "Limonene front", "position": 1},
        {"src": "https://example.com/img2.jpg", "alt": "Limonene back", "position": 2},
    ],
}


def test_normalize_basic_fields():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert isinstance(result, RawProduct)
    assert result.external_id == "LIM-10ML"
    assert result.name == "Limonene Terpene"
    assert result.brand == "Terpenes UK"
    assert result.category == "Cannabis Terpenes"
    assert result.price == 14.99
    assert result.compare_at_price == 19.99
    assert result.available is True


def test_normalize_variants():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert len(result.variants) == 2
    assert result.variants[0]["sku"] == "LIM-10ML"
    assert result.variants[0]["price"] == "14.99"
    assert result.variants[0]["options"] == {"Option 1": "10ml"}
    assert result.variants[1]["sku"] == "LIM-30ML"
    assert result.variants[1]["available"] is True


def test_normalize_images():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert len(result.images) == 2
    assert result.images[0]["url"] == "https://example.com/img1.jpg"
    assert result.images[0]["alt_text"] == "Limonene front"
    assert result.images[1]["position"] == 1


def test_normalize_options():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert len(result.options) == 1
    assert result.options[0]["name"] == "Size"
    assert "100ml" in result.options[0]["values"]


def test_normalize_metadata():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert result.metadata["vendor"] == "Terpenes UK"
    assert result.metadata["handle"] == "limonene-terpene"
    assert result.metadata["tags"] == "terpene, premium"


def test_raw_preserved():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT)
    assert result.raw == SAMPLE_PRODUCT
    assert result.raw["id"] == 123456789
    assert result.raw["title"] == "Limonene Terpene"


def test_normalize_with_collection():
    result = ShopifyNormalizer.normalize(SAMPLE_PRODUCT, collection="Premium Terpenes")
    assert result.collection == "Premium Terpenes"


def test_normalize_empty_product():
    result = ShopifyNormalizer.normalize({})
    assert result.external_id == ""
    assert result.name == ""
    assert result.price is None
    assert result.variants == []
    assert result.images == []
    assert result.raw == {}


def test_normalize_no_variants():
    product = {**SAMPLE_PRODUCT, "variants": []}
    result = ShopifyNormalizer.normalize(product)
    assert result.price is None
    assert result.available is True
    assert result.external_id != ""


def test_normalize_no_images():
    product = {**SAMPLE_PRODUCT, "images": []}
    result = ShopifyNormalizer.normalize(product)
    assert result.images == []
