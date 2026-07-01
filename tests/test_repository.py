import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from terpvault.domain.models import SupplierData, ProductData, VariantData, ImageData, SnapshotData
from terpvault.storage.database import Base
from terpvault.storage.repository import (
    SupplierRepo, ProductRepo, VariantRepo, ImageRepo, SnapshotRepo,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def test_supplier_repo(session):
    repo = SupplierRepo(session)
    data = SupplierData(slug="terpenes-uk", name="Terpenes UK", config={"url": "https://terpenesuk.com"})
    row = repo.get_or_create(data)
    assert row.slug == "terpenes-uk"
    assert json.loads(row.config)["url"] == "https://terpenesuk.com"
    fetched = repo.get_by_slug("terpenes-uk")
    assert fetched is not None
    assert fetched.id == row.id
    not_found = repo.get_by_slug("nonexistent")
    assert not_found is None


def test_product_repo(session):
    supplier_repo = SupplierRepo(session)
    supplier = supplier_repo.get_or_create(SupplierData(slug="test-supplier", name="Test"))
    session.flush()

    repo = ProductRepo(session)
    data = ProductData(
        external_id="SKU-001",
        name="Test Product",
        description="A test",
        brand="TestBrand",
        price=29.99,
        unit="ml",
        size="30ml",
        options=[{"name": "Size", "values": ["10ml", "30ml"]}],
        raw={"source": "test"},
    )
    row = repo.upsert(supplier.id, data)
    assert row.external_id == "SKU-001"
    assert row.name == "Test Product"
    assert json.loads(row.raw)["source"] == "test"

    count = repo.count_by_supplier(supplier.id)
    assert count == 1

    data2 = ProductData(external_id="SKU-002", name="Product 2")
    repo.upsert(supplier.id, data2)
    assert repo.count_by_supplier(supplier.id) == 2

    all_products = repo.all_by_supplier(supplier.id)
    assert len(all_products) == 2
    assert {p.external_id for p in all_products} == {"SKU-001", "SKU-002"}


def test_product_upsert_idempotent(session):
    supplier_repo = SupplierRepo(session)
    supplier = supplier_repo.get_or_create(SupplierData(slug="test-supplier", name="Test"))
    session.flush()

    repo = ProductRepo(session)
    data = ProductData(external_id="SKU-001", name="Original Name")
    row1 = repo.upsert(supplier.id, data)
    row2 = repo.upsert(supplier.id, data)
    assert row1.id == row2.id
    assert repo.count_by_supplier(supplier.id) == 1


def test_product_raw_preserved(session):
    supplier_repo = SupplierRepo(session)
    supplier = supplier_repo.get_or_create(SupplierData(slug="test-supplier", name="Test"))
    session.flush()

    repo = ProductRepo(session)
    raw = {"id": 123, "title": "Raw Title", "extra_field": "preserved"}
    data = ProductData(external_id="SKU-001", name="Product", raw=raw)
    row = repo.upsert(supplier.id, data)
    saved_raw = json.loads(row.raw)
    assert saved_raw["id"] == 123
    assert saved_raw["extra_field"] == "preserved"


def test_variant_repo(session):
    supplier_repo = SupplierRepo(session)
    supplier = supplier_repo.get_or_create(SupplierData(slug="test-supplier", name="Test"))
    product_repo = ProductRepo(session)
    product = product_repo.upsert(supplier.id, ProductData(external_id="SKU-001", name="Test"))
    session.flush()

    repo = VariantRepo(session)
    variants = [
        VariantData(sku="VAR-A", price=10.0, available=True, options={"Size": "10ml"}, position=0),
        VariantData(sku="VAR-B", price=20.0, available=False, options={"Size": "30ml"}, position=1),
    ]
    rows = repo.upsert_batch(product.id, variants)
    assert len(rows) == 2
    assert rows[0].sku == "VAR-A"
    assert rows[0].price == 10.0
    assert json.loads(rows[0].options) == {"Size": "10ml"}


def test_image_repo(session):
    supplier_repo = SupplierRepo(session)
    supplier = supplier_repo.get_or_create(SupplierData(slug="test-supplier", name="Test"))
    product_repo = ProductRepo(session)
    product = product_repo.upsert(supplier.id, ProductData(external_id="SKU-001", name="Test"))
    session.flush()

    repo = ImageRepo(session)
    images = [
        ImageData(url="https://example.com/img1.jpg", position=0, alt_text="Front view"),
        ImageData(url="https://example.com/img2.jpg", position=1),
    ]
    rows = repo.upsert_batch(product.id, images)
    assert len(rows) == 2
    assert rows[0].url == "https://example.com/img1.jpg"
    assert rows[0].alt_text == "Front view"


def test_snapshot_repo(session):
    repo = SnapshotRepo(session)
    products = [
        ProductData(external_id="SKU-001", name="P1"),
        ProductData(external_id="SKU-002", name="P2"),
    ]
    data = SnapshotData(
        supplier_slug="terpenes-uk",
        products=products,
        product_count=2,
    )
    row = repo.create(data)
    assert row.supplier_slug == "terpenes-uk"
    assert row.product_count == 2
    assert json.loads(row.products)[0]["name"] == "P1"

    count = repo.count_by_supplier("terpenes-uk")
    assert count == 1

    repo.create(data)
    assert repo.count_by_supplier("terpenes-uk") == 2
