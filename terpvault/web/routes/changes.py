import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from terpvault.storage.database import get_session
from terpvault.storage.tables import SnapshotRow

router = APIRouter()


@router.get("/catalogs/{slug}/recent-changes")
def recent_changes(slug: str):
    session = get_session()
    snaps = session.query(SnapshotRow).filter_by(
        supplier_slug=slug
    ).order_by(SnapshotRow.created_at.desc()).limit(2).all()

    if len(snaps) < 2:
        session.close()
        return JSONResponse({"changes": [], "has_changes": False})

    current = json.loads(snaps[0].products)
    previous = json.loads(snaps[1].products)

    current_names = {p["external_id"]: p for p in current}
    previous_names = {p["external_id"]: p for p in previous}

    current_ids = set(current_names.keys())
    previous_ids = set(previous_names.keys())

    added = [current_names[i]["name"] for i in (current_ids - previous_ids)]
    removed = [previous_names[i]["name"] for i in (previous_ids - current_ids)]

    updated = []
    for pid in current_ids & previous_ids:
        cp = current_names[pid]
        pp = previous_names[pid]
        if cp.get("price") != pp.get("price"):
            updated.append({
                "name": cp["name"],
                "field": "price",
                "old": pp.get("price"),
                "new": cp.get("price"),
            })
        elif cp.get("name") != pp.get("name"):
            updated.append({
                "name": cp["name"],
                "field": "name",
                "old": pp.get("name"),
                "new": cp.get("name"),
            })

    changes = {
        "added": len(added),
        "removed": len(removed),
        "updated": len(updated),
        "added_names": added[:5],
        "updated_details": updated[:5],
        "has_changes": len(added) + len(removed) + len(updated) > 0,
        "snapshot_id": snaps[0].id[:8],
        "previous_snapshot_id": snaps[1].id[:8],
    }
    session.close()
    return JSONResponse(changes)
