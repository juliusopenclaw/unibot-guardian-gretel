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
TIMELINE_EXPORT_RECEIPT_JOURNAL_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-timeline-export-receipt-journal-workspace-card-journal-alignment-v1"
)
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
    payload["workspace_card_journal_alignment"] = build_timeline_export_receipt_journal_workspace_card_alignment(
        timeline_export_receipt_journal_append=payload,
        timeline_export_receipt_journal_summary=summarize_timeline_export_receipt_records(
            [record],
            status="ok" if record.get("status") == "accepted" else "blocked",
        ),
    )
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
    return summarize_timeline_export_receipt_records(records, status=str(journal.get("status", "empty")))


def summarize_timeline_export_receipt_records(
    records: list[dict[str, Any]],
    *,
    status: str = "ok",
) -> dict[str, Any]:
    events = [record.get("event", {}) for record in records if isinstance(record.get("event"), dict)]
    accepted = [record for record in records if record.get("status") == "accepted"]
    blocked = [record for record in records if record.get("status") == "blocked"]
    skill_tags = unique_values(skill for event in events for skill in (event.get("skill_tags", []) or []))
    help_profile: dict[str, int] = {}
    reflection_statuses = []
    for event in events:
        for level, count in dict(event.get("help_level_profile", {}) or {}).items():
            help_profile[str(level)] = help_profile.get(str(level), 0) + int(count or 0)
        for reflection_status in event.get("reflection_statuses", []) or []:
            if reflection_status not in reflection_statuses:
                reflection_statuses.append(reflection_status)
    summary = {
        "schema_version": TIMELINE_EXPORT_RECEIPT_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "timeline_export_receipt_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
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


def timeline_export_receipt_journal_hash(
    append: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> str:
    append = append if isinstance(append, dict) else {}
    if records is None:
        records = []
        for key in ("stored_record", "preview_record"):
            record = append.get(key)
            if isinstance(record, dict):
                records.append(record)
    return sha256_text(
        json.dumps(
            {
                "append_status": append.get("status", ""),
                "journal_written": append.get("journal_written", None),
                "operator_confirmed": append.get(
                    "operator_confirmed_timeline_export_receipt_journal_append",
                    None,
                ),
                "write_preview": append.get("write_preview", {}),
                "records": [
                    {
                        "status": record.get("status", ""),
                        "event_type": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                            "event_type", ""
                        ),
                        "receipt_id": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                            "receipt_id", ""
                        ),
                        "receipt_hash": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                            "receipt_hash", ""
                        ),
                        "review_packet_hash": (
                            record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                        ).get("review_packet_hash", ""),
                        "event_count": (record.get("event", {}) if isinstance(record.get("event"), dict) else {}).get(
                            "event_count", 0
                        ),
                        "checkpoint_hash_count": (
                            record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                        ).get("checkpoint_hash_count", 0),
                        "reviewer_question_count": (
                            record.get("event", {}) if isinstance(record.get("event"), dict) else {}
                        ).get("reviewer_question_count", 0),
                    }
                    for record in records
                    if isinstance(record, dict)
                ],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def timeline_export_receipt_journal_summary_hash(summary: dict[str, Any] | None = None) -> str:
    summary = summary if isinstance(summary, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "status": summary.get("status", ""),
                "record_count": summary.get("record_count", 0),
                "accepted_record_count": summary.get("accepted_record_count", 0),
                "blocked_record_count": summary.get("blocked_record_count", 0),
                "skill_tags": summary.get("skill_tags", []),
                "event_count": summary.get("event_count", 0),
                "checkpoint_hash_count": summary.get("checkpoint_hash_count", 0),
                "reviewer_question_count": summary.get("reviewer_question_count", 0),
                "open_operator_confirmation_count": summary.get("open_operator_confirmation_count", 0),
                "help_level_profile": summary.get("help_level_profile", {}),
                "reflection_statuses": summary.get("reflection_statuses", []),
                "exam_deployment_status": summary.get("exam_deployment_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_timeline_export_receipt_journal_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic timeline export receipt journal workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic timeline receipt journal prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_timeline_receipt_journal_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_timeline_journal_before_local_write_or_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__TIMELINE_RECEIPT_JOURNAL_SUMMARY_HASH__",
            "checkpoint_hash": "__TIMELINE_RECEIPT_JOURNAL_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_timeline_export_receipt_journal_workspace_card(
    workspace_card: dict[str, Any],
    *,
    journal_hash: str = "",
    summary_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if journal_hash and checkpoint_hash == "__TIMELINE_RECEIPT_JOURNAL_HASH__":
        checkpoint_hash = journal_hash
    if summary_hash and task_hash == "__TIMELINE_RECEIPT_JOURNAL_SUMMARY_HASH__":
        task_hash = summary_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_timeline_receipt_journal_gate")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
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


def build_timeline_export_receipt_journal_workspace_card_alignment(
    timeline_export_receipt_journal_append: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    append = timeline_export_receipt_journal_append if isinstance(timeline_export_receipt_journal_append, dict) else {}
    summary = (
        timeline_export_receipt_journal_summary
        if isinstance(timeline_export_receipt_journal_summary, dict)
        else summarize_timeline_export_receipt_records(
            [
                record
                for key in ("stored_record", "preview_record")
                for record in [append.get(key)]
                if isinstance(record, dict)
            ],
            status="ok",
        )
    )
    journal_hash = timeline_export_receipt_journal_hash(append)
    summary_hash = timeline_export_receipt_journal_summary_hash(summary)
    workspace_card = safe_timeline_export_receipt_journal_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_timeline_export_receipt_journal_workspace_card(),
        journal_hash=journal_hash,
        summary_hash=summary_hash,
    )
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    raw_flag_names = [
        "raw_query_returned",
        "raw_text_returned",
        "raw_cell_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
    ]
    high_stakes_flag_names = [
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]
    local_write_boundary_ok = (
        append.get("operator_confirmation_required_for_write") is True
        and (
            (
                append.get("operator_confirmed_timeline_export_receipt_journal_append") is False
                and append.get("journal_written") is False
                and append.get("status") == "write_preview_ready"
            )
            or (
                append.get("operator_confirmed_timeline_export_receipt_journal_append") is True
                and append.get("journal_written") is True
                and append.get("status") == "stored"
            )
        )
    )
    contracts = {
        "append_public_safe": append.get("public_safety_status") == "pass",
        "summary_public_safe": summary.get("public_safety_status") == "pass",
        "accepted_rejected_counts_present": int(summary.get("record_count", 0) or 0)
        == int(summary.get("accepted_record_count", 0) or 0) + int(summary.get("blocked_record_count", 0) or 0)
        and int(summary.get("accepted_record_count", 0) or 0) >= 1,
        "local_write_boundary_preserved": local_write_boundary_ok,
        "no_clearance_or_deployment_claim": append.get("exam_deployment_status") == "not_cleared"
        and summary.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(append.get(flag) is False for flag in raw_flag_names)
        and all(summary.get(flag) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(append.get(flag) is False for flag in high_stakes_flag_names)
        and all(summary.get(flag) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_timeline_receipt_journal_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == journal_hash
        and workspace_card.get("task_hash") == summary_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "timeline_export_receipt_journal",
        "review_chain_integrity",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": TIMELINE_EXPORT_RECEIPT_JOURNAL_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "timeline_receipt_journal_hash": journal_hash,
        "timeline_receipt_journal_summary_hash": summary_hash,
        "append_status": append.get("status", "missing"),
        "summary_status": summary.get("status", "missing"),
        "journal_written": append.get("journal_written", None),
        "operator_confirmed_timeline_export_receipt_journal_append": append.get(
            "operator_confirmed_timeline_export_receipt_journal_append",
            None,
        ),
        "record_count": summary.get("record_count", 0),
        "accepted_record_count": summary.get("accepted_record_count", 0),
        "blocked_record_count": summary.get("blocked_record_count", 0),
        "event_count": summary.get("event_count", 0),
        "checkpoint_hash_count": summary.get("checkpoint_hash_count", 0),
        "reviewer_question_count": summary.get("reviewer_question_count", 0),
        "exam_deployment_status": summary.get("exam_deployment_status", append.get("exam_deployment_status", "missing")),
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "human_review_required",
            "public_safety_required",
            "operator_confirmation_required_for_local_write",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "autonomous publication",
            "approval claim",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
        "contracts": contracts,
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_operator_prefill_hash_present": workspace_card["task_hash"] != ""
        and workspace_card["checkpoint_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_timeline_receipt_journal_gate_linked": contracts[
            "workspace_card_timeline_receipt_journal_gate_linked"
        ],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Timeline export receipt journal claims are hash-only review aids for append previews, accepted or "
            "blocked counts, and local-write boundaries; they do not authorize publication, provider calls, "
            "grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "timeline-export-receipt-journal-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_timeline_export_receipt_journal_inputs() -> dict[str, Any]:
    append = build_timeline_export_receipt_journal_append(
        review_packet=synthetic_timeline_export_review_packet(),
        operator_confirmed_timeline_export_receipt_journal_append=False,
    )
    record = append.get("preview_record") if isinstance(append.get("preview_record"), dict) else {}
    summary = summarize_timeline_export_receipt_records([record], status="ok")
    return {"append": append, "summary": summary}


def synthetic_timeline_export_review_packet() -> dict[str, Any]:
    return {
        "schema_version": "unibot-timeline-export-review-packet-v1",
        "artifact_type": "timeline_export_review_packet",
        "status": "timeline_export_review_packet_ready",
        "exam_deployment_status": "not_cleared",
        "public_safety_status": "pass",
        "export_review_summary": {
            "timeline_count": 1,
            "event_count": 1,
            "skill_count": 1,
            "skill_tags": ["python_lists"],
            "packet_receipt_count": 1,
            "timeline_receipt_count": 1,
            "checkpoint_hash_count": 1,
            "help_level_profile": {"A2": 1},
            "open_operator_confirmation_count": 2,
            "reflection_statuses": ["reflection_evidence_present"],
            "reviewer_question_count": 6,
            "exam_deployment_status": "not_cleared",
        },
        "local_export_receipt": {
            "status": "timeline_export_review_packet_receipt_ready_not_exam_clearance",
            "receipt_id": "timeline-review-synthetic-1",
            "receipt_hash": "a" * 64,
            "local_write_started": False,
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
        },
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
    }


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
