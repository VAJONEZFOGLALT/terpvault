from pathlib import Path
from shutil import copy2

from terpvault.domain.catalog_document import CatalogDocument
from terpvault.generate.artifacts.base import ArtifactGenerator, Artifact, BuildContext


class HTMLGenerator(ArtifactGenerator):
    def generate(self, document: CatalogDocument, context: BuildContext) -> Artifact:
        output_dir = context.output_dir / context.supplier_config.slug
        output_dir.mkdir(parents=True, exist_ok=True)
        index_path = output_dir / "index.html"

        html = self._render_html(document, context)
        index_path.write_text(html, encoding="utf-8")

        return Artifact(
            path=index_path,
            artifact_type="html",
            checksum=self._checksum(html.encode("utf-8")),
            size_bytes=len(html.encode("utf-8")),
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
        template = env.get_template("catalog_html.html")
        return template.render(
            doc=doc,
            supplier=context.supplier_config,
            version=context.catalog_version,
        )
