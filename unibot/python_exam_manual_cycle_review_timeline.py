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
from .python_exam_manual_post_cycle_receipt_intake import safe_evidence_binder


PYTHON_EXAM_MANUAL_CYCLE_REVIEW_TIMELINE_SCHEMA_VERSION = "unibot-python-exam-manual-cycle-review-timeline-v1"
PYTHON_EXAM_MANUAL_CYCLE_REVIEW_TIMELINE_ENDPOINT = "/api/unibot/course/python-exam-manual-cycle-review-timeline"

TIMELINE_REVIEW_RECOMMENDATIONS = {
    "continue_cycle_review",
    "collect_missing_hashes",
    "ready_for_human_timeline_review",
    "reject_timeline_review",
}


def build_python_exam_manual_cycle_review_timeline(
    *,
    python_exam_manual_cycle_closure_ledger: dict[str, Any] | None = None,
    python_exam_manual_post_cycle_receipt_intake: dict[str, Any] | None = None,
    python_exam_manual_cycle_evidence_binder: dict[str, Any] | None = None,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
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
    closure_view = safe_closure_ledger(closure_ledger)
    intake_view = safe_post_cycle_intake(post_cycle_intake)
    binder_view = safe_evidence_binder(evidence_binder)
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    selected = str(
        selected_skill_tag
        or closure_view.get("selected_skill_tag", "")
        or intake_view.get("selected_skill_tag", "")
        or binder_view.get("selected_skill_tag", "")
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    events = timeline_events(
        closure_view=closure_view,
        intake_view=intake_view,
        binder_view=binder_view,
        launch_view=launch_view,
        console_view=console_view,
    )
    summary = timeline_summary(selected_skill_tag=selected, closure_view=closure_view, intake_view=intake_view, events=events)
    receipt = review_timeline_receipt(summary, events)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_CYCLE_REVIEW_TIMELINE_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_cycle_review_timeline",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_cycle_review_timeline_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Cycle Review Timeline. It consumes only Closure Ledger, Post-Cycle Receipt "
            "Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata to build a "
            "chronological hash-only review timeline. It exposes only stop-go state, launch decision, binder "
            "receipt, post-cycle intake, closure ledger, missing/accepted hashes, Source-Card anchors, "
            "task/checkpoint hashes, Help-Ledger hash, operator reflection hash, and one review recommendation. "
            "It executes nothing, writes nothing, and never returns raw queries, course raw text, notebook code, "
            "local paths, values, solutions, final interpretations, scores, rankings, grades, proctoring, AI "
            "detection, automatic grading, or exam clearance claims."
        ),
        "manual_cycle_review_timeline_endpoint": PYTHON_EXAM_MANUAL_CYCLE_REVIEW_TIMELINE_ENDPOINT,
        "selected_skill_tag": selected,
        "timeline_summary": summary,
        "timeline_review_recommendation": summary["timeline_review_recommendation"],
        "timeline_events": events,
        "manual_cycle_review_timeline_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Review Timeline bleibt not_cleared."
        ),
        "next_actions": [
            f"Timeline review recommendation: {summary['timeline_review_recommendation']}.",
            "Use this timeline only as a chronological, human-reviewable hash record.",
            "Keep raw notebook work, values, local files, scoring, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_closure_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    summary = ledger.get("closure_summary", {}) if isinstance(ledger.get("closure_summary"), dict) else {}
    receipt = (
        ledger.get("manual_cycle_closure_ledger_receipt", {})
        if isinstance(ledger.get("manual_cycle_closure_ledger_receipt"), dict)
        else {}
    )
    entries = ledger.get("closure_ledger_entries", []) if isinstance(ledger.get("closure_ledger_entries"), list) else []
    return {
        "status": str(ledger.get("status", "missing")),
        "selected_skill_tag": str(ledger.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "closure_ledger_decision": str(
            ledger.get("closure_ledger_decision") or summary.get("closure_ledger_decision", "keep_cycle_open")
        ),
        "closure_ledger_reason": str(summary.get("closure_ledger_reason", "")),
        "post_cycle_review_recommendation": str(summary.get("post_cycle_review_recommendation", "")),
        "pre_cycle_stop_go_action": str(summary.get("pre_cycle_stop_go_action", "")),
        "launch_decision": str(summary.get("launch_decision", "")),
        "manual_confirmation_action": str(summary.get("manual_confirmation_action", "")),
        "open_confirmation_count": int(summary.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes", []) or [])][:12],
        "forbidden_metadata_keys": [str(item) for item in (summary.get("forbidden_metadata_keys", []) or [])][:12],
        "invalid_hash_fields": [str(item) for item in (summary.get("invalid_hash_fields", []) or [])][:12],
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
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "binder_receipt_hash": str(summary.get("binder_receipt_hash", "")),
        "launch_receipt_hash": str(summary.get("launch_receipt_hash", "")),
        "post_cycle_receipt_hash": str(summary.get("post_cycle_receipt_hash", "")),
        "intake_receipt_hash": str(summary.get("intake_receipt_hash", "")),
        "closure_receipt_hash": str(receipt.get("receipt_hash", "")),
        "ledger_entry_hashes": [str(item.get("entry_hash", "")) for item in entries if isinstance(item, dict)][:8],
        "next_safe_review_action": str(summary.get("next_safe_review_action", "")),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def timeline_events(
    *,
    closure_view: dict[str, Any],
    intake_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
) -> list[dict[str, Any]]:
    seeds = [
        {
            "event_id": "pre_cycle_stop_go",
            "label": "Pre-Cycle Stop-Go",
            "status": binder_view.get("status", "missing"),
            "review_state": closure_view.get("pre_cycle_stop_go_action") or binder_view.get("next_safe_review_action", ""),
            "task_hash": closure_view.get("task_hash") or binder_view.get("task_hash", ""),
            "checkpoint_hash": closure_view.get("checkpoint_hash") or binder_view.get("checkpoint_hash", ""),
            "source_card_ids": closure_view.get("source_card_ids") or binder_view.get("source_card_ids", []),
            "receipt_hash": binder_view.get("binder_receipt_hash", ""),
        },
        {
            "event_id": "launch_decision",
            "label": "Launch Decision",
            "status": launch_view.get("status", "missing"),
            "review_state": closure_view.get("launch_decision") or launch_view.get("launch_decision", ""),
            "manual_confirmation_action": closure_view.get("manual_confirmation_action")
            or console_view.get("next_manual_confirmation_action", ""),
            "open_confirmation_count": closure_view.get("open_confirmation_count", 0),
            "confirmed_count": closure_view.get("confirmed_count", 0),
            "receipt_hash": launch_view.get("launch_receipt_hash", ""),
        },
        {
            "event_id": "evidence_binder",
            "label": "Evidence Binder",
            "status": binder_view.get("status", "missing"),
            "review_state": binder_view.get("next_safe_review_action", ""),
            "help_ledger_hash": closure_view.get("help_ledger_hash") or binder_view.get("help_ledger_preview_hash", ""),
            "receipt_hash": closure_view.get("binder_receipt_hash") or binder_view.get("binder_receipt_hash", ""),
        },
        {
            "event_id": "post_cycle_intake",
            "label": "Post-Cycle Intake",
            "status": intake_view.get("status", "missing"),
            "review_state": intake_view.get("post_cycle_review_recommendation", ""),
            "missing_required_hashes": closure_view.get("missing_required_hashes") or intake_view.get("missing_required_hashes", []),
            "post_cycle_receipt_hash": closure_view.get("post_cycle_receipt_hash") or intake_view.get("post_cycle_receipt_hash", ""),
            "operator_reflection_hash": closure_view.get("operator_reflection_hash")
            or intake_view.get("operator_reflection_hash", ""),
            "receipt_hash": closure_view.get("intake_receipt_hash") or intake_view.get("intake_receipt_hash", ""),
        },
        {
            "event_id": "closure_ledger",
            "label": "Closure Ledger",
            "status": closure_view.get("status", "missing"),
            "review_state": closure_view.get("closure_ledger_decision", "keep_cycle_open"),
            "next_safe_review_action": closure_view.get("next_safe_review_action", ""),
            "accepted_post_cycle_hashes": closure_view.get("accepted_post_cycle_hashes", {}),
            "receipt_hash": closure_view.get("closure_receipt_hash", ""),
        },
    ]
    events = []
    for index, seed in enumerate(seeds, start=1):
        event_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
        event = dict(seed)
        event.update(
            {
                "sequence_index": index,
                "event_hash": event_hash,
                "not_cleared_receipt": True,
                "local_writes_requested": False,
                "local_execution_started": False,
                "raw_text_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
                "exam_deployment_status": "not_cleared",
            }
        )
        events.append(event)
    return events


def timeline_summary(
    *,
    selected_skill_tag: str,
    closure_view: dict[str, Any],
    intake_view: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    closure_decision = closure_view.get("closure_ledger_decision", "keep_cycle_open")
    if closure_decision == "close_cycle_for_human_review":
        recommendation = "ready_for_human_timeline_review"
        reason = "closure_ledger_ready_for_human_review"
    elif closure_decision == "request_post_cycle_hash_review":
        recommendation = "collect_missing_hashes"
        reason = "closure_ledger_requests_post_cycle_hash_review"
    elif closure_decision == "reject_cycle_closure":
        recommendation = "reject_timeline_review"
        reason = "closure_ledger_rejected_cycle_closure"
    else:
        recommendation = "continue_cycle_review"
        reason = "cycle_still_open_for_review"
    return {
        "status": "python_exam_manual_cycle_review_timeline_ready",
        "selected_skill_tag": selected_skill_tag,
        "timeline_review_recommendation": recommendation,
        "timeline_review_reason": reason,
        "allowed_timeline_review_recommendations": sorted(TIMELINE_REVIEW_RECOMMENDATIONS),
        "closure_ledger_decision": closure_decision,
        "post_cycle_review_recommendation": closure_view.get(
            "post_cycle_review_recommendation",
            intake_view.get("post_cycle_review_recommendation", ""),
        ),
        "next_safe_review_action": closure_view.get("next_safe_review_action", ""),
        "missing_required_hashes": list(closure_view.get("missing_required_hashes", []) or [])[:12],
        "accepted_post_cycle_hashes": closure_view.get("accepted_post_cycle_hashes", {}),
        "task_hash": closure_view.get("task_hash", ""),
        "checkpoint_hash": closure_view.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": closure_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": closure_view.get("help_ledger_hash", ""),
        "operator_reflection_hash": closure_view.get("operator_reflection_hash", ""),
        "source_card_ids": list(closure_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(closure_view.get("source_anchor_hash_count", 0) or 0),
        "binder_receipt_hash": closure_view.get("binder_receipt_hash", ""),
        "launch_receipt_hash": closure_view.get("launch_receipt_hash", ""),
        "post_cycle_receipt_hash": closure_view.get("post_cycle_receipt_hash", ""),
        "intake_receipt_hash": closure_view.get("intake_receipt_hash", ""),
        "closure_receipt_hash": closure_view.get("closure_receipt_hash", ""),
        "timeline_event_count": len(events),
        "timeline_event_hashes": [event.get("event_hash", "") for event in events],
        "help_level": safe_help_level(str(closure_view.get("help_level", "A2"))),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def review_timeline_receipt(summary: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "timeline_event_hashes": [event.get("event_hash", "") for event in events],
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_cycle_review_timeline_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "timeline_review_recommendation": summary.get("timeline_review_recommendation", "continue_cycle_review"),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-cycle-review-timeline")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
