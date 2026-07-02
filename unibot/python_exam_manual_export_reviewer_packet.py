from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_review_packet import safe_review_timeline
from .python_exam_manual_export_review_queue import safe_authorization_gate
from .python_exam_manual_review_export_authorization_gate import safe_export_preview
from .python_exam_manual_review_export_preview import safe_review_packet


PYTHON_EXAM_MANUAL_EXPORT_REVIEWER_PACKET_SCHEMA_VERSION = "unibot-python-exam-manual-export-reviewer-packet-v1"
PYTHON_EXAM_MANUAL_EXPORT_REVIEWER_PACKET_ENDPOINT = "/api/unibot/course/python-exam-manual-export-reviewer-packet"

EXPORT_REVIEWER_PACKET_RECOMMENDATIONS = {
    "keep_reviewer_packet_open",
    "request_hash_completion",
    "ready_for_human_reviewer_packet",
    "reject_reviewer_packet",
}


def build_python_exam_manual_export_reviewer_packet(
    *,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    python_exam_manual_review_export_authorization_gate: dict[str, Any] | None = None,
    python_exam_manual_review_export_preview: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_packet: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_timeline: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    queue_view = safe_export_review_queue(
        python_exam_manual_export_review_queue
        if isinstance(python_exam_manual_export_review_queue, dict)
        else {}
    )
    gate_view = safe_authorization_gate(
        python_exam_manual_review_export_authorization_gate
        if isinstance(python_exam_manual_review_export_authorization_gate, dict)
        else {}
    )
    preview_view = safe_export_preview(
        python_exam_manual_review_export_preview
        if isinstance(python_exam_manual_review_export_preview, dict)
        else {}
    )
    packet_view = safe_review_packet(
        python_exam_manual_cycle_review_packet
        if isinstance(python_exam_manual_cycle_review_packet, dict)
        else {}
    )
    timeline_view = safe_review_timeline(
        python_exam_manual_cycle_review_timeline
        if isinstance(python_exam_manual_cycle_review_timeline, dict)
        else {}
    )
    selected = str(
        selected_skill_tag
        or queue_view.get("selected_skill_tag", "")
        or gate_view.get("selected_skill_tag", "")
        or preview_view.get("selected_skill_tag", "")
        or packet_view.get("selected_skill_tag", "")
        or timeline_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    packet_body = reviewer_packet_body(
        selected_skill_tag=selected,
        queue_view=queue_view,
        gate_view=gate_view,
        preview_view=preview_view,
        packet_view=packet_view,
        timeline_view=timeline_view,
    )
    packet_summary = reviewer_packet_summary(packet_body)
    receipt = reviewer_packet_receipt(packet_summary)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_EXPORT_REVIEWER_PACKET_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_export_reviewer_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_export_reviewer_packet_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Export Reviewer Packet. It consumes only Manual Export Review Queue, Export "
            "Authorization Gate, Export Preview, Review Packet, and Review Timeline metadata to prepare a "
            "hash-only packet for human review before any later archival or submission decision. It bundles "
            "queue recommendation, candidate hashes, gate decisions, export manifest hash, authorization gate "
            "hash, preview/packet/timeline receipt hashes, missing hashes, accepted post-cycle hashes, skill "
            "tag, help level, Source-Card anchors, timeline event hashes, queue hash, and next safe review "
            "action. It creates no export, writes nothing, starts no local action, authorizes nothing, and "
            "never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "manual_export_reviewer_packet_endpoint": PYTHON_EXAM_MANUAL_EXPORT_REVIEWER_PACKET_ENDPOINT,
        "selected_skill_tag": selected,
        "reviewer_packet_summary": packet_summary,
        "reviewer_packet_body": packet_body,
        "reviewer_packet_recommendation": packet_summary["reviewer_packet_recommendation"],
        "manual_export_reviewer_packet_receipt": receipt,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Reviewer Packet bleibt not_cleared."
        ),
        "next_actions": [
            f"Reviewer packet recommendation: {packet_summary['reviewer_packet_recommendation']}.",
            "Use this packet only for human review before any later archival or submission decision.",
            "Keep export creation, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_export_review_queue(queue: dict[str, Any]) -> dict[str, Any]:
    summary = queue.get("queue_summary", {}) if isinstance(queue.get("queue_summary"), dict) else {}
    receipt = (
        queue.get("manual_export_review_queue_receipt", {})
        if isinstance(queue.get("manual_export_review_queue_receipt"), dict)
        else {}
    )
    candidates = queue.get("queue_candidates", []) if isinstance(queue.get("queue_candidates"), list) else []
    safe_candidates = [safe_queue_candidate(item) for item in candidates if isinstance(item, dict)][:12]
    return {
        "status": str(queue.get("status", "missing")),
        "selected_skill_tag": str(queue.get("selected_skill_tag", "")),
        "queue_recommendation": str(queue.get("queue_recommendation") or summary.get("queue_recommendation", "keep_queue_open")),
        "queue_reason": str(summary.get("queue_reason", "")),
        "queue_hash": str(summary.get("queue_hash", "")),
        "candidate_count": int(summary.get("candidate_count", len(safe_candidates)) or 0),
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or [])][:12],
        "next_safe_review_action": str(summary.get("next_safe_review_action", "")),
        "queue_receipt_hash": str(receipt.get("receipt_hash", "")),
        "candidates": safe_candidates,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def safe_queue_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    receipt_hashes = candidate.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = candidate.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "candidate_hash": str(candidate.get("candidate_hash", "")),
        "queue_entry_recommendation": str(candidate.get("queue_entry_recommendation", "keep_queue_open")),
        "authorization_gate_decision": str(candidate.get("authorization_gate_decision", "keep_export_blocked")),
        "export_preview_recommendation": str(candidate.get("export_preview_recommendation", "")),
        "export_manifest_hash": str(candidate.get("export_manifest_hash", "")),
        "authorization_gate_hash": str(candidate.get("authorization_gate_hash", "")),
        "preview_receipt_hash": str(candidate.get("preview_receipt_hash", "")),
        "packet_receipt_hash": str(candidate.get("packet_receipt_hash", "")),
        "timeline_receipt_hash": str(candidate.get("timeline_receipt_hash", "")),
        "authorization_gate_receipt_hash": str(candidate.get("authorization_gate_receipt_hash", "")),
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "missing_required_hashes": [str(item) for item in (candidate.get("missing_required_hashes") or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "selected_skill_tag": str(candidate.get("selected_skill_tag", "")),
        "help_level": safe_help_level(str(candidate.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (candidate.get("source_card_ids") or [])][:8],
        "source_anchor_hash_count": int(candidate.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": [str(item) for item in (candidate.get("timeline_event_hashes") or [])][:12],
        "timeline_event_count": int(candidate.get("timeline_event_count", 0) or 0),
        "next_safe_review_action": str(candidate.get("next_safe_review_action", "")),
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def reviewer_packet_body(
    *,
    selected_skill_tag: str,
    queue_view: dict[str, Any],
    gate_view: dict[str, Any],
    preview_view: dict[str, Any],
    packet_view: dict[str, Any],
    timeline_view: dict[str, Any],
) -> dict[str, Any]:
    candidates = queue_view.get("candidates", []) or []
    first_candidate = candidates[0] if candidates else {}
    candidate_hashes = queue_view.get("candidate_hashes") or [item.get("candidate_hash", "") for item in candidates]
    missing_hashes = sorted(
        {
            str(item)
            for candidate in candidates
            for item in (candidate.get("missing_required_hashes", []) or [])
            if str(item)
        }
    )[:12]
    if not missing_hashes:
        missing_hashes = list(gate_view.get("missing_required_hashes") or preview_view.get("missing_required_hashes") or packet_view.get("missing_required_hashes") or [])[:12]
    accepted_hashes = first_candidate.get("accepted_post_cycle_hashes") or gate_view.get("accepted_post_cycle_hashes", {})
    receipt_hashes = dict(first_candidate.get("receipt_hashes", {}) or {})
    receipt_hashes["queue_receipt_hash"] = queue_view.get("queue_receipt_hash", "")
    receipt_hashes["authorization_gate_receipt_hash"] = first_candidate.get("authorization_gate_receipt_hash") or receipt_hashes.get("authorization_gate_receipt_hash", "")
    timeline_event_hashes = first_candidate.get("timeline_event_hashes") or gate_view.get("timeline_event_hashes") or preview_view.get("timeline_event_hashes") or packet_view.get("timeline_event_hashes", [])
    source_card_ids = first_candidate.get("source_card_ids") or packet_view.get("source_card_ids", [])
    packet_seed = {
        "queue_recommendation": queue_view.get("queue_recommendation", ""),
        "candidate_hashes": candidate_hashes,
        "gate_decisions": [candidate.get("authorization_gate_decision", "") for candidate in candidates],
        "export_manifest_hash": first_candidate.get("export_manifest_hash") or gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": first_candidate.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "selected_skill_tag": selected_skill_tag,
        "timeline_event_hashes": timeline_event_hashes,
        "queue_hash": queue_view.get("queue_hash", ""),
        "exam_deployment_status": "not_cleared",
    }
    reviewer_packet_hash = sha256_text(json.dumps(packet_seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_export_reviewer_packet_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "queue_recommendation": queue_view.get("queue_recommendation", "keep_queue_open"),
        "queue_hash": queue_view.get("queue_hash", ""),
        "candidate_count": queue_view.get("candidate_count", len(candidates)),
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "gate_decisions": [str(candidate.get("authorization_gate_decision", "")) for candidate in candidates][:12],
        "queue_entry_recommendations": [str(candidate.get("queue_entry_recommendation", "")) for candidate in candidates][:12],
        "export_manifest_hash": first_candidate.get("export_manifest_hash") or gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": first_candidate.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "preview_receipt_hash": first_candidate.get("preview_receipt_hash") or receipt_hashes.get("preview_receipt_hash", ""),
        "packet_receipt_hash": first_candidate.get("packet_receipt_hash") or receipt_hashes.get("packet_receipt_hash", ""),
        "timeline_receipt_hash": first_candidate.get("timeline_receipt_hash") or receipt_hashes.get("timeline_receipt_hash", ""),
        "authorization_gate_receipt_hash": first_candidate.get("authorization_gate_receipt_hash") or receipt_hashes.get("authorization_gate_receipt_hash", ""),
        "queue_receipt_hash": queue_view.get("queue_receipt_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "help_level": safe_help_level(str(first_candidate.get("help_level") or gate_view.get("help_level") or preview_view.get("help_level") or packet_view.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(first_candidate.get("source_anchor_hash_count", packet_view.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(first_candidate.get("timeline_event_count", timeline_view.get("timeline_event_count", 0)) or 0),
        "next_safe_review_action": queue_view.get("next_safe_review_action") or first_candidate.get("next_safe_review_action", ""),
        "reviewer_packet_hash": reviewer_packet_hash,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def reviewer_packet_summary(body: dict[str, Any]) -> dict[str, Any]:
    queue_recommendation = body.get("queue_recommendation", "keep_queue_open")
    if queue_recommendation == "reject_queue_entry":
        recommendation = "reject_reviewer_packet"
        reason = "queue_contains_rejected_entry"
    elif queue_recommendation == "request_hash_completion":
        recommendation = "request_hash_completion"
        reason = "queue_requests_hash_completion"
    elif queue_recommendation == "ready_for_manual_export_review_queue":
        recommendation = "ready_for_human_reviewer_packet"
        reason = "queue_ready_for_human_reviewer_packet"
    else:
        recommendation = "keep_reviewer_packet_open"
        reason = "queue_still_open_or_blocked"
    return {
        "status": "python_exam_manual_export_reviewer_packet_ready",
        "reviewer_packet_recommendation": recommendation,
        "reviewer_packet_reason": reason,
        "allowed_reviewer_packet_recommendations": sorted(EXPORT_REVIEWER_PACKET_RECOMMENDATIONS),
        "queue_recommendation": queue_recommendation,
        "queue_hash": body.get("queue_hash", ""),
        "candidate_count": body.get("candidate_count", 0),
        "candidate_hashes": body.get("candidate_hashes", []),
        "gate_decisions": body.get("gate_decisions", []),
        "export_manifest_hash": body.get("export_manifest_hash", ""),
        "authorization_gate_hash": body.get("authorization_gate_hash", ""),
        "preview_receipt_hash": body.get("preview_receipt_hash", ""),
        "packet_receipt_hash": body.get("packet_receipt_hash", ""),
        "timeline_receipt_hash": body.get("timeline_receipt_hash", ""),
        "authorization_gate_receipt_hash": body.get("authorization_gate_receipt_hash", ""),
        "queue_receipt_hash": body.get("queue_receipt_hash", ""),
        "missing_required_hashes": body.get("missing_required_hashes", []),
        "accepted_post_cycle_hashes": body.get("accepted_post_cycle_hashes", {}),
        "selected_skill_tag": body.get("selected_skill_tag", "general_python"),
        "help_level": safe_help_level(str(body.get("help_level", "A2"))),
        "source_card_ids": body.get("source_card_ids", []),
        "source_anchor_hash_count": int(body.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": body.get("timeline_event_hashes", []),
        "timeline_event_count": int(body.get("timeline_event_count", 0) or 0),
        "next_safe_review_action": body.get("next_safe_review_action", ""),
        "reviewer_packet_hash": body.get("reviewer_packet_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def reviewer_packet_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_export_reviewer_packet_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "reviewer_packet_recommendation": summary.get("reviewer_packet_recommendation", "keep_reviewer_packet_open"),
        "reviewer_packet_hash": summary.get("reviewer_packet_hash", ""),
        "not_cleared_receipt": True,
        "export_created": False,
        "export_authorized": False,
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-export-reviewer-packet")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
