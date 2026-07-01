from pathlib import Path

from terpvault.domain.catalog_document import CatalogDocument
from terpvault.generate.artifacts.base import ArtifactGenerator, Artifact, BuildContext


class PlaywrightPDFGenerator(ArtifactGenerator):
    def generate(self, document: CatalogDocument, context: BuildContext) -> Artifact:
        output_path = context.output_dir / context.supplier_config.slug / f"catalog-{context.catalog_version}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._render_html(document, context)
        pdf_bytes = self._to_pdf(html)
        output_path.write_bytes(pdf_bytes)

        return Artifact(
            path=output_path,
            artifact_type="pdf",
            checksum=self._checksum(pdf_bytes),
            size_bytes=len(pdf_bytes),
        )

    @staticmethod
    def _checksum(data: bytes) -> str:
        import hashlib
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _render_html(doc: CatalogDocument, context: BuildContext) -> str:
        from jinja2 import Environment, FileSystemLoader
        template_dir = Path(__file__).resolve().parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("catalog_pdf.html")
        return template.render(
            doc=doc,
            supplier=context.supplier_config,
            version=context.catalog_version,
        )

    @staticmethod
    def _to_pdf(html: str) -> bytes:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "2cm", "bottom": "2cm", "left": "1.8cm", "right": "1.8cm"},
            )
            browser.close()
            return pdf_bytes
