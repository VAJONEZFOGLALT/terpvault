from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    database_url: str = f"sqlite:///{project_root}/data/db/terpvault.sqlite"
    data_dir: Path = project_root / "data"
    images_dir: Path = data_dir / "images"
    catalogs_dir: Path = data_dir / "catalogs"
    config_dir: Path = project_root / "terpvault" / "config" / "suppliers"
    log_level: str = "INFO"

    model_config = {"env_prefix": "TERPVAULT_"}


settings = Settings()
