import pytest
from terpvault.config.supplier_config import SupplierConfig


def test_load_terpenes_uk_config():
    config = SupplierConfig.load("terpenes-uk")
    assert config.slug == "terpenes-uk"
    assert config.name == "Terpenes UK"
    assert config.base_url == "https://terpenes-uk.co.uk"
    assert config.rate_limit_per_second == 2
    assert config.retry_max == 3
    assert config.branding["primary_color"] == "#2C5F2D"


def test_load_nonexistent_config_raises():
    with pytest.raises(FileNotFoundError):
        SupplierConfig.load("nonexistent-supplier")
