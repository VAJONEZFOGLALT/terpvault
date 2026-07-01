import pytest
from pathlib import Path
from terpvault.domain.catalog_document import CatalogDocument, CatalogProduct, CatalogStats, CoverInfo, SectionInfo, SectionType, TocEntry
from terpvault.config.supplier_config import SupplierConfig
from terpvault.generate.artifacts.base import BuildContext, ArtifactGenerator, Artifact
from terpvault.generate.artifacts.pdf import PDFGenerator


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
            "P1": CatalogProduct(
                external_id="P1", name="Limonene", brand="Terpenes UK",
                description="Premium Limonene terpene.", price=14.99, unit="ml", size="10ml",
                variants=[{"sku": "LIM-10ML", "price": 14.99}],
                images=[{"url": "https://via.placeholder.com/300", "position": 0, "alt_text": ""}],
            ),
            "P2": CatalogProduct(
                external_id="P2", name="Orange Terpene", brand="Terpenes UK",
                description="Sweet orange profile.", price=12.99, unit="ml", size="10ml",
                variants=[{"sku": "ORA-10ML", "price": 12.99}],
                images=[],
            ),
            "P3": CatalogProduct(
                external_id="P3", name="Myrcene", brand="Terpenes UK",
                description="Earthy notes.", price=13.99, unit="ml", size="10ml",
                compare_at_price=16.99,
                variants=[{"sku": "MYR-10ML", "price": 13.99}],
                images=[{"url": "https://via.placeholder.com/300", "position": 0, "alt_text": ""}],
            ),
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


def test_pdf_generator_is_artifact_generator():
    gen = PDFGenerator()
    assert isinstance(gen, ArtifactGenerator)


def test_pdf_renders_html_without_error():
    doc = _make_doc()
    context = _make_context(Path("/tmp"))
    html = PDFGenerator._render_html(doc, context)
    assert "<html" in html
    assert "Limonene" in html
    assert "Terpenes UK" in html
    assert "14.99" in html


def test_pdf_checksum_is_sha256():
    data = b"test data"
    checksum = PDFGenerator._checksum(data)
    assert len(checksum) == 64
    assert checksum == PDFGenerator._checksum(data)


def test_pdf_generator_produces_artifact(tmp_path, monkeypatch):
    doc = _make_doc()
    context = _make_context(tmp_path)

    monkeypatch.setattr(PDFGenerator, "_to_pdf", lambda self, html: b"fake pdf content")
    gen = PDFGenerator()
    artifact = gen.generate(doc, context)
    assert artifact.path.exists()
    assert artifact.artifact_type == "pdf"
    assert artifact.size_bytes == 16
    assert len(artifact.checksum) == 64


def test_pdf_does_not_modify_document(tmp_path, monkeypatch):
    doc = _make_doc()
    context = _make_context(tmp_path)
    original_json = doc.model_dump_json()
    monkeypatch.setattr(PDFGenerator, "_to_pdf", lambda self, html: b"fake")
    gen = PDFGenerator()
    gen.generate(doc, context)
    assert doc.model_dump_json() == original_json


def test_pdf_does_not_modify_context(tmp_path, monkeypatch):
    doc = _make_doc()
    context = _make_context(tmp_path)
    monkeypatch.setattr(PDFGenerator, "_to_pdf", lambda self, html: b"fake")
    gen = PDFGenerator()
    gen.generate(doc, context)
    assert context.supplier_config.slug == "terpenes-uk"
    assert context.catalog_version == 1


def test_pdf_output_path_format(tmp_path, monkeypatch):
    doc = _make_doc()
    context = _make_context(tmp_path)
    monkeypatch.setattr(PDFGenerator, "_to_pdf", lambda self, html: b"fake")
    gen = PDFGenerator()
    artifact = gen.generate(doc, context)
    assert "terpenes-uk" in str(artifact.path)
    assert "catalog-1.pdf" in str(artifact.path.name)
