import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from terpvault.domain.models import ProductData, SnapshotData
from terpvault.domain.changes import ChangeSet
from terpvault.storage.database import Base
from terpvault.storage.repository import SnapshotRepo, ChangeRepo
from terpvault.sync.differ import diff_products
from terpvault.sync.report import ChangeReport


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def test_change_repo_create(session):
    snap_repo = SnapshotRepo(session)
    snap1 = snap_repo.create(SnapshotData(
        supplier_slug="terpenes-uk", products=[ProductData(external_id="A", name="A")], product_count=1
    ))
    snap2 = snap_repo.create(SnapshotData(
        supplier_slug="terpenes-uk", products=[ProductData(external_id="A", name="A"), ProductData(external_id="B", name="B")], product_count=2
    ))
    session.flush()

    cs = diff_products(
        [ProductData(external_id="A", name="A")],
        [ProductData(external_id="A", name="A"), ProductData(external_id="B", name="B")],
    )
    cs.source_snapshot_id = snap1.id
    cs.target_snapshot_id = snap2.id
    report = ChangeReport(cs)

    repo = ChangeRepo(session)
    row = repo.create(
        supplier_slug="terpenes-uk",
        source_snapshot_id=snap1.id,
        target_snapshot_id=snap2.id,
        changes_json=cs.model_dump_json(),
        report_json=report.to_json(),
        report_text=report.to_text(),
        total_changes=report.total,
        major_count=report.major,
        normal_count=report.normal,
        minor_count=report.minor,
    )
    assert row.supplier_slug == "terpenes-uk"
    assert row.total_changes == 1
    assert row.major_count == 1
    assert row.source_snapshot_id == snap1.id
    assert row.target_snapshot_id == snap2.id


def test_change_repo_latest(session):
    snap_repo = SnapshotRepo(session)
    repo = ChangeRepo(session)

    snap1 = snap_repo.create(SnapshotData(supplier_slug="terpenes-uk", products=[], product_count=0))
    snap2 = snap_repo.create(SnapshotData(supplier_slug="terpenes-uk", products=[], product_count=0))
    snap3 = snap_repo.create(SnapshotData(supplier_slug="terpenes-uk", products=[], product_count=0))
    session.flush()

    for s, t in [(snap1, snap2), (snap2, snap3)]:
        cs = ChangeSet(source_snapshot_id=s.id, target_snapshot_id=t.id)
        report = ChangeReport(cs)
        repo.create(
            supplier_slug="terpenes-uk",
            source_snapshot_id=s.id,
            target_snapshot_id=t.id,
            changes_json=cs.model_dump_json(),
            report_json=report.to_json(),
            report_text=report.to_text(),
            total_changes=0, major_count=0, normal_count=0, minor_count=0,
        )

    latest = repo.latest_by_supplier("terpenes-uk")
    assert latest is not None
    assert latest.target_snapshot_id == snap3.id
    assert repo.count_by_supplier("terpenes-uk") == 2
    assert repo.count_by_supplier("other") == 0


def test_snapshots_not_deleted_when_report_exists(session):
    """Referential integrity prevents deleting a snapshot that has change_sets referencing it."""
    snap_repo = SnapshotRepo(session)
    change_repo = ChangeRepo(session)

    snap1 = snap_repo.create(SnapshotData(supplier_slug="test", products=[], product_count=0))
    snap2 = snap_repo.create(SnapshotData(supplier_slug="test", products=[], product_count=0))
    session.flush()

    cs = ChangeSet(source_snapshot_id=snap1.id, target_snapshot_id=snap2.id)
    report = ChangeReport(cs)
    change_repo.create(
        supplier_slug="test",
        source_snapshot_id=snap1.id,
        target_snapshot_id=snap2.id,
        changes_json=cs.model_dump_json(),
        report_json=report.to_json(),
        report_text=report.to_text(),
        total_changes=0, major_count=0, normal_count=0, minor_count=0,
    )
    session.flush()

    from sqlalchemy import text
    result = session.execute(text("SELECT COUNT(*) FROM change_sets")).scalar()
    assert result == 1
