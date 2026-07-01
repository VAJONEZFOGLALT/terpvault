import json
from decimal import Decimal
from terpvault.domain.changes import ChangeSet, ChangeEntry, ChangeType, FieldChange
from terpvault.domain.models import ProductData
from terpvault.sync.differ import diff_products
from terpvault.sync.report import ChangeReport, Severity


def _make_products(*args) -> list[ProductData]:
    return list(args)


def test_empty_report():
    report = ChangeReport(ChangeSet())
    assert report.total == 0
    assert report.to_text() == "No changes detected."
    assert report.to_dict()["total"] == 0
    d = json.loads(report.to_json())
    assert d["total"] == 0


def test_report_summary():
    old = [ProductData(external_id="A", name="A")]
    new = [ProductData(external_id="A", name="A"), ProductData(external_id="B", name="B")]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    assert report.added == 1
    assert report.removed == 0
    assert report.updated == 0


def test_severity_product_added_is_major():
    old = [ProductData(external_id="A", name="A")]
    new = [ProductData(external_id="A", name="A"), ProductData(external_id="B", name="B")]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    assert report.major == 1
    assert report.entries[0].severity == Severity.major


def test_severity_price_change_is_normal():
    old = [ProductData(external_id="A", name="A", price=10.0)]
    new = [ProductData(external_id="A", name="A", price=15.0)]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    assert report.normal == 1
    assert report.entries[0].severity == Severity.normal


def test_severity_image_removed_is_minor():
    old = [ProductData(
        external_id="A", name="A",
        images=[{"url": "https://ex.com/img.jpg"}],
    )]
    new = [ProductData(external_id="A", name="A")]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    assert report.minor >= 1
    image_removed = [e for e in report.entries if e.entry.change_type == ChangeType.image_removed]
    assert image_removed[0].severity == Severity.minor


def test_report_text_contains_expected():
    old = [ProductData(external_id="SKU-001", name="Old Name", price=10.0)]
    new = [ProductData(external_id="SKU-001", name="New Name", price=15.0)]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    text = report.to_text()
    assert "Product Updated" in text
    assert "Old Name" in text
    assert "Price" in text
    assert "→" in text


def test_report_json_structure():
    old = [ProductData(external_id="SKU-001", name="Old", price=10.0)]
    new = [ProductData(external_id="SKU-001", name="New", price=15.0)]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    d = report.to_dict()
    assert "summary" in d
    assert "entries" in d
    assert len(d["entries"]) == 1
    assert d["entries"][0]["severity"] == "normal"
    assert d["entries"][0]["type"] == "product_updated"
    assert d["entries"][0]["fields_changed"][0]["field"] == "name"


def test_report_json_serializable():
    old = [ProductData(external_id="SKU-001", name="Old", price=Decimal("10.00"))]
    new = [ProductData(external_id="SKU-001", name="New", price=Decimal("15.00"))]
    cs = diff_products(old, new)
    report = ChangeReport(cs)
    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed["total"] == 1
