from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_final_review_ledger_integrity_gate import safe_final_review_receipt_ledger
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_archive_decision_draft import safe_reviewer_packet
from .python_exam_manual_export_reviewer_packet import safe_export_review_queue
from .python_exam_manual_final_review_handoff import safe_archive_decision_draft
from .python_exam_manual_final_review_receipt_ledger import safe_final_review_handoff


PYTHON_EXAM_FINAL_MANUAL_REVIEW_CONSOLE_SCHEMA_VERSION = "unibot-python-exam-final-manual-review-console-v1"
PYTHON_EXAM_FINAL_MANUAL_REVIEW_CONSOLE_ENDPOINT = (
    "/api/unibot/course/python-exam-final-manual-review-console"
)

FINAL_MANUAL_REVIEW_CONSOLE_RECOMMENDATIONS = {
    "keep_final_console_open",
    "request_integrity_reconciliation",
    "ready_for_manual_console_review",
    "reject_final_console",
}


def build_python_exam_final_manual_review_console(
    *,
    python_exam_final_review_ledger_integrity_gate: dict[str, Any] | None = None,
    python_exam_manual_final_review_receipt_ledger: dict[str, Any] | None = None,
    python_exam_manual_final_review_handoff: dict[str, Any] | None = None,
    python_exam_manual_archive_decision_draft: dict[str, Any] | None = None,
    python_exam_manual_export_reviewer_packet: dict[str, Any] | None = None,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    gate_view = safe_final_review_ledger_integrity_gate(
        python_exam_final_review_ledger_integrity_gate
        if isinstance(python_exam_final_review_ledger_integrity_gate, dict)
        else {}
    )
    ledger_view = safe_final_review_receipt_ledger(
        python_exam_manual_final_review_receipt_ledger
        if isinstance(python_exam_manual_final_review_receipt_ledger, dict)
        else {}
    )
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
        or gate_view.get("selected_skill_tag", "")
        or ledger_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
        or draft_view.get("selected_skill_tag", "")
        or reviewer_view.get("selected_skill_tag", "")
        or queue_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = final_manual_review_console_body(
        selected_skill_tag=selected,
        gate_view=gate_view,
        ledger_view=ledger_view,
        handoff_view=handoff_view,
        draft_view=draft_view,
        reviewer_view=reviewer_view,
        queue_view=queue_view,
    )
    summary = final_manual_review_console_summary(body)
    receipt = final_manual_review_console_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_FINAL_MANUAL_REVIEW_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "python_exam_final_manual_review_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_final_manual_review_console_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Final Manual Review Console. It consumes only Final Review Ledger Integrity Gate, "
            "Manual Final Review Receipt Ledger, Manual Final Review Handoff, Manual Archive Decision Draft, "
            "Manual Export Reviewer Packet, and Manual Export Review Queue metadata to present one human "
            "review view before any later export, archive, or submission proximity. It shows gate, ledger, "
            "handoff, draft, reviewer, and queue recommendations, integrity issues, missing hashes, mismatched "
            "hashes, Source-Card anchors, help level, skill tag, receipt hashes, timeline and ledger event "
            "hashes, accepted post-cycle hashes, and exactly one next safe human review action. It creates no "
            "export, writes nothing, starts no local action, archives nothing, submits nothing, authorizes "
            "nothing, and never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, rankings, grades, proctoring, AI detection, automatic "
            "grading, or exam clearance claims."
        ),
        "final_manual_review_console_endpoint": PYTHON_EXAM_FINAL_MANUAL_REVIEW_CONSOLE_ENDPOINT,
        "selected_skill_tag": selected,
        "final_manual_review_console_summary": summary,
        "final_manual_review_console_body": body,
        "final_manual_review_console_recommendation": summary["final_manual_review_console_recommendation"],
        "final_manual_review_console_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Final Manual Review Console bleibt not_cleared."
        ),
        "next_actions": [
            f"Final manual review console recommendation: {summary['final_manual_review_console_recommendation']}.",
            f"Next safe human review action: {summary['next_safe_human_review_action']}.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_final_review_ledger_integrity_gate(gate: dict[str, Any]) -> dict[str, Any]:
    summary = (
        gate.get("final_review_ledger_integrity_gate_summary", {})
        if isinstance(gate.get("final_review_ledger_integrity_gate_summary"), dict)
        else {}
    )
    body = (
        gate.get("final_review_ledger_integrity_gate_body", {})
        if isinstance(gate.get("final_review_ledger_integrity_gate_body"), dict)
        else {}
    )
    receipt = (
        gate.get("final_review_ledger_integrity_gate_receipt", {})
        if isinstance(gate.get("final_review_ledger_integrity_gate_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(gate.get("status", "missing")),
        "selected_skill_tag": str(gate.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "final_review_ledger_integrity_gate_recommendation": str(
            gate.get("final_review_ledger_integrity_gate_recommendation")
            or summary.get("final_review_ledger_integrity_gate_recommendation", "keep_integrity_gate_open")
        ),
        "final_review_receipt_ledger_recommendation": str(
            summary.get("final_review_receipt_ledger_recommendation")
            or body.get("final_review_receipt_ledger_recommendation", "")
        ),
        "final_review_handoff_recommendation": str(
            summary.get("final_review_handoff_recommendation")
            or body.get("final_review_handoff_recommendation", "")
        ),
        "archive_decision_draft_recommendation": str(
            summary.get("archive_decision_draft_recommendation")
            or body.get("archive_decision_draft_recommendation", "")
        ),
        "reviewer_packet_recommendation": str(
            summary.get("reviewer_packet_recommendation") or body.get("reviewer_packet_recommendation", "")
        ),
        "queue_recommendation": str(summary.get("queue_recommendation") or body.get("queue_recommendation", "")),
        "chain_issue_count": int(summary.get("chain_issue_count", body.get("chain_issue_count", 0)) or 0),
        "mismatched_hashes": [str(item) for item in (summary.get("mismatched_hashes") or body.get("mismatched_hashes", []) or [])][:12],
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "gate_decisions": [str(item) for item in (summary.get("gate_decisions") or body.get("gate_decisions", []) or [])][:12],
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "integrity_gate_receipt_hash": str(receipt.get("receipt_hash", "")),
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or body.get("candidate_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "ledger_event_hashes": [str(item) for item in (summary.get("ledger_event_hashes") or body.get("ledger_event_hashes", []) or [])][:12],
        "ledger_event_count": int(summary.get("ledger_event_count", body.get("ledger_event_count", 0)) or 0),
        "source_hashes": dict(summary.get("source_hashes", {}) or body.get("source_hashes", {}) or {}),
        "ledger_hashes": dict(summary.get("ledger_hashes", {}) or body.get("ledger_hashes", {}) or {}),
        "next_safe_human_review_action": str(
            summary.get("next_safe_human_review_action") or body.get("next_safe_human_review_action", "")
        ),
        "final_review_ledger_integrity_gate_hash": str(
            summary.get("final_review_ledger_integrity_gate_hash")
            or body.get("final_review_ledger_integrity_gate_hash", "")
        ),
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_manual_review_console_body(
    *,
    selected_skill_tag: str,
    gate_view: dict[str, Any],
    ledger_view: dict[str, Any],
    handoff_view: dict[str, Any],
    draft_view: dict[str, Any],
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(gate_view.get("receipt_hashes", {}) or {})
    if gate_view.get("integrity_gate_receipt_hash"):
        receipt_hashes["integrity_gate_receipt_hash"] = gate_view.get("integrity_gate_receipt_hash", "")
    if ledger_view.get("final_review_receipt_ledger_receipt_hash"):
        receipt_hashes["final_review_receipt_ledger_receipt_hash"] = ledger_view.get(
            "final_review_receipt_ledger_receipt_hash",
            "",
        )
    if handoff_view.get("final_review_handoff_receipt_hash"):
        receipt_hashes["final_review_handoff_receipt_hash"] = handoff_view.get("final_review_handoff_receipt_hash", "")
    if draft_view.get("archive_decision_draft_receipt_hash"):
        receipt_hashes["archive_decision_draft_receipt_hash"] = draft_view.get("archive_decision_draft_receipt_hash", "")
    missing_hashes = sorted(
        {
            str(item)
            for item in (
                list(gate_view.get("missing_required_hashes", []) or [])
                + list(ledger_view.get("missing_required_hashes", []) or [])
                + list(handoff_view.get("missing_required_hashes", []) or [])
            )
            if str(item)
        }
    )[:12]
    mismatched_hashes = [str(item) for item in (gate_view.get("mismatched_hashes", []) or [])][:12]
    accepted_hashes = (
        gate_view.get("accepted_post_cycle_hashes")
        or ledger_view.get("accepted_post_cycle_hashes")
        or handoff_view.get("accepted_post_cycle_hashes")
        or {}
    )
    timeline_event_hashes = (
        gate_view.get("timeline_event_hashes")
        or ledger_view.get("timeline_event_hashes")
        or handoff_view.get("timeline_event_hashes")
        or []
    )
    ledger_event_hashes = gate_view.get("ledger_event_hashes") or ledger_view.get("ledger_event_hashes") or []
    candidate_hashes = gate_view.get("candidate_hashes") or ledger_view.get("candidate_hashes") or []
    source_card_ids = gate_view.get("source_card_ids") or ledger_view.get("source_card_ids") or handoff_view.get("source_card_ids") or []
    console_seed = {
        "gate_recommendation": gate_view.get("final_review_ledger_integrity_gate_recommendation", ""),
        "ledger_recommendation": gate_view.get("final_review_receipt_ledger_recommendation")
        or ledger_view.get("final_review_receipt_ledger_recommendation", ""),
        "handoff_recommendation": gate_view.get("final_review_handoff_recommendation")
        or handoff_view.get("final_review_handoff_recommendation", ""),
        "missing_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": timeline_event_hashes,
        "ledger_event_hashes": ledger_event_hashes,
        "selected_skill_tag": selected_skill_tag,
        "exam_deployment_status": "not_cleared",
    }
    return {
        "status": "python_exam_final_manual_review_console_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "final_review_ledger_integrity_gate_recommendation": gate_view.get(
            "final_review_ledger_integrity_gate_recommendation",
            "keep_integrity_gate_open",
        ),
        "final_review_receipt_ledger_recommendation": gate_view.get("final_review_receipt_ledger_recommendation")
        or ledger_view.get("final_review_receipt_ledger_recommendation", ""),
        "final_review_handoff_recommendation": gate_view.get("final_review_handoff_recommendation")
        or handoff_view.get("final_review_handoff_recommendation", ""),
        "archive_decision_draft_recommendation": gate_view.get("archive_decision_draft_recommendation")
        or draft_view.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": gate_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": gate_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "integrity_issue_count": int(gate_view.get("chain_issue_count", 0) or 0),
        "missing_required_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "source_hashes": gate_view.get("source_hashes", {}),
        "ledger_hashes": gate_view.get("ledger_hashes", {}),
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(
            gate_view.get("source_anchor_hash_count", ledger_view.get("source_anchor_hash_count", 0)) or 0
        ),
        "help_level": safe_help_level(str(gate_view.get("help_level") or ledger_view.get("help_level") or "A2")),
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(gate_view.get("timeline_event_count", ledger_view.get("timeline_event_count", 0)) or 0),
        "ledger_event_hashes": [str(item) for item in (ledger_event_hashes or [])][:12],
        "ledger_event_count": int(gate_view.get("ledger_event_count", ledger_view.get("ledger_event_count", 0)) or 0),
        "accepted_post_cycle_hashes": accepted_hashes,
        "next_safe_human_review_action": one_next_safe_console_action(gate_view),
        "final_manual_review_console_hash": sha256_text(
            json.dumps(console_seed, sort_keys=True, ensure_ascii=False)
        ),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def final_manual_review_console_summary(body: dict[str, Any]) -> dict[str, Any]:
    gate_recommendation = body.get(
        "final_review_ledger_integrity_gate_recommendation",
        "keep_integrity_gate_open",
    )
    if gate_recommendation == "reject_integrity_chain":
        recommendation = "reject_final_console"
        reason = "integrity_chain_rejected"
    elif gate_recommendation == "request_hash_reconciliation":
        recommendation = "request_integrity_reconciliation"
        reason = "integrity_reconciliation_required"
    elif gate_recommendation == "ready_for_manual_integrity_review":
        recommendation = "ready_for_manual_console_review"
        reason = "final_console_ready_for_manual_review"
    else:
        recommendation = "keep_final_console_open"
        reason = "integrity_gate_still_open"
    return {
        "status": "python_exam_final_manual_review_console_ready",
        "final_manual_review_console_recommendation": recommendation,
        "final_manual_review_console_reason": reason,
        "allowed_final_manual_review_console_recommendations": sorted(
            FINAL_MANUAL_REVIEW_CONSOLE_RECOMMENDATIONS
        ),
        "final_review_ledger_integrity_gate_recommendation": gate_recommendation,
        "final_review_receipt_ledger_recommendation": body.get("final_review_receipt_ledger_recommendation", ""),
        "final_review_handoff_recommendation": body.get("final_review_handoff_recommendation", ""),
        "archive_decision_draft_recommendation": body.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": body.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": body.get("queue_recommendation", ""),
        "integrity_issue_count": int(body.get("integrity_issue_count", 0) or 0),
        "missing_required_hashes": body.get("missing_required_hashes", []),
        "mismatched_hashes": body.get("mismatched_hashes", []),
        "source_hashes": body.get("source_hashes", {}),
        "ledger_hashes": body.get("ledger_hashes", {}),
        "source_card_ids": body.get("source_card_ids", []),
        "source_anchor_hash_count": int(body.get("source_anchor_hash_count", 0) or 0),
        "selected_skill_tag": body.get("selected_skill_tag", "general_python"),
        "help_level": safe_help_level(str(body.get("help_level", "A2"))),
        "candidate_hashes": body.get("candidate_hashes", []),
        "receipt_hashes": body.get("receipt_hashes", {}),
        "timeline_event_hashes": body.get("timeline_event_hashes", []),
        "timeline_event_count": int(body.get("timeline_event_count", 0) or 0),
        "ledger_event_hashes": body.get("ledger_event_hashes", []),
        "ledger_event_count": int(body.get("ledger_event_count", 0) or 0),
        "accepted_post_cycle_hashes": body.get("accepted_post_cycle_hashes", {}),
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "final_manual_review_console_hash": body.get("final_manual_review_console_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def one_next_safe_console_action(gate_view: dict[str, Any]) -> str:
    recommendation = gate_view.get("final_review_ledger_integrity_gate_recommendation", "keep_integrity_gate_open")
    if recommendation == "ready_for_manual_integrity_review":
        return "present_final_hash_only_console_to_human_reviewer"
    if recommendation == "request_hash_reconciliation":
        return "reconcile_integrity_gate_hashes_before_final_console_review"
    if recommendation == "reject_integrity_chain":
        return "return_to_integrity_gate_or_final_review_ledger"
    return "keep_final_console_open_and_continue_manual_review"


def final_manual_review_console_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "final_manual_review_console_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "final_manual_review_console_recommendation": summary.get(
            "final_manual_review_console_recommendation",
            "keep_final_console_open",
        ),
        "final_manual_review_console_hash": summary.get("final_manual_review_console_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-final-manual-review-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
