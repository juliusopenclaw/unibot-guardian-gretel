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
from .python_exam_manual_final_review_receipt_ledger import safe_final_review_handoff


PYTHON_EXAM_FINAL_REVIEW_LEDGER_INTEGRITY_GATE_SCHEMA_VERSION = (
    "unibot-python-exam-final-review-ledger-integrity-gate-v1"
)
PYTHON_EXAM_FINAL_REVIEW_LEDGER_INTEGRITY_GATE_ENDPOINT = (
    "/api/unibot/course/python-exam-final-review-ledger-integrity-gate"
)

FINAL_REVIEW_LEDGER_INTEGRITY_GATE_RECOMMENDATIONS = {
    "keep_integrity_gate_open",
    "request_hash_reconciliation",
    "ready_for_manual_integrity_review",
    "reject_integrity_chain",
}


def build_python_exam_final_review_ledger_integrity_gate(
    *,
    python_exam_manual_final_review_receipt_ledger: dict[str, Any] | None = None,
    python_exam_manual_final_review_handoff: dict[str, Any] | None = None,
    python_exam_manual_archive_decision_draft: dict[str, Any] | None = None,
    python_exam_manual_export_reviewer_packet: dict[str, Any] | None = None,
    python_exam_manual_export_review_queue: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
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
        or ledger_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
        or draft_view.get("selected_skill_tag", "")
        or reviewer_view.get("selected_skill_tag", "")
        or queue_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = integrity_gate_body(
        selected_skill_tag=selected,
        ledger_view=ledger_view,
        handoff_view=handoff_view,
        draft_view=draft_view,
        reviewer_view=reviewer_view,
        queue_view=queue_view,
    )
    summary = integrity_gate_summary(body)
    receipt = integrity_gate_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_FINAL_REVIEW_LEDGER_INTEGRITY_GATE_SCHEMA_VERSION,
        "artifact_type": "python_exam_final_review_ledger_integrity_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_final_review_ledger_integrity_gate_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Final Review Ledger Integrity Gate. It consumes only Manual Final Review Receipt "
            "Ledger, Manual Final Review Handoff, Manual Archive Decision Draft, Manual Export Reviewer "
            "Packet, and Manual Export Review Queue metadata to check whether the final review chain is "
            "consistent, chronological, and human-reviewable before any later export, archive, or submission "
            "proximity. It compares ledger event hashes, handoff hash, draft hash, reviewer-packet hash, "
            "queue hash, export manifest hash, authorization gate hash, receipt hashes, candidate hashes, "
            "missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline "
            "event hashes, and next safe human review action. It creates no export, writes nothing, starts no "
            "local action, archives nothing, submits nothing, authorizes nothing, and never returns raw "
            "queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "final_review_ledger_integrity_gate_endpoint": PYTHON_EXAM_FINAL_REVIEW_LEDGER_INTEGRITY_GATE_ENDPOINT,
        "selected_skill_tag": selected,
        "final_review_ledger_integrity_gate_summary": summary,
        "final_review_ledger_integrity_gate_body": body,
        "final_review_ledger_integrity_gate_recommendation": summary[
            "final_review_ledger_integrity_gate_recommendation"
        ],
        "final_review_ledger_integrity_gate_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Final Review Ledger Integrity Gate bleibt not_cleared."
        ),
        "next_actions": [
            f"Final review ledger integrity gate recommendation: {summary['final_review_ledger_integrity_gate_recommendation']}.",
            "Use this gate only for human integrity review before any later export, archive, or submission proximity.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_final_review_receipt_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    summary = (
        ledger.get("final_review_receipt_ledger_summary", {})
        if isinstance(ledger.get("final_review_receipt_ledger_summary"), dict)
        else {}
    )
    body = (
        ledger.get("final_review_receipt_ledger_body", {})
        if isinstance(ledger.get("final_review_receipt_ledger_body"), dict)
        else {}
    )
    receipt = (
        ledger.get("manual_final_review_receipt_ledger_receipt", {})
        if isinstance(ledger.get("manual_final_review_receipt_ledger_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(ledger.get("status", "missing")),
        "selected_skill_tag": str(ledger.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "final_review_receipt_ledger_recommendation": str(
            ledger.get("final_review_receipt_ledger_recommendation")
            or summary.get("final_review_receipt_ledger_recommendation", "keep_final_ledger_open")
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
        "gate_decisions": [str(item) for item in (summary.get("gate_decisions") or body.get("gate_decisions", []) or [])][:12],
        "candidate_hashes": [str(item) for item in (summary.get("candidate_hashes") or body.get("candidate_hashes", []) or [])][:12],
        "final_review_receipt_ledger_hash": str(
            summary.get("final_review_receipt_ledger_hash") or body.get("final_review_receipt_ledger_hash", "")
        ),
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
        "final_review_receipt_ledger_receipt_hash": str(receipt.get("receipt_hash", "")),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])][:12],
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0),
        "timeline_event_hashes": [str(item) for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "ledger_event_hashes": [str(item) for item in (summary.get("ledger_event_hashes", []) or [])][:12],
        "ledger_event_count": int(summary.get("ledger_event_count", 0) or 0),
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


def integrity_gate_body(
    *,
    selected_skill_tag: str,
    ledger_view: dict[str, Any],
    handoff_view: dict[str, Any],
    draft_view: dict[str, Any],
    reviewer_view: dict[str, Any],
    queue_view: dict[str, Any],
) -> dict[str, Any]:
    source_hashes = {
        "final_review_handoff_hash": handoff_view.get("final_review_handoff_hash", ""),
        "archive_decision_draft_hash": draft_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": reviewer_view.get("reviewer_packet_hash", ""),
        "queue_hash": queue_view.get("queue_hash", ""),
        "export_manifest_hash": handoff_view.get("export_manifest_hash") or draft_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": handoff_view.get("authorization_gate_hash") or draft_view.get("authorization_gate_hash", ""),
    }
    ledger_hashes = {
        "final_review_handoff_hash": ledger_view.get("final_review_handoff_hash", ""),
        "archive_decision_draft_hash": ledger_view.get("archive_decision_draft_hash", ""),
        "reviewer_packet_hash": ledger_view.get("reviewer_packet_hash", ""),
        "queue_hash": ledger_view.get("queue_hash", ""),
        "export_manifest_hash": ledger_view.get("export_manifest_hash", ""),
        "authorization_gate_hash": ledger_view.get("authorization_gate_hash", ""),
    }
    mismatched_hashes = [
        key
        for key, source_value in source_hashes.items()
        if source_value and ledger_hashes.get(key) and source_value != ledger_hashes.get(key)
    ]
    missing_hashes = sorted(
        {
            str(item)
            for item in (
                list(ledger_view.get("missing_required_hashes", []) or [])
                + [
                    key
                    for key, value in {**source_hashes, **ledger_hashes}.items()
                    if not value
                ]
            )
            if str(item)
        }
    )[:12]
    skill_tags = [
        selected_skill_tag,
        ledger_view.get("selected_skill_tag", ""),
        handoff_view.get("selected_skill_tag", ""),
        draft_view.get("selected_skill_tag", ""),
        reviewer_view.get("selected_skill_tag", ""),
        queue_view.get("selected_skill_tag", ""),
    ]
    skill_tag_consistent = len({str(item) for item in skill_tags if str(item)}) <= 1
    help_levels = [
        ledger_view.get("help_level", ""),
        handoff_view.get("help_level", ""),
        draft_view.get("help_level", ""),
        reviewer_view.get("help_level", ""),
    ]
    help_level_consistent = len({str(item) for item in help_levels if str(item)}) <= 1
    receipt_hashes = dict(ledger_view.get("receipt_hashes", {}) or {})
    if ledger_view.get("final_review_receipt_ledger_receipt_hash"):
        receipt_hashes["final_review_receipt_ledger_receipt_hash"] = ledger_view.get(
            "final_review_receipt_ledger_receipt_hash",
            "",
        )
    candidate_hashes = ledger_view.get("candidate_hashes") or handoff_view.get("candidate_hashes") or []
    timeline_event_hashes = ledger_view.get("timeline_event_hashes") or handoff_view.get("timeline_event_hashes") or []
    source_card_ids = ledger_view.get("source_card_ids") or handoff_view.get("source_card_ids") or []
    chain_issue_count = (
        len(mismatched_hashes)
        + len(missing_hashes)
        + (0 if skill_tag_consistent else 1)
        + (0 if help_level_consistent else 1)
    )
    gate_seed = {
        "ledger_recommendation": ledger_view.get("final_review_receipt_ledger_recommendation", ""),
        "handoff_recommendation": ledger_view.get("final_review_handoff_recommendation")
        or handoff_view.get("final_review_handoff_recommendation", ""),
        "source_hashes": source_hashes,
        "ledger_hashes": ledger_hashes,
        "mismatched_hashes": mismatched_hashes,
        "missing_hashes": missing_hashes,
        "ledger_event_hashes": ledger_view.get("ledger_event_hashes", []),
        "selected_skill_tag": selected_skill_tag,
        "exam_deployment_status": "not_cleared",
    }
    return {
        "status": "python_exam_final_review_ledger_integrity_gate_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "final_review_receipt_ledger_recommendation": ledger_view.get(
            "final_review_receipt_ledger_recommendation",
            "keep_final_ledger_open",
        ),
        "final_review_handoff_recommendation": ledger_view.get("final_review_handoff_recommendation")
        or handoff_view.get("final_review_handoff_recommendation", ""),
        "archive_decision_draft_recommendation": ledger_view.get("archive_decision_draft_recommendation")
        or draft_view.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": ledger_view.get("reviewer_packet_recommendation")
        or reviewer_view.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": ledger_view.get("queue_recommendation") or queue_view.get("queue_recommendation", ""),
        "gate_decisions": ledger_view.get("gate_decisions") or handoff_view.get("gate_decisions", []),
        "source_hashes": source_hashes,
        "ledger_hashes": ledger_hashes,
        "mismatched_hashes": mismatched_hashes,
        "missing_required_hashes": missing_hashes,
        "receipt_hashes": receipt_hashes,
        "candidate_hashes": [str(item) for item in (candidate_hashes or [])][:12],
        "accepted_post_cycle_hashes": ledger_view.get("accepted_post_cycle_hashes")
        or handoff_view.get("accepted_post_cycle_hashes", {}),
        "help_level": safe_help_level(str(ledger_view.get("help_level") or handoff_view.get("help_level") or "A2")),
        "help_level_consistent": help_level_consistent,
        "skill_tag_consistent": skill_tag_consistent,
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(
            ledger_view.get("source_anchor_hash_count", handoff_view.get("source_anchor_hash_count", 0)) or 0
        ),
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(
            ledger_view.get("timeline_event_count", handoff_view.get("timeline_event_count", 0)) or 0
        ),
        "ledger_event_hashes": ledger_view.get("ledger_event_hashes", []),
        "ledger_event_count": int(ledger_view.get("ledger_event_count", 0) or 0),
        "chain_issue_count": chain_issue_count,
        "next_safe_human_review_action": next_integrity_gate_action(
            chain_issue_count,
            ledger_view,
            mismatched_hashes=mismatched_hashes,
            skill_tag_consistent=skill_tag_consistent,
            help_level_consistent=help_level_consistent,
        ),
        "final_review_ledger_integrity_gate_hash": sha256_text(
            json.dumps(gate_seed, sort_keys=True, ensure_ascii=False)
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


def integrity_gate_summary(body: dict[str, Any]) -> dict[str, Any]:
    ledger_recommendation = body.get("final_review_receipt_ledger_recommendation", "keep_final_ledger_open")
    handoff_recommendation = body.get("final_review_handoff_recommendation", "keep_final_handoff_open")
    chain_issue_count = int(body.get("chain_issue_count", 0) or 0)
    needs_reconciliation = (
        bool(body.get("mismatched_hashes", []))
        or not bool(body.get("skill_tag_consistent", False))
        or not bool(body.get("help_level_consistent", False))
        or ledger_recommendation == "request_hash_completion"
    )
    if ledger_recommendation == "reject_final_ledger" or handoff_recommendation == "reject_final_handoff":
        recommendation = "reject_integrity_chain"
        reason = "final_review_chain_rejected"
    elif needs_reconciliation:
        recommendation = "request_hash_reconciliation"
        reason = "hash_or_metadata_reconciliation_required"
    elif ledger_recommendation == "ready_for_manual_final_ledger_review":
        recommendation = "ready_for_manual_integrity_review"
        reason = "final_review_ledger_integrity_ready_for_manual_review"
    else:
        recommendation = "keep_integrity_gate_open"
        reason = "final_review_ledger_still_open"
    return {
        "status": "python_exam_final_review_ledger_integrity_gate_ready",
        "final_review_ledger_integrity_gate_recommendation": recommendation,
        "final_review_ledger_integrity_gate_reason": reason,
        "allowed_final_review_ledger_integrity_gate_recommendations": sorted(
            FINAL_REVIEW_LEDGER_INTEGRITY_GATE_RECOMMENDATIONS
        ),
        "final_review_receipt_ledger_recommendation": ledger_recommendation,
        "final_review_handoff_recommendation": handoff_recommendation,
        "archive_decision_draft_recommendation": body.get("archive_decision_draft_recommendation", ""),
        "reviewer_packet_recommendation": body.get("reviewer_packet_recommendation", ""),
        "queue_recommendation": body.get("queue_recommendation", ""),
        "gate_decisions": body.get("gate_decisions", []),
        "source_hashes": body.get("source_hashes", {}),
        "ledger_hashes": body.get("ledger_hashes", {}),
        "mismatched_hashes": body.get("mismatched_hashes", []),
        "missing_required_hashes": body.get("missing_required_hashes", []),
        "chain_issue_count": chain_issue_count,
        "receipt_hashes": body.get("receipt_hashes", {}),
        "candidate_hashes": body.get("candidate_hashes", []),
        "accepted_post_cycle_hashes": body.get("accepted_post_cycle_hashes", {}),
        "selected_skill_tag": body.get("selected_skill_tag", "general_python"),
        "help_level": safe_help_level(str(body.get("help_level", "A2"))),
        "help_level_consistent": bool(body.get("help_level_consistent", False)),
        "skill_tag_consistent": bool(body.get("skill_tag_consistent", False)),
        "source_card_ids": body.get("source_card_ids", []),
        "source_anchor_hash_count": int(body.get("source_anchor_hash_count", 0) or 0),
        "timeline_event_hashes": body.get("timeline_event_hashes", []),
        "timeline_event_count": int(body.get("timeline_event_count", 0) or 0),
        "ledger_event_hashes": body.get("ledger_event_hashes", []),
        "ledger_event_count": int(body.get("ledger_event_count", 0) or 0),
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "final_review_ledger_integrity_gate_hash": body.get("final_review_ledger_integrity_gate_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_integrity_gate_action(
    chain_issue_count: int,
    ledger_view: dict[str, Any],
    *,
    mismatched_hashes: list[str],
    skill_tag_consistent: bool,
    help_level_consistent: bool,
) -> str:
    recommendation = ledger_view.get("final_review_receipt_ledger_recommendation", "keep_final_ledger_open")
    if recommendation == "reject_final_ledger":
        return "return_to_final_review_receipt_ledger_or_handoff"
    if recommendation == "keep_final_ledger_open":
        return "keep_integrity_gate_open_and_continue_manual_review"
    if mismatched_hashes or not skill_tag_consistent or not help_level_consistent or recommendation == "request_hash_completion":
        return "reconcile_final_review_hash_chain_before_manual_integrity_review"
    if recommendation == "ready_for_manual_final_ledger_review":
        return "present_hash_only_integrity_gate_to_human_reviewer"
    return "keep_integrity_gate_open_and_continue_manual_review"


def integrity_gate_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "final_review_ledger_integrity_gate_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "final_review_ledger_integrity_gate_recommendation": summary.get(
            "final_review_ledger_integrity_gate_recommendation",
            "keep_integrity_gate_open",
        ),
        "final_review_ledger_integrity_gate_hash": summary.get("final_review_ledger_integrity_gate_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-final-review-ledger-integrity-gate")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
