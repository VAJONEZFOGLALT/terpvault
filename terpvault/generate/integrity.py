from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from terpvault.domain.catalog_document import CatalogDocument


class Severity(str, Enum):
    error = "error"
    warning = "warning"


class IntegrityIssue(BaseModel):
    severity: Severity
    category: str
    message: str
    location: Optional[str] = None


class IntegrityResult(BaseModel):
    issues: list[IntegrityIssue] = Field(default_factory=list)

    @property
    def errors(self) -> list[IntegrityIssue]:
        return [i for i in self.issues if i.severity == Severity.error]

    @property
    def warnings(self) -> list[IntegrityIssue]:
        return [i for i in self.issues if i.severity == Severity.warning]

    @property
    def is_ready(self) -> bool:
        return len(self.errors) == 0

    @property
    def can_publish(self) -> bool:
        return self.is_ready

    def summary(self) -> str:
        parts = [f"Errors: {len(self.errors)}", f"Warnings: {len(self.warnings)}"]
        if self.is_ready:
            parts.append("Ready to publish")
        else:
            parts.append("Cannot publish")
        return "\n".join(parts)


def check_catalog(doc: CatalogDocument) -> IntegrityResult:
    result = IntegrityResult()
    _check_structural(doc, result)
    _check_statistical(doc, result)
    _check_serialization(doc, result)
    _check_publishing(doc, result)
    return result


def _check_structural(doc: CatalogDocument, result: IntegrityResult):
    product_ids = set(doc.products.keys())

    for section in doc.sections:
        for pid in section.product_ids:
            if pid not in product_ids:
                result.issues.append(IntegrityIssue(
                    severity=Severity.error,
                    category="structural",
                    message=f"Section '{section.label}' references missing product '{pid}'",
                    location=f"sections[{section.index}]",
                ))
            else:
                dup_count = section.product_ids.count(pid)
                if dup_count > 1:
                    result.issues.append(IntegrityIssue(
                        severity=Severity.warning,
                        category="structural",
                        message=f"Section '{section.label}' contains duplicate reference to product '{pid}' ({dup_count}x)",
                        location=f"sections[{section.index}]",
                    ))

    all_referenced_product_ids = set()
    for s in doc.sections:
        all_referenced_product_ids.update(s.product_ids)
    for pid in product_ids:
        if pid not in all_referenced_product_ids:
            result.issues.append(IntegrityIssue(
                severity=Severity.warning,
                category="structural",
                message=f"Product '{doc.products[pid].name}' ({pid}) is not referenced by any section",
                location=f"products['{pid}']",
            ))

    for te in doc.toc:
        matching_sections = [s for s in doc.sections if s.index == te.section_index]
        if not matching_sections:
            result.issues.append(IntegrityIssue(
                severity=Severity.error,
                category="structural",
                message=f"TOC entry '{te.label}' references section index {te.section_index} which does not exist",
                location=f"toc[{te.section_index}]",
            ))

    seen_section_indexes = set()
    for s in doc.sections:
        if s.index in seen_section_indexes:
            result.issues.append(IntegrityIssue(
                severity=Severity.error,
                category="structural",
                message=f"Duplicate section index {s.index}",
                location=f"sections[{s.index}]",
            ))
        seen_section_indexes.add(s.index)


def _check_statistical(doc: CatalogDocument, result: IntegrityResult):
    s = doc.stats
    actual_product_count = len(doc.products)
    if s.product_count != actual_product_count:
        result.issues.append(IntegrityIssue(
            severity=Severity.error,
            category="statistical",
            message=f"stats.product_count ({s.product_count}) != actual product count ({actual_product_count})",
            location="stats.product_count",
        ))

    actual_section_count = len(doc.sections)
    if s.section_count != actual_section_count:
        result.issues.append(IntegrityIssue(
            severity=Severity.error,
            category="statistical",
            message=f"stats.section_count ({s.section_count}) != actual section count ({actual_section_count})",
            location="stats.section_count",
        ))

    actual_brands = {p.brand for p in doc.products.values() if p.brand}
    if s.brand_count != len(actual_brands):
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="statistical",
            message=f"stats.brand_count ({s.brand_count}) != actual brand count ({len(actual_brands)})",
            location="stats.brand_count",
        ))

    actual_variants = sum(len(p.variants) for p in doc.products.values())
    if s.variant_count != actual_variants:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="statistical",
            message=f"stats.variant_count ({s.variant_count}) != actual variant count ({actual_variants})",
            location="stats.variant_count",
        ))

    actual_images = sum(len(p.images) for p in doc.products.values())
    if s.image_count != actual_images:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="statistical",
            message=f"stats.image_count ({s.image_count}) != actual image count ({actual_images})",
            location="stats.image_count",
        ))


def _check_serialization(doc: CatalogDocument, result: IntegrityResult):
    try:
        json_str = doc.model_dump_json()
        restored = CatalogDocument.model_validate_json(json_str)
        if restored != doc:
            result.issues.append(IntegrityIssue(
                severity=Severity.error,
                category="serialization",
                message="CatalogDocument does not survive round-trip JSON serialization",
            ))
    except Exception as e:
        result.issues.append(IntegrityIssue(
            severity=Severity.error,
            category="serialization",
            message=f"CatalogDocument serialization failed: {e}",
        ))


def _check_publishing(doc: CatalogDocument, result: IntegrityResult):
    if not doc.cover.supplier_name:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="publishing",
            message="Cover has no supplier name",
            location="cover.supplier_name",
        ))

    if not doc.cover.catalog_label:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="publishing",
            message="Cover has no catalog label",
            location="cover.catalog_label",
        ))

    if not doc.toc:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="publishing",
            message="No table of contents entries",
            location="toc",
        ))

    if not doc.sections:
        result.issues.append(IntegrityIssue(
            severity=Severity.warning,
            category="publishing",
            message="No sections in document",
            location="sections",
        ))

    for pid, p in doc.products.items():
        if not p.name:
            result.issues.append(IntegrityIssue(
                severity=Severity.error,
                category="publishing",
                message=f"Product '{pid}' has no name",
                location=f"products['{pid}'].name",
            ))

    for s in doc.sections:
        if not s.label:
            result.issues.append(IntegrityIssue(
                severity=Severity.error,
                category="publishing",
                message=f"Section at index {s.index} has no label",
                location=f"sections[{s.index}].label",
            ))

    for pid, p in doc.products.items():
        if p.price is None and p.available:
            result.issues.append(IntegrityIssue(
                severity=Severity.warning,
                category="publishing",
                message=f"Product '{p.name}' ({pid}) is available but has no price",
                location=f"products['{pid}'].price",
            ))
