from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_all_jobs
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_operator import validate_extraction_receipt
from .extraction_progress import build_extraction_progress_report
from .materials import normalize_material_record, validate_material_record
from .public_safety import scan_text


EXTRACTION_MANIFEST_UPDATE_SCHEMA_VERSION = "unibot-extraction-manifest-update-plan-v1"


def build_extraction_manifest_update_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    decision_validation = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
    )
    authorized = decision_context_authorizes(decision_validation)
    rights_hash = str(decision_validation.get("rights_decision_reference_hash", ""))
    progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts or [],
        public_safe=public_safe,
    )
    jobs = build_all_jobs(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        authorized=authorized,
        rights_hash=rights_hash if authorized else "",
    )
    job_by_id = {str(job.get("job_id", "")): job for job in jobs if job.get("job_id")}
    receipt_records = [item for item in (receipts or []) if isinstance(item, dict)]
    validations = [
        validate_extraction_receipt(
            receipt,
            decision_record=decision_record or {},
            decision_reference_hash=rights_hash,
        )
        for receipt in receipt_records
    ]
    invalid = [item for item in validations if item.get("status") == "blocked"]
    eligible = [item for item in validations if item.get("eligible_for_private_tutor_index")]
    candidates = [manifest_update_candidate(item, job_by_id.get(str(item.get("job_id", "")))) for item in eligible]
    blocked_candidates = [item for item in candidates if item.get("validation_status") == "blocked"]
    plan = {
        "schema_version": EXTRACTION_MANIFEST_UPDATE_SCHEMA_VERSION,
        "artifact_type": "course_extraction_manifest_update_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": manifest_update_status(authorized, invalid, eligible, blocked_candidates),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a private manifest metadata update plan. It does not write manifest files, "
            "does not expose local paths, and does not store raw OCR text or transcripts."
        ),
        "decision_validation": public_decision_context_view(decision_validation),
        "progress_status": progress.get("status"),
        "queue_summary": progress.get("queue_summary", {}),
        "receipt_summary": progress.get("receipt_summary", {}),
        "candidate_summary": {
            "candidate_count": len(candidates),
            "blocked_candidate_count": len(blocked_candidates),
            "source_job_metadata_missing_count": len(
                [item for item in candidates if item.get("source_job_metadata_status") == "missing"]
            ),
            "ready_to_apply_private_count": len([item for item in candidates if item.get("validation_status") == "ok"]),
        },
        "manifest_update_candidates": candidates[:80],
        "candidate_output_truncated": len(candidates) > 80,
        "manifest_update_contract": {
            "required_before_apply": [
                "valid rights/privacy decision",
                "validated extraction receipt",
                "human_review_status reviewed_for_private_tutor",
                "private raw text artifact retained outside public reports",
                "source-card metadata assigned or confirmed",
            ],
            "public_fields_only": [
                "material_id",
                "job_id",
                "job_type",
                "sha256_after_review",
                "extracted_text_char_count",
                "skill_tags",
                "source_card_ids",
                "review_status_after_review",
            ],
            "never_apply_here": [
                "raw OCR text",
                "raw transcript",
                "local source path",
                "exam deployment switch",
                "automatic grade or score",
            ],
        },
        "next_actions": manifest_update_next_actions(authorized, invalid, eligible, blocked_candidates),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="extraction-manifest-update-plan")
    return plan


def manifest_update_candidate(validation: dict[str, Any], job: dict[str, Any] | None) -> dict[str, Any]:
    job_type = str(validation.get("job_type", ""))
    extraction_status_after_review = "captions_available" if job_type == "transcription" else "text_extracted"
    source_kind = str((job or {}).get("source_kind", "video_file" if job_type == "transcription" else "document"))
    title = str((job or {}).get("title", f"Reviewed private extraction for {validation.get('material_id', '')}"))
    record_preview = {
        "material_id": validation.get("material_id", ""),
        "title": title,
        "source_kind": source_kind,
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": extraction_status_after_review,
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": list((job or {}).get("skill_tags", []) or [])[:6],
        "source_card_ids": list((job or {}).get("source_card_ids", []) or [])[:6],
        "page_or_timestamp": "",
        "sha256": validation.get("raw_text_sha256", ""),
        "public_excerpt": "",
        "notes": "metadata_only_private_extraction_update",
    }
    material_record = normalize_material_record(record_preview)
    material_validation = validate_material_record(material_record)
    return {
        "material_id": validation.get("material_id", ""),
        "job_id": validation.get("job_id", ""),
        "job_type": job_type,
        "operation": "update_existing_private_material_metadata",
        "source_job_metadata_status": "matched" if job else "missing",
        "source_kind_after_review": source_kind,
        "extraction_status_after_review": extraction_status_after_review,
        "review_status_after_review": "reviewed_for_private_tutor",
        "permission_status_after_review": "private_course_use_only",
        "publish_policy_after_review": "private_only",
        "sha256_after_review": validation.get("raw_text_sha256", ""),
        "extracted_text_char_count": validation.get("extracted_text_char_count", 0),
        "skill_tags": record_preview["skill_tags"],
        "source_card_ids": record_preview["source_card_ids"],
        "validation_status": material_validation.get("status"),
        "validation_issues": material_validation.get("issues", []),
        "validation_warnings": material_validation.get("warnings", []),
        "tutor_usable_after_apply": material_validation.get("tutor_usable", False),
        "public_release_allowed_after_apply": False,
        "raw_text_stored": False,
        "local_path_stored": False,
    }


def manifest_update_status(
    authorized: bool,
    invalid_receipts: list[dict[str, Any]],
    eligible_receipts: list[dict[str, Any]],
    blocked_candidates: list[dict[str, Any]],
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid_receipts:
        return "blocked_invalid_receipts"
    if blocked_candidates:
        return "blocked_candidate_metadata"
    if eligible_receipts:
        return "ready_for_private_manifest_update"
    return "waiting_for_reviewed_receipts"


def manifest_update_next_actions(
    authorized: bool,
    invalid_receipts: list[dict[str, Any]],
    eligible_receipts: list[dict[str, Any]],
    blocked_candidates: list[dict[str, Any]],
) -> list[str]:
    if not authorized:
        return ["Validate the rights/privacy decision record before planning private manifest updates."]
    if invalid_receipts:
        return ["Fix invalid receipts before preparing manifest metadata updates."]
    if blocked_candidates:
        return ["Fix candidate metadata before applying private material manifest updates."]
    if eligible_receipts:
        return ["Apply reviewed metadata privately, rebuild ExamScopeMap, then rerun course tutor evaluation."]
    return ["Complete human review and mark accepted receipts reviewed_for_private_tutor."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
