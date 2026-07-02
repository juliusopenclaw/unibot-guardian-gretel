from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_operator import validate_extraction_receipt
from .public_safety import scan_text


EXTRACTION_PROGRESS_SCHEMA_VERSION = "unibot-extraction-progress-v1"


def build_extraction_progress_report(
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
    rights_reference = str((decision_record or {}).get("decision_reference", "")) if authorized else ""
    rights_hash = str(decision_validation.get("rights_decision_reference_hash", ""))
    queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        rights_decision_reference=rights_reference or None,
        rights_decision_reference_hash=rights_hash if authorized and not rights_reference else None,
        public_safe=public_safe,
    )
    receipt_records = list(receipts or [])
    validations = [
        validate_extraction_receipt(
            receipt,
            decision_record=decision_record or {},
            decision_reference_hash=rights_hash,
        )
        for receipt in receipt_records
    ]
    duplicate_job_ids = duplicate_values([item.get("job_id", "") for item in validations if item.get("job_id")])
    visible_job_ids = {str(job.get("job_id", "")) for job in queue.get("jobs", []) if job.get("job_id")}
    received_job_ids = {str(item.get("job_id", "")) for item in validations if item.get("job_id")}
    unknown_job_ids = sorted(job_id for job_id in received_job_ids if visible_job_ids and job_id not in visible_job_ids)
    missing_visible_job_ids = sorted(job_id for job_id in visible_job_ids if job_id not in received_job_ids)

    invalid = [item for item in validations if item.get("status") == "blocked"]
    valid = [item for item in validations if item.get("status") != "blocked"]
    ready_for_review = [item for item in valid if item.get("ready_for_human_review_queue")]
    eligible = [item for item in valid if item.get("eligible_for_private_tutor_index")]
    report = {
        "schema_version": EXTRACTION_PROGRESS_SCHEMA_VERSION,
        "artifact_type": "course_extraction_progress_report",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": progress_status(queue, authorized, receipt_records, invalid, ready_for_review, eligible),
        "exam_deployment_status": "not_cleared",
        "decision_validation": public_decision_context_view(decision_validation),
        "queue_summary": queue.get("counts", {}),
        "receipt_summary": {
            "receipt_count": len(receipt_records),
            "valid_receipt_count": len(valid),
            "invalid_receipt_count": len(invalid),
            "ready_for_human_review_count": len(ready_for_review),
            "eligible_for_private_tutor_index_count": len(eligible),
            "failed_or_skipped_count": len(
                [item for item in valid if item.get("extraction_status") in {"failed", "skipped"}]
            ),
            "duplicate_job_id_count": len(duplicate_job_ids),
            "unknown_visible_job_id_count": len(unknown_job_ids),
            "missing_visible_job_count": len(missing_visible_job_ids),
        },
        "coverage": {
            "queue_job_count": queue.get("counts", {}).get("job_count", 0),
            "visible_queue_job_count": len(visible_job_ids),
            "matched_visible_job_count": len(received_job_ids.intersection(visible_job_ids)) if visible_job_ids else 0,
            "batch_truncated_by_queue": queue.get("counts", {}).get("job_count", 0) > len(visible_job_ids),
            "duplicate_job_ids": duplicate_job_ids[:20],
            "unknown_visible_job_ids": unknown_job_ids[:20],
            "missing_visible_job_ids": missing_visible_job_ids[:20],
        },
        "review_queue": [review_queue_item(item) for item in ready_for_review],
        "manifest_update_candidates": [manifest_update_candidate(item) for item in eligible],
        "blocked_receipt_summaries": [
            {
                "job_id": item.get("job_id", ""),
                "material_id": item.get("material_id", ""),
                "issues": item.get("issues", []),
            }
            for item in invalid[:20]
        ],
        "policy": (
            "Progress reports aggregate receipt metadata only. They do not contain raw OCR text, raw transcripts, "
            "local paths, or public release permission. Reviewed candidates still require manifest update before tutor retrieval."
        ),
        "next_actions": progress_next_actions(authorized, receipt_records, invalid, ready_for_review, eligible),
    }
    attach_public_scan(report, public_safe=public_safe, source_name="extraction-progress-report")
    return report


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def progress_status(
    queue: dict[str, Any],
    authorized: bool,
    receipts: list[dict[str, Any]],
    invalid: list[dict[str, Any]],
    ready_for_review: list[dict[str, Any]],
    eligible: list[dict[str, Any]],
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid:
        return "blocked_invalid_receipts"
    if not receipts:
        if not queue.get("counts", {}).get("job_count", 0):
            return "empty"
        return "waiting_for_extraction_receipts"
    if eligible and len(eligible) == len(receipts):
        return "receipts_reviewed_for_private_tutor"
    if ready_for_review:
        return "receipts_ready_for_human_review"
    if not queue.get("counts", {}).get("job_count", 0):
        return "receipts_recorded_without_visible_queue"
    return "receipts_recorded_no_private_tutor_candidates"


def review_queue_item(validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": validation.get("job_id", ""),
        "material_id": validation.get("material_id", ""),
        "job_type": validation.get("job_type", ""),
        "raw_text_sha256": validation.get("raw_text_sha256", ""),
        "extracted_text_char_count": validation.get("extracted_text_char_count", 0),
        "human_review_status": validation.get("human_review_status", "pending_review"),
        "review_action": "review local private text artifact, assign source-card links, then update private material manifest",
    }


def manifest_update_candidate(validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_id": validation.get("material_id", ""),
        "job_id": validation.get("job_id", ""),
        "job_type": validation.get("job_type", ""),
        "extraction_status_after_review": "text_extracted",
        "review_status_after_review": "reviewed_for_private_tutor",
        "sha256": validation.get("raw_text_sha256", ""),
        "source_policy": "private tutor metadata candidate only; no raw text included",
    }


def progress_next_actions(
    authorized: bool,
    receipts: list[dict[str, Any]],
    invalid: list[dict[str, Any]],
    ready_for_review: list[dict[str, Any]],
    eligible: list[dict[str, Any]],
) -> list[str]:
    if not authorized:
        return ["Validate the rights/privacy decision record before accepting extraction receipts."]
    if invalid:
        return ["Fix blocked receipts before human review or manifest updates."]
    if eligible:
        return ["Apply reviewed manifest metadata privately, rebuild ExamScopeMap, then rerun completion audit."]
    if ready_for_review:
        return ["Human-review the local private extracted text artifacts and mark accepted items reviewed_for_private_tutor."]
    if receipts:
        return ["Inspect failed or skipped extraction receipts and decide whether to rerun the local job."]
    return ["Run local private OCR/transcription jobs and validate one receipt per job."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
