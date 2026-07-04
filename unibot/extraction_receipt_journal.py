from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extraction_operator import validate_extraction_receipt
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card


EXTRACTION_RECEIPT_JOURNAL_SCHEMA_VERSION = "unibot-extraction-receipt-journal-v1"
EXTRACTION_RECEIPT_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-extraction-receipt-journal-release-review-board-claim-alignment-v1"
)
DEFAULT_EXTRACTION_RECEIPT_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "extraction_receipts.jsonl"


def synthetic_extraction_receipt_decision_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic extraction receipt journal decision",
    }


def synthetic_extraction_receipt(*, human_review_status: str = "pending_review") -> dict[str, Any]:
    decision_reference = str(synthetic_extraction_receipt_decision_record()["decision_reference"])
    return {
        "job_id": "synthetic-receipt-job-1",
        "material_id": "synthetic-material-1",
        "job_type": "ocr",
        "extraction_status": "extracted_private",
        "raw_text_sha256": "d" * 64,
        "extracted_text_char_count": 640,
        "private_artifact_reference": "synthetic local private extraction artifact reference",
        "human_review_status": human_review_status,
        "decision_reference_hash": sha256_text(decision_reference),
    }


def resolve_extraction_receipt_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_EXTRACTION_RECEIPT_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_EXTRACTION_RECEIPT_JOURNAL_PATH


def sanitize_extraction_receipt_record(
    receipt: dict[str, Any] | None,
    *,
    decision_record: dict[str, Any] | None = None,
    decision_reference_hash: str | None = None,
) -> dict[str, Any]:
    validation = validate_extraction_receipt(
        receipt or {},
        decision_record=decision_record or {},
        decision_reference_hash=decision_reference_hash,
    )
    issues = list(validation.get("issues", []) or [])
    if validation.get("status") == "blocked":
        issues.append("receipt_validation_blocked")
    if validation.get("raw_text_stored_in_receipt") is True:
        issues.append("raw_text_fields_must_not_be_stored")

    event = {
        "event_type": "extraction_receipt_validated",
        "job_id": str(validation.get("job_id", "")),
        "material_id": str(validation.get("material_id", "")),
        "job_type": str(validation.get("job_type", "missing")),
        "extraction_status": str(validation.get("extraction_status", "missing")),
        "human_review_status": str(validation.get("human_review_status", "missing")),
        "raw_text_sha256": str(validation.get("raw_text_sha256", "")),
        "extracted_text_char_count": int(validation.get("extracted_text_char_count", 0) or 0),
        "private_artifact_reference_hash": str(validation.get("private_artifact_reference_hash", "")),
        "decision_reference_hash": str(validation.get("decision_reference_hash", "")),
        "receipt_validation_status": str(validation.get("status", "blocked")),
        "ready_for_human_review_queue": bool(validation.get("ready_for_human_review_queue", False)),
        "eligible_for_private_tutor_index": bool(validation.get("eligible_for_private_tutor_index", False)),
        "validation_hash": sha256_text(json.dumps(validation, sort_keys=True, ensure_ascii=False)),
        "issues": sorted(set(issues)),
        "warnings": sorted(set(validation.get("warnings", []) or [])),
        "raw_text_stored": False,
        "local_path_stored": False,
    }
    record = {
        "schema_version": EXTRACTION_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "course_extraction_receipt_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if not event["issues"] else "blocked",
        "event": event,
        "storage_policy": (
            "local-only jsonl; stores receipt hashes, statuses, counts, and review metadata only; "
            "no raw extracted course text or local paths"
        ),
    }
    scan = scan_text(json.dumps(record, ensure_ascii=False), "extraction-receipt-journal-record")
    record["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        record["status"] = "blocked"
        record["public_safety_findings"] = scan["findings"]
    return record


def append_extraction_receipt_record(
    receipt: dict[str, Any],
    *,
    decision_record: dict[str, Any] | None = None,
    decision_reference_hash: str | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    record = sanitize_extraction_receipt_record(
        receipt,
        decision_record=decision_record,
        decision_reference_hash=decision_reference_hash,
    )
    journal_path = resolve_extraction_receipt_journal_path(path)
    if record["status"] != "accepted":
        return {
            "status": "blocked",
            "path": str(journal_path),
            "record": record,
        }
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "stored",
        "path": str(journal_path),
        "record": record,
    }


def read_extraction_receipt_journal(path: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    journal_path = resolve_extraction_receipt_journal_path(path)
    if not journal_path.exists():
        return {"status": "empty", "path": str(journal_path), "count": 0, "records": [], "receipts_for_progress": []}
    rows = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {
        "status": "ok",
        "path": str(journal_path),
        "count": len(rows),
        "records": rows,
        "receipts_for_progress": extraction_receipts_for_progress(records=rows),
    }


def summarize_extraction_receipt_journal(path: str | Path | None = None) -> dict[str, Any]:
    payload = read_extraction_receipt_journal(path)
    return summarize_extraction_receipt_records(payload.get("records", []), status=str(payload.get("status", "empty")))


def summarize_extraction_receipt_records(records: list[dict[str, Any]], *, status: str = "ok") -> dict[str, Any]:
    events = [record.get("event", {}) for record in records if isinstance(record, dict)]
    by_job_type: dict[str, int] = {}
    by_review_status: dict[str, int] = {}
    duplicate_job_ids = duplicate_values([str(event.get("job_id", "")) for event in events if event.get("job_id")])
    accepted = [record for record in records if record.get("status") == "accepted"]
    blocked = [record for record in records if record.get("status") == "blocked"]
    ready = [event for event in events if event.get("ready_for_human_review_queue")]
    eligible = [event for event in events if event.get("eligible_for_private_tutor_index")]
    failed_or_skipped = [event for event in events if event.get("extraction_status") in {"failed", "skipped"}]
    for event in events:
        job_type = str(event.get("job_type", "missing"))
        review_status = str(event.get("human_review_status", "missing"))
        by_job_type[job_type] = by_job_type.get(job_type, 0) + 1
        by_review_status[review_status] = by_review_status.get(review_status, 0) + 1
    summary = {
        "schema_version": EXTRACTION_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "course_extraction_receipt_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "record_count": len(records),
        "accepted_record_count": len(accepted),
        "blocked_record_count": len(blocked),
        "ready_for_human_review_count": len(ready),
        "eligible_for_private_tutor_index_count": len(eligible),
        "failed_or_skipped_count": len(failed_or_skipped),
        "duplicate_job_id_count": len(duplicate_job_ids),
        "duplicate_job_ids": duplicate_job_ids[:20],
        "by_job_type": dict(sorted(by_job_type.items())),
        "by_human_review_status": dict(sorted(by_review_status.items())),
        "progress_receipt_count": len(extraction_receipts_for_progress(records=records)),
        "storage_policy": "summary excludes raw OCR text, raw transcripts, local paths, and private artifact references",
        "gate_policy": "journal entries are extraction evidence only; they do not update the tutor manifest or clear exam deployment",
    }
    scan = scan_text(json.dumps(summary, ensure_ascii=False), "extraction-receipt-journal-summary")
    summary["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        summary["status"] = "blocked_public_safety"
        summary["public_safety_findings"] = scan["findings"]
    return summary


def build_extraction_receipt_journal_release_claim_alignment(
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if records is None:
        decision = synthetic_extraction_receipt_decision_record()
        pending_receipt = synthetic_extraction_receipt(human_review_status="pending_review")
        reviewed_receipt = synthetic_extraction_receipt(human_review_status="reviewed_for_private_tutor")
        reviewed_receipt["job_id"] = "synthetic-receipt-job-2"
        reviewed_receipt["material_id"] = "synthetic-material-2"
        records = [
            sanitize_extraction_receipt_record(
                pending_receipt,
                decision_record=decision,
            ),
            sanitize_extraction_receipt_record(
                reviewed_receipt,
                decision_record=decision,
            ),
        ]
    summary = summarize_extraction_receipt_records(records)
    progress_receipts = extraction_receipts_for_progress(records=records)
    sections = [
        {
            "section_id": "receipt_hash_storage_trace",
            "summary_claim": "receipt journal stores receipt hashes, counts, statuses, and review metadata without raw extracted text or local paths",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": ["extraction_receipt_journal", "data_protection_screening", "public_safety"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "local_private_processing_trace",
            "summary_claim": "receipt evidence supports local-private processing only and does not authorize cloud processing or public raw text release",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["extraction_receipt_journal", "external_decision_state", "course_material_policy"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "public_safety_required"],
        },
        {
            "section_id": "human_review_queue_trace",
            "summary_claim": "reviewed receipts may feed progress metadata, but tutor-index or manifest updates remain separate human-reviewed steps",
            "source_card_ids": ["dfg-gwp"],
            "readiness_check_ids": ["extraction_receipt_journal", "review_board_packet", "release_runbook"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "receipt journals do not clear exam deployment, grading, proctoring, KI-detection evidence, or high-stakes education claims",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq"],
            "readiness_check_ids": ["extraction_receipt_journal", "exam_boundary", "gretel_bachelor_thesis_package"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    accepted_records = [record for record in records if record.get("status") == "accepted"]
    events = [record.get("event", {}) for record in accepted_records]
    blocked_claims = [
        "raw extracted text storage",
        "local path storage",
        "private artifact reference exposure",
        "tutor manifest update by receipt alone",
        "public raw course text release",
        "cloud processing",
        "exam deployment",
        "official grading",
        "proctoring",
        "KI-detection evidence",
    ]
    contracts = {
        "records_public_safe": all(record.get("public_safety_status") == "pass" for record in records),
        "records_accepted": bool(accepted_records) and len(accepted_records) == len(records),
        "summary_public_safe": summary.get("public_safety_status") == "pass",
        "summary_blocks_manifest_and_exam_clearance": "do not update the tutor manifest or clear exam deployment"
        in summary.get("gate_policy", ""),
        "summary_excludes_raw_and_paths": "excludes raw OCR text, raw transcripts, local paths, and private artifact references"
        in summary.get("storage_policy", ""),
        "records_hash_only": all(
            event.get("raw_text_stored") is False
            and event.get("local_path_stored") is False
            and bool(event.get("raw_text_sha256"))
            and bool(event.get("private_artifact_reference_hash"))
            and bool(event.get("decision_reference_hash"))
            for event in events
        ),
        "human_review_queue_linked": summary.get("ready_for_human_review_count", 0) >= 1,
        "private_tutor_index_still_separate": summary.get("eligible_for_private_tutor_index_count", 0) >= 1
        and all("private-artifact-hash:" in receipt.get("private_artifact_reference", "") for receipt in progress_receipts),
        "no_duplicate_job_ids": summary.get("duplicate_job_id_count") == 0,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "summary": summary,
        "progress_receipt_count": len(progress_receipts),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "extraction-receipt-journal-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXTRACTION_RECEIPT_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "record_count": len(records),
        "accepted_record_count": len(accepted_records),
        "summary_status": summary.get("status"),
        "summary_public_safety_status": summary.get("public_safety_status"),
        "ready_for_human_review_count": summary.get("ready_for_human_review_count", 0),
        "eligible_for_private_tutor_index_count": summary.get("eligible_for_private_tutor_index_count", 0),
        "progress_receipt_count": len(progress_receipts),
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
            "Extraction receipt journals are local-private evidence ledgers only; they may expose hashes, counts, "
            "statuses, and review metadata, but they do not store raw extracted text, expose local paths, update the "
            "tutor manifest by themselves, clear cloud processing, grade, proctor, detect KI, or clear exam use."
        ),
    }


def extraction_receipts_for_progress(
    path: str | Path | None = None,
    *,
    records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if records is None:
        records = read_extraction_receipt_journal(path).get("records", [])
    receipts = []
    for record in records:
        if not isinstance(record, dict) or record.get("status") != "accepted":
            continue
        event = record.get("event", {})
        private_ref_hash = str(event.get("private_artifact_reference_hash", ""))
        receipts.append(
            {
                "job_id": str(event.get("job_id", "")),
                "material_id": str(event.get("material_id", "")),
                "job_type": str(event.get("job_type", "")),
                "extraction_status": str(event.get("extraction_status", "")),
                "raw_text_sha256": str(event.get("raw_text_sha256", "")),
                "extracted_text_char_count": int(event.get("extracted_text_char_count", 0) or 0),
                "private_artifact_reference": f"private-artifact-hash:{private_ref_hash}",
                "human_review_status": str(event.get("human_review_status", "")),
                "decision_reference_hash": str(event.get("decision_reference_hash", "")),
            }
        )
    return receipts


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)
