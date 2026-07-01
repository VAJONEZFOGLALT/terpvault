from enum import Enum

from terpvault.domain.changes import ChangeSet, ChangeType, ChangeEntry


class Severity(str, Enum):
    minor = "minor"
    normal = "normal"
    major = "major"


_CHANGE_TYPE_SEVERITY: dict[ChangeType, Severity] = {
    ChangeType.product_added: Severity.major,
    ChangeType.product_removed: Severity.major,
    ChangeType.product_updated: Severity.normal,
    ChangeType.variant_added: Severity.normal,
    ChangeType.variant_removed: Severity.normal,
    ChangeType.variant_updated: Severity.minor,
    ChangeType.image_added: Severity.minor,
    ChangeType.image_removed: Severity.minor,
    ChangeType.image_updated: Severity.minor,
}

_CHANGE_TYPE_LABEL: dict[ChangeType, str] = {
    ChangeType.product_added: "Product Added",
    ChangeType.product_removed: "Product Removed",
    ChangeType.product_updated: "Product Updated",
    ChangeType.variant_added: "Variant Added",
    ChangeType.variant_removed: "Variant Removed",
    ChangeType.variant_updated: "Variant Updated",
    ChangeType.image_added: "Image Added",
    ChangeType.image_removed: "Image Removed",
    ChangeType.image_updated: "Image Updated",
}


class ReportEntry:
    def __init__(self, entry: ChangeEntry):
        self.entry = entry
        self.severity = _CHANGE_TYPE_SEVERITY[entry.change_type]
        self.label = _CHANGE_TYPE_LABEL[entry.change_type]

    def to_text(self) -> str:
        lines: list[str] = []
        prefix = _severity_prefix(self.severity)
        lines.append(f"{prefix} {self.label}: {self.entry.product_name} ({self.entry.product_external_id})")

        for fc in self.entry.fields_changed:
            ov = _format_value(fc.old_value)
            nv = _format_value(fc.new_value)
            lines.append(f"       {_field_label(fc.field)}: {ov} → {nv}")

        if self.entry.old_values and not self.entry.fields_changed:
            for key, val in self.entry.old_values.items():
                lines.append(f"       {key}: {_format_value(val)} (removed)")

        if self.entry.new_values and not self.entry.fields_changed:
            for key, val in self.entry.new_values.items():
                lines.append(f"       {key}: {_format_value(val)} (added)")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "type": self.entry.change_type,
            "product_external_id": self.entry.product_external_id,
            "product_name": self.entry.product_name,
            "fields_changed": [
                {"field": fc.field, "old_value": fc.old_value, "new_value": fc.new_value}
                for fc in self.entry.fields_changed
            ],
            "old_values": self.entry.old_values,
            "new_values": self.entry.new_values,
        }


class ChangeReport:
    def __init__(self, change_set: ChangeSet):
        self.entries = [ReportEntry(e) for e in change_set.entries]
        self.total = len(self.entries)
        self.added = sum(1 for e in self.entries if e.entry.change_type == ChangeType.product_added)
        self.removed = sum(1 for e in self.entries if e.entry.change_type == ChangeType.product_removed)
        self.updated = sum(1 for e in self.entries if e.entry.change_type == ChangeType.product_updated)
        self.major = sum(1 for e in self.entries if e.severity == Severity.major)
        self.normal = sum(1 for e in self.entries if e.severity == Severity.normal)
        self.minor = sum(1 for e in self.entries if e.severity == Severity.minor)

    def to_text(self) -> str:
        if self.total == 0:
            return "No changes detected."

        parts = [f"Changes: {self.total} total ({self.major} major, {self.normal} normal, {self.minor} minor)"]
        if self.added:
            parts.append(f"  Added:   {self.added}")
        if self.removed:
            parts.append(f"  Removed: {self.removed}")
        if self.updated:
            parts.append(f"  Updated: {self.updated}")
        parts.append("")

        for entry in self.entries:
            parts.append(entry.to_text())
            parts.append("")

        return "\n".join(parts).rstrip()

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "summary": {
                "added": self.added,
                "removed": self.removed,
                "updated": self.updated,
                "major": self.major,
                "normal": self.normal,
                "minor": self.minor,
            },
            "entries": [e.to_dict() for e in self.entries],
        }


def _severity_prefix(severity: Severity) -> str:
    return {"minor": "[~]", "normal": "[*]", "major": "[!]"}.get(severity, "[·]")


def _field_label(field: str) -> str:
    labels = {
        "name": "Name",
        "description": "Description",
        "brand": "Brand",
        "category": "Category",
        "collection": "Collection",
        "available": "Available",
        "price": "Price",
        "compare_at_price": "Compare at Price",
        "unit": "Unit",
        "size": "Size",
    }
    return labels.get(field, field)


def _format_value(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, bool):
        return "yes" if val else "no"
    if isinstance(val, float):
        return f"£{val:.2f}" if val else f"{val}"
    return str(val)
