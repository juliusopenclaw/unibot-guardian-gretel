from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clearance import validate_clearance_record
from .extraction_completion import validate_extraction_deferral_record
from .extraction_decision import validate_extraction_decision_record
from .materials import sha256_text
from .public_safety import scan_text


EXTERNAL_DECISION_JOURNAL_SCHEMA_VERSION = "unibot-external-decision-record-journal-v1"
DEFAULT_EXTERNAL_DECISION_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "external_decision_records.jsonl"

DECISION_RECORD_TYPES = {
    "local_extraction_decision",
    "exam_clearance",
    "extraction_deferral",
    "manual_deployment_go",
}


def resolve_external_decision_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_EXTERNAL_DECISION_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_EXTERNAL_DECISION_JOURNAL_PATH


def sanitize_external_decision_record_event(
    *,
    record_type: str,
    record: dict[str, Any] | None = None,
    deployment_go_reference: str | None = None,
) -> dict[str, Any]:
    normalized_type = str(record_type or "").strip()
    issues: list[str] = []
    warnings: list[str] = []
    if normalized_type not in DECISION_RECORD_TYPES:
        issues.append("unsupported_decision_record_type")

    validation: dict[str, Any] = {}
    event: dict[str, Any]
    if normalized_type == "local_extraction_decision":
        validation = validate_extraction_decision_record(record or {})
        accepted = validation.get("status") == "ok_authorizes_local_extraction"
        event = {
            "record_type": normalized_type,
            "validation_status": validation.get("status", "blocked"),
            "accepted_for_gate": accepted,
            "decision_status": validation.get("decision_status", "missing"),
            "decision_reference_hash": validation.get("rights_decision_reference_hash", ""),
            "allowed_job_types": list(validation.get("allowed_job_types", []) or []),
            "reviewer_roles": list(validation.get("reviewer_roles", []) or []),
            "raw_decision_reference_stored": False,
        }
        if not accepted:
            issues.append("local_extraction_decision_not_valid")
    elif normalized_type == "exam_clearance":
        validation = validate_clearance_record(record or {})
        accepted = validation.get("status") == "ok_exam_controlled_gateway_clearance_record"
        event = {
            "record_type": normalized_type,
            "validation_status": validation.get("status", "blocked"),
            "accepted_for_gate": accepted,
            "clearance_scope": validation.get("clearance_scope", "missing"),
            "decision_status": validation.get("decision_status", "missing"),
            "decision_reference_hash": validation.get("decision_reference_hash", ""),
            "allowed_modes": list(validation.get("allowed_modes", []) or []),
            "help_levels_allowed": list(validation.get("help_levels_allowed", []) or []),
            "reviewer_roles": list(validation.get("reviewer_roles", []) or []),
            "raw_decision_reference_stored": False,
            "exam_deployment_status": "not_cleared",
        }
        if not accepted:
            issues.append("exam_clearance_record_not_valid")
    elif normalized_type == "extraction_deferral":
        validation = validate_extraction_deferral_record(record or {})
        accepted = validation.get("status") == "ok_extraction_deferral_record"
        event = {
            "record_type": normalized_type,
            "validation_status": validation.get("status", "blocked"),
            "accepted_for_gate": accepted,
            "deferral_scope": validation.get("deferral_scope", "missing"),
            "decision_status": validation.get("decision_status", "missing"),
            "decision_reference_hash": validation.get("decision_reference_hash", ""),
            "deferred_job_types": list(validation.get("deferred_job_types", []) or []),
            "deferred_job_id_count": int(validation.get("deferred_job_id_count", 0) or 0),
            "reviewer_roles": list(validation.get("reviewer_roles", []) or []),
            "raw_decision_reference_stored": False,
            "raw_deferral_reason_stored": False,
            "exam_deployment_status": "not_cleared",
        }
        if not accepted:
            issues.append("extraction_deferral_record_not_valid")
    elif normalized_type == "manual_deployment_go":
        reference = str(deployment_go_reference or (record or {}).get("deployment_go_reference", "")).strip()
        accepted = bool(reference)
        if not accepted:
            issues.append("deployment_go_reference_required")
        event = {
            "record_type": normalized_type,
            "validation_status": "ok_manual_deployment_go_reference" if accepted else "blocked",
            "accepted_for_gate": accepted,
            "deployment_go_reference_hash": sha256_text(reference) if reference else "",
            "raw_deployment_go_reference_stored": False,
            "exam_deployment_status": "not_cleared",
            "deployment_effect": "manual_go_recorded_but_not_deployed" if accepted else "no_effect_blocked_record",
        }
        warnings.append("manual_go_record_does_not_switch_exam_deployment")
    else:
        event = {
            "record_type": normalized_type or "missing",
            "validation_status": "blocked",
            "accepted_for_gate": False,
        }

    event["issues"] = sorted(set(issues))
    event["warnings"] = sorted(set(warnings + list(validation.get("warnings", []) or [])))
    event["validation_issues"] = list(validation.get("issues", []) or [])
    event["raw_record_stored"] = False
    event_hash_payload = {key: value for key, value in event.items() if key != "validation_hash"}
    event["validation_hash"] = sha256_text(json.dumps(event_hash_payload, sort_keys=True, ensure_ascii=False))
    return event


def sanitize_external_decision_journal_record(
    *,
    record_type: str,
    record: dict[str, Any] | None = None,
    deployment_go_reference: str | None = None,
) -> dict[str, Any]:
    event = sanitize_external_decision_record_event(
        record_type=record_type,
        record=record,
        deployment_go_reference=deployment_go_reference,
    )
    record_payload = {
        "schema_version": EXTERNAL_DECISION_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "unibot_external_decision_record_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if event.get("accepted_for_gate") and not event.get("issues") else "blocked",
        "event": event,
        "storage_policy": (
            "local-only jsonl; stores validation status, scope metadata, hashes, and gate flags only; "
            "no raw written decisions, no personal contact data, and no deployment switch"
        ),
    }
    scan = scan_text(json.dumps(record_payload, ensure_ascii=False), "external-decision-journal-record")
    record_payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        record_payload["status"] = "blocked"
        record_payload["public_safety_findings"] = scan["findings"]
    return record_payload


def append_external_decision_journal_record(
    *,
    record_type: str,
    record: dict[str, Any] | None = None,
    deployment_go_reference: str | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    journal_record = sanitize_external_decision_journal_record(
        record_type=record_type,
        record=record,
        deployment_go_reference=deployment_go_reference,
    )
    journal_path = resolve_external_decision_journal_path(path)
    if journal_record["status"] != "accepted":
        return {
            "status": "blocked",
            "path": str(journal_path),
            "record": journal_record,
        }
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(journal_record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "stored",
        "path": str(journal_path),
        "record": journal_record,
    }


def read_external_decision_journal(path: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    journal_path = resolve_external_decision_journal_path(path)
    if not journal_path.exists():
        return {"status": "empty", "path": str(journal_path), "count": 0, "records": []}
    rows = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "path": str(journal_path), "count": len(rows), "records": rows}


def summarize_external_decision_journal(path: str | Path | None = None) -> dict[str, Any]:
    payload = read_external_decision_journal(path)
    return summarize_external_decision_records(payload.get("records", []), status=str(payload.get("status", "empty")))


def summarize_external_decision_records(records: list[dict[str, Any]], *, status: str = "ok") -> dict[str, Any]:
    events = [record.get("event", {}) for record in records if isinstance(record, dict)]
    accepted_events = [event for record in records if record.get("status") == "accepted" for event in [record.get("event", {})]]
    blocked_count = len([record for record in records if record.get("status") == "blocked"])
    by_type: dict[str, int] = {}
    deferred_job_types: set[str] = set()
    for event in events:
        record_type = str(event.get("record_type", "missing"))
        by_type[record_type] = by_type.get(record_type, 0) + 1
        if event.get("record_type") == "extraction_deferral" and event.get("accepted_for_gate"):
            deferred_job_types.update(str(item) for item in event.get("deferred_job_types", []) or [])
    local_extraction_valid = any(event.get("record_type") == "local_extraction_decision" and event.get("accepted_for_gate") for event in accepted_events)
    exam_clearance_valid = any(event.get("record_type") == "exam_clearance" and event.get("accepted_for_gate") for event in accepted_events)
    extraction_deferral_valid = any(event.get("record_type") == "extraction_deferral" and event.get("accepted_for_gate") for event in accepted_events)
    deployment_go_recorded = any(event.get("record_type") == "manual_deployment_go" and event.get("accepted_for_gate") for event in accepted_events)
    summary = {
        "schema_version": EXTERNAL_DECISION_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "unibot_external_decision_record_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "record_count": len(records),
        "accepted_record_count": len(accepted_events),
        "blocked_record_count": blocked_count,
        "by_record_type": dict(sorted(by_type.items())),
        "gate_summary": {
            "local_extraction_decision_valid": local_extraction_valid,
            "exam_clearance_record_valid": exam_clearance_valid,
            "extraction_deferral_record_valid": extraction_deferral_valid,
            "manual_deployment_go_recorded": deployment_go_recorded,
            "exam_deployment_status": "not_cleared",
            "exam_deployment_requires_manual_switch": True,
        },
        "extraction_deferral_summary": {
            "deferred_job_types": sorted(deferred_job_types),
            "covers_ocr": "ocr" in deferred_job_types,
            "covers_transcription": "transcription" in deferred_job_types,
        },
        "storage_policy": "summary excludes raw written decisions, raw reasons, names, emails, local paths, and deployment text",
        "gate_policy": "journal entries are evidence for human review only; they do not send requests or deploy exam mode",
    }
    scan = scan_text(json.dumps(summary, ensure_ascii=False), "external-decision-journal-summary")
    summary["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        summary["status"] = "blocked_public_safety"
        summary["public_safety_findings"] = scan["findings"]
    return summary
