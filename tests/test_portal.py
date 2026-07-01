import json
from pathlib import Path
from terpvault.web.app import app
from terpvault.config.settings import settings
from starlette.testclient import TestClient
import pytest


@pytest.fixture
def client():
    return TestClient(app)


def test_home_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "TerpVault" in r.text


def test_home_page_shows_suppliers(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Terpenes UK" in r.text
    assert "337 products" in r.text


def test_supplier_page(client):
    r = client.get("/supplier/terpenes-uk")
    assert r.status_code == 200
    assert "Terpenes UK" in r.text
    assert "Latest Catalog" in r.text
    assert "337" in r.text
    assert "13" in r.text
    assert "22" in r.text
    assert "Browse HTML" in r.text
    assert "Download JSON" in r.text


def test_supplier_page_shows_337_products(client):
    r = client.get("/supplier/terpenes-uk")
    assert r.status_code == 200
    assert "337" in r.text


def test_html_catalog_served(client):
    r = client.get("/catalogs/terpenes-uk/index.html")
    assert r.status_code == 200
    assert "Terpenes UK" in r.text


def test_json_catalog_served(client):
    import glob, json
    from pathlib import Path
    files = list(Path("data/catalogs/terpenes-uk").glob("catalog-*.json"))
    assert len(files) > 0, "No catalog files found"
    r = client.get(f"/catalogs/terpenes-uk/{files[0].name}")
    assert r.status_code == 200
    data = r.json()
    assert data["stats"]["product_count"] == 337


def test_nonexistent_page(client):
    r = client.get("/nonexistent")
    assert r.status_code == 404


def test_nonexistent_supplier(client):
    r = client.get("/supplier/nonexistent")
    assert r.status_code == 404


def test_timeline_page(client):
    r = client.get("/supplier/terpenes-uk/timeline")
    assert r.status_code == 200
    assert "Change History" in r.text
    assert "337" in r.text or "Added" in r.text or "Removed" in r.text


def test_timeline_nonexistent_supplier(client):
    r = client.get("/supplier/nonexistent/timeline")
    assert r.status_code == 404


def test_search_page_no_query(client):
    r = client.get("/supplier/terpenes-uk/search")
    assert r.status_code == 200
    assert "Search" in r.text


def test_search_page_with_query(client):
    # Need to build a valid search index first
    search_path = settings.catalogs_dir / "terpenes-uk" / "search_index.json"
    if search_path.exists():
        r = client.get("/supplier/terpenes-uk/search?q=terpene")
        assert r.status_code == 200


def test_search_page_no_results(client):
    r = client.get("/supplier/terpenes-uk/search?q=zzzznotfoundzzzz")
    assert r.status_code == 200
    assert "No products" in r.text


def test_search_page_missing_index(client):
    r = client.get("/supplier/nonexistent/search")
    assert r.status_code == 404
