from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .extraction_decision import ALLOWED_JOB_TYPES, validate_extraction_decision_record
from .materials import sha256_text
from .public_safety import scan_text


EXTRACTION_OPERATOR_SCHEMA_VERSION = "unibot-extraction-operator-v1"

RECEIPT_STATUSES = {"extracted_private", "failed", "skipped"}
HUMAN_REVIEW_STATUSES = {"pending_review", "reviewed_for_private_tutor", "rejected"}
FORBIDDEN_RECEIPT_FIELDS = {"raw_text", "extracted_text", "ocr_text", "transcript", "transcription"}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$", re.I)


def build_extraction_operator_packet(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    job_limit: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    validation = validate_extraction_decision_record(decision_record or {})
    authorized = validation.get("status") == "ok_authorizes_local_extraction"
    rights_reference = ""
    if authorized and decision_record:
        rights_reference = str(decision_record.get("decision_reference", ""))
    queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        rights_decision_reference=rights_reference or None,
        public_safe=public_safe,
    )
    jobs = list(queue.get("jobs", []))
    limited_jobs = jobs[: max(1, int(job_limit or 1))]
    operator_packet = {
        "schema_version": EXTRACTION_OPERATOR_SCHEMA_VERSION,
        "artifact_type": "course_extraction_operator_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": operator_status(queue, validation, authorized),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This packet is an operator harness. It does not perform OCR or transcription, "
            "does not expose local paths, and does not publish raw extracted course text."
        ),
        "decision_validation": {
            "status": validation.get("status"),
            "approved_for_local_extraction": validation.get("approved_for_local_extraction"),
            "issues": validation.get("issues", []),
            "warnings": validation.get("warnings", []),
            "rights_decision_reference_hash": validation.get("rights_decision_reference_hash", ""),
            "raw_decision_reference_stored": False,
        },
        "queue_summary": queue.get("counts", {}),
        "job_batch": [operator_job_view(job) for job in limited_jobs],
        "job_batch_count": len(limited_jobs),
        "job_batch_truncated": len(jobs) > len(limited_jobs),
        "operator_checklist": [
            "keep all source files and raw extracted text in a local private workspace",
            "resolve local source paths from the private manifest outside public output",
            "run local OCR or transcription only for queued jobs and only after the validated decision record",
            "write raw extracted text to private storage and record only hashes/counts in public-safe receipts",
            "validate one receipt per job before human review",
            "mark extracted content reviewed_for_private_tutor only after human source-card review",
            "rerun completion audit and pipeline smoke after review metadata is updated",
        ],
        "receipt_contract": {
            "required_fields": [
                "job_id",
                "material_id",
                "job_type",
                "extraction_status",
                "raw_text_sha256",
                "extracted_text_char_count",
                "private_artifact_reference",
                "human_review_status",
                "decision_reference_hash",
            ],
            "forbidden_fields": sorted(FORBIDDEN_RECEIPT_FIELDS),
            "public_output_policy": "receipts store hashes, status, counts, and review state only; no local paths or raw text",
        },
        "supported_adapters": [
            "local_manual_ocr",
            "local_manual_transcription",
            "future_mock_first_tool_adapter",
        ],
    }
    attach_public_scan(operator_packet, public_safe=public_safe, source_name="extraction-operator-packet")
    return operator_packet


def validate_extraction_receipt(
    receipt: dict[str, Any] | None,
    *,
    decision_record: dict[str, Any] | None = None,
    decision_reference_hash: str | None = None,
) -> dict[str, Any]:
    record = dict(receipt or {})
    validation = validate_extraction_decision_record(decision_record or {})
    trusted_decision_hash = str(decision_reference_hash or "").strip()
    trusted_decision_context = bool(SHA256_RE.match(trusted_decision_hash))
    issues: list[str] = []
    warnings: list[str] = []

    if validation.get("status") != "ok_authorizes_local_extraction" and not trusted_decision_context:
        issues.append("valid_extraction_decision_record_required")

    forbidden_present = sorted(field for field in FORBIDDEN_RECEIPT_FIELDS if field in record)
    if forbidden_present:
        issues.append("receipt_must_not_include_raw_text_fields")

    job_id = str(record.get("job_id", "")).strip()
    material_id = str(record.get("material_id", "")).strip()
    job_type = str(record.get("job_type", "")).strip()
    extraction_status = str(record.get("extraction_status", "")).strip()
    raw_text_sha256 = str(record.get("raw_text_sha256", "")).strip()
    private_artifact_reference = str(record.get("private_artifact_reference", "")).strip()
    human_review_status = str(record.get("human_review_status", "")).strip()
    decision_reference_hash = str(record.get("decision_reference_hash", "")).strip()

    if not job_id:
        issues.append("job_id_required")
    if not material_id:
        issues.append("material_id_required")
    if job_type not in ALLOWED_JOB_TYPES:
        issues.append("unsupported_job_type")
    if extraction_status not in RECEIPT_STATUSES:
        issues.append("unsupported_extraction_status")
    if human_review_status not in HUMAN_REVIEW_STATUSES:
        issues.append("unsupported_human_review_status")
    if not private_artifact_reference:
        issues.append("private_artifact_reference_required")
    if extraction_status == "extracted_private":
        if not SHA256_RE.match(raw_text_sha256):
            issues.append("raw_text_sha256_required")
        try:
            char_count = int(record.get("extracted_text_char_count", 0) or 0)
        except (TypeError, ValueError):
            char_count = 0
        if char_count <= 0:
            issues.append("positive_extracted_text_char_count_required")
    else:
        try:
            char_count = int(record.get("extracted_text_char_count", 0) or 0)
        except (TypeError, ValueError):
            char_count = 0

    expected_hash = str(validation.get("rights_decision_reference_hash", "")) or trusted_decision_hash
    if not decision_reference_hash:
        issues.append("decision_reference_hash_required")
    elif not expected_hash:
        issues.append("decision_reference_hash_unverifiable")
    elif expected_hash and decision_reference_hash != expected_hash:
        issues.append("decision_reference_hash_mismatch")

    if human_review_status == "reviewed_for_private_tutor":
        warnings.append("reviewed_receipt_still_requires_material_manifest_update_before_retrieval")

    safe_summary = {
        "schema_version": EXTRACTION_OPERATOR_SCHEMA_VERSION,
        "artifact_type": "course_extraction_receipt_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": receipt_status(issues, extraction_status),
        "exam_deployment_status": "not_cleared",
        "decision_context_status": (
            validation.get("status")
            if validation.get("status") == "ok_authorizes_local_extraction"
            else "ok_authorizes_local_extraction_from_journal" if trusted_decision_context else validation.get("status")
        ),
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "job_id": job_id,
        "material_id": material_id,
        "job_type": job_type or "missing",
        "extraction_status": extraction_status or "missing",
        "human_review_status": human_review_status or "missing",
        "raw_text_sha256": raw_text_sha256 if SHA256_RE.match(raw_text_sha256) else "",
        "extracted_text_char_count": char_count,
        "private_artifact_reference_hash": sha256_text(private_artifact_reference) if private_artifact_reference else "",
        "decision_reference_hash": decision_reference_hash,
        "raw_text_stored_in_receipt": bool(forbidden_present),
        "ready_for_human_review_queue": (
            not issues
            and extraction_status == "extracted_private"
            and human_review_status == "pending_review"
        ),
        "eligible_for_private_tutor_index": (
            not issues
            and extraction_status == "extracted_private"
            and human_review_status == "reviewed_for_private_tutor"
        ),
        "policy": (
            "Receipt validation proves local-private extraction evidence only. "
            "It does not publish raw text, update the tutor index by itself, or clear exam deployment."
        ),
    }
    scan = scan_text(json.dumps(safe_summary, ensure_ascii=False), "extraction-receipt-validation")
    safe_summary["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        safe_summary["status"] = "blocked"
        safe_summary["public_safety_findings"] = scan["findings"]
    return safe_summary


def operator_status(queue: dict[str, Any], validation: dict[str, Any], authorized: bool) -> str:
    if not queue.get("counts", {}).get("job_count", 0):
        return "empty"
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if validation.get("public_safety_status") != "pass":
        return "blocked_public_safety"
    return "private_operator_ready"


def operator_job_view(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id", ""),
        "material_id": job.get("material_id", ""),
        "title": job.get("title", ""),
        "job_type": job.get("job_type", ""),
        "status": job.get("status", ""),
        "priority": job.get("priority", ""),
        "sha256": job.get("sha256", ""),
        "skill_tags": list(job.get("skill_tags", []) or [])[:6],
        "source_card_ids": list(job.get("source_card_ids", []) or [])[:6],
    }


def receipt_status(issues: list[str], extraction_status: str) -> str:
    if issues:
        return "blocked"
    if extraction_status == "extracted_private":
        return "ok_private_extraction_receipt"
    if extraction_status == "failed":
        return "recorded_failed_extraction"
    return "recorded_skipped_extraction"


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
