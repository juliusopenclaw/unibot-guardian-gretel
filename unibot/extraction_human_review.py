from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .extraction_operator import validate_extraction_receipt
from .extraction_progress import build_extraction_progress_report
from .extraction_receipt_journal import (
    append_extraction_receipt_record,
    extraction_receipts_for_progress,
    read_extraction_receipt_journal,
    resolve_extraction_receipt_journal_path,
    summarize_extraction_receipt_records,
)
from .materials import sha256_text
from .public_safety import scan_text
from .tutor_coverage import build_course_tutor_coverage_plan


EXTRACTION_HUMAN_REVIEW_SCHEMA_VERSION = "unibot-extraction-human-review-v1"
DEFAULT_EXTRACTION_HUMAN_REVIEW_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "extraction_human_reviews.jsonl"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$", re.I)
REVIEW_DECISION_TO_RECEIPT_STATUS = {
    "accepted_for_private_tutor": "reviewed_for_private_tutor",
    "rejected": "rejected",
    "needs_rerun": "rejected",
}
FORBIDDEN_REVIEW_FIELDS = {
    "raw_text",
    "extracted_text",
    "ocr_text",
    "transcript",
    "transcription",
    "local_path",
    "local_paths",
    "artifact_path",
    "source_path",
    "file_path",
    "private_artifact_reference",
}


def resolve_extraction_human_review_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_EXTRACTION_HUMAN_REVIEW_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_EXTRACTION_HUMAN_REVIEW_JOURNAL_PATH


def validate_extraction_human_review_decision(
    review_decision: dict[str, Any] | None,
    *,
    receipt: dict[str, Any] | None = None,
    decision_reference_hash: str | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    decision = dict(review_decision or {})
    receipt_validation = validate_extraction_receipt(
        receipt or {},
        decision_reference_hash=decision_reference_hash,
    )
    issues: list[str] = []
    warnings: list[str] = []

    forbidden_present = sorted(field for field in FORBIDDEN_REVIEW_FIELDS if field in decision)
    if forbidden_present:
        issues.append("review_decision_must_not_include_raw_text_or_local_path_fields")

    job_id = str(decision.get("job_id", "")).strip()
    receipt_job_id = str(receipt_validation.get("job_id", "")).strip()
    if not job_id:
        issues.append("job_id_required")
    if receipt_job_id and job_id and job_id != receipt_job_id:
        issues.append("job_id_mismatch")

    decision_value = str(decision.get("review_decision", "")).strip()
    target_review_status = REVIEW_DECISION_TO_RECEIPT_STATUS.get(decision_value, "")
    if not target_review_status:
        issues.append("unsupported_review_decision")

    reviewer_roles = normalized_reviewer_roles(decision)
    if not reviewer_roles:
        issues.append("reviewer_role_required")

    reviewed_locally = bool(
        decision.get("raw_text_reviewed_locally")
        or decision.get("private_artifact_reviewed_locally")
        or decision.get("local_private_artifact_reviewed")
    )
    if not reviewed_locally:
        issues.append("local_private_artifact_review_required")

    review_reference_hash = review_reference_hash_from_decision(decision)
    if not review_reference_hash:
        issues.append("review_reference_hash_required")

    source_card_ids = decision.get("source_card_ids", [])
    if source_card_ids is None:
        source_card_ids = []
    if not isinstance(source_card_ids, list):
        issues.append("source_card_ids_must_be_list")
        source_card_ids = []

    if receipt_validation.get("status") == "blocked":
        issues.append("receipt_validation_blocked")
    if receipt_validation.get("extraction_status") != "extracted_private":
        issues.append("receipt_must_be_extracted_private")
    if receipt_validation.get("human_review_status") not in {"pending_review", "reviewed_for_private_tutor", "rejected"}:
        issues.append("receipt_review_status_not_supported")
    if receipt_validation.get("human_review_status") == "reviewed_for_private_tutor" and decision_value == "accepted_for_private_tutor":
        warnings.append("receipt_already_reviewed_for_private_tutor")
    if decision_value == "needs_rerun":
        warnings.append("needs_rerun_is_recorded_as_rejected_receipt_until_a_new_extraction_receipt_exists")

    validation = {
        "schema_version": EXTRACTION_HUMAN_REVIEW_SCHEMA_VERSION,
        "artifact_type": "course_extraction_human_review_decision_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok_human_review_decision" if not issues else "blocked",
        "exam_deployment_status": "not_cleared",
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "job_id": job_id,
        "material_id": receipt_validation.get("material_id", ""),
        "job_type": receipt_validation.get("job_type", "missing"),
        "review_decision": decision_value or "missing",
        "target_human_review_status": target_review_status or "missing",
        "reviewer_roles": reviewer_roles,
        "review_reference_hash": review_reference_hash,
        "review_notes_hash": review_notes_hash_from_decision(decision),
        "source_card_ids": [str(item) for item in source_card_ids if str(item)][:12],
        "raw_text_reviewed_locally": reviewed_locally,
        "raw_review_reference_stored": False,
        "raw_review_notes_stored": False,
        "raw_text_stored": False,
        "local_path_stored": False,
        "receipt_validation_status": receipt_validation.get("status", "blocked"),
        "receipt_ready_for_human_review_queue": bool(receipt_validation.get("ready_for_human_review_queue", False)),
        "receipt_eligible_for_private_tutor_index": bool(receipt_validation.get("eligible_for_private_tutor_index", False)),
        "policy": (
            "Human review records hash-only reviewer evidence and may mark receipts for private tutor metadata planning. "
            "It does not expose raw course text, write the material manifest, index the tutor, or clear exam deployment."
        ),
    }
    if public_safe:
        scan = scan_text(json.dumps(validation, ensure_ascii=False), "extraction-human-review-validation")
        validation["public_safety_status"] = scan["status"]
        if scan["status"] != "pass":
            validation["status"] = "blocked"
            validation["public_safety_findings"] = scan["findings"]
    else:
        validation["public_safety_status"] = "local_private_mode"
    return validation


def review_receipt_for_private_tutor(
    receipt: dict[str, Any],
    review_decision: dict[str, Any],
    *,
    decision_reference_hash: str,
    receipt_journal_path: str | Path | None = None,
    review_journal_path: str | Path | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    validation = validate_extraction_human_review_decision(
        review_decision,
        receipt=receipt,
        decision_reference_hash=decision_reference_hash,
        public_safe=public_safe,
    )
    if validation.get("status") != "ok_human_review_decision":
        return {
            "status": "blocked",
            "job_id": validation.get("job_id", ""),
            "material_id": validation.get("material_id", ""),
            "issues": validation.get("issues", []),
            "validation": validation,
            "review_receipt_appended": False,
            "review_record_appended": False,
            "receipt_journal_path_returned": False,
            "review_journal_path_returned": False,
            "raw_text_returned": False,
            "local_paths_returned": False,
        }

    reviewed_receipt = reviewed_receipt_from_decision(
        receipt,
        target_human_review_status=str(validation.get("target_human_review_status", "")),
    )
    receipt_append = append_extraction_receipt_record(
        reviewed_receipt,
        decision_reference_hash=decision_reference_hash,
        path=receipt_journal_path,
    )
    review_append = append_extraction_human_review_record(
        validation,
        path=review_journal_path,
        public_safe=public_safe,
    )
    receipt_stored = receipt_append.get("status") == "stored"
    review_stored = review_append.get("status") == "stored"
    return {
        "status": "stored" if receipt_stored and review_stored else "blocked",
        "job_id": validation.get("job_id", ""),
        "material_id": validation.get("material_id", ""),
        "review_decision": validation.get("review_decision", ""),
        "target_human_review_status": validation.get("target_human_review_status", ""),
        "review_reference_hash": validation.get("review_reference_hash", ""),
        "receipt_append_status": receipt_append.get("status", "blocked"),
        "review_append_status": review_append.get("status", "blocked"),
        "review_receipt_appended": receipt_stored,
        "review_record_appended": review_stored,
        "receipt_record_hash": receipt_append.get("record", {}).get("event", {}).get("validation_hash", ""),
        "review_record_hash": review_append.get("record", {}).get("event", {}).get("validation_hash", ""),
        "issues": validation.get("issues", []),
        "warnings": validation.get("warnings", []),
        "receipt_journal_path_returned": False,
        "review_journal_path_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def build_extraction_human_review_apply_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipt_journal_path: str | Path | None = None,
    review_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    review_decisions: list[dict[str, Any]] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    decision_context = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
    )
    authorized = decision_context_authorizes(decision_context)
    rights_hash = str(decision_context.get("rights_decision_reference_hash", ""))
    receipt_path = resolve_extraction_receipt_journal_path(receipt_journal_path) if receipt_journal_path else None
    review_path = resolve_extraction_human_review_journal_path(review_journal_path) if review_journal_path else None
    journal_records = read_extraction_receipt_journal(receipt_path).get("records", []) if receipt_path else []
    initial_receipts = [item for item in (receipts or []) if isinstance(item, dict)]
    initial_receipts.extend(extraction_receipts_for_progress(records=journal_records))
    latest_before = latest_receipts_by_job(initial_receipts)
    before_progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_before,
        public_safe=public_safe,
    )

    ready_by_job = ready_receipts_by_job(latest_before, decision_reference_hash=rights_hash)
    review_results: list[dict[str, Any]] = []
    applied_review_receipts: list[dict[str, Any]] = []
    decisions = [item for item in (review_decisions or []) if isinstance(item, dict)]
    if authorized:
        for decision in decisions:
            job_id = str(decision.get("job_id", "")).strip()
            receipt = ready_by_job.get(job_id)
            if receipt is None:
                validation = validate_extraction_human_review_decision(
                    decision,
                    receipt={},
                    decision_reference_hash=rights_hash,
                    public_safe=public_safe,
                )
                issues = sorted(set(list(validation.get("issues", []) or []) + ["review_ready_receipt_not_found"]))
                validation["status"] = "blocked"
                validation["issues"] = issues
                review_results.append(
                    {
                        "status": "blocked",
                        "job_id": job_id,
                        "issues": issues,
                        "validation": validation,
                        "review_receipt_appended": False,
                        "review_record_appended": False,
                        "raw_text_returned": False,
                        "local_paths_returned": False,
                    }
                )
                continue
            result = review_receipt_for_private_tutor(
                receipt,
                decision,
                decision_reference_hash=rights_hash,
                receipt_journal_path=receipt_path,
                review_journal_path=review_path,
                public_safe=public_safe,
            )
            review_results.append(result)
            if result.get("status") == "stored":
                applied_review_receipts.append(
                    reviewed_receipt_from_decision(
                        receipt,
                        target_human_review_status=str(result.get("target_human_review_status", "")),
                    )
                )

    if receipt_path and applied_review_receipts:
        after_records = read_extraction_receipt_journal(receipt_path).get("records", [])
        after_receipts = extraction_receipts_for_progress(records=after_records)
    else:
        after_receipts = [*initial_receipts, *applied_review_receipts]
    latest_after = latest_receipts_by_job(after_receipts)

    after_progress = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_after,
        public_safe=public_safe,
    )
    manifest = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_after,
        public_safe=public_safe,
    )
    coverage = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=latest_after,
        public_safe=public_safe,
    )
    receipt_summary = summarize_extraction_receipt_records(journal_records, status="ok" if journal_records else "empty")
    invalid_results = [item for item in review_results if item.get("status") != "stored"]
    plan = {
        "schema_version": EXTRACTION_HUMAN_REVIEW_SCHEMA_VERSION,
        "artifact_type": "course_extraction_human_review_apply_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": human_review_plan_status(
            authorized=authorized,
            decisions_submitted=bool(decisions),
            invalid_results=invalid_results,
            appended_count=len(applied_review_receipts),
            ready_count=int(after_progress.get("receipt_summary", {}).get("ready_for_human_review_count", 0) or 0),
            candidate_count=int(manifest.get("candidate_summary", {}).get("candidate_count", 0) or 0),
            receipt_count=len(latest_after),
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This harness records human review metadata and prepares a private manifest apply plan. "
            "It does not expose raw course text, expose local paths, write material manifests, run tutor indexing, "
            "or clear exam deployment."
        ),
        "decision_validation": public_decision_context_view(decision_context),
        "review_queue_summary": {
            "pre_review_ready_count": int(before_progress.get("receipt_summary", {}).get("ready_for_human_review_count", 0) or 0),
            "post_review_ready_count": int(after_progress.get("receipt_summary", {}).get("ready_for_human_review_count", 0) or 0),
            "post_reviewed_for_private_tutor_count": int(after_progress.get("receipt_summary", {}).get("eligible_for_private_tutor_index_count", 0) or 0),
            "latest_receipt_count": len(latest_after),
            "receipt_journal_record_count": int(receipt_summary.get("record_count", 0) or 0),
        },
        "review_decision_summary": review_decision_summary(review_results, decisions),
        "review_results": public_review_results(review_results),
        "manifest_apply_plan": {
            "status": manifest.get("status", "unknown"),
            "candidate_summary": manifest.get("candidate_summary", {}),
            "manifest_update_candidates": manifest.get("manifest_update_candidates", [])[:30],
            "candidate_output_truncated": bool(manifest.get("candidate_output_truncated", False))
            or len(manifest.get("manifest_update_candidates", [])) > 30,
            "next_actions": manifest.get("next_actions", []),
        },
        "post_review_reports": {
            "progress": progress_public_summary(after_progress),
            "manifest_update": manifest_public_summary(manifest),
            "tutor_coverage": coverage_public_summary(coverage),
        },
        "review_journal_used": bool(review_path and decisions),
        "receipt_journal_used": bool(receipt_path),
        "raw_decision_record_returned": False,
        "raw_review_reference_returned": False,
        "raw_review_notes_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "private_artifact_reference_returned": False,
        "manifest_written": False,
        "tutor_indexing_started": False,
        "next_actions": human_review_next_actions(authorized, invalid_results, after_progress, manifest, coverage),
    }
    attach_public_scan(plan, public_safe=public_safe)
    return plan


def append_extraction_human_review_record(
    validation: dict[str, Any],
    *,
    path: str | Path | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    record = sanitize_extraction_human_review_record(validation, public_safe=public_safe)
    journal_path = resolve_extraction_human_review_journal_path(path)
    if record["status"] != "accepted":
        return {"status": "blocked", "record": record}
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "stored", "record": record}


def sanitize_extraction_human_review_record(
    validation: dict[str, Any],
    *,
    public_safe: bool = True,
) -> dict[str, Any]:
    event = {
        "event_type": "extraction_human_review_decision_recorded",
        "job_id": str(validation.get("job_id", "")),
        "material_id": str(validation.get("material_id", "")),
        "job_type": str(validation.get("job_type", "missing")),
        "review_decision": str(validation.get("review_decision", "missing")),
        "target_human_review_status": str(validation.get("target_human_review_status", "missing")),
        "review_reference_hash": str(validation.get("review_reference_hash", "")),
        "review_notes_hash": str(validation.get("review_notes_hash", "")),
        "reviewer_roles": list(validation.get("reviewer_roles", []) or []),
        "reviewer_role_count": len(list(validation.get("reviewer_roles", []) or [])),
        "source_card_ids": list(validation.get("source_card_ids", []) or [])[:12],
        "raw_text_reviewed_locally": bool(validation.get("raw_text_reviewed_locally", False)),
        "validation_status": str(validation.get("status", "blocked")),
        "issues": list(validation.get("issues", []) or []),
        "warnings": list(validation.get("warnings", []) or []),
        "raw_review_reference_stored": False,
        "raw_review_notes_stored": False,
        "raw_text_stored": False,
        "local_path_stored": False,
    }
    event_payload = {key: value for key, value in event.items() if key != "validation_hash"}
    event["validation_hash"] = sha256_text(json.dumps(event_payload, sort_keys=True, ensure_ascii=False))
    record = {
        "schema_version": EXTRACTION_HUMAN_REVIEW_SCHEMA_VERSION,
        "artifact_type": "course_extraction_human_review_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if event["validation_status"] == "ok_human_review_decision" and not event["issues"] else "blocked",
        "event": event,
        "storage_policy": (
            "local-only jsonl; stores reviewer roles, decision status, hashes, and source-card ids only; "
            "no raw extracted text, raw review notes, raw review references, or local paths"
        ),
    }
    if public_safe:
        scan = scan_text(json.dumps(record, ensure_ascii=False), "extraction-human-review-journal-record")
        record["public_safety_status"] = scan["status"]
        if scan["status"] != "pass":
            record["status"] = "blocked"
            record["public_safety_findings"] = scan["findings"]
    else:
        record["public_safety_status"] = "local_private_mode"
    return record


def normalized_reviewer_roles(decision: dict[str, Any]) -> list[str]:
    roles = decision.get("reviewer_roles", decision.get("reviewer_role", []))
    if isinstance(roles, str):
        roles = [roles]
    if not isinstance(roles, list):
        return []
    return [str(item).strip() for item in roles if str(item).strip()][:8]


def review_reference_hash_from_decision(decision: dict[str, Any]) -> str:
    supplied_hash = str(decision.get("review_reference_hash", "")).strip()
    if SHA256_RE.match(supplied_hash):
        return supplied_hash.lower()
    reference = str(decision.get("review_reference", "")).strip()
    return sha256_text(reference) if reference else ""


def review_notes_hash_from_decision(decision: dict[str, Any]) -> str:
    supplied_hash = str(decision.get("review_notes_hash", "")).strip()
    if SHA256_RE.match(supplied_hash):
        return supplied_hash.lower()
    notes = str(decision.get("review_notes", "")).strip()
    return sha256_text(notes) if notes else ""


def reviewed_receipt_from_decision(
    receipt: dict[str, Any],
    *,
    target_human_review_status: str,
) -> dict[str, Any]:
    return {
        "job_id": str(receipt.get("job_id", "")),
        "material_id": str(receipt.get("material_id", "")),
        "job_type": str(receipt.get("job_type", "")),
        "extraction_status": str(receipt.get("extraction_status", "")),
        "raw_text_sha256": str(receipt.get("raw_text_sha256", "")),
        "extracted_text_char_count": int(receipt.get("extracted_text_char_count", 0) or 0),
        "private_artifact_reference": str(receipt.get("private_artifact_reference", "")),
        "human_review_status": target_human_review_status,
        "decision_reference_hash": str(receipt.get("decision_reference_hash", "")),
    }


def latest_receipts_by_job(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        job_id = str(receipt.get("job_id", "")).strip()
        if not job_id:
            anonymous.append(receipt)
            continue
        ordered[job_id] = receipt
    return [*ordered.values(), *anonymous]


def ready_receipts_by_job(
    receipts: list[dict[str, Any]],
    *,
    decision_reference_hash: str,
) -> dict[str, dict[str, Any]]:
    ready: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        validation = validate_extraction_receipt(
            receipt,
            decision_reference_hash=decision_reference_hash,
        )
        if validation.get("ready_for_human_review_queue"):
            ready[str(validation.get("job_id", ""))] = receipt
    return ready


def review_decision_summary(review_results: list[dict[str, Any]], review_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    stored = [item for item in review_results if item.get("status") == "stored"]
    invalid = [item for item in review_results if item.get("status") != "stored"]
    by_decision: dict[str, int] = {}
    for item in review_results:
        decision = str(item.get("review_decision", "missing"))
        by_decision[decision] = by_decision.get(decision, 0) + 1
    return {
        "submitted_review_decision_count": len(review_decisions),
        "processed_review_decision_count": len(review_results),
        "stored_review_decision_count": len(stored),
        "invalid_review_decision_count": len(invalid),
        "appended_review_receipt_count": len([item for item in stored if item.get("review_receipt_appended")]),
        "appended_review_record_count": len([item for item in stored if item.get("review_record_appended")]),
        "by_review_decision": dict(sorted(by_decision.items())),
    }


def public_review_results(review_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in review_results[:40]:
        validation = item.get("validation", {}) if isinstance(item.get("validation"), dict) else {}
        rows.append(
            {
                "status": item.get("status", "unknown"),
                "job_id": item.get("job_id", validation.get("job_id", "")),
                "material_id": item.get("material_id", validation.get("material_id", "")),
                "review_decision": item.get("review_decision", validation.get("review_decision", "")),
                "target_human_review_status": item.get(
                    "target_human_review_status",
                    validation.get("target_human_review_status", ""),
                ),
                "review_receipt_appended": bool(item.get("review_receipt_appended", False)),
                "review_record_appended": bool(item.get("review_record_appended", False)),
                "review_reference_hash": item.get("review_reference_hash", validation.get("review_reference_hash", "")),
                "issues": list(item.get("issues", validation.get("issues", [])) or []),
                "warnings": list(item.get("warnings", validation.get("warnings", [])) or []),
                "raw_text_returned": False,
                "local_paths_returned": False,
            }
        )
    return rows


def progress_public_summary(progress: dict[str, Any]) -> dict[str, Any]:
    receipt = progress.get("receipt_summary", {})
    return {
        "status": progress.get("status", "unknown"),
        "valid_receipt_count": receipt.get("valid_receipt_count", 0),
        "ready_for_human_review_count": receipt.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": receipt.get("eligible_for_private_tutor_index_count", 0),
        "invalid_receipt_count": receipt.get("invalid_receipt_count", 0),
        "public_safety_status": progress.get("public_safety_status", "unknown"),
    }


def manifest_public_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    summary = manifest.get("candidate_summary", {})
    return {
        "status": manifest.get("status", "unknown"),
        "candidate_count": summary.get("candidate_count", 0),
        "ready_to_apply_private_count": summary.get("ready_to_apply_private_count", 0),
        "blocked_candidate_count": summary.get("blocked_candidate_count", 0),
        "public_safety_status": manifest.get("public_safety_status", "unknown"),
    }


def coverage_public_summary(coverage: dict[str, Any]) -> dict[str, Any]:
    projected = coverage.get("projected_scope_summary", {})
    return {
        "status": coverage.get("status", "unknown"),
        "candidate_material_count": projected.get("candidate_material_count", 0),
        "ready_skill_uplift": projected.get("ready_skill_uplift", 0),
        "public_safety_status": coverage.get("public_safety_status", "unknown"),
    }


def human_review_plan_status(
    *,
    authorized: bool,
    decisions_submitted: bool,
    invalid_results: list[dict[str, Any]],
    appended_count: int,
    ready_count: int,
    candidate_count: int,
    receipt_count: int,
) -> str:
    if not authorized:
        return "blocked_until_valid_rights_privacy_decision"
    if invalid_results:
        return "blocked_invalid_human_review_decisions"
    if appended_count and candidate_count:
        return "review_decisions_recorded_manifest_apply_plan_ready"
    if appended_count:
        return "review_decisions_recorded_no_manifest_candidates"
    if candidate_count:
        return "manifest_apply_plan_ready_from_reviewed_receipts"
    if ready_count:
        return "waiting_for_human_review_decisions"
    if receipt_count:
        return "waiting_for_accepted_human_review"
    if decisions_submitted:
        return "blocked_no_review_ready_receipts"
    return "waiting_for_review_ready_receipts"


def human_review_next_actions(
    authorized: bool,
    invalid_results: list[dict[str, Any]],
    progress: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
) -> list[str]:
    if not authorized:
        return ["Record a valid local rights/privacy decision before accepting human review decisions."]
    if invalid_results:
        return ["Fix invalid review decisions, especially missing local review confirmation, reviewer role, or hash reference."]
    if manifest.get("status") == "ready_for_private_manifest_update":
        return ["Apply the reviewed metadata privately, then rebuild ExamScopeMap and tutor coverage."]
    if progress.get("status") == "receipts_ready_for_human_review":
        return ["Review the local private OCR artifacts and submit accepted_for_private_tutor or rejected decisions."]
    if coverage.get("status") == "coverage_uplift_ready_after_private_manifest_update":
        return ["After private manifest apply, rerun tutor eval and inspect remaining skill gaps."]
    return ["Run or inspect local extraction receipts, then regenerate the human review apply plan."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "extraction-human-review-apply-plan")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
