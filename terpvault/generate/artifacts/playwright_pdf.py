from pathlib import Path

from terpvault.domain.catalog_document import CatalogDocument
from terpvault.generate.artifacts.base import ArtifactGenerator, Artifact, BuildContext


class PlaywrightPDFGenerator(ArtifactGenerator):
    def generate(self, document: CatalogDocument, context: BuildContext) -> Artifact:
        suffix = f"-{context.edition}" if context.edition == "digital" else ""
        filename = f"catalog{suffix}-{context.catalog_version}.pdf"
        output_path = context.output_dir / context.supplier_config.slug / filename
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
    def generate_both(
        document: CatalogDocument,
        context: BuildContext,
    ) -> tuple[Artifact, Artifact]:
        html = PlaywrightPDFGenerator._render_html(document, context)
        pdf_bytes = PlaywrightPDFGenerator._to_pdf(html)

        base_dir = context.output_dir / context.supplier_config.slug
        base_dir.mkdir(parents=True, exist_ok=True)

        version = context.catalog_version
        print_path = base_dir / f"catalog-{version}.pdf"
        print_path.write_bytes(pdf_bytes)
        print_artifact = Artifact(
            path=print_path,
            artifact_type="pdf",
            checksum=PlaywrightPDFGenerator._checksum(pdf_bytes),
            size_bytes=len(pdf_bytes),
        )

        digital_bytes = PlaywrightPDFGenerator._compress_digital(pdf_bytes)
        digital_path = base_dir / f"catalog-digital-{version}.pdf"
        digital_path.write_bytes(digital_bytes)
        digital_artifact = Artifact(
            path=digital_path,
            artifact_type="pdf",
            checksum=PlaywrightPDFGenerator._checksum(digital_bytes),
            size_bytes=len(digital_bytes),
        )

        return print_artifact, digital_artifact

    @staticmethod
    def _compress_digital(pdf_bytes: bytes, max_dim: int = 600) -> bytes:
        from io import BytesIO
        from pypdf import PdfReader, PdfWriter
        from PIL import Image
        reader = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            for img in page.images:
                pil_img = img.image
                w, h = pil_img.size
                if max(w, h) <= max_dim:
                    continue
                scale = max_dim / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                resized = pil_img.resize((new_w, new_h), Image.LANCZOS)
                if resized.mode == "RGBA":
                    white = Image.new("RGB", resized.size, (255, 255, 255))
                    white.paste(resized, mask=resized.split()[3])
                    resized = white
                img.replace(resized, quality=75)
        buf = BytesIO()
        writer.write(buf)
        return buf.getvalue()

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
                margin={"top": "1.5cm", "bottom": "1.8cm", "left": "1.4cm", "right": "1.4cm"},
                scale=1.0,
            )
            browser.close()
            return pdf_bytes
