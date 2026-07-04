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
from .source_cards import get_source_card


EXTERNAL_DECISION_JOURNAL_SCHEMA_VERSION = "unibot-external-decision-record-journal-v1"
EXTERNAL_DECISION_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-external-decision-record-journal-release-review-board-claim-alignment-v1"
)
DEFAULT_EXTERNAL_DECISION_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "external_decision_records.jsonl"

DECISION_RECORD_TYPES = {
    "local_extraction_decision",
    "exam_clearance",
    "extraction_deferral",
    "manual_deployment_go",
}


def synthetic_local_extraction_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete local raw extraction artifacts after reviewed source-card metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic hash-only local extraction decision reference",
    }


def synthetic_exam_clearance_record() -> dict[str, Any]:
    return {
        "clearance_scope": "exam_controlled_gateway",
        "decision_status": "approved",
        "reviewer_roles": [
            "Pruefungsamt",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Inklusionsbuero / Nachteilsausgleich",
        ],
        "decision_reference": "synthetic hash-only exam clearance decision reference",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }


def synthetic_extraction_deferral_record() -> dict[str, Any]:
    return {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "synthetic hash-only extraction deferral reason",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic hash-only extraction deferral decision reference",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


def build_external_decision_record_journal_release_claim_alignment(
    records: list[dict[str, Any]] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if records is None:
        records = [
            sanitize_external_decision_journal_record(
                record_type="local_extraction_decision",
                record=synthetic_local_extraction_decision_record(),
            ),
            sanitize_external_decision_journal_record(
                record_type="exam_clearance",
                record=synthetic_exam_clearance_record(),
            ),
            sanitize_external_decision_journal_record(
                record_type="extraction_deferral",
                record=synthetic_extraction_deferral_record(),
            ),
            sanitize_external_decision_journal_record(
                record_type="manual_deployment_go",
                deployment_go_reference="synthetic hash-only deployment go reference",
            ),
        ]
        python_exam_local_cycle_operator_workspace_card = (
            python_exam_local_cycle_operator_workspace_card
            or synthetic_external_decision_record_journal_workspace_card()
        )

    sections = [
        {
            "section_id": "validated_record_storage_trace",
            "summary_claim": "external decision journal stores validation status, scope metadata, hashes, and gate flags only",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "external_decision_record_journal",
                "python_exam_local_cycle_operator_workspace_card",
                "stakeholder_decision_journal",
                "public_safety",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "local_extraction_record_trace",
            "summary_claim": "local extraction decision records can authorize only local private extraction, not public raw text release or cloud processing",
            "source_card_ids": ["gdpr-2016-679", "dfg-gwp"],
            "readiness_check_ids": [
                "external_decision_record_journal",
                "stakeholder_submission_bundle",
                "data_protection_screening",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "exam_clearance_record_trace",
            "summary_claim": "exam clearance records stay hash-only and do not switch exam deployment by themselves",
            "source_card_ids": ["hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq"],
            "readiness_check_ids": ["external_decision_record_journal", "authority_handoff", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
        {
            "section_id": "manual_deployment_go_trace",
            "summary_claim": "manual deployment-go references are recorded as hashes and explicitly do not deploy exam mode",
            "source_card_ids": ["uoc-hilfsmittel", "uoc-ki-faq"],
            "readiness_check_ids": ["external_decision_record_journal", "release_runbook", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)

    events = [record.get("event", {}) for record in records if isinstance(record, dict)]
    by_type = {event.get("record_type"): event for event in events}
    summary = summarize_external_decision_records(records)
    storage_policies = " ".join(str(record.get("storage_policy", "")) for record in records)
    workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {},
        journal_hash=external_decision_record_journal_hash(records),
        gate_hash=external_decision_record_gate_hash(summary),
    )
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )

    contracts = {
        "all_records_accepted_and_public_safe": all(record.get("status") == "accepted" for record in records)
        and all(record.get("public_safety_status") == "pass" for record in records),
        "records_use_external_decision_schema": all(
            record.get("schema_version") == EXTERNAL_DECISION_JOURNAL_SCHEMA_VERSION for record in records
        ),
        "records_store_no_raw_decisions_or_deploy_text": all(
            record.get("event", {}).get("raw_record_stored") is False
            and record.get("event", {}).get("raw_decision_reference_stored", False) is False
            and record.get("event", {}).get("raw_deployment_go_reference_stored", False) is False
            for record in records
        ),
        "storage_policy_hash_status_gate_flags_only": "stores validation status, scope metadata, hashes, and gate flags only"
        in storage_policies
        and "no raw written decisions" in storage_policies
        and "no deployment switch" in storage_policies,
        "local_extraction_record_hash_only": by_type.get("local_extraction_decision", {}).get("validation_status")
        == "ok_authorizes_local_extraction"
        and by_type.get("local_extraction_decision", {}).get("accepted_for_gate") is True
        and bool(by_type.get("local_extraction_decision", {}).get("decision_reference_hash"))
        and by_type.get("local_extraction_decision", {}).get("raw_decision_reference_stored") is False,
        "exam_clearance_record_hash_only_not_deployed": by_type.get("exam_clearance", {}).get("validation_status")
        == "ok_exam_controlled_gateway_clearance_record"
        and by_type.get("exam_clearance", {}).get("accepted_for_gate") is True
        and bool(by_type.get("exam_clearance", {}).get("decision_reference_hash"))
        and by_type.get("exam_clearance", {}).get("exam_deployment_status") == "not_cleared",
        "extraction_deferral_record_hash_only": by_type.get("extraction_deferral", {}).get("validation_status")
        == "ok_extraction_deferral_record"
        and by_type.get("extraction_deferral", {}).get("accepted_for_gate") is True
        and bool(by_type.get("extraction_deferral", {}).get("decision_reference_hash"))
        and by_type.get("extraction_deferral", {}).get("raw_deferral_reason_stored") is False,
        "manual_deployment_go_hash_only_no_switch": by_type.get("manual_deployment_go", {}).get("validation_status")
        == "ok_manual_deployment_go_reference"
        and by_type.get("manual_deployment_go", {}).get("deployment_effect") == "manual_go_recorded_but_not_deployed"
        and by_type.get("manual_deployment_go", {}).get("exam_deployment_status") == "not_cleared",
        "summary_preserves_not_cleared_boundary": summary.get("public_safety_status") == "pass"
        and summary.get("gate_summary", {}).get("exam_deployment_status") == "not_cleared"
        and summary.get("gate_summary", {}).get("exam_deployment_requires_manual_switch") is True,
        "workspace_card_decision_record_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("checkpoint_hash") == external_decision_record_journal_hash(records)
        and workspace_card.get("task_hash") == external_decision_record_gate_hash(summary)
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": [
            "raw written decision storage",
            "personal contact data storage",
            "deployment switch",
            "automatic gate change",
            "public raw course text release",
            "exam deployment",
            "official grading",
            "proctoring",
            "KI-detection evidence",
        ],
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "external-decision-record-journal-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXTERNAL_DECISION_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "contracts": contracts,
        "record_count": len(records),
        "record_types": sorted(str(event.get("record_type")) for event in events if event.get("record_type")),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_decision_record_gate_linked": contracts["workspace_card_decision_record_gate_linked"],
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": payload["blocked_claims"],
        "public_safety_status": scan["status"],
        "policy": (
            "External decision record journals are local hash/status evidence only; validated records can inform "
            "human review, but they do not store raw decisions, switch deployment, authorize grading/proctoring/KI "
            "detection, or clear exam use by themselves."
        ),
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


def synthetic_external_decision_record_journal_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic external decision record journal workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic external decision record journal prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_external_decision_record_journal_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_decision_record_journal_before_decision_state",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__DECISION_RECORD_GATE_HASH__",
            "checkpoint_hash": "__DECISION_RECORD_JOURNAL_HASH__",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def external_decision_record_journal_hash(records: list[dict[str, Any]]) -> str:
    return sha256_text(
        json.dumps(
            [
                {
                    "status": record.get("status", ""),
                    "record_type": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                        "record_type", ""
                    ),
                    "validation_status": (
                        record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                    ).get("validation_status", ""),
                    "accepted_for_gate": (
                        record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                    ).get("accepted_for_gate", False),
                    "validation_hash": (
                        record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                    ).get("validation_hash", ""),
                }
                for record in records
                if isinstance(record, dict)
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def external_decision_record_gate_hash(summary: dict[str, Any]) -> str:
    return sha256_text(
        json.dumps(
            {
                "record_count": summary.get("record_count", 0),
                "accepted_record_count": summary.get("accepted_record_count", 0),
                "blocked_record_count": summary.get("blocked_record_count", 0),
                "by_record_type": summary.get("by_record_type", {}),
                "gate_summary": summary.get("gate_summary", {}),
                "extraction_deferral_summary": summary.get("extraction_deferral_summary", {}),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def safe_local_cycle_workspace_card(
    workspace_card: dict[str, Any],
    *,
    journal_hash: str = "",
    gate_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    review = workspace_card.get("readiness_review", {}) if isinstance(workspace_card.get("readiness_review"), dict) else {}
    handoff = workspace_card.get("readiness_handoff", {}) if isinstance(workspace_card.get("readiness_handoff"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if journal_hash and checkpoint_hash == "__DECISION_RECORD_JOURNAL_HASH__":
        checkpoint_hash = journal_hash
    if gate_hash and task_hash == "__DECISION_RECORD_GATE_HASH__":
        task_hash = gate_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_decision_record_journal"))
        ),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }
