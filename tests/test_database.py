from terpvault.storage.database import get_engine, Base


def test_database_initializes():
    engine = get_engine()
    assert engine is not None


def test_tables_created():
    from sqlalchemy import inspect
    engine = get_engine()
    insp = inspect(engine)
    tables = insp.get_table_names()
    assert isinstance(tables, list)
