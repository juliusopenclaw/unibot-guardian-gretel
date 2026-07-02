from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id, scan_course_intake
from .extraction import build_course_extraction_queue, extraction_job, job_type_for_record
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_operator import FORBIDDEN_RECEIPT_FIELDS, validate_extraction_receipt
from .materials import sha256_text
from .public_safety import scan_text


EXTRACTION_BATCH_SCHEMA_VERSION = "unibot-extraction-batch-plan-v1"
EXTRACTION_BATCH_RECEIPT_SCHEMA_VERSION = "unibot-extraction-batch-receipt-packet-v1"


def build_extraction_batch_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    batch_size: int = 12,
    job_types: list[str] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    selected_job_types = normalize_job_types(job_types)
    decision_validation = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        requested_job_types=selected_job_types,
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
    jobs = build_all_jobs(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        authorized=authorized,
        rights_hash=rights_hash if authorized else "",
    )
    filtered_jobs = [job for job in jobs if not selected_job_types or str(job.get("job_type", "")) in selected_job_types]
    ordered_jobs = sorted(filtered_jobs, key=job_sort_key)
    size = max(1, min(int(batch_size or 12), 40))
    receipt_records = [item for item in (receipts or []) if isinstance(item, dict)]
    validations = [
        validate_extraction_receipt(
            receipt,
            decision_record=decision_record or {},
            decision_reference_hash=rights_hash,
        )
        for receipt in receipt_records
    ]
    valid_job_ids = {item.get("job_id", "") for item in validations if item.get("status") != "blocked" and item.get("job_id")}
    ready_job_ids = {item.get("job_id", "") for item in validations if item.get("ready_for_human_review_queue") and item.get("job_id")}
    eligible_job_ids = {item.get("job_id", "") for item in validations if item.get("eligible_for_private_tutor_index") and item.get("job_id")}
    invalid_receipts = [item for item in validations if item.get("status") == "blocked"]
    batches = [
        batch_view(
            batch_jobs,
            batch_index=index + 1,
            batch_size=size,
            authorized=authorized,
            valid_job_ids=valid_job_ids,
            ready_job_ids=ready_job_ids,
            eligible_job_ids=eligible_job_ids,
            course_id=safe_course_id(course_id),
            rights_hash=rights_hash,
        )
        for index, batch_jobs in enumerate(chunked(ordered_jobs, size))
    ]
    plan = {
        "schema_version": EXTRACTION_BATCH_SCHEMA_VERSION,
        "artifact_type": "course_extraction_batch_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": batch_plan_status(authorized, ordered_jobs, invalid_receipts, valid_job_ids),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a plan-only extraction backlog. It does not perform OCR or transcription, "
            "does not expose local paths, and does not store raw extracted course text."
        ),
        "decision_validation": public_decision_context_view(decision_validation),
        "queue_summary": queue.get("counts", {}),
        "coverage": {
            "job_count": len(ordered_jobs),
            "unfiltered_job_count": len(jobs),
            "batch_count": len(batches),
            "batch_size": size,
            "job_type_filter": sorted(selected_job_types),
            "ocr_job_count": len([job for job in ordered_jobs if job.get("job_type") == "ocr"]),
            "transcription_job_count": len([job for job in ordered_jobs if job.get("job_type") == "transcription"]),
            "high_priority_job_count": len([job for job in ordered_jobs if job.get("priority") == "high"]),
            "visible_queue_job_count": len(queue.get("jobs", [])),
            "queue_public_output_truncated": len(ordered_jobs) > len(queue.get("jobs", [])),
        },
        "receipt_backlog": {
            "expected_receipt_count": len(ordered_jobs),
            "submitted_receipt_count": len(receipt_records),
            "valid_receipt_count": len(valid_job_ids),
            "invalid_receipt_count": len(invalid_receipts),
            "ready_for_human_review_count": len(ready_job_ids),
            "eligible_for_private_tutor_index_count": len(eligible_job_ids),
            "missing_receipt_count": max(0, len(ordered_jobs) - len(valid_job_ids)),
        },
        "batches": batches[:80],
        "batch_output_truncated": len(batches) > 80,
        "next_batch": next_batch(batches),
        "batch_policy": {
            "execution": "local private OCR/transcription only after valid rights/privacy decision",
            "receipt_rule": "one validated receipt per job before progress can advance",
            "review_rule": "human review is required before private tutor indexing",
            "public_output": "batch plan contains metadata, hashes, and counts only",
            "job_type_filter": "optional metadata-only filter for ocr or transcription batches",
        },
        "next_actions": batch_next_actions(authorized, ordered_jobs, invalid_receipts, valid_job_ids, ready_job_ids, eligible_job_ids),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="extraction-batch-plan")
    return plan


def build_extraction_batch_receipt_packet(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    batch_size: int = 12,
    batch_index: int | None = None,
    job_types: list[str] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    plan = build_extraction_batch_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts or [],
        batch_size=batch_size,
        job_types=job_types,
        public_safe=public_safe,
    )
    selected = selected_batch(plan, batch_index=batch_index)
    receipt_records = [item for item in (receipts or []) if isinstance(item, dict)]
    rights_hash = str(plan.get("decision_validation", {}).get("rights_decision_reference_hash", ""))
    validations = [
        validate_extraction_receipt(
            receipt,
            decision_record=decision_record or {},
            decision_reference_hash=rights_hash,
        )
        for receipt in receipt_records
    ]
    selected_job_ids = {str(job.get("job_id", "")) for job in selected.get("jobs", []) if job.get("job_id")}
    selected_validations = [item for item in validations if str(item.get("job_id", "")) in selected_job_ids]
    invalid = [item for item in selected_validations if item.get("status") == "blocked"]
    packet = {
        "schema_version": EXTRACTION_BATCH_RECEIPT_SCHEMA_VERSION,
        "artifact_type": "course_extraction_batch_receipt_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": batch_receipt_packet_status(plan, selected, selected_validations, invalid),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a packet-only extraction receipt workflow. It does not perform OCR or transcription, "
            "does not expose local paths, and does not store raw extracted course text."
        ),
        "source_batch_plan_status": plan.get("status"),
        "decision_validation": plan.get("decision_validation", {}),
        "selected_batch": selected_batch_summary(selected),
        "receipt_validation_summary": {
            "submitted_receipt_count": len(selected_validations),
            "valid_receipt_count": len([item for item in selected_validations if item.get("status") != "blocked"]),
            "invalid_receipt_count": len(invalid),
            "ready_for_human_review_count": len(
                [item for item in selected_validations if item.get("ready_for_human_review_queue")]
            ),
            "eligible_for_private_tutor_index_count": len(
                [item for item in selected_validations if item.get("eligible_for_private_tutor_index")]
            ),
        },
        "receipt_templates": [
            receipt_template_for_job(job, rights_hash=rights_hash)
            for job in selected.get("jobs", [])
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
            "status_values": {
                "extraction_status": ["extracted_private", "failed", "skipped"],
                "human_review_status": ["pending_review", "reviewed_for_private_tutor", "rejected"],
            },
            "public_output_policy": "receipt packets contain templates and metadata only; raw text and local paths stay private",
        },
        "local_operator_steps": local_operator_steps(plan, selected),
        "human_review_checklist": [
            "open only the local private artifact referenced by the operator, outside public reports",
            "check that extracted text belongs to the queued material and is not a solution or exam key",
            "link the accepted material to source-card metadata before tutor retrieval",
            "mark human_review_status reviewed_for_private_tutor only after reviewer acceptance",
            "keep rejected or failed items out of the tutor index until a new receipt is validated",
        ],
        "manifest_update_policy": {
            "allowed_after": "validated receipt plus human review acceptance",
            "public_manifest_content": "metadata, hashes, source-card ids, and review status only",
            "not_allowed": "raw OCR text, raw transcripts, local file paths, grading decisions, exam clearance",
        },
        "next_actions": batch_receipt_next_actions(plan, selected, invalid),
    }
    attach_public_scan(packet, public_safe=public_safe, source_name="extraction-batch-receipt-packet")
    return packet


def build_all_jobs(
    course_id: str,
    *,
    base_path: str | None,
    max_files: int,
    review_policy: str,
    authorized: bool,
    rights_hash: str,
) -> list[dict[str, Any]]:
    scan = scan_course_intake(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=True,
    )
    jobs: list[dict[str, Any]] = []
    for record in scan.get("records", []):
        notes = str(record.get("notes", ""))
        if record.get("review_status") == "blocked" or "quarantined_solution_or_exam" in notes:
            continue
        if record.get("extraction_status") in {"text_extracted", "captions_available"}:
            continue
        job_type = job_type_for_record(record)
        if not job_type:
            continue
        jobs.append(extraction_job(record, job_type=job_type, authorized=authorized, rights_hash=rights_hash))
    return jobs


def normalize_job_types(job_types: list[str] | None) -> set[str]:
    allowed = {"ocr", "transcription"}
    return {str(item) for item in (job_types or []) if str(item) in allowed}


def batch_view(
    jobs: list[dict[str, Any]],
    *,
    batch_index: int,
    batch_size: int,
    authorized: bool,
    valid_job_ids: set[str],
    ready_job_ids: set[str],
    eligible_job_ids: set[str],
    course_id: str,
    rights_hash: str,
) -> dict[str, Any]:
    job_ids = [str(job.get("job_id", "")) for job in jobs if job.get("job_id")]
    valid_count = len([job_id for job_id in job_ids if job_id in valid_job_ids])
    ready_count = len([job_id for job_id in job_ids if job_id in ready_job_ids])
    eligible_count = len([job_id for job_id in job_ids if job_id in eligible_job_ids])
    return {
        "batch_id": sha256_text(f"{course_id}:{rights_hash or 'pending'}:{batch_index}:{','.join(job_ids)}")[:20],
        "batch_index": batch_index,
        "batch_size": batch_size,
        "status": batch_status(authorized, len(job_ids), valid_count, ready_count, eligible_count),
        "job_count": len(jobs),
        "job_type_counts": count_by(jobs, "job_type"),
        "priority_counts": count_by(jobs, "priority"),
        "receipt_count": valid_count,
        "missing_receipt_count": max(0, len(job_ids) - valid_count),
        "ready_for_human_review_count": ready_count,
        "eligible_for_private_tutor_index_count": eligible_count,
        "job_ids": job_ids,
        "jobs": [batch_job_view(job) for job in jobs],
    }


def batch_job_view(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id", ""),
        "material_id": job.get("material_id", ""),
        "job_type": job.get("job_type", ""),
        "status": job.get("status", ""),
        "priority": job.get("priority", ""),
        "sha256": job.get("sha256", ""),
        "skill_tags": list(job.get("skill_tags", []) or [])[:6],
    }


def batch_status(
    authorized: bool,
    job_count: int,
    valid_count: int,
    ready_count: int,
    eligible_count: int,
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if job_count and eligible_count == job_count:
        return "reviewed_for_private_tutor_manifest_update_ready"
    if ready_count:
        return "ready_for_human_review"
    if valid_count and valid_count < job_count:
        return "partially_receipted"
    if valid_count == job_count and job_count:
        return "receipts_recorded"
    return "waiting_for_local_private_receipts"


def batch_plan_status(
    authorized: bool,
    jobs: list[dict[str, Any]],
    invalid_receipts: list[dict[str, Any]],
    valid_job_ids: set[str],
) -> str:
    if not jobs:
        return "empty"
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid_receipts:
        return "blocked_invalid_receipts"
    if len(valid_job_ids) >= len(jobs):
        return "all_jobs_receipted"
    if valid_job_ids:
        return "partially_receipted"
    return "ready_for_local_private_execution"


def next_batch(batches: list[dict[str, Any]]) -> dict[str, Any]:
    for batch in batches:
        if batch.get("status") in {
            "ready_for_local_private_execution",
            "waiting_for_local_private_receipts",
            "partially_receipted",
            "ready_for_human_review",
            "blocked_until_valid_rights_privacy_decision",
        }:
            return {
                "batch_id": batch.get("batch_id"),
                "batch_index": batch.get("batch_index"),
                "status": batch.get("status"),
                "job_count": batch.get("job_count"),
                "job_type_counts": batch.get("job_type_counts", {}),
                "missing_receipt_count": batch.get("missing_receipt_count", 0),
                "ready_for_human_review_count": batch.get("ready_for_human_review_count", 0),
                "eligible_for_private_tutor_index_count": batch.get("eligible_for_private_tutor_index_count", 0),
            }
    return {}


def selected_batch(plan: dict[str, Any], *, batch_index: int | None) -> dict[str, Any]:
    batches = [item for item in plan.get("batches", []) if isinstance(item, dict)]
    if not batches:
        return {}
    if batch_index is not None:
        for batch in batches:
            if int(batch.get("batch_index", 0) or 0) == int(batch_index):
                return batch
        return {}
    next_index = int((plan.get("next_batch") or {}).get("batch_index", 0) or 0)
    if next_index:
        for batch in batches:
            if int(batch.get("batch_index", 0) or 0) == next_index:
                return batch
    return batches[0]


def selected_batch_summary(batch: dict[str, Any]) -> dict[str, Any]:
    if not batch:
        return {
            "status": "empty",
            "job_count": 0,
            "receipt_count": 0,
            "missing_receipt_count": 0,
        }
    return {
        "batch_id": batch.get("batch_id", ""),
        "batch_index": batch.get("batch_index", 0),
        "status": batch.get("status", ""),
        "job_count": batch.get("job_count", 0),
        "job_type_counts": batch.get("job_type_counts", {}),
        "priority_counts": batch.get("priority_counts", {}),
        "receipt_count": batch.get("receipt_count", 0),
        "missing_receipt_count": batch.get("missing_receipt_count", 0),
        "ready_for_human_review_count": batch.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": batch.get("eligible_for_private_tutor_index_count", 0),
    }


def receipt_template_for_job(job: dict[str, Any], *, rights_hash: str) -> dict[str, Any]:
    job_id = str(job.get("job_id", ""))
    return {
        "job_id": job_id,
        "material_id": job.get("material_id", ""),
        "job_type": job.get("job_type", ""),
        "extraction_status": "extracted_private",
        "raw_text_sha256": "",
        "extracted_text_char_count": 0,
        "private_artifact_reference": f"local-private-artifact-reference-{job_id}",
        "human_review_status": "pending_review",
        "decision_reference_hash": rights_hash,
        "raw_text_must_not_be_added": True,
        "local_path_must_not_be_added": True,
        "source_sha256": job.get("sha256", ""),
        "skill_tags": list(job.get("skill_tags", []) or [])[:6],
    }


def batch_receipt_packet_status(
    plan: dict[str, Any],
    batch: dict[str, Any],
    validations: list[dict[str, Any]],
    invalid: list[dict[str, Any]],
) -> str:
    if not batch:
        return "empty"
    if plan.get("status") == "blocked_until_valid_rights_privacy_decision":
        return "blocked_until_valid_rights_privacy_decision"
    if invalid:
        return "blocked_invalid_receipts"
    job_count = int(batch.get("job_count", 0) or 0)
    ready_count = len([item for item in validations if item.get("ready_for_human_review_queue")])
    eligible_count = len([item for item in validations if item.get("eligible_for_private_tutor_index")])
    valid_count = len([item for item in validations if item.get("status") != "blocked"])
    if job_count and eligible_count == job_count:
        return "batch_reviewed_for_private_tutor_manifest_ready"
    if ready_count:
        return "ready_for_human_review"
    if valid_count:
        return "batch_partially_receipted"
    return "ready_for_local_private_execution"


def local_operator_steps(plan: dict[str, Any], batch: dict[str, Any]) -> list[str]:
    if not batch:
        return ["No batch selected; rebuild the batch plan after materials are updated."]
    if plan.get("status") == "blocked_until_valid_rights_privacy_decision":
        return ["Record and validate the rights/privacy decision before opening any local extraction artifact."]
    return [
        "resolve each material from the local private manifest outside this public packet",
        "run OCR only for ocr jobs and transcription only for transcription jobs",
        "store raw extracted text in a local private artifact, never in this packet",
        "hash the private text artifact and fill exactly one receipt per job",
        "validate the receipts before moving the batch into human review",
    ]


def batch_receipt_next_actions(
    plan: dict[str, Any],
    batch: dict[str, Any],
    invalid: list[dict[str, Any]],
) -> list[str]:
    if not batch:
        return ["No batch is available; rebuild the compiler plan and extraction batch plan."]
    if plan.get("status") == "blocked_until_valid_rights_privacy_decision":
        return ["Validate the written rights/privacy decision record before running batch receipts."]
    if invalid:
        return ["Fix blocked receipts in this batch before human review."]
    if batch.get("eligible_for_private_tutor_index_count") == batch.get("job_count") and batch.get("job_count"):
        return ["Apply reviewed private manifest updates for this batch, then rebuild ExamScopeMap."]
    if batch.get("ready_for_human_review_count"):
        return ["Human-review the local private artifacts for this batch."]
    if batch.get("receipt_count"):
        return ["Continue receipt collection until this batch is complete."]
    return ["Run local private extraction for this selected batch and validate one receipt per job."]


def batch_next_actions(
    authorized: bool,
    jobs: list[dict[str, Any]],
    invalid_receipts: list[dict[str, Any]],
    valid_job_ids: set[str],
    ready_job_ids: set[str],
    eligible_job_ids: set[str],
) -> list[str]:
    if not jobs:
        return ["No OCR/transcription batch work remains; rebuild the ExamScopeMap from reviewed materials."]
    if not authorized:
        return ["Validate the rights/privacy decision record before running any local extraction batch."]
    if invalid_receipts:
        return ["Fix invalid extraction receipts before advancing any batch."]
    if eligible_job_ids and len(eligible_job_ids) == len(jobs):
        return ["Apply reviewed private manifest updates, rebuild tutor retrieval, then rerun completion audit."]
    if ready_job_ids:
        return ["Human-review the ready private extracted artifacts before marking them reviewed_for_private_tutor."]
    if valid_job_ids:
        return ["Continue local private extraction for missing receipts in the next incomplete batch."]
    return ["Run the next local private OCR/transcription batch and validate one receipt per job."]


def count_by(jobs: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        value = str(job.get(key, "missing") or "missing")
        counts[value] = counts.get(value, 0) + 1
    return counts


def chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def job_sort_key(job: dict[str, Any]) -> tuple[int, str, str]:
    priority_rank = {"high": 0, "medium": 1, "normal": 2}
    return (
        priority_rank.get(str(job.get("priority", "normal")), 3),
        str(job.get("job_type", "")),
        str(job.get("job_id", "")),
    )


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
