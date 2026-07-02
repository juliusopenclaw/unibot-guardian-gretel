from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_archive_decision_draft import safe_reviewer_packet
from .python_exam_manual_export_reviewer_packet import safe_export_review_queue
from .python_exam_manual_final_review_handoff import safe_archive_decision_draft


PYTHON_EXAM_MANUAL_FINAL_REVIEW_RECEIPT_LEDGER_SCHEMA_VERSION = (
    "unibot-python-exam-manual-final-review-receipt-ledger-v1"
)
PYTHON_EXAM_MANUAL_FINAL_REVIEW_RECEIPT_LEDGER_ENDPOINT = (
    "/api/unibot/course/python-exam-manual-final-review-receipt-ledger"
)

FINAL_REVIEW_RECEIPT_LEDGER_RECOMMENDATIONS = {
    "keep_final_ledger_open",
    "request_hash_completion",
    "ready_for_manual_final_ledger_review",
    "reject_final_ledger",
}


def build_python_exam_manual_final_review_receipt_ledger(
    *,
    python_exam_manual_final_review_handoff: dict[str, Any] | None = None,
    python_exam_manual_archive_decision_draft: dict[str, Any] | None = None,
    python_exam_manual_export_reviewer_packet: dict[str, Any] | None = None,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    handoff_view = safe_final_review_handoff(
        python_exam_manual_final_review_handoff
        if isinstance(python_exam_manual_final_review_handoff, dict)
        else {}
    )
    draft_view = safe_archive_decision_draft(
        python_exam_manual_archive_decision_draft
        if isinstance(python_exam_manual_archive_decision_draft, dict)
        else {}
    )
    reviewer_view = safe_reviewer_packet(
        python_exam_manual_export_reviewer_packet
        if isinstance(python_exam_manual_export_reviewer_packet, dict)
        else {}
    )
    queue_view = safe_export_review_queue(
        python_exam_manual_export_review_queue
        if isinstance(python_exam_manual_export_review_queue, dict)
        else {}
    )
    selected = str(
        selected_skill_tag
        or handoff_view.get("selected_skill_tag", "")
        or draft_view.get("selected_skill_tag", "")
        or reviewer_view.get("selected_skill_tag", "")
        or queue_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = final_review_receipt_ledger_body(
        selected_skill_tag=selected,
        handoff_view=handoff_view,
        draft_view=draft_view,
        reviewer_view=reviewer_view,
        queue_view=queue_view,
    )
    ledger_events = final_review_receipt_ledger_events(body, handoff_view, draft_view, reviewer_view, queue_view)
    summary = final_review_receipt_ledger_summary(body, ledger_events)
    receipt = final_review_receipt_ledger_receipt(summary, ledger_events)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_FINAL_REVIEW_RECEIPT_LEDGER_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_final_review_receipt_ledger",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_final_review_receipt_ledger_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Final Review Receipt Ledger. It consumes only Manual Final Review Handoff, "
            "Manual Archive Decision Draft, Manual Export Reviewer Packet, and Manual Export Review Queue "
            "metadata to make the final human review chain chronologically inspectable. It bundles handoff "
            "recommendation, archive-decision-draft recommendation, reviewer-packet recommendation, queue "
            "recommendation, gate decisions, handoff hash, draft hash, reviewer-packet hash, queue hash, "
            "export manifest hash, authorization gate hash, receipt hashes, candidate hashes, missing hashes, "
            "accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, "
            "ledger event hashes, and next safe human review action. It creates no export, writes nothing, "
            "starts no local action, archives nothing, submits nothing, authorizes nothing, and never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_final_review_receipt_ledger_endpoint": PYTHON_EXAM_MANUAL_FINAL_REVIEW_RECEIPT_LEDGER_ENDPOINT,
        "selected_skill_tag": selected,
        "final_review_receipt_ledger_summary": summary,
        "final_review_receipt_ledger_body": body,
        "final_review_receipt_ledger_events": ledger_events,
        "final_review_receipt_ledger_recommendation": summary["final_review_receipt_ledger_recommendation"],
        "manual_final_review_receipt_ledger_receipt": receipt,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Final Review Receipt Ledger bleibt not_cleared."
        ),
        "next_actions": [
            f"Final review receipt ledger recommendation: {summary['final_review_receipt_ledger_recommendation']}.",
            "Use this ledger only for chronological human review of the final hash-only review chain.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_final_review_handoff(handoff: dict[str, Any]) -> dict[str, Any]:
    summary = (
        handoff.get("final_review_handoff_summary", {})
        if isinstance(handoff.get("final_review_handoff_summary"), dict)
        else {}
    )
    body = (
        handoff.get("final_review_handoff_body", {})
        if isinstance(handoff.get("final_review_handoff_body"), dict)
        else {}
    )
    receipt = (
        handoff.get("manual_final_review_handoff_receipt", {})
        if isinstance(handoff.get("manual_final_review_handoff_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(handoff.get("status", "missing")),
        "selected_skill_tag": str(handoff.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "final_review_handoff_recommendation": str(
            handoff.get("final_review_handoff_recommendation")
            or summary.get("final_review_handoff_recommendation", "keep_final_handoff_open")
        ),
        "archive_decision_draft_recommendation": str(
            summary.get("archive_decision_draft_recommendation")
            or body.get("archive_decision_draft_recommendation", "")
        ),
        "reviewer_packet_recommendation": str(
            summary.get("reviewer_packet_recommendation") or body.get("reviewer_packet_recommendation", "")
        ),
        "queue_recommendation": str(summary.get("queue_recommendation") or body.get("queue_recommendation", "")),
        "gate_decisions": [str(item) for item in (summary.get("gate_decisions") or body.get("gate_decisions", []) or [])][:12],
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or body.get("candidate_hashes", []) or [])][:12],
        "final_review_handoff_hash": str(
            summary.get("final_review_handoff_hash") or body.get("final_review_handoff_hash", "")
        ),
        "archive_decision_draft_hash": str(
            summary.get("archive_decision_draft_hash") or body.get("archive_decision_draft_hash", "")
        ),
        "reviewer_packet_hash": str(summary.get("reviewer_packet_hash") or body.get("reviewer_packet_hash", "")),
        "queue_hash": str(summary.get("queue_hash") or body.get("queue_hash", "")),
        "export_manifest_hash": str(summary.get("export_manifest_hash") or body.get("export_manifest_hash", "")),
        "authorization_gate_hash": str(
            summary.get("authorization_gate_hash") or body.get("authorization_gate_hash", "")
        ),
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "final_review_handoff_receipt_hash": str(receipt.get("receipt_hash", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "next_safe_human_review_action": str(
            summary.get("next_safe_human_review_action") or body.get("next_safe_human_review_action", "")
        ),
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_review_receipt_ledger_body(
    *,
    selected_skill_tag: str,
    handoff_view: dict[str, Any],
    draft_view: dict[str, Any],
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(handoff_view.get("receipt_hashes", {}) or {})
    receipt_hashes["final_review_handoff_receipt_hash"] = handoff_view.get(
        "final_review_handoff_receipt_hash",
        "",
    )
    if draft_view.get("archive_decision_draft_receipt_hash"):
        receipt_hashes["archive_decision_draft_receipt_hash"] = draft_view.get(
            "archive_decision_draft_receipt_hash",
            "",
        )
    if reviewer_view.get("reviewer_packet_receipt_hash"):
        receipt_hashes["reviewer_packet_receipt_hash"] = reviewer_view.get("reviewer_packet_receipt_hash", "")
    if queue_view.get("queue_receipt_hash"):
        receipt_hashes["queue_receipt_hash"] = queue_view.get("queue_receipt_hash", "")
    missing_hashes = list(
        handoff_view.get("missing_required_hashes")
        or draft_view.get("missing_required_hashes")
        or reviewer_view.get("missing_required_hashes")
        or []
    )
    accepted_hashes = (
        handoff_view.get("accepted_post_cycle_hashes")
        or draft_view.get("accepted_post_cycle_hashes")
        or reviewer_view.get("accepted_post_cycle_hashes")
        or {}
    )
    candidate_hashes = (
        handoff_view.get("candidate_hashes")
        or draft_view.get("candidate_hashes")
        or reviewer_view.get("candidate_hashes")
        or queue_view.get("candidate_hashes")
        or []
    )
    gate_decisions = handoff_view.get("gate_decisions") or draft_view.get("gate_decisions") or reviewer_view.get("gate_decisions") or []
    seed = {
        "final_review_handoff_recommendation": handoff_view.get("final_review_handoff_recommendation", ""),
        "archive_decision_draft_recommendation": handoff_view.get("archive_decision_draft_recommendation")
        or draft_view.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": handoff_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": handoff_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "final_review_handoff_hash": handoff_view.get("final_review_handoff_hash", ""),
        "archive_decision_draft_hash": handoff_view.get("archive_decision_draft_hash")
        or draft_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": handoff_view.get("reviewer_packet_hash") or reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": handoff_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": handoff_view.get("export_manifest_hash") or draft_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": handoff_view.get("authorization_gate_hash") or draft_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "candidate_hashes": candidate_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "selected_skill_tag": selected_skill_tag,
        "timeline_event_hashes": handoff_view.get("timeline_event_hashes", []),
        "exam_deployment_status": "not_cleared",
    }
    ledger_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_final_review_receipt_ledger_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "final_review_handoff_recommendation": handoff_view.get(
            "final_review_handoff_recommendation",
            "keep_final_handoff_open",
        ),
        "archive_decision_draft_recommendation": handoff_view.get("archive_decision_draft_recommendation")
        or draft_view.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": handoff_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": handoff_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "gate_decisions": [str(item) for item in (gate_decisions or [])][:12],
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "final_review_handoff_hash": handoff_view.get("final_review_handoff_hash", ""),
        "archive_decision_draft_hash": handoff_view.get("archive_decision_draft_hash")
        or draft_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": handoff_view.get("reviewer_packet_hash") or reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": handoff_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": handoff_view.get("export_manifest_hash") or draft_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": handoff_view.get("authorization_gate_hash") or draft_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes[:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "help_level": safe_help_level(str(handoff_view.get("help_level") or draft_view.get("help_level") or "A2")),
        "source_card_ids": handoff_view.get("source_card_ids") or draft_view.get("source_card_ids") or reviewer_view.get("source_card_ids", []),
        "source_anchor_hash_count": int(
            handoff_view.get("source_anchor_hash_count", draft_view.get("source_anchor_hash_count", 0)) or 0
        ),
        "timeline_event_hashes": handoff_view.get("timeline_event_hashes") or draft_view.get("timeline_event_hashes", []),
        "timeline_event_count": int(
            handoff_view.get("timeline_event_count", draft_view.get("timeline_event_count", 0)) or 0
        ),
        "next_safe_human_review_action": next_ledger_action_from_handoff(
            handoff_view.get("final_review_handoff_recommendation", "keep_final_handoff_open")
        ),
        "final_review_receipt_ledger_hash": ledger_hash,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_review_receipt_ledger_events(
    body: dict[str, Any],
    handoff_view: dict[str, Any],
    draft_view: dict[str, Any],
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
) -> list[dict[str, Any]]:
    seeds = [
        {
            "event_id": "manual_export_review_queue",
            "status": queue_view.get("status", "missing"),
            "recommendation": body.get("queue_recommendation", ""),
            "queue_hash": body.get("queue_hash", ""),
        },
        {
            "event_id": "manual_export_reviewer_packet",
            "status": reviewer_view.get("status", "missing"),
            "recommendation": body.get("reviewer_packet_recommendation", ""),
            "reviewer_packet_hash": body.get("reviewer_packet_hash", ""),
        },
        {
            "event_id": "manual_archive_decision_draft",
            "status": draft_view.get("status", "missing"),
            "recommendation": body.get("archive_decision_draft_recommendation", ""),
            "archive_decision_draft_hash": body.get("archive_decision_draft_hash", ""),
        },
        {
            "event_id": "manual_final_review_handoff",
            "status": handoff_view.get("status", "missing"),
            "recommendation": body.get("final_review_handoff_recommendation", ""),
            "final_review_handoff_hash": body.get("final_review_handoff_hash", ""),
        },
        {
            "event_id": "manual_final_review_receipt_ledger",
            "status": body.get("status", ""),
            "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
            "final_review_receipt_ledger_hash": body.get("final_review_receipt_ledger_hash", ""),
        },
    ]
    events = []
    for seed in seeds:
        event_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
        event = dict(seed)
        event.update(
            {
                "ledger_event_hash": event_hash,
                "not_cleared_receipt": True,
                "export_created": False,
                "export_authorized": False,
                "archive_created": False,
                "submission_started": False,
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


def final_review_receipt_ledger_summary(
    body: dict[str, Any],
    ledger_events: list[dict[str, Any]],
) -> dict[str, Any]:
    handoff_recommendation = body.get("final_review_handoff_recommendation", "keep_final_handoff_open")
    if handoff_recommendation == "reject_final_handoff":
        recommendation = "reject_final_ledger"
        reason = "final_review_handoff_rejected"
    elif handoff_recommendation == "request_hash_completion":
        recommendation = "request_hash_completion"
        reason = "final_review_handoff_requests_hash_completion"
    elif handoff_recommendation == "ready_for_manual_final_review":
        recommendation = "ready_for_manual_final_ledger_review"
        reason = "final_review_handoff_ready_for_manual_final_ledger_review"
    else:
        recommendation = "keep_final_ledger_open"
        reason = "final_review_handoff_still_open"
    return {
        "status": "python_exam_manual_final_review_receipt_ledger_ready",
        "final_review_receipt_ledger_recommendation": recommendation,
        "final_review_receipt_ledger_reason": reason,
        "allowed_final_review_receipt_ledger_recommendations": sorted(
            FINAL_REVIEW_RECEIPT_LEDGER_RECOMMENDATIONS
        ),
        "final_review_handoff_recommendation": handoff_recommendation,
        "archive_decision_draft_recommendation": body.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": body.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": body.get("queue_recommendation", ""),
        "gate_decisions": body.get("gate_decisions", []),
        "candidate_hashes": body.get("candidate_hashes", []),
        "final_review_handoff_hash": body.get("final_review_handoff_hash", ""),
        "archive_decision_draft_hash": body.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": body.get("reviewer_packet_hash", ""),
        "queue_hash": body.get("queue_hash", ""),
        "export_manifest_hash": body.get("export_manifest_hash", ""),
        "authorization_gate_hash": body.get("authorization_gate_hash", ""),
        "receipt_hashes": body.get("receipt_hashes", {}),
        "missing_required_hashes": body.get("missing_required_hashes", []),
        "accepted_post_cycle_hashes": body.get("accepted_post_cycle_hashes", {}),
        "selected_skill_tag": body.get("selected_skill_tag", "general_python"),
        "help_level": safe_help_level(str(body.get("help_level", "A2"))),
        "source_card_ids": body.get("source_card_ids", []),
        "source_anchor_hash_count": int(body.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": body.get("timeline_event_hashes", []),
        "timeline_event_count": int(body.get("timeline_event_count", 0) or 0),
        "ledger_event_hashes": [str(event.get("ledger_event_hash", "")) for event in ledger_events],
        "ledger_event_count": len(ledger_events),
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "final_review_receipt_ledger_hash": body.get("final_review_receipt_ledger_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_ledger_action_from_handoff(handoff_recommendation: str) -> str:
    if handoff_recommendation == "ready_for_manual_final_review":
        return "present_hash_only_final_receipt_ledger_to_human_reviewer"
    if handoff_recommendation == "request_hash_completion":
        return "complete_missing_hashes_before_final_ledger_review"
    if handoff_recommendation == "reject_final_handoff":
        return "return_to_final_review_handoff_or_archive_decision_draft"
    return "keep_final_receipt_ledger_open_and_continue_manual_review"


def final_review_receipt_ledger_receipt(
    summary: dict[str, Any],
    ledger_events: list[dict[str, Any]],
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "ledger_event_hashes": [event.get("ledger_event_hash", "") for event in ledger_events],
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_final_review_receipt_ledger_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "final_review_receipt_ledger_recommendation": summary.get(
            "final_review_receipt_ledger_recommendation",
            "keep_final_ledger_open",
        ),
        "final_review_receipt_ledger_hash": summary.get("final_review_receipt_ledger_hash", ""),
        "not_cleared_receipt": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-final-review-receipt-ledger")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
