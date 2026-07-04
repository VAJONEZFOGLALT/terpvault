from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from terpvault.domain.catalog_document import CatalogDocument
from terpvault.config.supplier_config import SupplierConfig


@dataclass(frozen=True)
class BuildContext:
    snapshot_id: str
    catalog_version: int
    supplier_config: SupplierConfig
    template_name: str = "wholesale-premium"
    output_dir: Path = Path("data/catalogs")
    build_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    git_commit: Optional[str] = None
    edition: str = "print"  # "digital" or "print"


@dataclass(frozen=True)
class Artifact:
    path: Path
    artifact_type: str
    checksum: str
    size_bytes: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ArtifactGenerator(ABC):
    @abstractmethod
    def generate(self, document: CatalogDocument, context: BuildContext) -> Artifact:
        ...
