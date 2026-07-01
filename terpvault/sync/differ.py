import json
from typing import Any

from terpvault.domain.changes import ChangeSet, ChangeEntry, ChangeType, FieldChange
from terpvault.domain.models import ProductData


def _product_key(p: ProductData) -> str:
    return p.external_id


def _normalize_price(v: Any) -> Any:
    if v is None:
        return None
    return round(float(v), 2)


def _compare_fields(old: ProductData, new: ProductData) -> list[FieldChange]:
    changes = []
    scalar_fields = [
        ("name", str, None),
        ("description", str, None),
        ("brand", str, None),
        ("category", str, None),
        ("collection", str, None),
        ("available", bool, None),
        ("unit", str, None),
        ("size", str, None),
    ]
    for field_name, _, _ in scalar_fields:
        ov = getattr(old, field_name)
        nv = getattr(new, field_name)
        if ov != nv:
            changes.append(FieldChange(field=field_name, old_value=ov, new_value=nv))

    op = _normalize_price(old.price)
    np = _normalize_price(new.price)
    if op != np:
        changes.append(FieldChange(field="price", old_value=op, new_value=np))

    ocap = _normalize_price(old.compare_at_price)
    ncap = _normalize_price(new.compare_at_price)
    if ocap != ncap:
        changes.append(FieldChange(field="compare_at_price", old_value=ocap, new_value=ncap))

    return changes


def _compare_variants(old: ProductData, new: ProductData) -> list[ChangeEntry]:
    entries = []
    old_by_sku = {v["sku"]: v for v in old.variants}
    new_by_sku = {v["sku"]: v for v in new.variants}

    old_skus = set(old_by_sku.keys())
    new_skus = set(new_by_sku.keys())

    for sku in new_skus - old_skus:
        v = new_by_sku[sku]
        entries.append(ChangeEntry(
            change_type=ChangeType.variant_added,
            product_external_id=new.external_id,
            product_name=new.name,
            new_values={"sku": sku, "price": v.get("price"), "available": v.get("available")},
        ))

    for sku in old_skus - new_skus:
        v = old_by_sku[sku]
        entries.append(ChangeEntry(
            change_type=ChangeType.variant_removed,
            product_external_id=old.external_id,
            product_name=old.name,
            old_values={"sku": sku, "price": v.get("price"), "available": v.get("available")},
        ))

    for sku in old_skus & new_skus:
        ov = old_by_sku[sku]
        nv = new_by_sku[sku]
        fields = []
        for f in ("price", "available"):
            if ov.get(f) != nv.get(f):
                fields.append(FieldChange(field=f, old_value=ov.get(f), new_value=nv.get(f)))
        if fields:
            entries.append(ChangeEntry(
                change_type=ChangeType.variant_updated,
                product_external_id=new.external_id,
                product_name=new.name,
                fields_changed=fields,
                old_values={f.field: f.old_value for f in fields},
                new_values={f.field: f.new_value for f in fields},
            ))

    return entries


def _compare_images(old: ProductData, new: ProductData) -> list[ChangeEntry]:
    entries = []
    old_by_url = {img.url: img for img in old.images}
    new_by_url = {img.url: img for img in new.images}

    old_urls = set(old_by_url.keys())
    new_urls = set(new_by_url.keys())

    for url in new_urls - old_urls:
        entries.append(ChangeEntry(
            change_type=ChangeType.image_added,
            product_external_id=new.external_id,
            product_name=new.name,
            new_values={"url": url},
        ))

    for url in old_urls - new_urls:
        entries.append(ChangeEntry(
            change_type=ChangeType.image_removed,
            product_external_id=old.external_id,
            product_name=old.name,
            old_values={"url": url},
        ))

    for url in old_urls & new_urls:
        oi = old_by_url[url]
        ni = new_by_url[url]
        fields = []
        if oi.alt_text != ni.alt_text:
            fields.append(FieldChange(field="alt_text", old_value=oi.alt_text, new_value=ni.alt_text))
        if oi.position != ni.position:
            fields.append(FieldChange(field="position", old_value=oi.position, new_value=ni.position))
        if fields:
            entries.append(ChangeEntry(
                change_type=ChangeType.image_updated,
                product_external_id=new.external_id,
                product_name=new.name,
                fields_changed=fields,
                old_values={f.field: f.old_value for f in fields},
                new_values={f.field: f.new_value for f in fields},
            ))

    return entries


def diff_products(old_products: list[ProductData], new_products: list[ProductData]) -> ChangeSet:
    old_by_id = {_product_key(p): p for p in old_products}
    new_by_id = {_product_key(p): p for p in new_products}

    old_ids = set(old_by_id.keys())
    new_ids = set(new_by_id.keys())

    entries: list[ChangeEntry] = []

    for pid in sorted(new_ids - old_ids):
        p = new_by_id[pid]
        entries.append(ChangeEntry(
            change_type=ChangeType.product_added,
            product_external_id=pid,
            product_name=p.name,
            new_values={"name": p.name, "price": p.price},
        ))

    for pid in sorted(old_ids - new_ids):
        p = old_by_id[pid]
        entries.append(ChangeEntry(
            change_type=ChangeType.product_removed,
            product_external_id=pid,
            product_name=p.name,
            old_values={"name": p.name, "price": p.price},
        ))

    for pid in sorted(old_ids & new_ids):
        old_p = old_by_id[pid]
        new_p = new_by_id[pid]

        field_changes = _compare_fields(old_p, new_p)
        variant_entries = _compare_variants(old_p, new_p)
        image_entries = _compare_images(old_p, new_p)

        if field_changes or variant_entries or image_entries:
            entry = ChangeEntry(
                change_type=ChangeType.product_updated,
                product_external_id=pid,
                product_name=new_p.name,
                fields_changed=field_changes,
                old_values={f.field: f.old_value for f in field_changes},
                new_values={f.field: f.new_value for f in field_changes},
            )
            entries.append(entry)

        entries.extend(variant_entries)
        entries.extend(image_entries)

    return ChangeSet(entries=entries)


def diff_snapshot_products(snapshot_a_json: str, snapshot_b_json: str) -> ChangeSet:
    old_data = json.loads(snapshot_a_json)
    new_data = json.loads(snapshot_b_json)
    old_products = [ProductData(**p) for p in old_data]
    new_products = [ProductData(**p) for p in new_data]
    return diff_products(old_products, new_products)
