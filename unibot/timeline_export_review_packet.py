from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_packet_timeline import build_exam_packet_timeline
from .materials import sha256_text
from .public_safety import scan_text


TIMELINE_EXPORT_REVIEW_PACKET_SCHEMA_VERSION = "unibot-timeline-export-review-packet-v1"
TIMELINE_EXPORT_REVIEW_PACKET_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-timeline-export-review-packet-workspace-card-review-alignment-v1"
)
TIMELINE_EXPORT_REVIEW_PACKET_ENDPOINT = "/api/unibot/course/timeline-export-review-packet"


def build_timeline_export_review_packet(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    selected_skill_tag: str = "",
    focus_query: str = "",
    exam_packet_timeline: dict[str, Any] | None = None,
    exam_packet_timelines: list[dict[str, Any]] | None = None,
    exam_run_packets: list[dict[str, Any]] | None = None,
    exam_run_packet: dict[str, Any] | None = None,
    dashboard_report: dict[str, Any] | None = None,
    router_report: dict[str, Any] | None = None,
    executor_report: dict[str, Any] | None = None,
    run_history_report: dict[str, Any] | None = None,
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_manifest_path: str | Path | None = None,
    manifest_apply_journal_path: str | Path | None = None,
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    checkpoint_journal_path: str | Path | None = None,
    query: str = "",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_source: str = "",
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    operator_confirmed_local_export_receipt: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    timelines = normalized_timelines(exam_packet_timelines, exam_packet_timeline)
    if not timelines:
        timelines = [
            build_exam_packet_timeline(
                course_id=safe_id,
                selected_skill_tag=selected_skill_tag,
                focus_query=focus_query or query,
                exam_run_packets=exam_run_packets,
                exam_run_packet=exam_run_packet,
                dashboard_report=dashboard_report,
                router_report=router_report,
                executor_report=executor_report,
                run_history_report=run_history_report,
                console_reports=console_reports,
                console_receipts=console_receipts,
                base_path=base_path,
                max_files=max_files,
                review_policy=review_policy,
                decision_record=decision_record,
                decision_record_journal_path=decision_record_journal_path,
                receipts=receipts,
                receipt_journal_path=receipt_journal_path,
                private_manifest_path=private_manifest_path,
                manifest_apply_journal_path=manifest_apply_journal_path,
                tutor_index_path=tutor_index_path,
                tutor_index_journal_path=tutor_index_journal_path,
                ledger_path=ledger_path,
                checkpoint_journal_path=checkpoint_journal_path,
                query=query,
                requested_help_level=requested_help_level,
                exam_status=exam_status,
                student_reflection=student_reflection,
                study_receipt=study_receipt,
                notebook_checkpoint=notebook_checkpoint,
                cell_source=cell_source,
                cell_index=cell_index,
                cell_id=cell_id,
                cell_type=cell_type,
                public_safe=public_safe,
            )
        ]
    events = timeline_events(timelines, selected_skill_tag or focus_query or query)
    skill_packets = skill_review_packets(events)
    summary = export_review_summary(timelines, events, skill_packets)
    receipt = export_packet_receipt(
        safe_id,
        summary,
        skill_packets,
        operator_confirmed_local_export_receipt=operator_confirmed_local_export_receipt,
    )
    payload = {
        "schema_version": TIMELINE_EXPORT_REVIEW_PACKET_SCHEMA_VERSION,
        "artifact_type": "timeline_export_review_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "timeline_export_review_packet_ready",
        "packet_title": "Timeline Export Review Packet",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Timeline Export Review Packet. It bundles Timeline events, packet receipts, router/executor "
            "receipts, checkpoint hashes, help-level profile, open operator confirmations, reflection status, "
            "next safe action, and human reviewer questions. It never returns raw queries, course raw text, "
            "notebook code, local paths, values, solutions, final interpretations, proctoring, AI detection, "
            "automatic assessment, or exam clearance."
        ),
        "export_review_summary": summary,
        "skill_review_packets": skill_packets,
        "human_reviewer_questions": reviewer_questions_for_summary(summary),
        "local_export_receipt": receipt,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "ledger_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; das Review-Paket bleibt not_cleared."
        ),
        "next_actions": [
            "Give this packet to a human reviewer together with the matching notebook/export receipts.",
            "Resolve open operator confirmations before any write-capable local export step.",
            "Keep real-world exam clearance outside UniBot; this packet remains not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    payload["workspace_card_review_alignment"] = build_timeline_export_review_packet_workspace_card_alignment(payload)
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def timeline_export_review_packet_hash(review_packet: dict[str, Any] | None = None) -> str:
    packet = review_packet if isinstance(review_packet, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": packet.get("schema_version", ""),
                "artifact_type": packet.get("artifact_type", ""),
                "status": packet.get("status", ""),
                "course_id": packet.get("course_id", ""),
                "exam_deployment_status": packet.get("exam_deployment_status", ""),
                "export_review_summary": packet.get("export_review_summary", {}),
                "skill_review_packets": packet.get("skill_review_packets", []),
                "human_reviewer_questions": packet.get("human_reviewer_questions", []),
                "public_safety_status": packet.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def timeline_export_review_packet_receipt_hash(review_packet: dict[str, Any] | None = None) -> str:
    packet = review_packet if isinstance(review_packet, dict) else {}
    receipt = packet.get("local_export_receipt", {}) if isinstance(packet.get("local_export_receipt"), dict) else {}
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", ""),
                "local_write_started": receipt.get("local_write_started", None),
                "operator_confirmation_required_for_write": receipt.get(
                    "operator_confirmation_required_for_write",
                    None,
                ),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "summary_hash": sha256_text(
                    json.dumps(packet.get("export_review_summary", {}), sort_keys=True, ensure_ascii=False)
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_timeline_export_review_packet_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic timeline export review packet workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic timeline export review packet prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_timeline_export_review_packet_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_timeline_review_packet_before_local_write_or_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__TIMELINE_EXPORT_REVIEW_PACKET_RECEIPT_HASH__",
            "checkpoint_hash": "__TIMELINE_EXPORT_REVIEW_PACKET_HASH__",
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


def safe_timeline_export_review_packet_workspace_card(
    workspace_card: dict[str, Any],
    *,
    review_packet_hash: str = "",
    receipt_hash: str = "",
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
    if review_packet_hash and checkpoint_hash == "__TIMELINE_EXPORT_REVIEW_PACKET_HASH__":
        checkpoint_hash = review_packet_hash
    if receipt_hash and task_hash == "__TIMELINE_EXPORT_REVIEW_PACKET_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_timeline_export_review_packet_gate")),
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


def build_timeline_export_review_packet_workspace_card_alignment(
    timeline_export_review_packet: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else {}
    summary = packet.get("export_review_summary", {}) if isinstance(packet.get("export_review_summary"), dict) else {}
    receipt = packet.get("local_export_receipt", {}) if isinstance(packet.get("local_export_receipt"), dict) else {}
    review_hash = timeline_export_review_packet_hash(packet)
    receipt_hash = timeline_export_review_packet_receipt_hash(packet)
    workspace_card = safe_timeline_export_review_packet_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_timeline_export_review_packet_workspace_card(),
        review_packet_hash=review_hash,
        receipt_hash=receipt_hash,
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
        receipt.get("operator_confirmation_required_for_write") is True
        and receipt.get("local_write_started") is False
        and receipt.get("status") == "timeline_export_review_packet_receipt_ready_not_exam_clearance"
    )
    contracts = {
        "review_packet_public_safe": packet.get("public_safety_status") == "pass",
        "review_packet_ready": packet.get("status") == "timeline_export_review_packet_ready"
        and summary.get("event_count", 0) >= 1
        and summary.get("skill_count", 0) >= 1,
        "receipt_ready_not_clearance": receipt.get("status")
        == "timeline_export_review_packet_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and bool(receipt.get("receipt_hash"))
        and receipt.get("not_cleared_receipt") is True,
        "reviewer_questions_present": int(summary.get("reviewer_question_count", 0) or 0) >= 1
        and len(packet.get("human_reviewer_questions", []) or []) >= 1,
        "local_write_boundary_preserved": local_write_boundary_ok,
        "no_clearance_or_deployment_claim": packet.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(packet.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(packet.get(flag) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_timeline_review_packet_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == review_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "timeline_export_review_packet",
        "timeline_export_receipt_journal",
        "review_chain_integrity",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": TIMELINE_EXPORT_REVIEW_PACKET_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "timeline_export_review_packet_hash": review_hash,
        "timeline_export_review_packet_receipt_hash": receipt_hash,
        "review_packet_status": packet.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "local_write_started": receipt.get("local_write_started", None),
        "operator_confirmation_required_for_write": receipt.get("operator_confirmation_required_for_write", None),
        "event_count": summary.get("event_count", 0),
        "skill_count": summary.get("skill_count", 0),
        "reviewer_question_count": summary.get("reviewer_question_count", 0),
        "checkpoint_hash_count": summary.get("checkpoint_hash_count", 0),
        "open_operator_confirmation_count": summary.get("open_operator_confirmation_count", 0),
        "exam_deployment_status": packet.get("exam_deployment_status", "missing"),
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
        "workspace_card_timeline_review_packet_gate_linked": contracts[
            "workspace_card_timeline_review_packet_gate_linked"
        ],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Timeline export review packet claims are hash-only review aids for summaries, local export receipts, "
            "reviewer questions, and local-write boundaries; they do not authorize publication, provider calls, "
            "grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "timeline-export-review-packet-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_timeline_export_review_packet_inputs() -> dict[str, Any]:
    packet = build_timeline_export_review_packet(
        selected_skill_tag="python_lists",
        focus_query="Python Listen",
        public_safe=True,
    )
    return {"review_packet": packet}


def normalized_timelines(
    timelines: list[dict[str, Any]] | None,
    timeline: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    items = [item for item in (timelines or []) if isinstance(item, dict)]
    if isinstance(timeline, dict):
        receipt_id = timeline.get("timeline_receipt", {}).get("receipt_id", "") if isinstance(timeline.get("timeline_receipt"), dict) else ""
        existing_ids = {
            item.get("timeline_receipt", {}).get("receipt_id", "")
            for item in items
            if isinstance(item.get("timeline_receipt"), dict)
        }
        if not receipt_id or receipt_id not in existing_ids:
            items.append(timeline)
    return items


def timeline_events(timelines: list[dict[str, Any]], selector: str) -> list[dict[str, Any]]:
    events = [event for timeline in timelines for event in timeline.get("timeline_events", []) if isinstance(event, dict)]
    if not selector:
        return events
    selected = str(selector).lower()
    matches = []
    for event in events:
        tag = str(event.get("skill_tag", "")).lower()
        if selected == tag or selected in tag or tag in selected:
            matches.append(event)
    return matches or events


def skill_review_packets(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault(str(event.get("skill_tag", "unassigned_skill") or "unassigned_skill"), []).append(event)
    packets = []
    for skill_tag, skill_events in sorted(grouped.items()):
        help_profile = aggregate_help_profile(skill_events)
        checkpoint_hashes = unique_values(
            hash_value for event in skill_events for hash_value in (event.get("checkpoint_hashes", []) or [])
        )
        open_confirmations = unique_values(
            confirmation for event in skill_events for confirmation in (event.get("open_operator_confirmations", []) or [])
        )
        reflection_statuses = unique_values(
            status for event in skill_events for status in (event.get("reflection_statuses", []) or [])
        )
        next_actions = unique_values(event.get("next_safe_action", "") for event in skill_events if event.get("next_safe_action"))
        packet = {
            "skill_tag": skill_tag,
            "status": "ready_for_human_review",
            "event_count": len(skill_events),
            "packet_receipts": unique_values(event.get("packet_receipt_id", "") for event in skill_events),
            "route_ids": unique_values(event.get("route_id", "") for event in skill_events),
            "executed_artifacts": unique_values(event.get("executed_artifact_type", "") for event in skill_events),
            "executor_receipts": unique_values(event.get("executor_receipt_id", "") for event in skill_events),
            "checkpoint_hashes": checkpoint_hashes,
            "checkpoint_hash_count": len(checkpoint_hashes),
            "help_level_profile": help_profile,
            "open_operator_confirmations": open_confirmations,
            "open_operator_confirmation_count": sum(int(event.get("open_operator_confirmation_count", 0) or 0) for event in skill_events),
            "reflection_statuses": reflection_statuses,
            "next_safe_actions": next_actions,
            "human_reviewer_questions": reviewer_questions_for_skill(
                skill_tag=skill_tag,
                help_profile=help_profile,
                checkpoint_hash_count=len(checkpoint_hashes),
                open_confirmation_count=sum(int(event.get("open_operator_confirmation_count", 0) or 0) for event in skill_events),
                reflection_statuses=reflection_statuses,
            ),
            "exam_deployment_status": "not_cleared",
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
            "automatic_grading_started": False,
            "proctoring_started": False,
            "ai_detection_started": False,
            "exam_clearance_claimed": False,
        }
        packets.append(packet)
    return packets


def aggregate_help_profile(events: list[dict[str, Any]]) -> dict[str, int]:
    profile: dict[str, int] = {}
    for event in events:
        for key, value in dict(event.get("help_level_profile", {}) or {}).items():
            profile[str(key)] = profile.get(str(key), 0) + int(value or 0)
    return profile


def unique_values(values: Any) -> list[str]:
    result = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def export_review_summary(
    timelines: list[dict[str, Any]],
    events: list[dict[str, Any]],
    skill_packets: list[dict[str, Any]],
) -> dict[str, Any]:
    checkpoint_hashes = unique_values(
        hash_value for event in events for hash_value in (event.get("checkpoint_hashes", []) or [])
    )
    packet_receipts = unique_values(event.get("packet_receipt_id", "") for event in events)
    timeline_receipts = unique_values(
        timeline.get("timeline_receipt", {}).get("receipt_id", "")
        for timeline in timelines
        if isinstance(timeline.get("timeline_receipt"), dict)
    )
    return {
        "timeline_count": len(timelines),
        "event_count": len(events),
        "skill_count": len(skill_packets),
        "skill_tags": [packet.get("skill_tag", "") for packet in skill_packets],
        "packet_receipt_count": len(packet_receipts),
        "timeline_receipt_count": len(timeline_receipts),
        "checkpoint_hash_count": len(checkpoint_hashes),
        "help_level_profile": aggregate_help_profile(events),
        "open_operator_confirmation_count": sum(
            int(packet.get("open_operator_confirmation_count", 0) or 0) for packet in skill_packets
        ),
        "reflection_statuses": unique_values(
            status for packet in skill_packets for status in (packet.get("reflection_statuses", []) or [])
        ),
        "reviewer_question_count": sum(len(packet.get("human_reviewer_questions", []) or []) for packet in skill_packets),
        "export_mode": "metadata_hash_receipt_review_packet",
        "exam_deployment_status": "not_cleared",
    }


def reviewer_questions_for_skill(
    *,
    skill_tag: str,
    help_profile: dict[str, int],
    checkpoint_hash_count: int,
    open_confirmation_count: int,
    reflection_statuses: list[str],
) -> list[str]:
    questions = [
        f"Does the checkpoint-hash trail for {skill_tag} match the submitted notebook/export receipt set?",
        "Are all active help events within A0-A2, or are any higher-help exceptions separately documented?",
        "Do packet and executor receipts support the claimed dry-run route without exposing raw notebook code?",
        "Does the reflection status show human-reviewable evidence without claiming an Eigenleistung percentage?",
        "Is the next safe action compatible with exam_deployment_status not_cleared?",
    ]
    if checkpoint_hash_count == 0:
        questions.append("No checkpoint hash is present: should this skill remain waiting before export review?")
    if open_confirmation_count:
        questions.append("Which open operator confirmations must be resolved before any local write/export step?")
    if "reflection_evidence_present" not in reflection_statuses:
        questions.append("Reflection evidence is missing or unclear: should the reviewer request a short student reflection?")
    if any(level not in {"A0", "A1", "A2"} and count for level, count in help_profile.items()):
        questions.append("Higher-help levels appear in the profile: are they explicitly approved exceptions?")
    return questions


def reviewer_questions_for_summary(summary: dict[str, Any]) -> list[str]:
    return [
        "Do packet receipts, timeline receipts, and checkpoint hashes form a consistent review chain?",
        "Does the help-level profile stay within the A0-A2 standard?",
        "Are open operator confirmations clearly visible before any local write/export action?",
        "Is the packet usable for human review without raw queries, course raw text, notebook code, values, or solutions?",
        "Does every visible status preserve exam_deployment_status not_cleared?",
        f"Are all {summary.get('skill_count', 0)} skill review packets ready for human review?",
    ]


def export_packet_receipt(
    course_id: str,
    summary: dict[str, Any],
    skill_packets: list[dict[str, Any]],
    *,
    operator_confirmed_local_export_receipt: bool,
) -> dict[str, Any]:
    seed = {
        "course_id": course_id,
        "summary": summary,
        "skill_packets": [
            {
                "skill_tag": packet.get("skill_tag", ""),
                "packet_receipts": packet.get("packet_receipts", []),
                "executor_receipts": packet.get("executor_receipts", []),
                "checkpoint_hashes": packet.get("checkpoint_hashes", []),
                "help_level_profile": packet.get("help_level_profile", {}),
                "open_operator_confirmation_count": packet.get("open_operator_confirmation_count", 0),
                "reflection_statuses": packet.get("reflection_statuses", []),
            }
            for packet in skill_packets
        ],
        "operator_confirmed_local_export_receipt": bool(operator_confirmed_local_export_receipt),
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "timeline_export_review_packet_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "local_write_started": bool(operator_confirmed_local_export_receipt),
        "operator_confirmation_required_for_write": True,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "timeline-export-review-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
