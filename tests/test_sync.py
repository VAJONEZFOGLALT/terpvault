import json
import pytest

from terpvault.sync.engine import SyncEngine
from terpvault.storage.database import get_session
from terpvault.storage.repository import ProductRepo, SnapshotRepo, SupplierRepo


SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "title": "Limonene",
        "body_html": "<p>Premium Limonene</p>",
        "vendor": "Terpenes UK",
        "product_type": "Terpene",
        "handle": "limonene",
        "tags": "premium",
        "published_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
        "options": [{"name": "Size", "values": ["10ml", "30ml"]}],
        "variants": [
            {"id": 101, "sku": "LIM-10ML", "price": "14.99", "compare_at_price": "19.99", "available": True, "option1": "10ml"},
            {"id": 102, "sku": "LIM-30ML", "price": "29.99", "compare_at_price": None, "available": True, "option1": "30ml"},
        ],
        "images": [
            {"src": "https://example.com/limonene.jpg", "alt": "Limonene bottle", "position": 1},
        ],
    },
    {
        "id": 2,
        "title": "Myrcene",
        "body_html": "<p>Premium Myrcene</p>",
        "vendor": "Terpenes UK",
        "product_type": "Terpene",
        "handle": "myrcene",
        "tags": "premium",
        "published_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
        "options": [{"name": "Size", "values": ["10ml", "100ml"]}],
        "variants": [
            {"id": 201, "sku": "MYR-10ML", "price": "13.99", "compare_at_price": None, "available": True, "option1": "10ml"},
            {"id": 202, "sku": "MYR-100ML", "price": "49.99", "compare_at_price": "59.99", "available": False, "option1": "100ml"},
        ],
        "images": [
            {"src": "https://example.com/myrcene.jpg", "alt": "Myrcene bottle", "position": 1},
        ],
    },
]


@pytest.fixture(autouse=True)
def clean_db():
    from terpvault.storage.database import drop_db, init_db
    drop_db()
    init_db()
    yield


@pytest.mark.asyncio
async def test_sync_engine_full_pipeline(monkeypatch):
    async def mock_fetch_via_collections(self):
        from terpvault.sync.importer.normalizer import ShopifyNormalizer
        return [ShopifyNormalizer.normalize(p) for p in SAMPLE_PRODUCTS]

    monkeypatch.setattr(
        "terpvault.sync.importer.terpenes_uk.TerpenesUKImporter._fetch_via_collections",
        mock_fetch_via_collections,
    )

    engine = SyncEngine("terpenes-uk")
    result = await engine.run()

    assert result["products"] == 2
    assert result["variants"] == 4
    assert result["images"] == 2
    assert result["supplier"] == "terpenes-uk"
    assert result["snapshot_id"] is not None
    assert result["checksum"] is not None


@pytest.mark.asyncio
async def test_sync_idempotent(monkeypatch):
    async def mock_fetch(self):
        from terpvault.sync.importer.normalizer import ShopifyNormalizer
        return [ShopifyNormalizer.normalize(p) for p in SAMPLE_PRODUCTS]

    monkeypatch.setattr(
        "terpvault.sync.importer.terpenes_uk.TerpenesUKImporter._fetch_via_collections",
        mock_fetch,
    )

    engine = SyncEngine("terpenes-uk")
    r1 = await engine.run()
    r2 = await engine.run()

    assert r1["products"] == r2["products"]
    assert r1["variants"] == r2["variants"]
    assert r1["images"] == r2["images"]

    session = get_session()
    try:
        supplier = SupplierRepo(session).get_by_slug("terpenes-uk")
        count = ProductRepo(session).count_by_supplier(supplier.id)
        assert count == 2
    finally:
        session.close()


@pytest.mark.asyncio
async def test_sync_rollback_on_failure(monkeypatch):
    original_store = SyncEngine._store

    async def mock_fetch(self):
        from terpvault.sync.importer.normalizer import ShopifyNormalizer
        return [ShopifyNormalizer.normalize(p) for p in SAMPLE_PRODUCTS]

    monkeypatch.setattr(
        "terpvault.sync.importer.terpenes_uk.TerpenesUKImporter._fetch_via_collections",
        mock_fetch,
    )

    def broken_store(self, raw_products):
        raise RuntimeError("Database failure")

    monkeypatch.setattr(SyncEngine, "_store", broken_store)

    with pytest.raises(RuntimeError, match="Database failure"):
        engine = SyncEngine("terpenes-uk")
        await engine.run()

    session = get_session()
    try:
        supplier = SupplierRepo(session).get_by_slug("terpenes-uk")
        assert supplier is None
    finally:
        session.close()


@pytest.mark.asyncio
async def test_raw_metadata_preserved_through_sync(monkeypatch):
    async def mock_fetch(self):
        from terpvault.sync.importer.normalizer import ShopifyNormalizer
        return [ShopifyNormalizer.normalize(p) for p in SAMPLE_PRODUCTS]

    monkeypatch.setattr(
        "terpvault.sync.importer.terpenes_uk.TerpenesUKImporter._fetch_via_collections",
        mock_fetch,
    )

    engine = SyncEngine("terpenes-uk")
    await engine.run()

    session = get_session()
    try:
        supplier = SupplierRepo(session).get_by_slug("terpenes-uk")
        products = ProductRepo(session).all_by_supplier(supplier.id)

        for p in products:
            raw = json.loads(p.raw)
            assert "title" in raw
            assert "variants" in raw
            assert "images" in raw

            meta = json.loads(p.extra_metadata)
            assert "vendor" in meta
            assert "handle" in meta
    finally:
        session.close()


@pytest.mark.asyncio
async def test_snapshot_created_per_sync(monkeypatch):
    async def mock_fetch(self):
        from terpvault.sync.importer.normalizer import ShopifyNormalizer
        return [ShopifyNormalizer.normalize(p) for p in SAMPLE_PRODUCTS]

    monkeypatch.setattr(
        "terpvault.sync.importer.terpenes_uk.TerpenesUKImporter._fetch_via_collections",
        mock_fetch,
    )

    engine = SyncEngine("terpenes-uk")
    await engine.run()
    await engine.run()
    await engine.run()

    session = get_session()
    try:
        count = SnapshotRepo(session).count_by_supplier("terpenes-uk")
        assert count == 3
    finally:
        session.close()
