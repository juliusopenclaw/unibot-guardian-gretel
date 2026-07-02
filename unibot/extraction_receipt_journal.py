from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extraction_operator import validate_extraction_receipt
from .materials import sha256_text
from .public_safety import scan_text


EXTRACTION_RECEIPT_JOURNAL_SCHEMA_VERSION = "unibot-extraction-receipt-journal-v1"
DEFAULT_EXTRACTION_RECEIPT_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "extraction_receipts.jsonl"


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
