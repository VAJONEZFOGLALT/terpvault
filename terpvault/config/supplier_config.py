from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
import yaml


class SupplierConfig(BaseModel):
    slug: str
    name: str
    importer_module: str
    client_type: str = "shopify"
    base_url: str = ""
    rate_limit_per_second: int = 10
    retry_max: int = 3

    branding: dict = Field(default_factory=lambda: {
        "primary_color": "#000000",
        "secondary_color": "#ffffff",
        "font_heading": "Inter",
        "font_body": "Inter",
    })

    @classmethod
    def load(cls, slug: str) -> "SupplierConfig":
        from terpvault.config.settings import settings
        path = settings.config_dir / f"{slug}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Supplier config not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
