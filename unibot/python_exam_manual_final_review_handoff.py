from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_archive_decision_draft import safe_reviewer_packet
from .python_exam_manual_export_reviewer_packet import safe_export_review_queue
from .python_exam_manual_export_review_queue import safe_authorization_gate


PYTHON_EXAM_MANUAL_FINAL_REVIEW_HANDOFF_SCHEMA_VERSION = "unibot-python-exam-manual-final-review-handoff-v1"
PYTHON_EXAM_MANUAL_FINAL_REVIEW_HANDOFF_ENDPOINT = "/api/unibot/course/python-exam-manual-final-review-handoff"

FINAL_REVIEW_HANDOFF_RECOMMENDATIONS = {
    "keep_final_handoff_open",
    "request_hash_completion",
    "ready_for_manual_final_review",
    "reject_final_handoff",
}


def build_python_exam_manual_final_review_handoff(
    *,
    python_exam_manual_archive_decision_draft: dict[str, Any] | None = None,
    python_exam_manual_export_reviewer_packet: dict[str, Any] | None = None,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    python_exam_manual_review_export_authorization_gate: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
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
    gate_view = safe_authorization_gate(
        python_exam_manual_review_export_authorization_gate
        if isinstance(python_exam_manual_review_export_authorization_gate, dict)
        else {}
    )
    selected = str(
        selected_skill_tag
        or draft_view.get("selected_skill_tag", "")
        or reviewer_view.get("selected_skill_tag", "")
        or queue_view.get("selected_skill_tag", "")
        or gate_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = final_review_handoff_body(
        selected_skill_tag=selected,
        draft_view=draft_view,
        reviewer_view=reviewer_view,
        queue_view=queue_view,
        gate_view=gate_view,
    )
    summary = final_review_handoff_summary(body)
    receipt = final_review_handoff_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_FINAL_REVIEW_HANDOFF_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_final_review_handoff",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_final_review_handoff_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Final Review Handoff. It consumes only Manual Archive Decision Draft, Manual "
            "Export Reviewer Packet, Manual Export Review Queue, and Export Authorization Gate metadata to "
            "prepare the final human review view before any later archive, submission, or export action. It "
            "bundles archive-decision-draft recommendation, reviewer-packet recommendation, queue "
            "recommendation, gate decisions, candidate hashes, draft hash, reviewer-packet hash, queue hash, "
            "export manifest hash, authorization gate hash, receipt hashes, missing hashes, accepted "
            "post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, and next "
            "safe human review action. It creates no export, writes nothing, starts no local action, archives "
            "nothing, submits nothing, authorizes nothing, and never returns raw queries, course raw text, "
            "notebook code, local paths, values, solutions, final interpretations, scores, rankings, grades, "
            "proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_final_review_handoff_endpoint": PYTHON_EXAM_MANUAL_FINAL_REVIEW_HANDOFF_ENDPOINT,
        "selected_skill_tag": selected,
        "final_review_handoff_summary": summary,
        "final_review_handoff_body": body,
        "final_review_handoff_recommendation": summary["final_review_handoff_recommendation"],
        "manual_final_review_handoff_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Final Review Handoff bleibt not_cleared."
        ),
        "next_actions": [
            f"Final review handoff recommendation: {summary['final_review_handoff_recommendation']}.",
            "Use this handoff only for human final review before any later export, archive, or submission action.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_archive_decision_draft(draft: dict[str, Any]) -> dict[str, Any]:
    summary = (
        draft.get("archive_decision_draft_summary", {})
        if isinstance(draft.get("archive_decision_draft_summary"), dict)
        else {}
    )
    body = (
        draft.get("archive_decision_draft_body", {})
        if isinstance(draft.get("archive_decision_draft_body"), dict)
        else {}
    )
    receipt = (
        draft.get("manual_archive_decision_draft_receipt", {})
        if isinstance(draft.get("manual_archive_decision_draft_receipt"), dict)
        else {}
    )
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    return {
        "status": str(draft.get("status", "missing")),
        "selected_skill_tag": str(draft.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "archive_decision_draft_recommendation": str(
            draft.get("archive_decision_draft_recommendation")
            or summary.get("archive_decision_draft_recommendation", "keep_archive_decision_draft_open")
        ),
        "reviewer_packet_recommendation": str(
            summary.get("reviewer_packet_recommendation") or body.get("reviewer_packet_recommendation", "")
        ),
        "queue_recommendation": str(summary.get("queue_recommendation") or body.get("queue_recommendation", "")),
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or body.get("candidate_hashes", []) or [])][:12],
        "gate_decisions": [str(item) for item in (summary.get("gate_decisions") or body.get("gate_decisions", []) or [])][:12],
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
        "archive_decision_draft_receipt_hash": str(receipt.get("receipt_hash", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "next_safe_decision_action": str(
            summary.get("next_safe_decision_action") or body.get("next_safe_decision_action", "")
        ),
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_review_handoff_body(
    *,
    selected_skill_tag: str,
    draft_view: dict[str, Any],
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
    gate_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(draft_view.get("receipt_hashes", {}) or {})
    receipt_hashes["archive_decision_draft_receipt_hash"] = draft_view.get(
        "archive_decision_draft_receipt_hash",
        "",
    )
    if reviewer_view.get("reviewer_packet_receipt_hash"):
        receipt_hashes["reviewer_packet_receipt_hash"] = reviewer_view.get("reviewer_packet_receipt_hash", "")
    if queue_view.get("queue_receipt_hash"):
        receipt_hashes["queue_receipt_hash"] = queue_view.get("queue_receipt_hash", "")
    if gate_view.get("gate_receipt_hash"):
        receipt_hashes["authorization_gate_receipt_hash"] = gate_view.get("gate_receipt_hash", "")
    missing_hashes = list(
        draft_view.get("missing_required_hashes")
        or reviewer_view.get("missing_required_hashes")
        or gate_view.get("missing_required_hashes")
        or []
    )
    accepted_hashes = draft_view.get("accepted_post_cycle_hashes") or reviewer_view.get("accepted_post_cycle_hashes", {})
    candidate_hashes = draft_view.get("candidate_hashes") or reviewer_view.get("candidate_hashes") or queue_view.get("candidate_hashes", [])
    gate_decisions = draft_view.get("gate_decisions") or reviewer_view.get("gate_decisions") or [gate_view.get("authorization_gate_decision", "")]
    seed = {
        "archive_decision_draft_recommendation": draft_view.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": draft_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": draft_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "gate_decisions": gate_decisions,
        "candidate_hashes": candidate_hashes,
        "archive_decision_draft_hash": draft_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": draft_view.get("reviewer_packet_hash") or reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": draft_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": draft_view.get("export_manifest_hash") or gate_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": draft_view.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes,
        "accepted_post_cycle_hashes": accepted_hashes,
        "selected_skill_tag": selected_skill_tag,
        "timeline_event_hashes": draft_view.get("timeline_event_hashes", []),
        "exam_deployment_status": "not_cleared",
    }
    handoff_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_manual_final_review_handoff_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "archive_decision_draft_recommendation": draft_view.get(
            "archive_decision_draft_recommendation",
            "keep_archive_decision_draft_open",
        ),
        "reviewer_packet_recommendation": draft_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": draft_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "gate_decisions": [str(item) for item in (gate_decisions or [])][:12],
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "archive_decision_draft_hash": draft_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": draft_view.get("reviewer_packet_hash") or reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": draft_view.get("queue_hash") or queue_view.get("queue_hash", ""),
        "export_manifest_hash": draft_view.get("export_manifest_hash") or gate_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": draft_view.get("authorization_gate_hash") or gate_view.get("authorization_gate_hash", ""),
        "receipt_hashes": receipt_hashes,
        "missing_required_hashes": missing_hashes[:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "help_level": safe_help_level(str(draft_view.get("help_level") or reviewer_view.get("help_level") or gate_view.get("help_level", "A2"))),
        "source_card_ids": draft_view.get("source_card_ids") or reviewer_view.get("source_card_ids", []),
        "source_anchor_hash_count": int(draft_view.get("source_anchor_hash_count", reviewer_view.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": draft_view.get("timeline_event_hashes") or reviewer_view.get("timeline_event_hashes", []),
        "timeline_event_count": int(draft_view.get("timeline_event_count", reviewer_view.get("timeline_event_count", 0)) or 0),
        "next_safe_human_review_action": next_handoff_action_from_draft(
            draft_view.get("archive_decision_draft_recommendation", "keep_archive_decision_draft_open")
        ),
        "final_review_handoff_hash": handoff_hash,
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_review_handoff_summary(body: dict[str, Any]) -> dict[str, Any]:
    draft_recommendation = body.get("archive_decision_draft_recommendation", "keep_archive_decision_draft_open")
    if draft_recommendation == "reject_archive_decision_draft":
        recommendation = "reject_final_handoff"
        reason = "archive_decision_draft_rejected"
    elif draft_recommendation == "request_hash_completion":
        recommendation = "request_hash_completion"
        reason = "archive_decision_draft_requests_hash_completion"
    elif draft_recommendation == "ready_for_manual_archive_decision_review":
        recommendation = "ready_for_manual_final_review"
        reason = "archive_decision_draft_ready_for_manual_final_review"
    else:
        recommendation = "keep_final_handoff_open"
        reason = "archive_decision_draft_still_open"
    return {
        "status": "python_exam_manual_final_review_handoff_ready",
        "final_review_handoff_recommendation": recommendation,
        "final_review_handoff_reason": reason,
        "allowed_final_review_handoff_recommendations": sorted(FINAL_REVIEW_HANDOFF_RECOMMENDATIONS),
        "archive_decision_draft_recommendation": draft_recommendation,
        "reviewer_packet_recommendation": body.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": body.get("queue_recommendation", ""),
        "gate_decisions": body.get("gate_decisions", []),
        "candidate_hashes": body.get("candidate_hashes", []),
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
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "final_review_handoff_hash": body.get("final_review_handoff_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_handoff_action_from_draft(draft_recommendation: str) -> str:
    if draft_recommendation == "ready_for_manual_archive_decision_review":
        return "present_hash_only_final_review_handoff_to_human_reviewer"
    if draft_recommendation == "request_hash_completion":
        return "complete_missing_hashes_before_final_review"
    if draft_recommendation == "reject_archive_decision_draft":
        return "return_to_archive_decision_draft_or_reviewer_packet"
    return "keep_final_handoff_open_and_continue_manual_review"


def final_review_handoff_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_final_review_handoff_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "final_review_handoff_recommendation": summary.get(
            "final_review_handoff_recommendation",
            "keep_final_handoff_open",
        ),
        "final_review_handoff_hash": summary.get("final_review_handoff_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-final-review-handoff")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
