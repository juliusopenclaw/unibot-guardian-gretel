from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .public_safety import scan_text


MATERIAL_MANIFEST_SCHEMA_VERSION = "unibot-course-material-manifest-v1"
PRIVATE_MATERIAL_ROOT = Path("knowledge") / ("private_course" + "_materials")

ALLOWED_SOURCE_KINDS = {
    "slide_pdf",
    "slide_deck",
    "notebook",
    "python_file",
    "data_file",
    "document",
    "course_manifest",
    "video_file",
    "video_caption",
    "transcript",
    "exercise_sheet",
    "official_doc",
    "synthetic_demo",
    "other_staged",
}
ALLOWED_PERMISSION_STATUS = {
    "unknown",
    "private_course_use_only",
    "owned_or_authorized",
    "public_link_only",
    "synthetic",
}
ALLOWED_PUBLISH_POLICIES = {
    "private_only",
    "public_link_only",
    "public_excerpt_allowed",
    "synthetic_public",
}
ALLOWED_EXTRACTION_STATUS = {
    "not_started",
    "staged",
    "text_extracted",
    "captions_available",
    "ocr_needed",
    "blocked",
}
ALLOWED_REVIEW_STATUS = {
    "unreviewed",
    "reviewed_for_private_tutor",
    "reviewed_public_safe",
    "blocked",
}

PUBLIC_REVIEW_STATUSES = {"reviewed_public_safe"}
PRIVATE_TUTOR_REVIEW_STATUSES = {"reviewed_for_private_tutor", "reviewed_public_safe"}
PUBLIC_POLICIES = {"public_link_only", "public_excerpt_allowed", "synthetic_public"}


@dataclass(frozen=True)
class CourseMaterialRecord:
    material_id: str
    title: str
    source_kind: str
    permission_status: str
    publish_policy: str
    extraction_status: str
    review_status: str
    skill_tags: tuple[str, ...] = field(default_factory=tuple)
    source_card_ids: tuple[str, ...] = field(default_factory=tuple)
    page_or_timestamp: str = ""
    sha256: str = ""
    public_excerpt: str = ""
    notes: str = ""

    def to_private_manifest_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["skill_tags"] = list(self.skill_tags)
        payload["source_card_ids"] = list(self.source_card_ids)
        payload["tutor_usable"] = is_tutor_usable(self)
        payload["public_release_allowed"] = is_public_release_allowed(self)
        payload["path_policy"] = "local paths stay outside the public manifest"
        return payload

    def to_public_summary_dict(self) -> dict[str, Any]:
        payload = {
            "material_id": self.material_id,
            "title": self.title,
            "source_kind": self.source_kind,
            "permission_status": self.permission_status,
            "publish_policy": self.publish_policy,
            "extraction_status": self.extraction_status,
            "review_status": self.review_status,
            "skill_tags": list(self.skill_tags),
            "source_card_ids": list(self.source_card_ids),
            "page_or_timestamp": self.page_or_timestamp,
            "sha256": self.sha256,
            "tutor_usable": is_tutor_usable(self),
            "public_release_allowed": is_public_release_allowed(self),
            "content_policy": "no private course files, local paths, or raw copied course text in public output",
        }
        if self.public_excerpt and is_public_release_allowed(self):
            payload["public_excerpt"] = self.public_excerpt
        return payload


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_material_record(raw: dict[str, Any], *, content_text: str = "") -> CourseMaterialRecord:
    sha = str(raw.get("sha256", "") or "")
    local_path = raw.get("local_path")
    if not sha and local_path:
        path = Path(str(local_path)).expanduser()
        if path.exists() and path.is_file():
            sha = sha256_file(path)
    if not sha and content_text:
        sha = sha256_text(content_text)

    return CourseMaterialRecord(
        material_id=str(raw.get("material_id", "")).strip(),
        title=str(raw.get("title", "")).strip(),
        source_kind=str(raw.get("source_kind", "slide_pdf")).strip(),
        permission_status=str(raw.get("permission_status", "unknown")).strip(),
        publish_policy=str(raw.get("publish_policy", "private_only")).strip(),
        extraction_status=str(raw.get("extraction_status", "staged")).strip(),
        review_status=str(raw.get("review_status", "unreviewed")).strip(),
        skill_tags=tuple(str(tag).strip() for tag in raw.get("skill_tags", []) if str(tag).strip()),
        source_card_ids=tuple(str(card).strip() for card in raw.get("source_card_ids", []) if str(card).strip()),
        page_or_timestamp=str(raw.get("page_or_timestamp", "")).strip(),
        sha256=sha,
        public_excerpt=str(raw.get("public_excerpt", "") or "").strip(),
        notes=str(raw.get("notes", "") or "").strip(),
    )


def validate_material_record(record: CourseMaterialRecord) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    if not record.material_id:
        issues.append("missing_material_id")
    if not record.title:
        issues.append("missing_title")
    if record.source_kind not in ALLOWED_SOURCE_KINDS:
        issues.append("unsupported_source_kind")
    if record.permission_status not in ALLOWED_PERMISSION_STATUS:
        issues.append("unsupported_permission_status")
    if record.publish_policy not in ALLOWED_PUBLISH_POLICIES:
        issues.append("unsupported_publish_policy")
    if record.extraction_status not in ALLOWED_EXTRACTION_STATUS:
        issues.append("unsupported_extraction_status")
    if record.review_status not in ALLOWED_REVIEW_STATUS:
        issues.append("unsupported_review_status")
    if record.review_status in PRIVATE_TUTOR_REVIEW_STATUSES and not record.sha256:
        issues.append("reviewed_material_requires_sha256")
    if record.publish_policy in {"public_excerpt_allowed", "synthetic_public"} and not record.public_excerpt:
        warnings.append("public_excerpt_missing")
    if record.public_excerpt:
        scan = scan_text(record.public_excerpt, source_name=record.material_id or "material")
        if scan["status"] != "pass":
            issues.append("public_excerpt_not_public_safe")
    if record.permission_status == "unknown" and record.review_status != "unreviewed":
        issues.append("unknown_permission_cannot_be_reviewed_for_use")
    if record.publish_policy in PUBLIC_POLICIES and record.permission_status not in {
        "owned_or_authorized",
        "public_link_only",
        "synthetic",
    }:
        issues.append("public_policy_requires_public_or_authorized_permission")

    return {
        "status": "blocked" if issues else "ok",
        "issues": issues,
        "warnings": warnings,
        "tutor_usable": is_tutor_usable(record) and not issues,
        "public_release_allowed": is_public_release_allowed(record) and not issues,
    }


def is_tutor_usable(record: CourseMaterialRecord) -> bool:
    return (
        record.permission_status in {"private_course_use_only", "owned_or_authorized", "public_link_only", "synthetic"}
        and record.review_status in PRIVATE_TUTOR_REVIEW_STATUSES
        and record.extraction_status in {"text_extracted", "captions_available"}
        and bool(record.sha256)
    )


def is_public_release_allowed(record: CourseMaterialRecord) -> bool:
    return (
        record.permission_status in {"owned_or_authorized", "public_link_only", "synthetic"}
        and record.publish_policy in PUBLIC_POLICIES
        and record.review_status in PUBLIC_REVIEW_STATUSES
        and record.extraction_status in {"text_extracted", "captions_available"}
        and bool(record.sha256)
    )


def build_material_manifest(records: Iterable[dict[str, Any] | CourseMaterialRecord]) -> dict[str, Any]:
    normalized = [record if isinstance(record, CourseMaterialRecord) else normalize_material_record(record) for record in records]
    entries = []
    blocked = 0
    tutor_usable = 0
    public_allowed = 0
    for record in normalized:
        validation = validate_material_record(record)
        if validation["status"] != "ok":
            blocked += 1
        if validation["tutor_usable"]:
            tutor_usable += 1
        if validation["public_release_allowed"]:
            public_allowed += 1
        entry = record.to_private_manifest_dict()
        entry["validation"] = validation
        entries.append(entry)

    return {
        "schema_version": MATERIAL_MANIFEST_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if blocked == 0 else "needs_review",
        "record_count": len(entries),
        "blocked_count": blocked,
        "tutor_usable_count": tutor_usable,
        "public_release_allowed_count": public_allowed,
        "private_storage_policy": "store source files locally only; never publish private course files or local paths",
        "records": entries,
    }


def build_public_material_summary(records: Iterable[dict[str, Any] | CourseMaterialRecord]) -> dict[str, Any]:
    normalized = [record if isinstance(record, CourseMaterialRecord) else normalize_material_record(record) for record in records]
    summaries = []
    for record in normalized:
        validation = validate_material_record(record)
        summary = record.to_public_summary_dict()
        summary["validation_status"] = validation["status"]
        if validation["status"] != "ok":
            summary["public_release_allowed"] = False
        summaries.append(summary)

    return {
        "schema_version": MATERIAL_MANIFEST_SCHEMA_VERSION,
        "status": "public_summary_only",
        "record_count": len(summaries),
        "public_release_allowed_count": len([record for record in summaries if record["public_release_allowed"]]),
        "excluded": ["source files", "local paths", "raw private course text", "student data", "exam data"],
        "records": summaries,
    }


def demo_material_records() -> list[dict[str, Any]]:
    return [
        {
            "material_id": "python-lists-demo",
            "title": "Synthetic Python lists micro-task",
            "source_kind": "synthetic_demo",
            "permission_status": "synthetic",
            "publish_policy": "synthetic_public",
            "extraction_status": "text_extracted",
            "review_status": "reviewed_public_safe",
            "skill_tags": ["python_lists", "loops"],
            "source_card_ids": ["vanlehn-2011"],
            "page_or_timestamp": "demo",
            "sha256": sha256_text("synthetic python lists demo"),
            "public_excerpt": "Create a list of three reaction times and describe the first indexing step.",
        },
        {
            "material_id": "course-slides-staged",
            "title": "Private Python course slide deck placeholder",
            "source_kind": "slide_pdf",
            "permission_status": "private_course_use_only",
            "publish_policy": "private_only",
            "extraction_status": "staged",
            "review_status": "unreviewed",
            "skill_tags": ["pandas", "boxplots"],
            "source_card_ids": ["dfg-gwp"],
            "page_or_timestamp": "week-03",
            "sha256": sha256_text("private staged slide placeholder"),
        },
    ]


def build_demo_material_manifest() -> dict[str, Any]:
    return build_material_manifest(demo_material_records())
