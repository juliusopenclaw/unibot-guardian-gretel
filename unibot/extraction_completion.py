from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_all_jobs, build_extraction_batch_plan
from .extraction_decision import ALLOWED_JOB_TYPES
from .extraction_operator import validate_extraction_receipt
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card


EXTRACTION_COMPLETION_SCHEMA_VERSION = "unibot-extraction-completion-v1"
EXTRACTION_DEFERRAL_SCHEMA_VERSION = "unibot-extraction-deferral-v1"
EXTRACTION_COMPLETION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-extraction-completion-release-review-board-claim-alignment-v1"
)

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


def build_extraction_completion_release_claim_alignment(
    receipt_completion_report: dict[str, Any] | None = None,
    deferral_completion_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if receipt_completion_report is None or deferral_completion_report is None:
        decision_record = synthetic_completion_decision_record()
        with tempfile.TemporaryDirectory(prefix="unibot_completion_alignment_") as temp_dir:
            fixture_root = Path(temp_dir)
            (fixture_root / "Week 1").mkdir(parents=True)
            (fixture_root / "Videos").mkdir(parents=True)
            (fixture_root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
            (fixture_root / "Videos" / "lecture.mov").write_bytes(b"video")
            jobs = build_all_jobs(
                DEFAULT_COURSE_ID,
                base_path=str(fixture_root),
                max_files=260,
                review_policy="staged",
                authorized=True,
                rights_hash=sha256_text(str(decision_record["decision_reference"])),
            )
            receipts = [synthetic_completion_receipt(job, decision_record) for job in jobs]
            deferral_record = synthetic_completion_deferral_record()
            if receipt_completion_report is None:
                receipt_completion_report = build_extraction_completion_report(
                    base_path=str(fixture_root),
                    decision_record=decision_record,
                    receipts=receipts,
                )
            if deferral_completion_report is None:
                deferral_completion_report = build_extraction_completion_report(
                    base_path=str(fixture_root),
                    decision_record=decision_record,
                    deferral_record=deferral_record,
                )

    sections = [
        {
            "section_id": "reviewed_receipt_completion_trace",
            "summary_claim": "completion by reviewed receipts requires all open jobs to be covered by reviewed, failed, or skipped receipt evidence",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": ["extraction_completion", "extraction_receipt_journal", "extraction_progress"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "intentional_deferral_trace",
            "summary_claim": "completion by deferral requires a valid hash-only human deferral record and does not store raw deferral reasons",
            "source_card_ids": ["gdpr-2016-679", "dfg-gwp"],
            "readiness_check_ids": ["extraction_completion", "external_decision_record_journal", "data_protection_screening"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "completion_boundary_trace",
            "summary_claim": "completion reports classify extraction work only and do not run extraction, update manifests, or start tutor indexing",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["extraction_completion", "extraction_manifest_update", "extraction_manifest_apply"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "completion reports do not clear public release, cloud processing, official grading, proctoring, KI-detection evidence, or exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["extraction_completion", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    receipt_job_summary = receipt_completion_report.get("job_summary", {})
    receipt_summary = receipt_completion_report.get("receipt_summary", {})
    deferral_job_summary = deferral_completion_report.get("job_summary", {})
    deferral_summary = deferral_completion_report.get("deferral_summary", {})
    blocked_claims = [
        "raw deferral reason storage",
        "raw decision reference storage",
        "raw extracted text storage",
        "manifest update by completion report",
        "tutor indexing by completion report",
        "public raw course text release",
        "cloud processing",
        "exam deployment",
        "official grading",
        "proctoring",
        "KI-detection evidence",
    ]
    receipt_boundary = str(receipt_completion_report.get("execution_boundary", ""))
    deferral_boundary = str(deferral_completion_report.get("execution_boundary", ""))
    contracts = {
        "receipt_completion_public_safe": receipt_completion_report.get("public_safety_status") == "pass",
        "deferral_completion_public_safe": deferral_completion_report.get("public_safety_status") == "pass",
        "receipt_completion_covers_all_jobs": receipt_completion_report.get("status") == "complete_by_reviewed_receipts"
        and receipt_job_summary.get("missing_job_count") == 0
        and receipt_job_summary.get("completed_by_reviewed_receipt_count", 0) >= receipt_job_summary.get("open_job_count", 0)
        and receipt_summary.get("invalid_receipt_count") == 0
        and receipt_summary.get("eligible_for_private_tutor_index_count", 0) >= receipt_job_summary.get("open_job_count", 0),
        "deferral_completion_covers_all_jobs_hash_only": deferral_completion_report.get("status") == "complete_intentionally_deferred"
        and deferral_job_summary.get("missing_job_count") == 0
        and deferral_job_summary.get("deferred_job_count", 0) >= deferral_job_summary.get("open_job_count", 0)
        and deferral_summary.get("status") == "ok_extraction_deferral_record"
        and deferral_summary.get("raw_decision_reference_stored") is False,
        "completion_boundaries_block_execution_manifest_and_exam": all(
            "does not run OCR/transcription" in boundary
            and "does not store raw extracted text" in boundary
            and "does not update manifests" in boundary
            and "does not clear exam deployment" in boundary
            for boundary in [receipt_boundary, deferral_boundary]
        ),
        "completion_policy_blocks_invalid_or_uncovered_jobs": "receipts are invalid"
        in receipt_completion_report.get("completion_policy", {}).get("not_complete_when", [])
        and "open jobs lack reviewed receipt or valid deferral evidence"
        in receipt_completion_report.get("completion_policy", {}).get("not_complete_when", []),
        "exam_deployment_not_cleared": receipt_completion_report.get("exam_deployment_status") == "not_cleared"
        and deferral_completion_report.get("exam_deployment_status") == "not_cleared",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "receipt_completion_status": receipt_completion_report.get("status"),
        "deferral_completion_status": deferral_completion_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "extraction-completion-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXTRACTION_COMPLETION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "receipt_completion_status": receipt_completion_report.get("status"),
        "deferral_completion_status": deferral_completion_report.get("status"),
        "receipt_completion_public_safety_status": receipt_completion_report.get("public_safety_status"),
        "deferral_completion_public_safety_status": deferral_completion_report.get("public_safety_status"),
        "receipt_open_job_count": receipt_job_summary.get("open_job_count", 0),
        "receipt_completed_job_count": receipt_job_summary.get("completed_by_reviewed_receipt_count", 0),
        "deferral_open_job_count": deferral_job_summary.get("open_job_count", 0),
        "deferral_deferred_job_count": deferral_job_summary.get("deferred_job_count", 0),
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": blocked_claims,
        "public_safety_status": scan["status"],
        "policy": (
            "Extraction completion reports are classification evidence only: completion can be shown by reviewed "
            "receipts or valid intentional deferral, but completion does not run extraction, store raw text, update "
            "manifests, start tutor indexing, approve public release, approve cloud processing, or clear exam use."
        ),
    }


def synthetic_completion_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic extraction completion release alignment decision",
    }


def synthetic_completion_receipt(job: dict[str, Any], decision_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id", "synthetic-completion-job"),
        "material_id": job.get("material_id", "synthetic-completion-material"),
        "job_type": job.get("job_type", "ocr"),
        "extraction_status": "extracted_private",
        "raw_text_sha256": "a" * 64,
        "extracted_text_char_count": 900,
        "private_artifact_reference": "synthetic local private completion artifact reference",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(decision_record["decision_reference"])),
    }


def synthetic_completion_deferral_record() -> dict[str, Any]:
    return {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "current public draft can proceed with reviewed anchors while remaining extraction is deferred",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic extraction completion deferral release alignment decision",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


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
