from terpvault.storage.database import get_engine
from sqlalchemy import inspect


def test_database_initializes():
    engine = get_engine()
    assert engine is not None


def test_tables_created():
    engine = get_engine()
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    expected = {"suppliers", "products", "variants", "images", "snapshots", "change_sets"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
