from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .extraction_decision import validate_extraction_decision_record


EXTRACTION_DECISION_CONTEXT_SCHEMA_VERSION = "unibot-extraction-decision-context-v1"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$", re.I)


def resolve_extraction_decision_context(
    *,
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    requested_job_types: set[str] | list[str] | None = None,
) -> dict[str, Any]:
    if decision_record:
        validation = validate_extraction_decision_record(decision_record)
        validation["decision_record_source"] = "inline_decision_record"
        return apply_requested_job_type_gate(validation, requested_job_types)
    if decision_record_journal_path:
        validation = local_extraction_decision_context_from_journal(decision_record_journal_path)
        return apply_requested_job_type_gate(validation, requested_job_types)
    validation = validate_extraction_decision_record({})
    validation["decision_record_source"] = "missing_decision_record"
    return apply_requested_job_type_gate(validation, requested_job_types)


def local_extraction_decision_context_from_journal(path: str | Path) -> dict[str, Any]:
    from .external_decision_journal import read_external_decision_journal

    journal = read_external_decision_journal(path=path)
    records = [record for record in journal.get("records", []) if isinstance(record, dict)]
    accepted_events = []
    for record in records:
        event = record.get("event", {})
        if (
            record.get("status") == "accepted"
            and isinstance(event, dict)
            and event.get("record_type") == "local_extraction_decision"
            and event.get("accepted_for_gate") is True
            and event.get("validation_status") == "ok_authorizes_local_extraction"
            and event.get("raw_record_stored") is False
            and event.get("raw_decision_reference_stored") is False
        ):
            accepted_events.append(event)
    if not accepted_events:
        return {
            "schema_version": EXTRACTION_DECISION_CONTEXT_SCHEMA_VERSION,
            "artifact_type": "course_extraction_decision_context",
            "status": "blocked",
            "decision_status": "missing",
            "approved_for_local_extraction": False,
            "issues": ["accepted_local_extraction_decision_record_required"],
            "warnings": [],
            "rights_decision_reference_hash": "",
            "allowed_job_types": [],
            "decision_record_source": "external_decision_record_journal",
            "journal_status": journal.get("status", "empty"),
            "journal_record_count": journal.get("count", 0),
            "raw_record_stored": False,
            "raw_decision_reference_stored": False,
            "public_safety_status": "pass",
        }
    event = accepted_events[-1]
    rights_hash = str(event.get("decision_reference_hash", ""))
    issues = []
    if not SHA256_RE.match(rights_hash):
        issues.append("decision_reference_hash_required")
    return {
        "schema_version": EXTRACTION_DECISION_CONTEXT_SCHEMA_VERSION,
        "artifact_type": "course_extraction_decision_context",
        "status": "ok_authorizes_local_extraction_from_journal" if not issues else "blocked",
        "decision_status": event.get("decision_status", "approved_for_local_extraction"),
        "approved_for_local_extraction": not issues,
        "issues": issues,
        "warnings": list(event.get("warnings", []) or []),
        "rights_decision_reference_hash": rights_hash,
        "allowed_job_types": list(event.get("allowed_job_types", []) or []),
        "reviewer_roles": list(event.get("reviewer_roles", []) or []),
        "decision_record_source": "external_decision_record_journal",
        "journal_status": journal.get("status", "ok"),
        "journal_record_count": journal.get("count", 0),
        "selected_journal_validation_hash": event.get("validation_hash", ""),
        "raw_record_stored": False,
        "raw_decision_reference_stored": False,
        "public_safety_status": "pass",
    }


def apply_requested_job_type_gate(
    validation: dict[str, Any],
    requested_job_types: set[str] | list[str] | None,
) -> dict[str, Any]:
    validation = dict(validation)
    issues = list(validation.get("issues", []) or [])
    allowed = {str(item) for item in validation.get("allowed_job_types", []) or [] if str(item)}
    requested = {str(item) for item in (requested_job_types or []) if str(item)}
    if decision_context_authorizes(validation) and requested and allowed and not requested.issubset(allowed):
        issues.append("requested_job_type_not_allowed_by_decision")
    if issues:
        validation["status"] = "blocked"
        validation["approved_for_local_extraction"] = False
    validation["issues"] = sorted(set(issues))
    validation["requested_job_types"] = sorted(requested)
    return validation


def decision_context_authorizes(validation: dict[str, Any]) -> bool:
    return validation.get("status") in {
        "ok_authorizes_local_extraction",
        "ok_authorizes_local_extraction_from_journal",
    }


def public_decision_context_view(validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": validation.get("status"),
        "approved_for_local_extraction": decision_context_authorizes(validation),
        "issues": list(validation.get("issues", []) or []),
        "warnings": list(validation.get("warnings", []) or []),
        "rights_decision_reference_hash": validation.get("rights_decision_reference_hash", ""),
        "allowed_job_types": list(validation.get("allowed_job_types", []) or []),
        "requested_job_types": list(validation.get("requested_job_types", []) or []),
        "decision_record_source": validation.get("decision_record_source", "missing_decision_record"),
        "journal_status": validation.get("journal_status", ""),
        "journal_record_count": validation.get("journal_record_count", 0),
        "raw_decision_reference_stored": False,
        "raw_decision_record_returned": False,
    }
