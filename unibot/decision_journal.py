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
from .source_cards import get_source_card


DECISION_JOURNAL_SCHEMA_VERSION = "unibot-stakeholder-decision-journal-v1"
DECISION_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-stakeholder-decision-journal-release-review-board-claim-alignment-v1"
)
DEFAULT_DECISION_JOURNAL_PATH = Path.home() / ".unibot_guardian" / "stakeholder_decision_journal.jsonl"
ALLOWED_JOURNAL_EVENT_TYPES = {"decision_request_prepared", "decision_request_receipt_validated"}


def build_decision_journal_release_claim_alignment(
    records: list[dict[str, Any]] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if records is None:
        request = build_stakeholder_decision_request()
        receipt = dict(request["receipt_template"])
        receipt.update(
            {
                "manual_submission_status": "sent_for_human_review",
                "channel": "synthetic manual review channel",
                "submission_reference": "synthetic hash-only journal reference",
            }
        )
        records = [
            sanitize_decision_journal_event(
                {
                    "event_type": "decision_request_prepared",
                    "request": request,
                }
            ),
            sanitize_decision_journal_event(
                {
                    "event_type": "decision_request_receipt_validated",
                    "receipt": receipt,
                }
            ),
        ]
        python_exam_local_cycle_operator_workspace_card = (
            python_exam_local_cycle_operator_workspace_card or synthetic_decision_journal_workspace_card()
        )

    sections = [
        {
            "section_id": "journal_storage_boundary_trace",
            "summary_claim": "decision journal stores local hash/status/lane metadata only, never raw request or written decision text",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "stakeholder_decision_journal",
                "python_exam_local_cycle_operator_workspace_card",
                "stakeholder_decision_request",
                "public_safety",
            ],
            "human_gates": ["human_submission_review_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "prepared_request_trace",
            "summary_claim": "prepared-request journal entries preserve request and markdown hashes without claiming external submission",
            "source_card_ids": ["dfg-gwp"],
            "readiness_check_ids": [
                "stakeholder_decision_journal",
                "stakeholder_decision_request",
                "stakeholder_submission_bundle",
            ],
            "human_gates": ["human_submission_review_required"],
        },
        {
            "section_id": "receipt_validation_trace",
            "summary_claim": "receipt entries prove a receipt validation status while storing only hash-safe submission references",
            "source_card_ids": ["gdpr-2016-679"],
            "readiness_check_ids": ["stakeholder_decision_journal", "data_protection_screening", "public_safety"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "gate_boundary_trace",
            "summary_claim": "journal evidence is process continuity only and never authorizes extraction, exam deployment, grading, or proctoring",
            "source_card_ids": ["hg-nrw-2025", "uoc-hilfsmittel", "uoc-ki-faq"],
            "readiness_check_ids": ["stakeholder_decision_journal", "review_board_packet", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)

    accepted_records = [record for record in records if record.get("status") == "accepted"]
    events = [record.get("event", {}) for record in records]
    event_types = {event.get("event_type") for event in events}
    prepared_events = [event for event in events if event.get("event_type") == "decision_request_prepared"]
    receipt_events = [event for event in events if event.get("event_type") == "decision_request_receipt_validated"]
    storage_policies = " ".join(str(record.get("storage_policy", "")) for record in records)
    workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {},
        journal_hash=decision_journal_hash(records),
        request_hash=decision_request_journal_hash(events),
    )
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )

    contracts = {
        "all_records_accepted_and_public_safe": len(accepted_records) == len(records)
        and all(record.get("public_safety_status") == "pass" for record in records),
        "records_use_decision_journal_schema": all(
            record.get("schema_version") == DECISION_JOURNAL_SCHEMA_VERSION for record in records
        ),
        "records_store_no_raw_text_or_tool_send": all(
            record.get("event", {}).get("raw_text_stored") is False
            and record.get("event", {}).get("tool_sent_message") is False
            for record in records
        ),
        "storage_policy_hash_status_lane_only": "stores hashes, statuses, and lane metadata only" in storage_policies
        and "no raw messages or written decisions" in storage_policies,
        "prepared_request_event_hash_only": bool(prepared_events)
        and all(
            event.get("request_status") == "ready_for_manual_review_not_sent"
            and event.get("exam_deployment_status") == "not_cleared"
            and event.get("manual_submission_status") == "draft_not_sent"
            and bool(event.get("request_hash"))
            for event in prepared_events
        ),
        "receipt_event_hash_only_no_gate_change": bool(receipt_events)
        and all(
            event.get("receipt_validation_status") in {"ok_manual_request_receipt", "draft_receipt_not_sent"}
            and event.get("raw_submission_reference_stored") is False
            and bool(event.get("validation_hash"))
            and str(event.get("receipt_effect", "")).endswith("_no_decision_record_yet")
            for event in receipt_events
        ),
        "prepared_and_receipt_events_present": {
            "decision_request_prepared",
            "decision_request_receipt_validated",
        }.issubset(event_types),
        "workspace_card_decision_journal_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("checkpoint_hash") == decision_journal_hash(records)
        and workspace_card.get("task_hash") == decision_request_journal_hash(events)
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
            "raw request text storage",
            "raw written decision storage",
            "tool-sent stakeholder message",
            "automatic gate change",
            "extraction approval",
            "exam clearance",
            "official grading",
            "proctoring",
            "KI-detection evidence",
        ],
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "stakeholder-decision-journal-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": DECISION_JOURNAL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "contracts": contracts,
        "record_count": len(records),
        "event_types": sorted(str(event_type) for event_type in event_types if event_type),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_decision_journal_gate_linked": contracts["workspace_card_decision_journal_gate_linked"],
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": payload["blocked_claims"],
        "public_safety_status": scan["status"],
        "policy": (
            "Stakeholder decision journals are local process evidence only; they store hashes, statuses, "
            "lane metadata, and validation hashes, not raw messages or written decisions, and never approve "
            "extraction, exam deployment, grading, proctoring, KI detection, or gate changes by themselves."
        ),
    }


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


def synthetic_decision_journal_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic stakeholder decision journal workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic stakeholder decision journal prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_stakeholder_decision_journal_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_decision_journal_before_external_decision_records",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__DECISION_REQUEST_JOURNAL_HASH__",
            "checkpoint_hash": "__DECISION_JOURNAL_HASH__",
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


def decision_journal_hash(records: list[dict[str, Any]]) -> str:
    return sha256_text(
        json.dumps(
            [
                {
                    "status": record.get("status", ""),
                    "event_type": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                        "event_type", ""
                    ),
                    "request_id": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                        "request_id", ""
                    ),
                    "lane_id": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                        "lane_id", ""
                    ),
                    "request_hash": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                        "request_hash", ""
                    ),
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


def decision_request_journal_hash(events: list[dict[str, Any]]) -> str:
    return sha256_text(
        json.dumps(
            [
                {
                    "event_type": event.get("event_type", ""),
                    "request_id": event.get("request_id", ""),
                    "lane_id": event.get("lane_id", ""),
                    "request_hash": event.get("request_hash", ""),
                    "markdown_hash": event.get("markdown_hash", ""),
                    "receipt_validation_status": event.get("receipt_validation_status", ""),
                    "receipt_effect": event.get("receipt_effect", ""),
                    "submission_reference_hash": event.get("submission_reference_hash", ""),
                    "validation_hash": event.get("validation_hash", ""),
                }
                for event in events
                if isinstance(event, dict)
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def safe_local_cycle_workspace_card(
    workspace_card: dict[str, Any],
    *,
    journal_hash: str = "",
    request_hash: str = "",
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
    if journal_hash and checkpoint_hash == "__DECISION_JOURNAL_HASH__":
        checkpoint_hash = journal_hash
    if request_hash and task_hash == "__DECISION_REQUEST_JOURNAL_HASH__":
        task_hash = request_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_decision_journal"))
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
