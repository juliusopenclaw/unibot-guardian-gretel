from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_review_packet import safe_review_timeline
from .python_exam_manual_review_export_authorization_gate import safe_export_preview
from .python_exam_manual_review_export_preview import safe_review_packet


PYTHON_EXAM_MANUAL_EXPORT_REVIEW_QUEUE_SCHEMA_VERSION = "unibot-python-exam-manual-export-review-queue-v1"
PYTHON_EXAM_MANUAL_EXPORT_REVIEW_QUEUE_ENDPOINT = "/api/unibot/course/python-exam-manual-export-review-queue"

EXPORT_REVIEW_QUEUE_RECOMMENDATIONS = {
    "keep_queue_open",
    "request_hash_completion",
    "ready_for_manual_export_review_queue",
    "reject_queue_entry",
}


def build_python_exam_manual_export_review_queue(
    *,
    python_exam_manual_review_export_authorization_gate: dict[str, Any] | None = None,
    python_exam_manual_review_export_preview: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_packet: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_timeline: dict[str, Any] | None = None,
    queue_candidates: list[dict[str, Any]] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
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
        or gate_view.get("selected_skill_tag", "")
        or preview_view.get("selected_skill_tag", "")
        or packet_view.get("selected_skill_tag", "")
        or timeline_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    primary_candidate = export_review_queue_candidate(
        candidate_id="primary-export-review-candidate",
        selected_skill_tag=selected,
        gate_view=gate_view,
        preview_view=preview_view,
        packet_view=packet_view,
        timeline_view=timeline_view,
    )
    candidates = [primary_candidate]
    for index, candidate in enumerate(queue_candidates or [], start=2):
        if isinstance(candidate, dict):
            candidates.append(safe_queue_candidate(candidate, fallback_index=index))
    summary = export_review_queue_summary(candidates)
    receipt = export_review_queue_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_EXPORT_REVIEW_QUEUE_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_export_review_queue",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_export_review_queue_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Export Review Queue. It consumes only Export Authorization Gate, Export "
            "Preview, Review Packet, Review Timeline, and optional hash-only queue candidate metadata. It "
            "groups human-review candidates by gate decision, export manifest hash, authorization gate hash, "
            "preview/packet/timeline receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, "
            "help level, Source-Card anchors, timeline event hashes, and next safe review action. It creates "
            "no export, writes nothing, starts no local action, authorizes nothing, and never returns raw "
            "queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_export_review_queue_endpoint": PYTHON_EXAM_MANUAL_EXPORT_REVIEW_QUEUE_ENDPOINT,
        "selected_skill_tag": selected,
        "queue_summary": summary,
        "queue_recommendation": summary["queue_recommendation"],
        "queue_candidates": candidates,
        "manual_export_review_queue_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Export Review Queue bleibt not_cleared."
        ),
        "next_actions": [
            f"Queue recommendation: {summary['queue_recommendation']}.",
            "Use this queue only to prepare human review of hash-only export candidates.",
            "Keep export creation, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_authorization_gate(gate: dict[str, Any]) -> dict[str, Any]:
    summary = (
        gate.get("authorization_gate_summary", {})
        if isinstance(gate.get("authorization_gate_summary"), dict)
        else {}
    )
    receipt = (
        gate.get("manual_review_export_authorization_gate_receipt", {})
        if isinstance(gate.get("manual_review_export_authorization_gate_receipt"), dict)
        else {}
    )
    accepted_hashes = summary.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    receipt_hashes = summary.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    return {
        "status": str(gate.get("status", "missing")),
        "selected_skill_tag": str(gate.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "authorization_gate_decision": str(
            gate.get("authorization_gate_decision")
            or summary.get("authorization_gate_decision", "keep_export_blocked")
        ),
        "authorization_gate_reason": str(summary.get("authorization_gate_reason", "")),
        "authorization_gate_hash": str(summary.get("authorization_gate_hash", "")),
        "export_preview_recommendation": str(summary.get("export_preview_recommendation", "")),
        "export_manifest_hash": str(summary.get("export_manifest_hash", "")),
        "packet_recommendation": str(summary.get("packet_recommendation", "")),
        "timeline_recommendation": str(summary.get("timeline_recommendation", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", 0) or 0),
        "next_safe_review_action": str(summary.get("next_safe_review_action", "")),
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "gate_receipt_hash": str(receipt.get("receipt_hash", "")),
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def export_review_queue_candidate(
    *,
    candidate_id: str,
    selected_skill_tag: str,
    gate_view: dict[str, Any],
    preview_view: dict[str, Any],
    packet_view: dict[str, Any],
    timeline_view: dict[str, Any],
) -> dict[str, Any]:
    gate_decision = gate_view.get("authorization_gate_decision", "keep_export_blocked")
    missing_hashes = list(gate_view.get("missing_required_hashes", []) or [])
    if not missing_hashes:
        missing_hashes = list(preview_view.get("missing_required_hashes", []) or packet_view.get("missing_required_hashes", []) or [])
    receipt_hashes = dict(gate_view.get("receipt_hashes", {}) or {})
    receipt_hashes["authorization_gate_receipt_hash"] = gate_view.get("gate_receipt_hash", "")
    timeline_event_hashes = gate_view.get("timeline_event_hashes") or preview_view.get("timeline_event_hashes") or packet_view.get("timeline_event_hashes", [])
    source_card_ids = packet_view.get("source_card_ids", []) or []
    seed = {
        "candidate_id": candidate_id,
        "gate_decision": gate_decision,
        "export_manifest_hash": gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": gate_view.get("accepted_post_cycle_hashes", {}),
        "skill_tag": selected_skill_tag,
        "timeline_event_hashes": timeline_event_hashes,
        "exam_deployment_status": "not_cleared",
    }
    candidate_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "queue_entry_recommendation": queue_entry_recommendation(gate_decision, missing_hashes),
        "authorization_gate_decision": gate_decision,
        "export_preview_recommendation": gate_view.get("export_preview_recommendation") or preview_view.get("export_preview_recommendation", ""),
        "export_manifest_hash": gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": gate_view.get("authorization_gate_hash", ""),
        "preview_receipt_hash": receipt_hashes.get("preview_receipt_hash", ""),
        "packet_receipt_hash": receipt_hashes.get("packet_receipt_hash", ""),
        "timeline_receipt_hash": receipt_hashes.get("timeline_receipt_hash", ""),
        "authorization_gate_receipt_hash": receipt_hashes.get("authorization_gate_receipt_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes[:12],
        "accepted_post_cycle_hashes": gate_view.get("accepted_post_cycle_hashes", {}),
        "selected_skill_tag": selected_skill_tag,
        "help_level": safe_help_level(str(gate_view.get("help_level") or preview_view.get("help_level") or packet_view.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in source_card_ids][:8],
        "source_anchor_hash_count": int(packet_view.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(gate_view.get("timeline_event_count", timeline_view.get("timeline_event_count", 0)) or 0),
        "next_safe_review_action": gate_view.get("next_safe_review_action") or preview_view.get("next_safe_review_action", ""),
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def safe_queue_candidate(candidate: dict[str, Any], *, fallback_index: int) -> dict[str, Any]:
    gate_decision = str(candidate.get("authorization_gate_decision", "keep_export_blocked"))
    missing_hashes = [str(item) for item in (candidate.get("missing_required_hashes") or [])][:12]
    receipt_hashes = candidate.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = candidate.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    timeline_hashes = [str(item) for item in (candidate.get("timeline_event_hashes") or [])][:12]
    seed = {
        "candidate_id": str(candidate.get("candidate_id") or f"queue-candidate-{fallback_index}"),
        "gate_decision": gate_decision,
        "export_manifest_hash": str(candidate.get("export_manifest_hash", "")),
        "authorization_gate_hash": str(candidate.get("authorization_gate_hash", "")),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "timeline_event_hashes": timeline_hashes,
        "exam_deployment_status": "not_cleared",
    }
    candidate_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "candidate_id": seed["candidate_id"],
        "candidate_hash": candidate_hash,
        "queue_entry_recommendation": queue_entry_recommendation(gate_decision, missing_hashes),
        "authorization_gate_decision": gate_decision,
        "export_preview_recommendation": str(candidate.get("export_preview_recommendation", "")),
        "export_manifest_hash": str(candidate.get("export_manifest_hash", "")),
        "authorization_gate_hash": str(candidate.get("authorization_gate_hash", "")),
        "preview_receipt_hash": str(candidate.get("preview_receipt_hash") or receipt_hashes.get("preview_receipt_hash", "")),
        "packet_receipt_hash": str(candidate.get("packet_receipt_hash") or receipt_hashes.get("packet_receipt_hash", "")),
        "timeline_receipt_hash": str(candidate.get("timeline_receipt_hash") or receipt_hashes.get("timeline_receipt_hash", "")),
        "authorization_gate_receipt_hash": str(
            candidate.get("authorization_gate_receipt_hash") or receipt_hashes.get("authorization_gate_receipt_hash", "")
        ),
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "selected_skill_tag": str(candidate.get("selected_skill_tag", "general_python")),
        "help_level": safe_help_level(str(candidate.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (candidate.get("source_card_ids") or [])][:8],
        "source_anchor_hash_count": int(candidate.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": timeline_hashes,
        "timeline_event_count": int(candidate.get("timeline_event_count", len(timeline_hashes)) or 0),
        "next_safe_review_action": str(candidate.get("next_safe_review_action", "")),
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def queue_entry_recommendation(gate_decision: str, missing_hashes: list[str]) -> str:
    if gate_decision == "reject_export_authorization":
        return "reject_queue_entry"
    if gate_decision == "request_hash_completion":
        return "request_hash_completion"
    if gate_decision == "ready_for_manual_export_authorization_review":
        if missing_hashes:
            return "request_hash_completion"
        return "ready_for_manual_export_review_queue"
    return "keep_queue_open"


def export_review_queue_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    recommendations = [str(item.get("queue_entry_recommendation", "keep_queue_open")) for item in candidates]
    if "reject_queue_entry" in recommendations:
        queue_recommendation = "reject_queue_entry"
        reason = "at_least_one_queue_entry_rejected"
    elif "request_hash_completion" in recommendations:
        queue_recommendation = "request_hash_completion"
        reason = "at_least_one_queue_entry_needs_hash_completion"
    elif recommendations and all(item == "ready_for_manual_export_review_queue" for item in recommendations):
        queue_recommendation = "ready_for_manual_export_review_queue"
        reason = "all_queue_entries_ready_for_manual_export_review"
    else:
        queue_recommendation = "keep_queue_open"
        reason = "queue_entries_still_blocked_or_open"
    seed = {
        "queue_recommendation": queue_recommendation,
        "candidate_hashes": [item.get("candidate_hash", "") for item in candidates],
        "candidate_count": len(candidates),
        "exam_deployment_status": "not_cleared",
    }
    queue_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_export_review_queue_ready",
        "queue_recommendation": queue_recommendation,
        "queue_reason": reason,
        "allowed_queue_recommendations": sorted(EXPORT_REVIEW_QUEUE_RECOMMENDATIONS),
        "queue_hash": queue_hash,
        "candidate_count": len(candidates),
        "ready_candidate_count": sum(1 for item in recommendations if item == "ready_for_manual_export_review_queue"),
        "blocked_candidate_count": sum(1 for item in recommendations if item == "keep_queue_open"),
        "missing_hash_candidate_count": sum(1 for item in recommendations if item == "request_hash_completion"),
        "rejected_candidate_count": sum(1 for item in recommendations if item == "reject_queue_entry"),
        "candidate_hashes": [item.get("candidate_hash", "") for item in candidates],
        "next_safe_review_action": next_queue_action(queue_recommendation),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_queue_action(recommendation: str) -> str:
    if recommendation == "ready_for_manual_export_review_queue":
        return "present_hash_only_queue_to_human_export_reviewer"
    if recommendation == "request_hash_completion":
        return "complete_missing_hashes_before_queue_review"
    if recommendation == "reject_queue_entry":
        return "remove_or_rework_rejected_queue_entry"
    return "keep_queue_open_and_continue_manual_review"


def export_review_queue_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_export_review_queue_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "queue_recommendation": summary.get("queue_recommendation", "keep_queue_open"),
        "queue_hash": summary.get("queue_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-export-review-queue")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
