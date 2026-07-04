from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    database_url: str = f"sqlite:///{project_root}/data/db/terpvault.sqlite"
    data_dir: Path = project_root / "data"
    images_dir: Path = data_dir / "images"
    catalogs_dir: Path = data_dir / "catalogs"
    prod_dir: Path = project_root / "prod"
    config_dir: Path = project_root / "terpvault" / "config" / "suppliers"
    version_file: Path = project_root / "VERSION"
    log_level: str = "INFO"

    @property
    def version(self) -> str:
        try:
            return self.version_file.read_text(encoding="utf-8").strip()
        except (OSError, IOError):
            return "unknown"

    model_config = {"env_prefix": "TERPVAULT_"}


settings = Settings()
