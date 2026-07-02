from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_closure_ledger import safe_post_cycle_intake
from .python_exam_manual_cycle_evidence_binder import safe_launch_receipt
from .python_exam_manual_cycle_launch_receipt import safe_manual_confirmation_console
from .python_exam_manual_cycle_review_timeline import safe_closure_ledger
from .python_exam_manual_post_cycle_receipt_intake import safe_evidence_binder


PYTHON_EXAM_MANUAL_CYCLE_REVIEW_PACKET_SCHEMA_VERSION = "unibot-python-exam-manual-cycle-review-packet-v1"
PYTHON_EXAM_MANUAL_CYCLE_REVIEW_PACKET_ENDPOINT = "/api/unibot/course/python-exam-manual-cycle-review-packet"

PACKET_RECOMMENDATIONS = {
    "keep_review_packet_open",
    "request_hash_completion",
    "ready_for_human_packet_review",
    "reject_review_packet",
}


def build_python_exam_manual_cycle_review_packet(
    *,
    python_exam_manual_cycle_review_timeline: dict[str, Any] | None = None,
    python_exam_manual_cycle_closure_ledger: dict[str, Any] | None = None,
    python_exam_manual_post_cycle_receipt_intake: dict[str, Any] | None = None,
    python_exam_manual_cycle_evidence_binder: dict[str, Any] | None = None,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    timeline = python_exam_manual_cycle_review_timeline if isinstance(python_exam_manual_cycle_review_timeline, dict) else {}
    closure_ledger = (
        python_exam_manual_cycle_closure_ledger if isinstance(python_exam_manual_cycle_closure_ledger, dict) else {}
    )
    post_cycle_intake = (
        python_exam_manual_post_cycle_receipt_intake
        if isinstance(python_exam_manual_post_cycle_receipt_intake, dict)
        else {}
    )
    evidence_binder = (
        python_exam_manual_cycle_evidence_binder if isinstance(python_exam_manual_cycle_evidence_binder, dict) else {}
    )
    launch_receipt = python_exam_manual_cycle_launch_receipt if isinstance(python_exam_manual_cycle_launch_receipt, dict) else {}
    manual_console = (
        python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    )
    timeline_view = safe_review_timeline(timeline)
    closure_view = safe_closure_ledger(closure_ledger)
    intake_view = safe_post_cycle_intake(post_cycle_intake)
    binder_view = safe_evidence_binder(evidence_binder)
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    selected = str(
        selected_skill_tag
        or timeline_view.get("selected_skill_tag", "")
        or closure_view.get("selected_skill_tag", "")
        or intake_view.get("selected_skill_tag", "")
        or binder_view.get("selected_skill_tag", "")
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    packet_body = review_packet_body(
        timeline_view=timeline_view,
        closure_view=closure_view,
        intake_view=intake_view,
        binder_view=binder_view,
        launch_view=launch_view,
        console_view=console_view,
    )
    summary = review_packet_summary(selected_skill_tag=selected, timeline_view=timeline_view, packet_body=packet_body)
    receipt = review_packet_receipt(summary, packet_body)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_CYCLE_REVIEW_PACKET_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_cycle_review_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_cycle_review_packet_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Cycle Review Packet. It consumes only Review Timeline, Closure Ledger, "
            "Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console "
            "metadata to create a compact hash-only packet for human review before submission or archiving. "
            "It exposes only recommendation state, closure decision, missing/accepted hashes, Source-Card "
            "anchors, task/checkpoint hashes, Help-Ledger hash, operator reflection hash, receipt hashes, "
            "timeline event hashes, and one packet recommendation. It executes nothing, writes nothing, and "
            "never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "manual_cycle_review_packet_endpoint": PYTHON_EXAM_MANUAL_CYCLE_REVIEW_PACKET_ENDPOINT,
        "selected_skill_tag": selected,
        "review_packet_summary": summary,
        "packet_recommendation": summary["packet_recommendation"],
        "review_packet_body": packet_body,
        "manual_cycle_review_packet_receipt": receipt,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Review Packet bleibt not_cleared."
        ),
        "next_actions": [
            f"Packet recommendation: {summary['packet_recommendation']}.",
            "Use this packet only as compact, human-reviewable hash evidence before submission or archiving.",
            "Keep raw notebook work, values, local files, scoring, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_review_timeline(timeline: dict[str, Any]) -> dict[str, Any]:
    summary = timeline.get("timeline_summary", {}) if isinstance(timeline.get("timeline_summary"), dict) else {}
    receipt = (
        timeline.get("manual_cycle_review_timeline_receipt", {})
        if isinstance(timeline.get("manual_cycle_review_timeline_receipt"), dict)
        else {}
    )
    events = timeline.get("timeline_events", []) if isinstance(timeline.get("timeline_events"), list) else []
    return {
        "status": str(timeline.get("status", "missing")),
        "selected_skill_tag": str(timeline.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "timeline_review_recommendation": str(
            timeline.get("timeline_review_recommendation")
            or summary.get("timeline_review_recommendation", "continue_cycle_review")
        ),
        "timeline_review_reason": str(summary.get("timeline_review_reason", "")),
        "closure_ledger_decision": str(summary.get("closure_ledger_decision", "")),
        "post_cycle_review_recommendation": str(summary.get("post_cycle_review_recommendation", "")),
        "next_safe_review_action": str(summary.get("next_safe_review_action", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": (
            summary.get("accepted_post_cycle_hashes", {})
            if isinstance(summary.get("accepted_post_cycle_hashes"), dict)
            else {}
        ),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "notebook_checkpoint_hash": str(summary.get("notebook_checkpoint_hash", "")),
        "help_ledger_hash": str(summary.get("help_ledger_hash", "")),
        "operator_reflection_hash": str(summary.get("operator_reflection_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", 0) or 0),
        "binder_receipt_hash": str(summary.get("binder_receipt_hash", "")),
        "launch_receipt_hash": str(summary.get("launch_receipt_hash", "")),
        "post_cycle_receipt_hash": str(summary.get("post_cycle_receipt_hash", "")),
        "intake_receipt_hash": str(summary.get("intake_receipt_hash", "")),
        "closure_receipt_hash": str(summary.get("closure_receipt_hash", "")),
        "timeline_receipt_hash": str(receipt.get("receipt_hash", "")),
        "timeline_event_count": int(summary.get("timeline_event_count", len(events)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes", []) or [])][:12],
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def review_packet_body(
    *,
    timeline_view: dict[str, Any],
    closure_view: dict[str, Any],
    intake_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
) -> dict[str, Any]:
    accepted_hashes = timeline_view.get("accepted_post_cycle_hashes") or closure_view.get("accepted_post_cycle_hashes", {})
    return {
        "timeline_recommendation": timeline_view.get("timeline_review_recommendation", "continue_cycle_review"),
        "closure_decision": timeline_view.get("closure_ledger_decision")
        or closure_view.get("closure_ledger_decision", "keep_cycle_open"),
        "post_cycle_recommendation": timeline_view.get("post_cycle_review_recommendation")
        or intake_view.get("post_cycle_review_recommendation", ""),
        "launch_decision": closure_view.get("launch_decision") or launch_view.get("launch_decision", ""),
        "manual_confirmation_action": closure_view.get("manual_confirmation_action")
        or console_view.get("next_manual_confirmation_action", ""),
        "open_confirmation_count": int(closure_view.get("open_confirmation_count", console_view.get("open_confirmation_count", 0)) or 0),
        "confirmed_count": int(closure_view.get("confirmed_count", console_view.get("confirmed_count", 0)) or 0),
        "missing_required_hashes": list(timeline_view.get("missing_required_hashes") or closure_view.get("missing_required_hashes", []) or [])[:12],
        "accepted_post_cycle_hashes": accepted_hashes if isinstance(accepted_hashes, dict) else {},
        "source_card_ids": list(timeline_view.get("source_card_ids") or closure_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(
            timeline_view.get("source_anchor_hash_count", closure_view.get("source_anchor_hash_count", 0)) or 0
        ),
        "task_hash": timeline_view.get("task_hash") or closure_view.get("task_hash") or binder_view.get("task_hash", ""),
        "checkpoint_hash": timeline_view.get("checkpoint_hash") or closure_view.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": timeline_view.get("notebook_checkpoint_hash") or closure_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": timeline_view.get("help_ledger_hash") or closure_view.get("help_ledger_hash", ""),
        "operator_reflection_hash": timeline_view.get("operator_reflection_hash") or closure_view.get("operator_reflection_hash", ""),
        "receipt_hashes": {
            "binder_receipt_hash": timeline_view.get("binder_receipt_hash") or closure_view.get("binder_receipt_hash", ""),
            "launch_receipt_hash": timeline_view.get("launch_receipt_hash") or launch_view.get("launch_receipt_hash", ""),
            "post_cycle_receipt_hash": timeline_view.get("post_cycle_receipt_hash") or intake_view.get("post_cycle_receipt_hash", ""),
            "intake_receipt_hash": timeline_view.get("intake_receipt_hash") or intake_view.get("intake_receipt_hash", ""),
            "closure_receipt_hash": timeline_view.get("closure_receipt_hash") or closure_view.get("closure_receipt_hash", ""),
            "timeline_receipt_hash": timeline_view.get("timeline_receipt_hash", ""),
        },
        "timeline_event_hashes": list(timeline_view.get("timeline_event_hashes", []) or [])[:12],
        "timeline_event_count": int(timeline_view.get("timeline_event_count", 0) or 0),
        "help_level": safe_help_level(str(timeline_view.get("help_level", closure_view.get("help_level", "A2")))),
        "next_safe_review_action": timeline_view.get("next_safe_review_action") or closure_view.get("next_safe_review_action", ""),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def review_packet_summary(
    *,
    selected_skill_tag: str,
    timeline_view: dict[str, Any],
    packet_body: dict[str, Any],
) -> dict[str, Any]:
    timeline_recommendation = packet_body.get("timeline_recommendation", "continue_cycle_review")
    if timeline_view.get("status") != "python_exam_manual_cycle_review_timeline_ready":
        recommendation = "keep_review_packet_open"
        reason = "review_timeline_missing_or_not_ready"
    elif timeline_recommendation == "ready_for_human_timeline_review":
        recommendation = "ready_for_human_packet_review"
        reason = "timeline_ready_for_human_packet_review"
    elif timeline_recommendation == "collect_missing_hashes":
        recommendation = "request_hash_completion"
        reason = "timeline_requests_missing_hash_completion"
    elif timeline_recommendation == "reject_timeline_review":
        recommendation = "reject_review_packet"
        reason = "timeline_rejected_cycle_review"
    else:
        recommendation = "keep_review_packet_open"
        reason = "timeline_review_still_open"
    return {
        "status": "python_exam_manual_cycle_review_packet_ready",
        "selected_skill_tag": selected_skill_tag,
        "packet_recommendation": recommendation,
        "packet_recommendation_reason": reason,
        "allowed_packet_recommendations": sorted(PACKET_RECOMMENDATIONS),
        "timeline_recommendation": timeline_recommendation,
        "closure_decision": packet_body.get("closure_decision", "keep_cycle_open"),
        "post_cycle_recommendation": packet_body.get("post_cycle_recommendation", ""),
        "missing_required_hashes": list(packet_body.get("missing_required_hashes", []) or [])[:12],
        "accepted_post_cycle_hashes": packet_body.get("accepted_post_cycle_hashes", {}),
        "task_hash": packet_body.get("task_hash", ""),
        "checkpoint_hash": packet_body.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": packet_body.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": packet_body.get("help_ledger_hash", ""),
        "operator_reflection_hash": packet_body.get("operator_reflection_hash", ""),
        "source_card_ids": list(packet_body.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(packet_body.get("source_anchor_hash_count", 0) or 0),
        "receipt_hashes": packet_body.get("receipt_hashes", {}),
        "timeline_event_hashes": list(packet_body.get("timeline_event_hashes", []) or [])[:12],
        "timeline_event_count": int(packet_body.get("timeline_event_count", 0) or 0),
        "next_safe_review_action": packet_body.get("next_safe_review_action", ""),
        "help_level": safe_help_level(str(packet_body.get("help_level", "A2"))),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def review_packet_receipt(summary: dict[str, Any], packet_body: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "packet_body": packet_body,
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_cycle_review_packet_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "packet_recommendation": summary.get("packet_recommendation", "keep_review_packet_open"),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-cycle-review-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
