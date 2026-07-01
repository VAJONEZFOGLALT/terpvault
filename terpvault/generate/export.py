from pathlib import Path

from terpvault.domain.catalog_document import CatalogDocument


def export_json(doc: CatalogDocument, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_str = doc.model_dump_json(indent=2)
    output_path.write_text(json_str, encoding="utf-8")
    return output_path
