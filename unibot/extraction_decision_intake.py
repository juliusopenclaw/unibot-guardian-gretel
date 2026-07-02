from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_batches import build_extraction_batch_plan
from .extraction_decision import REQUIRED_REVIEWER_ROLES, build_extraction_decision_packet
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .extraction_progress import build_extraction_progress_report
from .extraction_receipt_journal import extraction_receipts_for_progress, summarize_extraction_receipt_journal
from .external_decision_journal import append_external_decision_journal_record, summarize_external_decision_journal
from .public_safety import scan_text
from .tutor_coverage import build_course_tutor_coverage_plan


LOCAL_EXTRACTION_DECISION_INTAKE_SCHEMA_VERSION = "unibot-local-extraction-decision-intake-v1"


def build_local_extraction_decision_intake_packet(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipt_journal_path: str | None = None,
    job_types: list[str] | None = None,
    batch_size: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    requested_job_types = [str(item) for item in (job_types or ["ocr"]) if str(item)]
    decision_context = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        requested_job_types=requested_job_types,
    )
    receipts = extraction_receipts_for_progress(path=receipt_journal_path) if receipt_journal_path else []
    decision_packet = build_extraction_decision_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    batch_plan = build_extraction_batch_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        batch_size=batch_size,
        job_types=requested_job_types,
        public_safe=public_safe,
    )
    progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        public_safe=public_safe,
    )
    manifest = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        public_safe=public_safe,
    )
    coverage = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        public_safe=public_safe,
    )
    decision_journal_summary = summarize_external_decision_journal(path=decision_record_journal_path)
    receipt_journal_summary = summarize_extraction_receipt_journal(path=receipt_journal_path)
    packet = {
        "schema_version": LOCAL_EXTRACTION_DECISION_INTAKE_SCHEMA_VERSION,
        "artifact_type": "course_local_extraction_decision_intake_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": intake_status(decision_context, batch_plan, receipts),
        "exam_deployment_status": "not_cleared",
        "decision_boundary": (
            "This packet supports local rights/privacy decision intake for private course extraction only. "
            "It does not send messages, store raw written decisions in public output, run OCR by itself, "
            "clear exams, or authorize cloud processing."
        ),
        "decision_record_template": {
            **decision_packet.get("minimum_decision_record", {}),
            "decision_status": "approved_for_local_extraction",
            "reviewer_roles": REQUIRED_REVIEWER_ROLES,
        },
        "decision_validation": public_decision_context_view(decision_context),
        "decision_journal_summary": public_journal_summary(decision_journal_summary),
        "ocr_first_readiness": {
            "status": batch_plan.get("status"),
            "job_type_filter": batch_plan.get("coverage", {}).get("job_type_filter", requested_job_types),
            "job_count": batch_plan.get("coverage", {}).get("job_count", 0),
            "unfiltered_job_count": batch_plan.get("coverage", {}).get("unfiltered_job_count", 0),
            "batch_count": batch_plan.get("coverage", {}).get("batch_count", 0),
            "batch_size": batch_plan.get("coverage", {}).get("batch_size", batch_size),
            "next_batch": safe_batch_summary(batch_plan.get("next_batch", {})),
            "expected_receipt_count": batch_plan.get("receipt_backlog", {}).get("expected_receipt_count", 0),
            "missing_receipt_count": batch_plan.get("receipt_backlog", {}).get("missing_receipt_count", 0),
        },
        "receipt_journal_summary": public_receipt_summary(receipt_journal_summary),
        "post_run_report_summary": {
            "progress_status": progress.get("status"),
            "manifest_update_status": manifest.get("status"),
            "tutor_coverage_status": coverage.get("status"),
            "ready_for_human_review_count": progress.get("receipt_summary", {}).get("ready_for_human_review_count", 0),
            "eligible_for_private_tutor_index_count": progress.get("receipt_summary", {}).get(
                "eligible_for_private_tutor_index_count",
                0,
            ),
            "manifest_candidate_count": manifest.get("candidate_summary", {}).get("candidate_count", 0),
            "coverage_candidate_material_count": coverage.get("projected_scope_summary", {}).get(
                "candidate_material_count",
                0,
            ),
        },
        "safe_payload_templates": {
            "store_decision_record": {
                "endpoint": "/api/unibot/course/extraction-decision/local-intake/record",
                "record_type": "local_extraction_decision",
                "path_fields": ["decision_record_journal_path"],
                "raw_decision_record_returned": False,
            },
            "run_ocr_first_batch_1": {
                "endpoint": "/api/unibot/course/private-extraction/run-batch",
                "required_payload_fields": [
                    "base_path",
                    "decision_record_journal_path",
                    "receipt_journal_path",
                    "private_output_dir",
                ],
                "fixed_payload": {"job_types": ["ocr"], "max_jobs": 12, "review_policy": review_policy},
                "public_output": "hash-only receipts, counts, adapter status; no raw text or local paths",
            },
            "review_after_run": {
                "endpoints": [
                    "/api/unibot/course/extraction-progress-report",
                    "/api/unibot/course/extraction-manifest-update-plan",
                    "/api/unibot/course/tutor-coverage-plan",
                ],
                "required_payload_fields": ["decision_record_journal_path", "receipt_journal_path"],
            },
        },
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": intake_next_actions(decision_context, batch_plan, progress, manifest, coverage),
    }
    attach_public_scan(packet, public_safe=public_safe, source_name="local-extraction-decision-intake")
    return packet


def record_local_extraction_decision_and_build_intake_packet(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipt_journal_path: str | None = None,
    job_types: list[str] | None = None,
    batch_size: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    append_result = append_external_decision_journal_record(
        record_type="local_extraction_decision",
        record=decision_record or {},
        path=decision_record_journal_path,
    )
    intake = build_local_extraction_decision_intake_packet(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=None if append_result.get("status") == "stored" else decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipt_journal_path=receipt_journal_path,
        job_types=job_types,
        batch_size=batch_size,
        public_safe=public_safe,
    )
    result = {
        "schema_version": LOCAL_EXTRACTION_DECISION_INTAKE_SCHEMA_VERSION,
        "artifact_type": "course_local_extraction_decision_record_result",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "decision_record_stored_hash_only" if append_result.get("status") == "stored" else "blocked_decision_record_not_stored",
        "exam_deployment_status": "not_cleared",
        "journal_append_status": append_result.get("status"),
        "journal_record_status": append_result.get("record", {}).get("status"),
        "journal_event": {
            "record_type": append_result.get("record", {}).get("event", {}).get("record_type", "local_extraction_decision"),
            "validation_status": append_result.get("record", {}).get("event", {}).get("validation_status", "blocked"),
            "accepted_for_gate": append_result.get("record", {}).get("event", {}).get("accepted_for_gate", False),
            "decision_reference_hash": append_result.get("record", {}).get("event", {}).get("decision_reference_hash", ""),
            "raw_record_stored": False,
            "raw_decision_reference_stored": False,
            "issues": append_result.get("record", {}).get("event", {}).get("issues", []),
        },
        "intake_packet": intake,
        "raw_decision_record_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }
    attach_public_scan(result, public_safe=public_safe, source_name="local-extraction-decision-record-result")
    return result


def intake_status(
    decision_context: dict[str, Any],
    batch_plan: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> str:
    if not decision_context_authorizes(decision_context):
        return "waiting_for_local_rights_privacy_decision_record"
    if receipts:
        return "decision_record_and_receipt_journal_ready_for_review_reports"
    if str(batch_plan.get("status", "")).startswith("blocked"):
        return "decision_record_present_but_ocr_first_blocked"
    return "decision_record_journal_ready_for_ocr_first"


def public_journal_summary(summary: dict[str, Any]) -> dict[str, Any]:
    gate = summary.get("gate_summary", {})
    return {
        "status": summary.get("status"),
        "record_count": summary.get("record_count", 0),
        "accepted_record_count": summary.get("accepted_record_count", 0),
        "local_extraction_decision_valid": gate.get("local_extraction_decision_valid", False),
        "exam_deployment_status": gate.get("exam_deployment_status", "not_cleared"),
        "raw_decision_records_returned": False,
    }


def public_receipt_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": summary.get("status"),
        "record_count": summary.get("record_count", 0),
        "accepted_record_count": summary.get("accepted_record_count", 0),
        "ready_for_human_review_count": summary.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": summary.get("eligible_for_private_tutor_index_count", 0),
        "progress_receipt_count": summary.get("progress_receipt_count", 0),
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def safe_batch_summary(batch: dict[str, Any]) -> dict[str, Any]:
    return {
        "batch_index": batch.get("batch_index", 0),
        "job_count": batch.get("job_count", 0),
        "job_type_counts": batch.get("job_type_counts", {}),
        "status": batch.get("status", ""),
    }


def intake_next_actions(
    decision_context: dict[str, Any],
    batch_plan: dict[str, Any],
    progress: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
) -> list[str]:
    if not decision_context_authorizes(decision_context):
        return [
            "Fill the local extraction decision record from the template and store it through the hash-only decision-record journal.",
            "Do not run private OCR until the journal shows a valid local_extraction_decision gate.",
        ]
    if progress.get("receipt_summary", {}).get("ready_for_human_review_count", 0):
        return ["Human-review the private artifacts referenced by receipt hashes, then mark accepted receipts reviewed_for_private_tutor."]
    if manifest.get("candidate_summary", {}).get("candidate_count", 0):
        return ["Apply reviewed private manifest metadata, rebuild ExamScopeMap, and rerun tutor coverage."]
    if coverage.get("status") == "coverage_uplift_ready_after_private_manifest_update":
        return ["Apply private manifest updates, then rerun course tutor eval and completion audit."]
    return [
        "Run OCR-first Batch 1 through the private extraction harness with job_types ['ocr'] and max_jobs 12.",
        f"Current OCR-first batch plan status: {batch_plan.get('status')}.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
