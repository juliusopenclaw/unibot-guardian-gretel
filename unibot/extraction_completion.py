from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_all_jobs, build_extraction_batch_plan
from .extraction_decision import ALLOWED_JOB_TYPES
from .extraction_operator import validate_extraction_receipt
from .materials import sha256_text
from .public_safety import scan_text


EXTRACTION_COMPLETION_SCHEMA_VERSION = "unibot-extraction-completion-v1"
EXTRACTION_DEFERRAL_SCHEMA_VERSION = "unibot-extraction-deferral-v1"

DEFERRAL_STATUSES = {"approved_deferral", "deferred_for_current_scope"}
DEFERRAL_SCOPES = {"course_material_extraction", "current_exam_scope"}
REQUIRED_DEFERRAL_ROLES = {"Datenschutz", "Lehreinheit / Modulverantwortliche"}
DEFERRAL_REASON_MIN_CHARS = 12


def validate_extraction_deferral_record(
    record: dict[str, Any] | None,
    *,
    public_safe: bool = True,
) -> dict[str, Any]:
    raw = dict(record or {})
    issues: list[str] = []
    warnings: list[str] = []
    scope = str(raw.get("deferral_scope", raw.get("scope", ""))).strip()
    status = str(raw.get("decision_status", raw.get("deferral_status", ""))).strip()
    job_types = [str(item).strip() for item in raw.get("deferred_job_types", raw.get("job_types", [])) or []]
    job_ids = [str(item).strip() for item in raw.get("deferred_job_ids", []) or [] if str(item).strip()]
    reviewer_roles = [str(item).strip() for item in raw.get("reviewer_roles", []) or []]
    reason = str(raw.get("deferral_reason", raw.get("reason", ""))).strip()
    reference = str(raw.get("decision_reference", raw.get("deferral_reference", ""))).strip()
    review_before_future_use = bool(raw.get("human_review_before_future_tutor_use", raw.get("human_review_before_tutor_index", False)))
    no_raw_text_release = raw.get("raw_text_public_release_allowed") is False
    no_exam_deployment = raw.get("exam_deployment_status", "not_cleared") == "not_cleared"

    if scope not in DEFERRAL_SCOPES:
        issues.append("unsupported_deferral_scope")
    if status not in DEFERRAL_STATUSES:
        issues.append("unsupported_deferral_status")
    if not job_types and not job_ids:
        issues.append("deferred_job_types_or_ids_required")
    unsupported_job_types = sorted(item for item in job_types if item not in ALLOWED_JOB_TYPES)
    if unsupported_job_types:
        issues.append("unsupported_deferred_job_type")
    missing_roles = sorted(role for role in REQUIRED_DEFERRAL_ROLES if role not in reviewer_roles)
    if missing_roles:
        issues.append("required_reviewer_roles_missing")
    if len(reason) < DEFERRAL_REASON_MIN_CHARS:
        issues.append("deferral_reason_required")
    if not reference:
        issues.append("decision_reference_required")
    if not review_before_future_use:
        issues.append("human_review_before_future_tutor_use_required")
    if not no_raw_text_release:
        issues.append("raw_text_public_release_must_remain_false")
    if not no_exam_deployment:
        issues.append("exam_deployment_must_remain_not_cleared")
    if len(job_ids) > 80:
        warnings.append("deferred_job_ids_truncated_in_public_output")

    validation = {
        "schema_version": EXTRACTION_DEFERRAL_SCHEMA_VERSION,
        "artifact_type": "course_extraction_deferral_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok_extraction_deferral_record" if not issues else "blocked",
        "exam_deployment_status": "not_cleared",
        "deferral_scope": scope or "missing",
        "decision_status": status or "missing",
        "deferred_job_types": sorted(set(job_types)),
        "deferred_job_id_count": len(job_ids),
        "deferred_job_id_hashes": [sha256_text(job_id) for job_id in job_ids[:80]],
        "deferred_job_ids_stored": False,
        "reviewer_roles": reviewer_roles,
        "missing_reviewer_roles": missing_roles,
        "decision_reference_hash": sha256_text(reference) if reference else "",
        "raw_decision_reference_stored": False,
        "deferral_reason_hash": sha256_text(reason) if reason else "",
        "raw_deferral_reason_stored": False,
        "human_review_before_future_tutor_use": review_before_future_use,
        "raw_text_public_release_allowed": False,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "policy": (
            "A deferral record documents intentional postponement only. It does not extract material, "
            "does not update the tutor index, and does not clear exam deployment."
        ),
    }
    attach_public_scan(validation, public_safe=public_safe, source_name="extraction-deferral-validation")
    return validation


def build_extraction_completion_report(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    receipts: list[dict[str, Any]] | None = None,
    deferral_record: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    batch = build_extraction_batch_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        receipts=receipts or [],
        public_safe=public_safe,
    )
    jobs = build_all_jobs(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        authorized=batch.get("decision_validation", {}).get("status") == "ok_authorizes_local_extraction",
        rights_hash=str(batch.get("decision_validation", {}).get("rights_decision_reference_hash", "")),
    )
    job_ids = {str(job.get("job_id", "")) for job in jobs if job.get("job_id")}
    job_types = {str(job.get("job_type", "")) for job in jobs if job.get("job_type")}
    receipt_records = [item for item in (receipts or []) if isinstance(item, dict)]
    validations = [validate_extraction_receipt(receipt, decision_record=decision_record or {}) for receipt in receipt_records]
    valid = [item for item in validations if item.get("status") != "blocked"]
    eligible = [item for item in valid if item.get("eligible_for_private_tutor_index")]
    failed_or_skipped = [item for item in valid if item.get("extraction_status") in {"failed", "skipped"}]
    invalid = [item for item in validations if item.get("status") == "blocked"]
    completed_job_ids = {
        str(item.get("job_id", ""))
        for item in eligible + failed_or_skipped
        if item.get("job_id")
    }
    deferred_validation = validate_extraction_deferral_record(deferral_record, public_safe=public_safe) if deferral_record else {}
    deferred_job_ids = deferred_job_id_set(deferral_record or {}, job_ids=job_ids, job_types=job_types, jobs=jobs)
    covered_job_ids = completed_job_ids.union(deferred_job_ids)
    missing_job_ids = sorted(job_id for job_id in job_ids if job_id not in covered_job_ids)
    deferral_valid = deferred_validation.get("status") == "ok_extraction_deferral_record"
    report = {
        "schema_version": EXTRACTION_COMPLETION_SCHEMA_VERSION,
        "artifact_type": "course_extraction_completion_report",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": extraction_completion_status(
            job_count=len(job_ids),
            invalid_receipt_count=len(invalid),
            missing_job_count=len(missing_job_ids),
            deferred_job_count=len(deferred_job_ids),
            deferral_valid=deferral_valid,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This completion report classifies extraction work only. It does not run OCR/transcription, "
            "does not store raw extracted text, does not update manifests, and does not clear exam deployment."
        ),
        "job_summary": {
            "open_job_count": len(job_ids),
            "ocr_job_count": len([job for job in jobs if job.get("job_type") == "ocr"]),
            "transcription_job_count": len([job for job in jobs if job.get("job_type") == "transcription"]),
            "completed_by_reviewed_receipt_count": len(completed_job_ids),
            "deferred_job_count": len(deferred_job_ids) if deferral_valid else 0,
            "missing_job_count": len(missing_job_ids),
            "missing_job_ids": missing_job_ids[:20],
            "missing_job_output_truncated": len(missing_job_ids) > 20,
        },
        "receipt_summary": {
            "submitted_receipt_count": len(receipt_records),
            "valid_receipt_count": len(valid),
            "invalid_receipt_count": len(invalid),
            "eligible_for_private_tutor_index_count": len(eligible),
            "failed_or_skipped_count": len(failed_or_skipped),
        },
        "deferral_summary": {
            "present": bool(deferral_record),
            "status": deferred_validation.get("status", "missing"),
            "deferred_job_count": len(deferred_job_ids) if deferral_valid else 0,
            "deferred_job_types": deferred_validation.get("deferred_job_types", []),
            "issues": deferred_validation.get("issues", []),
            "raw_decision_reference_stored": deferred_validation.get("raw_decision_reference_stored", False),
        },
        "source_batch_status": batch.get("status"),
        "completion_policy": {
            "complete_when": [
                "no OCR/transcription jobs remain",
                "or every queued job has a reviewed/failed/skipped receipt",
                "or every remaining queued job is covered by a valid intentional deferral record",
            ],
            "not_complete_when": [
                "receipts are invalid",
                "open jobs lack reviewed receipt or valid deferral evidence",
                "deferral tries to imply public release, grading, proctoring, or exam deployment",
            ],
        },
        "next_actions": extraction_completion_next_actions(invalid, missing_job_ids, deferral_valid, bool(deferral_record)),
    }
    attach_public_scan(report, public_safe=public_safe, source_name="extraction-completion-report")
    return report


def deferred_job_id_set(
    record: dict[str, Any],
    *,
    job_ids: set[str],
    job_types: set[str],
    jobs: list[dict[str, Any]],
) -> set[str]:
    validation = validate_extraction_deferral_record(record)
    if validation.get("status") != "ok_extraction_deferral_record":
        return set()
    explicit = {str(item).strip() for item in record.get("deferred_job_ids", []) or [] if str(item).strip()}
    if explicit:
        return explicit.intersection(job_ids)
    deferred_types = {str(item).strip() for item in record.get("deferred_job_types", record.get("job_types", [])) or []}
    if not deferred_types:
        return set()
    if job_types.issubset(deferred_types):
        return set(job_ids)
    return {str(job.get("job_id", "")) for job in jobs if str(job.get("job_type", "")) in deferred_types}


def extraction_completion_status(
    *,
    job_count: int,
    invalid_receipt_count: int,
    missing_job_count: int,
    deferred_job_count: int,
    deferral_valid: bool,
) -> str:
    if invalid_receipt_count:
        return "blocked_invalid_receipts"
    if job_count == 0:
        return "complete_no_open_extraction_jobs"
    if missing_job_count == 0 and deferred_job_count:
        return "complete_intentionally_deferred"
    if missing_job_count == 0:
        return "complete_by_reviewed_receipts"
    if deferral_valid and deferred_job_count:
        return "partial_completion_with_deferral"
    return "open_extraction_jobs_require_receipts_or_deferral"


def extraction_completion_next_actions(
    invalid_receipts: list[dict[str, Any]],
    missing_job_ids: list[str],
    deferral_valid: bool,
    deferral_present: bool,
) -> list[str]:
    if invalid_receipts:
        return ["Fix invalid extraction receipts before claiming completion or deferral."]
    if not missing_job_ids:
        return ["Use this report as completion evidence, then rebuild the private manifest/tutor coverage if receipts changed."]
    if not deferral_present:
        return ["Finish receipts for remaining jobs or record a valid intentional deferral decision for the current scope."]
    if not deferral_valid:
        return ["Fix the deferral record: reviewer roles, reason, job coverage, no raw-text release, and not_cleared exam status are required."]
    return ["Finish or defer the remaining uncovered extraction jobs."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
