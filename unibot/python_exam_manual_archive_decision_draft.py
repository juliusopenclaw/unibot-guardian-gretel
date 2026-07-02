from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_export_reviewer_packet import safe_export_review_queue
from .python_exam_manual_export_review_queue import safe_authorization_gate
from .python_exam_manual_review_export_authorization_gate import safe_export_preview


PYTHON_EXAM_MANUAL_ARCHIVE_DECISION_DRAFT_SCHEMA_VERSION = "unibot-python-exam-manual-archive-decision-draft-v1"
PYTHON_EXAM_MANUAL_ARCHIVE_DECISION_DRAFT_ENDPOINT = "/api/unibot/course/python-exam-manual-archive-decision-draft"

ARCHIVE_DECISION_DRAFT_RECOMMENDATIONS = {
    "keep_archive_decision_draft_open",
    "request_hash_completion",
    "ready_for_manual_archive_decision_review",
    "reject_archive_decision_draft",
}


def build_python_exam_manual_archive_decision_draft(
    *,
    python_exam_manual_export_reviewer_packet: dict[str, Any] | None = None,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    python_exam_manual_review_export_authorization_gate: dict[str, Any] | None = None,
    python_exam_manual_review_export_preview: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
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
    selected = str(
        selected_skill_tag
        or reviewer_view.get("selected_skill_tag", "")
        or queue_view.get("selected_skill_tag", "")
        or gate_view.get("selected_skill_tag", "")
        or preview_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = archive_decision_draft_body(
        selected_skill_tag=selected,
        reviewer_view=reviewer_view,
        queue_view=queue_view,
        gate_view=gate_view,
        preview_view=preview_view,
    )
    summary = archive_decision_draft_summary(body)
    receipt = archive_decision_draft_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_ARCHIVE_DECISION_DRAFT_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_archive_decision_draft",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_archive_decision_draft_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Archive Decision Draft. It consumes only Manual Export Reviewer Packet, Manual "
            "Export Review Queue, Export Authorization Gate, and Export Preview metadata to prepare a later "
            "human archive or submission decision. It bundles reviewer-packet recommendation, queue "
            "recommendation, candidate hashes, reviewer-packet hash, queue hash, export manifest hash, "
            "authorization gate hash, receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, "
            "help level, Source-Card anchors, timeline event hashes, and next safe decision action. It creates "
            "no export, writes nothing, starts no local action, archives nothing, submits nothing, authorizes "
            "nothing, and never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, rankings, grades, proctoring, AI detection, automatic "
            "grading, or exam clearance claims."
        ),
        "manual_archive_decision_draft_endpoint": PYTHON_EXAM_MANUAL_ARCHIVE_DECISION_DRAFT_ENDPOINT,
        "selected_skill_tag": selected,
        "archive_decision_draft_summary": summary,
        "archive_decision_draft_body": body,
        "archive_decision_draft_recommendation": summary["archive_decision_draft_recommendation"],
        "manual_archive_decision_draft_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Archive Decision Draft bleibt not_cleared."
        ),
        "next_actions": [
            f"Archive decision draft recommendation: {summary['archive_decision_draft_recommendation']}.",
            "Use this draft only for human review before any later archive or submission decision.",
            "Keep archiving, submission, export creation, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_reviewer_packet(packet: dict[str, Any]) -> dict[str, Any]:
    summary = (
        packet.get("reviewer_packet_summary", {})
        if isinstance(packet.get("reviewer_packet_summary"), dict)
        else {}
    )
    body = packet.get("reviewer_packet_body", {}) if isinstance(packet.get("reviewer_packet_body"), dict) else {}
    receipt = (
        packet.get("manual_export_reviewer_packet_receipt", {})
        if isinstance(packet.get("manual_export_reviewer_packet_receipt"), dict)
        else {}
    )
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    return {
        "status": str(packet.get("status", "missing")),
        "selected_skill_tag": str(packet.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "reviewer_packet_recommendation": str(
            packet.get("reviewer_packet_recommendation")
            or summary.get("reviewer_packet_recommendation", "keep_reviewer_packet_open")
        ),
        "queue_recommendation": str(summary.get("queue_recommendation") or body.get("queue_recommendation", "")),
        "queue_hash": str(summary.get("queue_hash") or body.get("queue_hash", "")),
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or body.get("candidate_hashes", []) or [])][:12],
        "gate_decisions": [str(item) for item in (summary.get("gate_decisions") or body.get("gate_decisions", []) or [])][:12],
        "export_manifest_hash": str(summary.get("export_manifest_hash") or body.get("export_manifest_hash", "")),
        "authorization_gate_hash": str(summary.get("authorization_gate_hash") or body.get("authorization_gate_hash", "")),
        "reviewer_packet_hash": str(summary.get("reviewer_packet_hash") or body.get("reviewer_packet_hash", "")),
        "preview_receipt_hash": str(summary.get("preview_receipt_hash") or body.get("preview_receipt_hash", "")),
        "packet_receipt_hash": str(summary.get("packet_receipt_hash") or body.get("packet_receipt_hash", "")),
        "timeline_receipt_hash": str(summary.get("timeline_receipt_hash") or body.get("timeline_receipt_hash", "")),
        "authorization_gate_receipt_hash": str(
            summary.get("authorization_gate_receipt_hash") or body.get("authorization_gate_receipt_hash", "")
        ),
        "queue_receipt_hash": str(summary.get("queue_receipt_hash") or body.get("queue_receipt_hash", "")),
        "reviewer_packet_receipt_hash": str(receipt.get("receipt_hash", "")),
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "next_safe_review_action": str(summary.get("next_safe_review_action") or body.get("next_safe_review_action", "")),
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def archive_decision_draft_body(
    *,
    selected_skill_tag: str,
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
    gate_view: dict[str, Any],
    preview_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(reviewer_view.get("receipt_hashes", {}) or {})
    receipt_hashes["reviewer_packet_receipt_hash"] = reviewer_view.get("reviewer_packet_receipt_hash", "")
    receipt_hashes["queue_receipt_hash"] = reviewer_view.get("queue_receipt_hash") or queue_view.get("queue_receipt_hash", "")
    receipt_hashes["authorization_gate_receipt_hash"] = reviewer_view.get("authorization_gate_receipt_hash") or gate_view.get("gate_receipt_hash", "")
    missing_hashes = list(reviewer_view.get("missing_required_hashes") or gate_view.get("missing_required_hashes") or preview_view.get("missing_required_hashes") or [])
    accepted_hashes = reviewer_view.get("accepted_post_cycle_hashes") or gate_view.get("accepted_post_cycle_hashes", {})
    candidate_hashes = reviewer_view.get("candidate_hashes") or queue_view.get("candidate_hashes", [])
    seed = {
        "reviewer_packet_recommendation": reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": reviewer_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "candidate_hashes": candidate_hashes,
        "reviewer_packet_hash": reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": reviewer_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": reviewer_view.get("export_manifest_hash") or gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": reviewer_view.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "selected_skill_tag": selected_skill_tag,
        "timeline_event_hashes": reviewer_view.get("timeline_event_hashes", []),
        "exam_deployment_status": "not_cleared",
    }
    draft_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_archive_decision_draft_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "reviewer_packet_recommendation": reviewer_view.get("reviewer_packet_recommendation", "keep_reviewer_packet_open"),
        "queue_recommendation": reviewer_view.get("queue_recommendation") or queue_view.get("queue_recommendation", "keep_queue_open"),
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "gate_decisions": reviewer_view.get("gate_decisions") or [gate_view.get("authorization_gate_decision", "")],
        "reviewer_packet_hash": reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": reviewer_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": reviewer_view.get("export_manifest_hash") or gate_view.get("export_manifest_hash") or preview_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": reviewer_view.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "preview_receipt_hash": reviewer_view.get("preview_receipt_hash") or receipt_hashes.get("preview_receipt_hash", ""),
        "packet_receipt_hash": reviewer_view.get("packet_receipt_hash") or receipt_hashes.get("packet_receipt_hash", ""),
        "timeline_receipt_hash": reviewer_view.get("timeline_receipt_hash") or receipt_hashes.get("timeline_receipt_hash", ""),
        "authorization_gate_receipt_hash": receipt_hashes.get("authorization_gate_receipt_hash", ""),
        "queue_receipt_hash": receipt_hashes.get("queue_receipt_hash", ""),
        "reviewer_packet_receipt_hash": receipt_hashes.get("reviewer_packet_receipt_hash", ""),
        "missing_required_hashes": missing_hashes[:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "help_level": safe_help_level(str(reviewer_view.get("help_level") or gate_view.get("help_level") or preview_view.get("help_level", "A2"))),
        "source_card_ids": reviewer_view.get("source_card_ids", []),
        "source_anchor_hash_count": int(reviewer_view.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": reviewer_view.get("timeline_event_hashes", []),
        "timeline_event_count": int(reviewer_view.get("timeline_event_count", 0) or 0),
        "next_safe_decision_action": next_decision_action_from_reviewer(
            reviewer_view.get("reviewer_packet_recommendation", "keep_reviewer_packet_open")
        ),
        "archive_decision_draft_hash": draft_hash,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def archive_decision_draft_summary(body: dict[str, Any]) -> dict[str, Any]:
    reviewer_recommendation = body.get("reviewer_packet_recommendation", "keep_reviewer_packet_open")
    if reviewer_recommendation == "reject_reviewer_packet":
        recommendation = "reject_archive_decision_draft"
        reason = "reviewer_packet_rejected"
    elif reviewer_recommendation == "request_hash_completion":
        recommendation = "request_hash_completion"
        reason = "reviewer_packet_requests_hash_completion"
    elif reviewer_recommendation == "ready_for_human_reviewer_packet":
        recommendation = "ready_for_manual_archive_decision_review"
        reason = "reviewer_packet_ready_for_manual_archive_decision_review"
    else:
        recommendation = "keep_archive_decision_draft_open"
        reason = "reviewer_packet_still_open"
    return {
        "status": "python_exam_manual_archive_decision_draft_ready",
        "archive_decision_draft_recommendation": recommendation,
        "archive_decision_draft_reason": reason,
        "allowed_archive_decision_draft_recommendations": sorted(ARCHIVE_DECISION_DRAFT_RECOMMENDATIONS),
        "reviewer_packet_recommendation": reviewer_recommendation,
        "queue_recommendation": body.get("queue_recommendation", ""),
        "candidate_hashes": body.get("candidate_hashes", []),
        "gate_decisions": body.get("gate_decisions", []),
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
        "next_safe_decision_action": body.get("next_safe_decision_action", ""),
        "archive_decision_draft_hash": body.get("archive_decision_draft_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_decision_action_from_reviewer(reviewer_recommendation: str) -> str:
    if reviewer_recommendation == "ready_for_human_reviewer_packet":
        return "present_hash_only_archive_decision_draft_to_human_reviewer"
    if reviewer_recommendation == "request_hash_completion":
        return "complete_missing_hashes_before_archive_decision_review"
    if reviewer_recommendation == "reject_reviewer_packet":
        return "return_to_reviewer_packet_or_queue_review"
    return "keep_archive_decision_draft_open_and_continue_manual_review"


def archive_decision_draft_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_archive_decision_draft_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "archive_decision_draft_recommendation": summary.get(
            "archive_decision_draft_recommendation",
            "keep_archive_decision_draft_open",
        ),
        "archive_decision_draft_hash": summary.get("archive_decision_draft_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-archive-decision-draft")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
