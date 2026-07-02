from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID
from .decision_request import build_stakeholder_decision_request, validate_decision_request_receipt
from .materials import sha256_text
from .public_safety import scan_text


DECISION_JOURNAL_SCHEMA_VERSION = "unibot-stakeholder-decision-journal-v1"
DEFAULT_DECISION_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "stakeholder_decision_journal.jsonl"
ALLOWED_JOURNAL_EVENT_TYPES = {"decision_request_prepared", "decision_request_receipt_validated"}


def resolve_decision_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_DECISION_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_DECISION_JOURNAL_PATH


def append_decision_request_journal_event(
    event: dict[str, Any],
    *,
    path: str | Path | None = None,
) -> dict[str, Any]:
    record = sanitize_decision_journal_event(event)
    if record["status"] != "accepted":
        return {
            "status": "blocked",
            "path": str(resolve_decision_journal_path(path)),
            "record": record,
        }
    journal_path = resolve_decision_journal_path(path)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "stored",
        "path": str(journal_path),
        "record": record,
    }


def sanitize_decision_journal_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event or {})
    event_type = str(payload.get("event_type", "")).strip()
    issues: list[str] = []
    warnings: list[str] = []
    if event_type not in ALLOWED_JOURNAL_EVENT_TYPES:
        issues.append("unsupported_event_type")

    if event_type == "decision_request_prepared":
        safe_event = request_prepared_event(payload, issues, warnings)
    elif event_type == "decision_request_receipt_validated":
        safe_event = receipt_validated_event(payload, issues, warnings)
    else:
        safe_event = {
            "event_type": event_type or "missing",
            "request_id": str(payload.get("request_id", "")).strip() or "missing",
            "lane_id": str(payload.get("lane_id", "")).strip() or "missing",
        }

    safe_event["issues"] = sorted(set(issues))
    safe_event["warnings"] = sorted(set(warnings))
    safe_event["raw_text_stored"] = False
    safe_event["tool_sent_message"] = bool(payload.get("tool_sent_message", False))
    if safe_event["tool_sent_message"]:
        issues.append("tool_sent_message_must_remain_false")
        safe_event["issues"] = sorted(set(issues))

    record = {
        "schema_version": DECISION_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_decision_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if not safe_event["issues"] else "blocked",
        "event": safe_event,
        "storage_policy": "local-only jsonl; stores hashes, statuses, and lane metadata only; no raw messages or written decisions",
    }
    scan = scan_text(json.dumps(record, ensure_ascii=False), "decision-journal-record")
    record["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        record["status"] = "blocked"
        record["public_safety_findings"] = scan["findings"]
    return record


def request_prepared_event(payload: dict[str, Any], issues: list[str], warnings: list[str]) -> dict[str, Any]:
    request = payload.get("request")
    if not isinstance(request, dict):
        issues.append("request_required")
        request = {}
    if request and request.get("artifact_type") != "unibot_stakeholder_decision_request":
        issues.append("request_artifact_type_invalid")
    if request and request.get("status") != "ready_for_manual_review_not_sent":
        issues.append("request_must_be_ready_not_sent")
    if request and request.get("public_safety_status") != "pass":
        issues.append("request_public_safety_must_pass")
    if request and request.get("exam_deployment_status") != "not_cleared":
        issues.append("exam_deployment_must_remain_not_cleared")
    if request.get("receipt_template", {}).get("tool_sent_message") is not False:
        issues.append("receipt_template_must_not_claim_tool_send")

    markdown = str(payload.get("markdown", "") or "")
    if markdown and scan_text(markdown, "decision-request-journal-markdown")["status"] != "pass":
        issues.append("markdown_public_safety_must_pass")
    if not markdown:
        warnings.append("markdown_not_recorded_hash_empty")

    request_id = str(request.get("request_id", payload.get("request_id", ""))).strip()
    lane_id = str(request.get("lane_id", payload.get("lane_id", ""))).strip()
    return {
        "event_type": "decision_request_prepared",
        "request_id": request_id or "missing",
        "lane_id": lane_id or "missing",
        "request_status": request.get("status", "missing"),
        "exam_deployment_status": request.get("exam_deployment_status", "not_cleared"),
        "request_hash": sha256_text(json.dumps(request, sort_keys=True, ensure_ascii=False)) if request else "",
        "markdown_hash": sha256_text(markdown) if markdown else "",
        "reviewer_role_count": len(request.get("target_reviewer_roles", []) or []),
        "evidence_count": len(request.get("evidence_manifest", []) or []),
        "manual_submission_status": request.get("receipt_template", {}).get("manual_submission_status", "missing"),
    }


def receipt_validated_event(payload: dict[str, Any], issues: list[str], warnings: list[str]) -> dict[str, Any]:
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict):
        issues.append("receipt_required")
        receipt = {}
    validation = validate_decision_request_receipt(receipt)
    if validation.get("status") == "blocked":
        issues.append("receipt_validation_blocked")
    if validation.get("public_safety_status") != "pass":
        issues.append("receipt_public_safety_must_pass")
    if validation.get("tool_sent_message") is True:
        issues.append("receipt_must_not_claim_tool_send")
    if validation.get("raw_decision_text_included") is True:
        issues.append("receipt_must_not_include_raw_decision_text")
    if validation.get("status") == "draft_receipt_not_sent":
        warnings.append("draft_receipt_records_no_external_submission")
    return {
        "event_type": "decision_request_receipt_validated",
        "request_id": validation.get("request_id", "missing"),
        "lane_id": validation.get("lane_id", "missing"),
        "receipt_validation_status": validation.get("status"),
        "manual_submission_status": validation.get("manual_submission_status"),
        "receipt_effect": validation.get("receipt_effect"),
        "submission_reference_hash": validation.get("submission_reference_hash", ""),
        "validation_hash": sha256_text(json.dumps(validation, sort_keys=True, ensure_ascii=False)),
        "raw_submission_reference_stored": False,
    }


def append_prepared_request_to_journal(
    *,
    lane_id: str = "rights_privacy_local_extraction",
    course_id: str = DEFAULT_COURSE_ID,
    base_path: str | None = None,
    review_policy: str = "staged",
    markdown: str = "",
    path: str | Path | None = None,
) -> dict[str, Any]:
    request = build_stakeholder_decision_request(
        course_id,
        lane_id=lane_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=True,
    )
    return append_decision_request_journal_event(
        {
            "event_type": "decision_request_prepared",
            "request": request,
            "markdown": markdown,
        },
        path=path,
    )


def read_decision_journal(path: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    journal_path = resolve_decision_journal_path(path)
    if not journal_path.exists():
        return {"status": "empty", "path": str(journal_path), "count": 0, "events": []}
    rows = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "path": str(journal_path), "count": len(rows), "events": rows}


def summarize_decision_journal(path: str | Path | None = None) -> dict[str, Any]:
    payload = read_decision_journal(path)
    events = [row.get("event", {}) for row in payload.get("events", [])]
    by_event_type: dict[str, int] = {}
    by_lane: dict[str, int] = {}
    sent_receipt_count = 0
    draft_receipt_count = 0
    blocked_record_count = 0
    for row in payload.get("events", []):
        if row.get("status") == "blocked":
            blocked_record_count += 1
    for event in events:
        event_type = str(event.get("event_type", "missing"))
        lane_id = str(event.get("lane_id", "missing"))
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        by_lane[lane_id] = by_lane.get(lane_id, 0) + 1
        if event.get("receipt_validation_status") == "ok_manual_request_receipt":
            sent_receipt_count += 1
        if event.get("receipt_validation_status") == "draft_receipt_not_sent":
            draft_receipt_count += 1
    return {
        "schema_version": DECISION_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_decision_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": payload.get("status"),
        "path": payload.get("path"),
        "event_count": len(events),
        "blocked_record_count": blocked_record_count,
        "sent_receipt_count": sent_receipt_count,
        "draft_receipt_count": draft_receipt_count,
        "by_event_type": by_event_type,
        "by_lane": by_lane,
        "storage_policy": "summary excludes raw request text, mail text, decision text, names, and local course paths",
        "gate_policy": "journal entries are process evidence only; they do not authorize extraction or exam deployment",
    }
