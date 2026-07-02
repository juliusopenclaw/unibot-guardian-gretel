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
    return payload


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
