import pytest
from pathlib import Path
from terpvault.domain.catalog_document import CatalogDocument, CatalogProduct, CatalogStats, CoverInfo, SectionInfo, SectionType, TocEntry
from terpvault.config.supplier_config import SupplierConfig
from terpvault.generate.artifacts.base import BuildContext, ArtifactGenerator
from terpvault.generate.artifacts.html import HTMLGenerator


def _make_doc() -> CatalogDocument:
    return CatalogDocument(
        supplier_slug="terpenes-uk",
        cover=CoverInfo(supplier_name="Terpenes UK", catalog_label="June 2026", product_count=2, brand_count=1),
        toc=[
            TocEntry(label="Citrus", section_index=0),
            TocEntry(label="Herbal", section_index=1),
        ],
        sections=[
            SectionInfo(index=0, label="Citrus", type=SectionType.collection, product_ids=["P1", "P2"]),
            SectionInfo(index=1, label="Herbal", type=SectionType.collection, product_ids=["P3"]),
        ],
        products={
            "P1": CatalogProduct(external_id="P1", name="Limonene", brand="Terpenes UK", price=14.99, unit="ml", size="10ml", images=[{"url": "https://via.placeholder.com/300", "position": 0}]),
            "P2": CatalogProduct(external_id="P2", name="Orange Terpene", brand="Terpenes UK", price=12.99, variants=[{"sku": "ORA-10ML", "price": 12.99}], images=[]),
            "P3": CatalogProduct(external_id="P3", name="Myrcene", brand="Terpenes UK", price=13.99, compare_at_price=16.99, images=[{"url": "https://via.placeholder.com/300", "position": 0}]),
        },
        stats=CatalogStats(product_count=3, brand_count=1, section_count=2, variant_count=3, image_count=2),
    )


def _make_context(tmp_path: Path) -> BuildContext:
    config = SupplierConfig(
        slug="terpenes-uk",
        name="Terpenes UK",
        importer_module="terpvault.sync.importer.terpenes_uk.TerpenesUKImporter",
        base_url="https://terpenesuk.com",
        branding={"primary_color": "#2C5F2D", "secondary_color": "#97BC62", "font_heading": "Helvetica", "font_body": "Helvetica"},
    )
    return BuildContext(
        snapshot_id="test-snap",
        catalog_version=1,
        supplier_config=config,
        output_dir=tmp_path,
    )


def test_html_generator_is_artifact_generator():
    gen = HTMLGenerator()
    assert isinstance(gen, ArtifactGenerator)


def test_html_generates_without_error(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    assert artifact.path.exists()
    assert artifact.artifact_type == "html"
    assert artifact.size_bytes > 0
    assert len(artifact.checksum) == 64


def test_html_contains_all_products(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    html = artifact.path.read_text(encoding="utf-8")
    assert "Limonene" in html
    assert "Orange Terpene" in html
    assert "Myrcene" in html


def test_html_contains_supplier_name(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    html = artifact.path.read_text(encoding="utf-8")
    assert "Terpenes UK" in html


def test_html_contains_all_sections(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    html = artifact.path.read_text(encoding="utf-8")
    assert "Citrus" in html
    assert "Herbal" in html


def test_html_output_is_index_html(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    assert artifact.path.name == "index.html"


def test_html_output_path_contains_supplier(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    assert "terpenes-uk" in str(artifact.path)


def test_html_does_not_modify_document(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    original_json = doc.model_dump_json()
    gen = HTMLGenerator()
    gen.generate(doc, context)
    assert doc.model_dump_json() == original_json


def test_html_does_not_modify_context(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    gen.generate(doc, context)
    assert context.supplier_config.slug == "terpenes-uk"
    assert context.catalog_version == 1


def test_html_product_count_matches(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    artifact = gen.generate(doc, context)
    html = artifact.path.read_text(encoding="utf-8")
    assert "3 products" in html


def test_html_shares_template_structure(tmp_path):
    doc = _make_doc()
    context = _make_context(tmp_path)
    gen = HTMLGenerator()
    html = gen._render_html(doc, context)
    assert "<!DOCTYPE html>" in html
    assert "product-card" in html
    assert "{{" not in html
