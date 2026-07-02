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
    return payload


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
