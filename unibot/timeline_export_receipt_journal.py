from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .timeline_export_review_packet import build_timeline_export_review_packet


TIMELINE_EXPORT_RECEIPT_JOURNAL_SCHEMA_VERSION = "unibot-timeline-export-receipt-journal-v1"
DEFAULT_TIMELINE_EXPORT_RECEIPT_JOURNAL_PATH = (
    Path.home() / ".unibot_guardian" / "timeline_export_receipts.jsonl"
)


def resolve_timeline_export_receipt_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_TIMELINE_EXPORT_RECEIPT_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_TIMELINE_EXPORT_RECEIPT_JOURNAL_PATH


def build_timeline_export_receipt_journal_append(
    *,
    review_packet: dict[str, Any] | None = None,
    journal_path: str | Path | None = None,
    operator_confirmed_timeline_export_receipt_journal_append: bool = False,
    public_safe: bool = True,
    **review_packet_kwargs: Any,
) -> dict[str, Any]:
    packet = review_packet if isinstance(review_packet, dict) else build_timeline_export_review_packet(
        public_safe=public_safe,
        **review_packet_kwargs,
    )
    record = sanitize_timeline_export_receipt_record(packet)
    will_write = bool(operator_confirmed_timeline_export_receipt_journal_append and record.get("status") == "accepted")
    append_status = "stored" if will_write else "write_preview_ready"
    if operator_confirmed_timeline_export_receipt_journal_append and record.get("status") != "accepted":
        append_status = "blocked_record_not_accepted"
    if will_write:
        target = resolve_timeline_export_receipt_journal_path(journal_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    payload = {
        "schema_version": TIMELINE_EXPORT_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "timeline_export_receipt_journal_append",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": append_status,
        "exam_deployment_status": "not_cleared",
        "journal_written": will_write,
        "operator_confirmation_required_for_write": True,
        "operator_confirmed_timeline_export_receipt_journal_append": bool(
            operator_confirmed_timeline_export_receipt_journal_append
        ),
        "write_preview": {
            "status": "ready_to_append" if record.get("status") == "accepted" else "blocked",
            "would_append": bool(record.get("status") == "accepted"),
            "record_status": record.get("status", "blocked"),
            "receipt_id": record.get("event", {}).get("receipt_id", ""),
            "skill_tags": record.get("event", {}).get("skill_tags", []),
            "event_count": record.get("event", {}).get("event_count", 0),
            "checkpoint_hash_count": record.get("event", {}).get("checkpoint_hash_count", 0),
            "reviewer_question_count": record.get("event", {}).get("reviewer_question_count", 0),
            "open_operator_confirmation_count": record.get("event", {}).get("open_operator_confirmation_count", 0),
        },
        "stored_record": record if will_write else None,
        "preview_record": record if not will_write else None,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "storage_policy": (
            "local jsonl receipt journal; API output stores receipt metadata, counts, hashes, help profile, "
            "reflection status, and not_cleared status only; no raw text, notebook code, values, or paths"
        ),
        "next_actions": [
            "Review the write preview before appending the receipt journal record.",
            "Append only with explicit operator confirmation.",
            "Use the journal summary to verify repeated review packets over time.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe, source_name="timeline-export-receipt-journal-append")
    return payload


def sanitize_timeline_export_receipt_record(review_packet: dict[str, Any] | None) -> dict[str, Any]:
    packet = review_packet if isinstance(review_packet, dict) else {}
    summary = packet.get("export_review_summary", {}) if isinstance(packet.get("export_review_summary"), dict) else {}
    receipt = packet.get("local_export_receipt", {}) if isinstance(packet.get("local_export_receipt"), dict) else {}
    issues: list[str] = []
    if packet.get("artifact_type") != "timeline_export_review_packet":
        issues.append("review_packet_artifact_type_invalid")
    if packet.get("exam_deployment_status") != "not_cleared":
        issues.append("exam_deployment_must_remain_not_cleared")
    if packet.get("public_safety_status") not in {"pass", "local_private_mode"}:
        issues.append("review_packet_public_safety_must_pass")
    if receipt.get("status") != "timeline_export_review_packet_receipt_ready_not_exam_clearance":
        issues.append("local_export_receipt_status_invalid")
    if not receipt.get("receipt_id") or not receipt.get("receipt_hash"):
        issues.append("local_export_receipt_hash_required")
    for flag in [
        "raw_query_returned",
        "raw_text_returned",
        "raw_cell_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]:
        if packet.get(flag) is True:
            issues.append(f"{flag}_must_be_false")
    packet_hash = sha256_text(json.dumps(packet, sort_keys=True, ensure_ascii=False)) if packet else ""
    event = {
        "event_type": "timeline_export_review_packet_receipt",
        "receipt_id": str(receipt.get("receipt_id", "")),
        "receipt_hash": str(receipt.get("receipt_hash", "")),
        "review_packet_hash": packet_hash,
        "skill_tags": [str(item) for item in (summary.get("skill_tags", []) or [])],
        "event_count": int(summary.get("event_count", 0) or 0),
        "timeline_count": int(summary.get("timeline_count", 0) or 0),
        "packet_receipt_count": int(summary.get("packet_receipt_count", 0) or 0),
        "timeline_receipt_count": int(summary.get("timeline_receipt_count", 0) or 0),
        "checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
        "reviewer_question_count": int(summary.get("reviewer_question_count", 0) or 0),
        "help_level_profile": dict(summary.get("help_level_profile", {}) or {}),
        "open_operator_confirmation_count": int(summary.get("open_operator_confirmation_count", 0) or 0),
        "reflection_statuses": [str(item) for item in (summary.get("reflection_statuses", []) or [])],
        "exam_deployment_status": "not_cleared",
        "raw_text_stored": False,
        "notebook_code_stored": False,
        "local_path_stored": False,
        "issues": sorted(set(issues)),
    }
    record = {
        "schema_version": TIMELINE_EXPORT_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "timeline_export_receipt_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if not event["issues"] else "blocked",
        "event": event,
        "storage_policy": (
            "local-only jsonl; stores receipt id/hash, skill tags, counts, help profile, reflection status, "
            "and not_cleared status only"
        ),
    }
    attach_public_scan(record, public_safe=True, source_name="timeline-export-receipt-journal-record")
    if record.get("public_safety_status") != "pass":
        record["status"] = "blocked"
    return record


def read_timeline_export_receipt_journal(
    path: str | Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    journal_path = resolve_timeline_export_receipt_journal_path(path)
    if not journal_path.exists():
        return {"status": "empty", "count": 0, "records": []}
    rows = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "count": len(rows), "records": rows}


def summarize_timeline_export_receipt_journal(path: str | Path | None = None) -> dict[str, Any]:
    journal = read_timeline_export_receipt_journal(path)
    records = [record for record in journal.get("records", []) if isinstance(record, dict)]
    events = [record.get("event", {}) for record in records if isinstance(record.get("event"), dict)]
    accepted = [record for record in records if record.get("status") == "accepted"]
    blocked = [record for record in records if record.get("status") == "blocked"]
    skill_tags = unique_values(skill for event in events for skill in (event.get("skill_tags", []) or []))
    help_profile: dict[str, int] = {}
    reflection_statuses = []
    for event in events:
        for level, count in dict(event.get("help_level_profile", {}) or {}).items():
            help_profile[str(level)] = help_profile.get(str(level), 0) + int(count or 0)
        for status in event.get("reflection_statuses", []) or []:
            if status not in reflection_statuses:
                reflection_statuses.append(status)
    summary = {
        "schema_version": TIMELINE_EXPORT_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "timeline_export_receipt_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": journal.get("status", "empty"),
        "record_count": len(records),
        "accepted_record_count": len(accepted),
        "blocked_record_count": len(blocked),
        "skill_tags": skill_tags,
        "event_count": sum(int(event.get("event_count", 0) or 0) for event in events),
        "checkpoint_hash_count": sum(int(event.get("checkpoint_hash_count", 0) or 0) for event in events),
        "reviewer_question_count": sum(int(event.get("reviewer_question_count", 0) or 0) for event in events),
        "open_operator_confirmation_count": sum(
            int(event.get("open_operator_confirmation_count", 0) or 0) for event in events
        ),
        "help_level_profile": help_profile,
        "reflection_statuses": reflection_statuses,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "storage_policy": "summary excludes raw queries, course raw text, notebook code, values, solutions, and paths",
        "gate_policy": "journal entries are review evidence only; they do not authorize exam deployment",
    }
    attach_public_scan(summary, public_safe=True, source_name="timeline-export-receipt-journal-summary")
    return summary


def unique_values(values: Any) -> list[str]:
    result = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
