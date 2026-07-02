from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_review_packet import safe_review_timeline
from .python_exam_manual_cycle_review_timeline import safe_closure_ledger
from .python_exam_manual_review_export_preview import safe_review_packet


PYTHON_EXAM_MANUAL_REVIEW_EXPORT_AUTHORIZATION_GATE_SCHEMA_VERSION = (
    "unibot-python-exam-manual-review-export-authorization-gate-v1"
)
PYTHON_EXAM_MANUAL_REVIEW_EXPORT_AUTHORIZATION_GATE_ENDPOINT = (
    "/api/unibot/course/python-exam-manual-review-export-authorization-gate"
)

EXPORT_AUTHORIZATION_GATE_DECISIONS = {
    "keep_export_blocked",
    "request_hash_completion",
    "ready_for_manual_export_authorization_review",
    "reject_export_authorization",
}


def build_python_exam_manual_review_export_authorization_gate(
    *,
    python_exam_manual_review_export_preview: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_packet: dict[str, Any] | None = None,
    python_exam_manual_cycle_review_timeline: dict[str, Any] | None = None,
    python_exam_manual_cycle_closure_ledger: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    export_preview = (
        python_exam_manual_review_export_preview
        if isinstance(python_exam_manual_review_export_preview, dict)
        else {}
    )
    review_packet = (
        python_exam_manual_cycle_review_packet
        if isinstance(python_exam_manual_cycle_review_packet, dict)
        else {}
    )
    review_timeline = (
        python_exam_manual_cycle_review_timeline
        if isinstance(python_exam_manual_cycle_review_timeline, dict)
        else {}
    )
    closure_ledger = (
        python_exam_manual_cycle_closure_ledger
        if isinstance(python_exam_manual_cycle_closure_ledger, dict)
        else {}
    )
    preview_view = safe_export_preview(export_preview)
    packet_view = safe_review_packet(review_packet)
    timeline_view = safe_review_timeline(review_timeline)
    closure_view = safe_closure_ledger(closure_ledger)
    selected = str(
        selected_skill_tag
        or preview_view.get("selected_skill_tag", "")
        or packet_view.get("selected_skill_tag", "")
        or timeline_view.get("selected_skill_tag", "")
        or closure_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    gate_summary = export_authorization_gate_summary(
        selected_skill_tag=selected,
        preview_view=preview_view,
        packet_view=packet_view,
        timeline_view=timeline_view,
        closure_view=closure_view,
    )
    gate_receipt = export_authorization_gate_receipt(gate_summary)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_REVIEW_EXPORT_AUTHORIZATION_GATE_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_review_export_authorization_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_review_export_authorization_gate_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Review Export Authorization Gate. It consumes only Manual Review Export "
            "Preview, Review Packet, Review Timeline, and Closure Ledger metadata to decide whether a human "
            "could review export authorization as the next step. It creates no export, writes nothing, starts "
            "no local action, and exposes only gate decision state, export-preview recommendation, export "
            "manifest hash, packet/timeline/closure decisions, missing hashes, accepted post-cycle hashes, "
            "receipt hashes, timeline event hashes, and the next safe review action. It never returns raw "
            "queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_review_export_authorization_gate_endpoint": (
            PYTHON_EXAM_MANUAL_REVIEW_EXPORT_AUTHORIZATION_GATE_ENDPOINT
        ),
        "selected_skill_tag": selected,
        "authorization_gate_summary": gate_summary,
        "authorization_gate_decision": gate_summary["authorization_gate_decision"],
        "manual_review_export_authorization_gate_receipt": gate_receipt,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_export": True,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Authorization Gate bleibt not_cleared."
        ),
        "next_actions": [
            f"Authorization gate decision: {gate_summary['authorization_gate_decision']}.",
            "Use this gate only to prepare human export-authorization review.",
            "Keep export creation, local writes, raw notebook work, scoring, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_export_preview(preview: dict[str, Any]) -> dict[str, Any]:
    summary = (
        preview.get("export_preview_summary", {})
        if isinstance(preview.get("export_preview_summary"), dict)
        else {}
    )
    manifest = (
        preview.get("export_manifest_preview", {})
        if isinstance(preview.get("export_manifest_preview"), dict)
        else {}
    )
    receipt = (
        preview.get("manual_review_export_preview_receipt", {})
        if isinstance(preview.get("manual_review_export_preview_receipt"), dict)
        else {}
    )
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or manifest.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    receipt_hashes = summary.get("receipt_hashes") or manifest.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    return {
        "status": str(preview.get("status", "missing")),
        "selected_skill_tag": str(preview.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "export_preview_recommendation": str(
            preview.get("export_preview_recommendation")
            or summary.get("export_preview_recommendation", "keep_export_preview_open")
        ),
        "export_preview_reason": str(summary.get("export_preview_reason", "")),
        "export_manifest_hash": str(summary.get("export_manifest_hash") or manifest.get("export_manifest_hash", "")),
        "packet_recommendation": str(summary.get("packet_recommendation") or manifest.get("packet_recommendation", "")),
        "timeline_recommendation": str(
            summary.get("timeline_recommendation") or manifest.get("timeline_recommendation", "")
        ),
        "closure_decision": str(summary.get("closure_decision") or manifest.get("closure_decision", "")),
        "missing_required_hashes": [
            str(item) for item in (summary.get("missing_required_hashes") or manifest.get("missing_required_hashes", []) or [])
        ][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "timeline_event_hashes": [
            str(item) for item in (summary.get("timeline_event_hashes") or manifest.get("timeline_event_hashes", []) or [])
        ][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", manifest.get("timeline_event_count", 0)) or 0),
        "preview_receipt_hash": str(receipt.get("receipt_hash", "")),
        "next_safe_review_action": str(
            summary.get("next_safe_review_action") or manifest.get("next_safe_review_action", "")
        ),
        "help_level": safe_help_level(str(summary.get("help_level") or manifest.get("help_level", "A2"))),
        "export_created": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def export_authorization_gate_summary(
    *,
    selected_skill_tag: str,
    preview_view: dict[str, Any],
    packet_view: dict[str, Any],
    timeline_view: dict[str, Any],
    closure_view: dict[str, Any],
) -> dict[str, Any]:
    preview_recommendation = preview_view.get("export_preview_recommendation", "keep_export_preview_open")
    missing_hashes = list(preview_view.get("missing_required_hashes", []) or [])
    if not missing_hashes:
        missing_hashes = list(packet_view.get("missing_required_hashes", []) or [])
    packet_recommendation = preview_view.get("packet_recommendation") or packet_view.get("packet_recommendation", "")
    timeline_recommendation = (
        preview_view.get("timeline_recommendation")
        or packet_view.get("timeline_recommendation")
        or timeline_view.get("timeline_review_recommendation", "")
    )
    closure_decision = (
        preview_view.get("closure_decision")
        or packet_view.get("closure_decision")
        or closure_view.get("closure_ledger_decision", "")
    )
    if preview_view.get("status") != "python_exam_manual_review_export_preview_ready":
        decision = "keep_export_blocked"
        reason = "export_preview_missing_or_not_ready"
    elif preview_recommendation == "reject_export_preview":
        decision = "reject_export_authorization"
        reason = "export_preview_rejected"
    elif preview_recommendation == "keep_export_preview_open":
        decision = "keep_export_blocked"
        reason = "export_preview_still_open"
    elif preview_recommendation == "request_hash_completion" or missing_hashes:
        decision = "request_hash_completion"
        reason = "export_preview_or_packet_requires_hash_completion"
    elif preview_recommendation == "ready_for_human_export_review":
        decision = "ready_for_manual_export_authorization_review"
        reason = "export_preview_ready_for_manual_authorization_review"
    else:
        decision = "keep_export_blocked"
        reason = "export_preview_not_ready_for_authorization"
    accepted_hashes = preview_view.get("accepted_post_cycle_hashes") or packet_view.get("accepted_post_cycle_hashes", {})
    receipt_hashes = dict(preview_view.get("receipt_hashes", {}) or {})
    receipt_hashes["preview_receipt_hash"] = preview_view.get("preview_receipt_hash", "")
    timeline_event_hashes = preview_view.get("timeline_event_hashes") or packet_view.get("timeline_event_hashes", [])
    summary_seed = {
        "decision": decision,
        "export_preview_recommendation": preview_recommendation,
        "export_manifest_hash": preview_view.get("export_manifest_hash", ""),
        "packet_recommendation": packet_recommendation,
        "timeline_recommendation": timeline_recommendation,
        "closure_decision": closure_decision,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": timeline_event_hashes,
        "exam_deployment_status": "not_cleared",
    }
    gate_hash = sha256_text(json.dumps(summary_seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_review_export_authorization_gate_ready",
        "selected_skill_tag": selected_skill_tag,
        "authorization_gate_decision": decision,
        "authorization_gate_reason": reason,
        "allowed_authorization_gate_decisions": sorted(EXPORT_AUTHORIZATION_GATE_DECISIONS),
        "export_preview_recommendation": preview_recommendation,
        "export_manifest_hash": preview_view.get("export_manifest_hash", ""),
        "packet_recommendation": packet_recommendation,
        "timeline_recommendation": timeline_recommendation,
        "closure_decision": closure_decision,
        "missing_required_hashes": missing_hashes[:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": list(timeline_event_hashes or [])[:12],
        "timeline_event_count": int(preview_view.get("timeline_event_count", packet_view.get("timeline_event_count", 0)) or 0),
        "next_safe_review_action": next_safe_review_action(decision),
        "help_level": safe_help_level(str(preview_view.get("help_level") or packet_view.get("help_level", "A2"))),
        "authorization_gate_hash": gate_hash,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_safe_review_action(decision: str) -> str:
    if decision == "ready_for_manual_export_authorization_review":
        return "present_hash_only_gate_to_human_export_authorization_reviewer"
    if decision == "request_hash_completion":
        return "complete_missing_hash_review_before_export_authorization"
    if decision == "reject_export_authorization":
        return "stop_export_authorization_review_and_return_to_manual_cycle_review"
    return "keep_export_blocked_and_continue_manual_review"


def export_authorization_gate_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_review_export_authorization_gate_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "authorization_gate_decision": summary.get("authorization_gate_decision", "keep_export_blocked"),
        "export_manifest_hash": summary.get("export_manifest_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-review-export-authorization-gate")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
