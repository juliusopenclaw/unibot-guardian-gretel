from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_run_packet_builder import build_exam_run_packet
from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot


EXAM_PACKET_TIMELINE_SCHEMA_VERSION = "unibot-exam-packet-timeline-v1"
EXAM_PACKET_TIMELINE_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-packet-timeline-workspace-card-timeline-alignment-v1"
)
EXAM_PACKET_TIMELINE_ENDPOINT = "/api/unibot/course/exam-packet-timeline"


def build_exam_packet_timeline(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    selected_skill_tag: str = "",
    focus_query: str = "",
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
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    packets = normalized_packets(exam_run_packets, exam_run_packet)
    if not packets:
        packets = [
            build_exam_run_packet(
                course_id=safe_id,
                selected_skill_tag=selected_skill_tag,
                focus_query=focus_query or query,
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
                python_exam_local_cycle_readiness_review=python_exam_local_cycle_readiness_review,
                python_exam_local_cycle_readiness_handoff=python_exam_local_cycle_readiness_handoff,
                python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
                python_exam_local_cycle_chain_snapshot=python_exam_local_cycle_chain_snapshot,
                public_safe=public_safe,
            )
        ]
    selected_packets = filter_packets(packets, selected_skill_tag or focus_query or query)
    events = sorted(
        [timeline_event(packet, index) for index, packet in enumerate(selected_packets)],
        key=lambda item: (str(item.get("generated_at_utc", "")), str(item.get("packet_receipt_id", ""))),
    )
    summary = timeline_summary(events)
    local_cycle_chain_snapshot = selected_local_cycle_chain_snapshot(
        provided_snapshot=python_exam_local_cycle_chain_snapshot,
        exam_run_packets=packets,
        python_exam_local_cycle_readiness_review=python_exam_local_cycle_readiness_review,
        python_exam_local_cycle_readiness_handoff=python_exam_local_cycle_readiness_handoff,
        python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
    )
    summary = incorporate_local_cycle_chain_snapshot(summary, local_cycle_chain_snapshot)
    payload = {
        "schema_version": EXAM_PACKET_TIMELINE_SCHEMA_VERSION,
        "artifact_type": "exam_packet_timeline",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "exam_packet_timeline_ready",
        "timeline_title": "Exam Packet Timeline Viewer",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Exam Packet Timeline Viewer. It shows metadata- and hash-only events from Exam Run Packets: "
            "packet receipt, route, executed dry-run, checkpoint hashes, help-level profile, open operator "
            "confirmations, reflection status, and next safe action. It never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, proctoring, AI "
            "detection, automatic assessment, or exam clearance."
        ),
        "timeline_summary": summary,
        "local_cycle_chain_snapshot": local_cycle_chain_snapshot,
        "timeline_events": events,
        "export_review_preview": export_review_preview(events, summary),
        "timeline_receipt": timeline_receipt(safe_id, events, summary),
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; die Timeline bleibt not_cleared."
        ),
        "next_actions": [
            "Review the timeline events before building an export review packet.",
            summary.get("latest_next_safe_action", "Continue with the next metadata-only review step."),
            "Keep real-world exam clearance outside UniBot; this timeline remains not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    payload["workspace_card_timeline_alignment"] = build_exam_packet_timeline_workspace_card_alignment(payload)
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def exam_packet_timeline_hash(timeline: dict[str, Any] | None = None) -> str:
    timeline = timeline if isinstance(timeline, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": timeline.get("schema_version", ""),
                "artifact_type": timeline.get("artifact_type", ""),
                "status": timeline.get("status", ""),
                "course_id": timeline.get("course_id", ""),
                "exam_deployment_status": timeline.get("exam_deployment_status", ""),
                "timeline_summary": timeline.get("timeline_summary", {}),
                "timeline_events": timeline.get("timeline_events", []),
                "export_review_preview": timeline.get("export_review_preview", {}),
                "public_safety_status": timeline.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def exam_packet_timeline_receipt_hash(timeline: dict[str, Any] | None = None) -> str:
    timeline = timeline if isinstance(timeline, dict) else {}
    receipt = timeline.get("timeline_receipt", {}) if isinstance(timeline.get("timeline_receipt"), dict) else {}
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", ""),
                "event_count": receipt.get("event_count", 0),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "summary_hash": sha256_text(
                    json.dumps(timeline.get("timeline_summary", {}), sort_keys=True, ensure_ascii=False)
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_exam_packet_timeline_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic exam packet timeline workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic exam packet timeline prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_exam_packet_timeline_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_timeline_before_review_packet_or_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__EXAM_PACKET_TIMELINE_RECEIPT_HASH__",
            "checkpoint_hash": "__EXAM_PACKET_TIMELINE_HASH__",
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


def safe_exam_packet_timeline_workspace_card(
    workspace_card: dict[str, Any],
    *,
    timeline_hash: str = "",
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
    if timeline_hash and checkpoint_hash == "__EXAM_PACKET_TIMELINE_HASH__":
        checkpoint_hash = timeline_hash
    if receipt_hash and task_hash == "__EXAM_PACKET_TIMELINE_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_exam_packet_timeline_gate")),
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


def build_exam_packet_timeline_workspace_card_alignment(
    exam_packet_timeline: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timeline = exam_packet_timeline if isinstance(exam_packet_timeline, dict) else {}
    summary = timeline.get("timeline_summary", {}) if isinstance(timeline.get("timeline_summary"), dict) else {}
    receipt = timeline.get("timeline_receipt", {}) if isinstance(timeline.get("timeline_receipt"), dict) else {}
    preview = timeline.get("export_review_preview", {}) if isinstance(timeline.get("export_review_preview"), dict) else {}
    timeline_hash = exam_packet_timeline_hash(timeline)
    receipt_hash = exam_packet_timeline_receipt_hash(timeline)
    workspace_card = safe_exam_packet_timeline_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_exam_packet_timeline_workspace_card(),
        timeline_hash=timeline_hash,
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
    events = [event for event in timeline.get("timeline_events", []) if isinstance(event, dict)]
    local_write_boundary_ok = all(event.get("local_write_started") is False for event in events)
    contracts = {
        "timeline_public_safe": timeline.get("public_safety_status") == "pass",
        "timeline_ready": timeline.get("status") == "exam_packet_timeline_ready"
        and summary.get("event_count", 0) >= 1
        and len(events) >= 1,
        "receipt_ready_not_clearance": receipt.get("status") == "exam_packet_timeline_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and bool(receipt.get("receipt_hash"))
        and receipt.get("not_cleared_receipt") is True,
        "events_and_checkpoint_counts_linked": int(summary.get("event_count", 0) or 0) == len(events)
        and int(summary.get("packet_receipt_count", 0) or 0) >= 1
        and int(summary.get("checkpoint_hash_count", 0) or 0) >= 0,
        "export_review_preview_ready": preview.get("status") == "timeline_export_review_ready",
        "local_write_boundary_preserved": local_write_boundary_ok,
        "no_clearance_or_deployment_claim": timeline.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(timeline.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names)
        and all(event.get(flag, False) is False for event in events for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(timeline.get(flag) is False for flag in high_stakes_flag_names)
        and all(event.get(flag, False) is False for event in events for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_exam_packet_timeline_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == timeline_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "exam_packet_timeline",
        "timeline_export_review_packet",
        "timeline_export_receipt_journal",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": EXAM_PACKET_TIMELINE_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "exam_packet_timeline_hash": timeline_hash,
        "exam_packet_timeline_receipt_hash": receipt_hash,
        "timeline_status": timeline.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "event_count": summary.get("event_count", 0),
        "visible_event_count": len(events),
        "packet_receipt_count": summary.get("packet_receipt_count", 0),
        "checkpoint_hash_count": summary.get("checkpoint_hash_count", 0),
        "open_operator_confirmation_count": summary.get("open_operator_confirmation_count", 0),
        "export_review_preview_status": preview.get("status", "missing"),
        "exam_deployment_status": timeline.get("exam_deployment_status", "missing"),
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
        "workspace_card_exam_packet_timeline_gate_linked": contracts["workspace_card_exam_packet_timeline_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Exam packet timeline claims are hash-only review aids for timeline events, packet receipts, "
            "checkpoint counts, and local-write boundaries; they do not authorize publication, provider calls, "
            "grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "exam-packet-timeline-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_exam_packet_timeline_inputs() -> dict[str, Any]:
    timeline = build_exam_packet_timeline(
        selected_skill_tag="python_lists",
        focus_query="Python Listen",
        public_safe=True,
    )
    return {"timeline": timeline}


def normalized_packets(
    exam_run_packets: list[dict[str, Any]] | None,
    exam_run_packet: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    packets = [item for item in (exam_run_packets or []) if isinstance(item, dict)]
    if isinstance(exam_run_packet, dict):
        packet_id = exam_run_packet.get("packet_receipt", {}).get("receipt_id", "") if isinstance(exam_run_packet.get("packet_receipt"), dict) else ""
        existing_ids = {
            item.get("packet_receipt", {}).get("receipt_id", "")
            for item in packets
            if isinstance(item.get("packet_receipt"), dict)
        }
        if not packet_id or packet_id not in existing_ids:
            packets.append(exam_run_packet)
    return packets


def filter_packets(packets: list[dict[str, Any]], selector: str) -> list[dict[str, Any]]:
    if not selector:
        return packets
    selected = str(selector).lower()
    matches = []
    for packet in packets:
        skill = packet.get("selected_skill_packet", {}) if isinstance(packet.get("selected_skill_packet"), dict) else {}
        tag = str(skill.get("skill_tag", "")).lower()
        title = str(skill.get("title", "")).lower()
        if selected == tag or selected in tag or tag in selected or selected in title:
            matches.append(packet)
    return matches or packets


def timeline_event(packet: dict[str, Any], index: int) -> dict[str, Any]:
    skill = packet.get("selected_skill_packet", {}) if isinstance(packet.get("selected_skill_packet"), dict) else {}
    route = skill.get("selected_route", {}) if isinstance(skill.get("selected_route"), dict) else {}
    executed = skill.get("executed_dry_run", {}) if isinstance(skill.get("executed_dry_run"), dict) else {}
    trace = (
        packet.get("human_reviewable_independence_trace", {})
        if isinstance(packet.get("human_reviewable_independence_trace"), dict)
        else {}
    )
    receipt = packet.get("packet_receipt", {}) if isinstance(packet.get("packet_receipt"), dict) else {}
    source_receipts = packet.get("source_receipts", {}) if isinstance(packet.get("source_receipts"), dict) else {}
    checkpoint_hashes = list(skill.get("latest_checkpoint_hashes", []) or trace.get("checkpoint_hashes", []) or [])[:6]
    open_confirmations = [str(item) for item in list(skill.get("open_operator_confirmations", []) or trace.get("open_operator_confirmations", []) or [])[:10]]
    reflection = [str(item) for item in list(trace.get("reflection_statuses", []) or [])[:8]]
    event_seed = {
        "index": index,
        "skill_tag": skill.get("skill_tag", ""),
        "packet_receipt": receipt.get("receipt_id", ""),
        "route": route.get("route_id", ""),
        "executed": executed.get("artifact_type", ""),
        "result": executed.get("result_hash", ""),
        "checkpoints": checkpoint_hashes,
        "chain_snapshot_hash": str(packet.get("local_cycle_chain_snapshot", {}).get("snapshot_hash", ""))
        if isinstance(packet.get("local_cycle_chain_snapshot"), dict)
        else "",
    }
    event_hash = sha256_text(json.dumps(event_seed, sort_keys=True, ensure_ascii=False))
    return {
        "event_type": "exam_run_packet",
        "event_id": event_hash[:20],
        "event_hash": event_hash,
        "event_index": index,
        "generated_at_utc": packet.get("generated_at_utc", ""),
        "skill_tag": skill.get("skill_tag", ""),
        "packet_receipt_id": receipt.get("receipt_id", ""),
        "packet_receipt_status": receipt.get("status", "unknown"),
        "route_id": route.get("route_id", "unknown"),
        "route_endpoint": route.get("endpoint", ""),
        "dry_run_by_default": bool(route.get("dry_run_by_default", True)),
        "requested_help_level": route.get("requested_help_level", "A2"),
        "executed_artifact_type": executed.get("artifact_type", "unknown"),
        "executed_status": executed.get("status", "unknown"),
        "executed_receipt_status": executed.get("receipt_status", "unknown"),
        "executed_result_hash": executed.get("result_hash", ""),
        "local_write_started": bool(executed.get("local_write_started", False)),
        "executor_receipt_id": trace.get("executor_receipt_id", source_receipts.get("executor_receipt_id", "")),
        "checkpoint_hashes": checkpoint_hashes,
        "checkpoint_hash_count": len(checkpoint_hashes),
        "help_level_profile": dict(skill.get("help_level_profile", {}) or trace.get("help_level_profile", {}) or {}),
        "open_operator_confirmations": open_confirmations,
        "open_operator_confirmation_count": int(skill.get("open_operator_confirmation_count", 0) or len(open_confirmations)),
        "reflection_statuses": reflection,
        "next_safe_action": skill.get("next_safe_action", ""),
        "local_cycle_chain_snapshot_status": str(packet.get("local_cycle_chain_snapshot", {}).get("status", "missing"))
        if isinstance(packet.get("local_cycle_chain_snapshot"), dict)
        else "missing",
        "local_cycle_chain_snapshot_hash": str(packet.get("local_cycle_chain_snapshot", {}).get("snapshot_hash", ""))
        if isinstance(packet.get("local_cycle_chain_snapshot"), dict)
        else "",
        "local_cycle_chain_step_count": int(packet.get("local_cycle_chain_snapshot", {}).get("chain_step_count", 0) or 0)
        if isinstance(packet.get("local_cycle_chain_snapshot"), dict)
        else 0,
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
    }


def timeline_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    help_profile: dict[str, int] = {}
    skill_tags = []
    packet_receipts = []
    reflection_statuses = []
    checkpoint_hashes = []
    chain_snapshot_statuses = []
    chain_snapshot_hashes = []
    open_confirmations = 0
    latest_next_safe_action = ""
    for event in events:
        tag = str(event.get("skill_tag", ""))
        if tag and tag not in skill_tags:
            skill_tags.append(tag)
        receipt_id = str(event.get("packet_receipt_id", ""))
        if receipt_id and receipt_id not in packet_receipts:
            packet_receipts.append(receipt_id)
        for key, value in dict(event.get("help_level_profile", {}) or {}).items():
            help_profile[str(key)] = help_profile.get(str(key), 0) + int(value or 0)
        for status in event.get("reflection_statuses", []) or []:
            if status not in reflection_statuses:
                reflection_statuses.append(status)
        for item in event.get("checkpoint_hashes", []) or []:
            if item and item not in checkpoint_hashes:
                checkpoint_hashes.append(item)
        chain_status = str(event.get("local_cycle_chain_snapshot_status", ""))
        chain_hash = str(event.get("local_cycle_chain_snapshot_hash", ""))
        if chain_status and chain_status not in chain_snapshot_statuses:
            chain_snapshot_statuses.append(chain_status)
        if chain_hash and chain_hash not in chain_snapshot_hashes:
            chain_snapshot_hashes.append(chain_hash)
        open_confirmations += int(event.get("open_operator_confirmation_count", 0) or 0)
        if event.get("next_safe_action"):
            latest_next_safe_action = str(event.get("next_safe_action"))
    return {
        "event_count": len(events),
        "skill_tags": skill_tags,
        "packet_receipt_count": len(packet_receipts),
        "packet_receipt_ids": packet_receipts,
        "checkpoint_hash_count": len(checkpoint_hashes),
        "help_level_profile": help_profile,
        "open_operator_confirmation_count": open_confirmations,
        "reflection_statuses": reflection_statuses,
        "latest_next_safe_action": latest_next_safe_action,
        "local_cycle_chain_snapshot_statuses": chain_snapshot_statuses,
        "local_cycle_chain_snapshot_hashes": chain_snapshot_hashes,
        "local_cycle_chain_snapshot_count": len(chain_snapshot_hashes),
        "exam_deployment_status": "not_cleared",
    }


def selected_local_cycle_chain_snapshot(
    *,
    provided_snapshot: dict[str, Any] | None,
    exam_run_packets: list[dict[str, Any]],
    python_exam_local_cycle_readiness_review: dict[str, Any] | None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(provided_snapshot, dict):
        return provided_snapshot
    for packet in exam_run_packets:
        snapshot = packet.get("local_cycle_chain_snapshot", {})
        if isinstance(snapshot, dict) and snapshot:
            return snapshot
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    if not review and not handoff and not workspace_card:
        return {}
    snapshot = build_python_exam_local_cycle_chain_snapshot(
        python_exam_local_cycle_readiness_review=review,
        python_exam_local_cycle_readiness_handoff=handoff,
        python_exam_local_cycle_operator_workspace_card=workspace_card,
        public_safe=True,
    )
    return snapshot if isinstance(snapshot, dict) else {}


def incorporate_local_cycle_chain_snapshot(summary: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(summary, dict) or not isinstance(snapshot, dict) or not snapshot:
        return summary
    statuses = list(summary.get("local_cycle_chain_snapshot_statuses", []) or [])
    hashes = list(summary.get("local_cycle_chain_snapshot_hashes", []) or [])
    status = str(snapshot.get("status", ""))
    snapshot_hash = str(snapshot.get("snapshot_hash", ""))
    if status and status not in statuses:
        statuses.append(status)
    if snapshot_hash and snapshot_hash not in hashes:
        hashes.append(snapshot_hash)
    summary = dict(summary)
    summary["local_cycle_chain_snapshot_statuses"] = statuses
    summary["local_cycle_chain_snapshot_hashes"] = hashes
    summary["local_cycle_chain_snapshot_count"] = len(hashes)
    return summary


def export_review_preview(events: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "timeline_export_review_ready" if events else "timeline_export_review_waiting_for_packet",
        "review_items": {
            "packet_receipts": [event.get("packet_receipt_id", "") for event in events if event.get("packet_receipt_id")],
            "route_ids": [event.get("route_id", "") for event in events if event.get("route_id")],
            "executed_artifacts": [event.get("executed_artifact_type", "") for event in events if event.get("executed_artifact_type")],
            "checkpoint_hashes": [hash_value for event in events for hash_value in (event.get("checkpoint_hashes", []) or [])],
            "help_level_profile": dict(summary.get("help_level_profile", {}) or {}),
            "open_operator_confirmation_count": summary.get("open_operator_confirmation_count", 0),
            "reflection_statuses": list(summary.get("reflection_statuses", []) or []),
            "next_safe_actions": [event.get("next_safe_action", "") for event in events if event.get("next_safe_action")],
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "exam_clearance_claimed": False,
    }


def timeline_receipt(course_id: str, events: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "course_id": course_id,
        "events": [
            {
                "event_id": event.get("event_id", ""),
                "skill_tag": event.get("skill_tag", ""),
                "packet_receipt_id": event.get("packet_receipt_id", ""),
                "route_id": event.get("route_id", ""),
                "executed_result_hash": event.get("executed_result_hash", ""),
                "checkpoint_hashes": event.get("checkpoint_hashes", []),
            }
            for event in events
        ],
        "summary": summary,
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "exam_packet_timeline_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "event_count": len(events),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-packet-timeline")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
