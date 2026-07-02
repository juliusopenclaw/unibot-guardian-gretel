from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_final_manual_review_console import safe_final_review_ledger_integrity_gate
from .python_exam_final_review_ledger_integrity_gate import safe_final_review_receipt_ledger
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level


PYTHON_EXAM_FINAL_MANUAL_REVIEW_ACTION_LOCK_SCHEMA_VERSION = (
    "unibot-python-exam-final-manual-review-action-lock-v1"
)
PYTHON_EXAM_FINAL_MANUAL_REVIEW_ACTION_LOCK_ENDPOINT = (
    "/api/unibot/course/python-exam-final-manual-review-action-lock"
)

FINAL_MANUAL_REVIEW_ACTION_LOCK_RECOMMENDATIONS = {
    "keep_action_locked",
    "request_manual_reconciliation",
    "ready_for_manual_action_review",
    "reject_action_path",
}


def build_python_exam_final_manual_review_action_lock(
    *,
    python_exam_final_manual_review_console: dict[str, Any] | None = None,
    python_exam_final_review_ledger_integrity_gate: dict[str, Any] | None = None,
    python_exam_manual_final_review_receipt_ledger: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    console_view = safe_final_manual_review_console(
        python_exam_final_manual_review_console
        if isinstance(python_exam_final_manual_review_console, dict)
        else {}
    )
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
    selected = str(
        selected_skill_tag
        or console_view.get("selected_skill_tag", "")
        or gate_view.get("selected_skill_tag", "")
        or ledger_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = final_manual_review_action_lock_body(
        selected_skill_tag=selected,
        console_view=console_view,
        gate_view=gate_view,
        ledger_view=ledger_view,
    )
    summary = final_manual_review_action_lock_summary(body)
    receipt = final_manual_review_action_lock_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_FINAL_MANUAL_REVIEW_ACTION_LOCK_SCHEMA_VERSION,
        "artifact_type": "python_exam_final_manual_review_action_lock",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_final_manual_review_action_lock_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Final Manual Review Action Lock. It consumes only Final Manual Review Console, "
            "Final Review Ledger Integrity Gate, and Manual Final Review Receipt Ledger metadata to keep "
            "any later export, archive, or submission proximity visibly locked until a human review path is "
            "hash-consistent. It checks console recommendation, integrity-gate recommendation, open integrity "
            "issues, missing and mismatched hashes, receipt hashes, timeline and ledger event hashes, skill "
            "tag, help level, Source-Card anchors, and the next safe human review action. It creates no export, "
            "writes nothing, starts no local action, archives nothing, submits nothing, authorizes nothing, and "
            "never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "final_manual_review_action_lock_endpoint": PYTHON_EXAM_FINAL_MANUAL_REVIEW_ACTION_LOCK_ENDPOINT,
        "selected_skill_tag": selected,
        "final_manual_review_action_lock_summary": summary,
        "final_manual_review_action_lock_body": body,
        "final_manual_review_action_lock_recommendation": summary[
            "final_manual_review_action_lock_recommendation"
        ],
        "final_manual_review_action_lock_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Final Manual Review Action Lock bleibt not_cleared."
        ),
        "next_actions": [
            f"Final manual review action lock recommendation: {summary['final_manual_review_action_lock_recommendation']}.",
            f"Next safe human review action: {summary['next_safe_human_review_action']}.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_final_manual_review_console(console: dict[str, Any]) -> dict[str, Any]:
    summary = (
        console.get("final_manual_review_console_summary", {})
        if isinstance(console.get("final_manual_review_console_summary"), dict)
        else {}
    )
    body = (
        console.get("final_manual_review_console_body", {})
        if isinstance(console.get("final_manual_review_console_body"), dict)
        else {}
    )
    receipt = (
        console.get("final_manual_review_console_receipt", {})
        if isinstance(console.get("final_manual_review_console_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(console.get("status", "missing")),
        "selected_skill_tag": str(console.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "final_manual_review_console_recommendation": str(
            console.get("final_manual_review_console_recommendation")
            or summary.get("final_manual_review_console_recommendation", "keep_final_console_open")
        ),
        "final_review_ledger_integrity_gate_recommendation": str(
            summary.get("final_review_ledger_integrity_gate_recommendation")
            or body.get("final_review_ledger_integrity_gate_recommendation", "")
        ),
        "final_review_receipt_ledger_recommendation": str(
            summary.get("final_review_receipt_ledger_recommendation")
            or body.get("final_review_receipt_ledger_recommendation", "")
        ),
        "integrity_issue_count": int(summary.get("integrity_issue_count", body.get("integrity_issue_count", 0)) or 0),
        "missing_required_hashes": [
            str(item)
            for item in (summary.get("missing_required_hashes") or body.get("missing_required_hashes", []) or [])
        ][:12],
        "mismatched_hashes": [
            str(item)
            for item in (summary.get("mismatched_hashes") or body.get("mismatched_hashes", []) or [])
        ][:12],
        "receipt_hashes": {str(key): str(value) for key, value in receipt_hashes.items()},
        "console_receipt_hash": str(receipt.get("receipt_hash", "")),
        "final_manual_review_console_hash": str(
            summary.get("final_manual_review_console_hash") or body.get("final_manual_review_console_hash", "")
        ),
        "accepted_post_cycle_hashes": {str(key): str(value) for key, value in accepted_hashes.items()},
        "help_level": safe_help_level(str(summary.get("help_level") or body.get("help_level", "A2"))),
        "source_card_ids": [
            str(item)
            for item in (summary.get("source_card_ids") or body.get("source_card_ids", []) or [])
        ][:8],
        "source_anchor_hash_count": int(
            summary.get("source_anchor_hash_count", body.get("source_anchor_hash_count", 0)) or 0
        ),
        "timeline_event_hashes": [
            str(item)
            for item in (summary.get("timeline_event_hashes") or body.get("timeline_event_hashes", []) or [])
        ][:12],
        "timeline_event_count": int(summary.get("timeline_event_count", body.get("timeline_event_count", 0)) or 0),
        "ledger_event_hashes": [
            str(item)
            for item in (summary.get("ledger_event_hashes") or body.get("ledger_event_hashes", []) or [])
        ][:12],
        "ledger_event_count": int(summary.get("ledger_event_count", body.get("ledger_event_count", 0)) or 0),
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


def final_manual_review_action_lock_body(
    *,
    selected_skill_tag: str,
    console_view: dict[str, Any],
    gate_view: dict[str, Any],
    ledger_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(console_view.get("receipt_hashes", {}) or {})
    if console_view.get("console_receipt_hash"):
        receipt_hashes["final_manual_review_console_receipt_hash"] = console_view.get("console_receipt_hash", "")
    if gate_view.get("integrity_gate_receipt_hash"):
        receipt_hashes["integrity_gate_receipt_hash"] = gate_view.get("integrity_gate_receipt_hash", "")
    if ledger_view.get("final_review_receipt_ledger_receipt_hash"):
        receipt_hashes["final_review_receipt_ledger_receipt_hash"] = ledger_view.get(
            "final_review_receipt_ledger_receipt_hash",
            "",
        )
    missing_hashes = sorted(
        {
            str(item)
            for item in (
                list(console_view.get("missing_required_hashes", []) or [])
                + list(gate_view.get("missing_required_hashes", []) or [])
                + list(ledger_view.get("missing_required_hashes", []) or [])
            )
            if str(item)
        }
    )[:12]
    mismatched_hashes = sorted(
        {
            str(item)
            for item in (
                list(console_view.get("mismatched_hashes", []) or [])
                + list(gate_view.get("mismatched_hashes", []) or [])
            )
            if str(item)
        }
    )[:12]
    accepted_hashes = (
        console_view.get("accepted_post_cycle_hashes")
        or gate_view.get("accepted_post_cycle_hashes")
        or ledger_view.get("accepted_post_cycle_hashes")
        or {}
    )
    timeline_event_hashes = (
        console_view.get("timeline_event_hashes")
        or gate_view.get("timeline_event_hashes")
        or ledger_view.get("timeline_event_hashes")
        or []
    )
    ledger_event_hashes = (
        console_view.get("ledger_event_hashes")
        or gate_view.get("ledger_event_hashes")
        or ledger_view.get("ledger_event_hashes")
        or []
    )
    source_card_ids = (
        console_view.get("source_card_ids")
        or gate_view.get("source_card_ids")
        or ledger_view.get("source_card_ids")
        or []
    )
    integrity_issue_count = max(
        int(console_view.get("integrity_issue_count", 0) or 0),
        int(gate_view.get("chain_issue_count", 0) or 0),
    )
    lock_seed = {
        "console_recommendation": console_view.get("final_manual_review_console_recommendation", ""),
        "gate_recommendation": gate_view.get("final_review_ledger_integrity_gate_recommendation", ""),
        "ledger_recommendation": ledger_view.get("final_review_receipt_ledger_recommendation", ""),
        "integrity_issue_count": integrity_issue_count,
        "missing_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": receipt_hashes,
        "timeline_event_hashes": timeline_event_hashes,
        "ledger_event_hashes": ledger_event_hashes,
        "selected_skill_tag": selected_skill_tag,
        "exam_deployment_status": "not_cleared",
    }
    return {
        "status": "python_exam_final_manual_review_action_lock_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "final_manual_review_console_recommendation": console_view.get(
            "final_manual_review_console_recommendation",
            "keep_final_console_open",
        ),
        "final_review_ledger_integrity_gate_recommendation": gate_view.get(
            "final_review_ledger_integrity_gate_recommendation",
            console_view.get("final_review_ledger_integrity_gate_recommendation", ""),
        ),
        "final_review_receipt_ledger_recommendation": ledger_view.get(
            "final_review_receipt_ledger_recommendation",
            console_view.get("final_review_receipt_ledger_recommendation", ""),
        ),
        "integrity_issue_count": integrity_issue_count,
        "missing_required_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": receipt_hashes,
        "receipt_hash_count": len([value for value in receipt_hashes.values() if value]),
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(
            console_view.get("timeline_event_count", gate_view.get("timeline_event_count", 0)) or 0
        ),
        "ledger_event_hashes": [str(item) for item in (ledger_event_hashes or [])][:12],
        "ledger_event_count": int(
            console_view.get("ledger_event_count", gate_view.get("ledger_event_count", 0)) or 0
        ),
        "accepted_post_cycle_hashes": accepted_hashes,
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(
            console_view.get("source_anchor_hash_count", gate_view.get("source_anchor_hash_count", 0)) or 0
        ),
        "help_level": safe_help_level(
            str(console_view.get("help_level") or gate_view.get("help_level") or ledger_view.get("help_level") or "A2")
        ),
        "next_safe_human_review_action": next_safe_action_lock_action(console_view, gate_view, ledger_view),
        "final_manual_review_console_hash": console_view.get("final_manual_review_console_hash", ""),
        "final_review_ledger_integrity_gate_hash": gate_view.get("final_review_ledger_integrity_gate_hash", ""),
        "final_review_receipt_ledger_hash": ledger_view.get("final_review_receipt_ledger_hash", ""),
        "final_manual_review_action_lock_hash": sha256_text(
            json.dumps(lock_seed, sort_keys=True, ensure_ascii=False)
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


def final_manual_review_action_lock_summary(body: dict[str, Any]) -> dict[str, Any]:
    console_recommendation = body.get("final_manual_review_console_recommendation", "keep_final_console_open")
    gate_recommendation = body.get("final_review_ledger_integrity_gate_recommendation", "keep_integrity_gate_open")
    ledger_recommendation = body.get("final_review_receipt_ledger_recommendation", "keep_final_ledger_open")
    integrity_issue_count = int(body.get("integrity_issue_count", 0) or 0)
    missing_hashes = body.get("missing_required_hashes", []) or []
    mismatched_hashes = body.get("mismatched_hashes", []) or []
    has_reconciliation_need = (
        console_recommendation == "request_integrity_reconciliation"
        or gate_recommendation == "request_hash_reconciliation"
        or ledger_recommendation == "request_hash_completion"
        or bool(mismatched_hashes)
    )
    ready_inputs = (
        console_recommendation == "ready_for_manual_console_review"
        and gate_recommendation == "ready_for_manual_integrity_review"
        and ledger_recommendation == "ready_for_manual_final_ledger_review"
        and integrity_issue_count == 0
        and not missing_hashes
        and not mismatched_hashes
        and bool(body.get("receipt_hash_count", 0))
        and bool(body.get("final_manual_review_console_hash", ""))
        and bool(body.get("final_review_ledger_integrity_gate_hash", ""))
        and bool(body.get("final_review_receipt_ledger_hash", ""))
    )
    if (
        console_recommendation == "reject_final_console"
        or gate_recommendation == "reject_integrity_chain"
        or ledger_recommendation == "reject_final_ledger"
    ):
        recommendation = "reject_action_path"
        reason = "final_review_path_rejected"
    elif ready_inputs:
        recommendation = "ready_for_manual_action_review"
        reason = "final_action_lock_ready_for_human_review"
    elif has_reconciliation_need:
        recommendation = "request_manual_reconciliation"
        reason = "manual_hash_reconciliation_required_before_action_review"
    else:
        recommendation = "keep_action_locked"
        reason = "final_action_path_still_locked"
    return {
        "status": "python_exam_final_manual_review_action_lock_ready",
        "final_manual_review_action_lock_recommendation": recommendation,
        "final_manual_review_action_lock_reason": reason,
        "allowed_final_manual_review_action_lock_recommendations": sorted(
            FINAL_MANUAL_REVIEW_ACTION_LOCK_RECOMMENDATIONS
        ),
        "final_manual_review_console_recommendation": console_recommendation,
        "final_review_ledger_integrity_gate_recommendation": gate_recommendation,
        "final_review_receipt_ledger_recommendation": ledger_recommendation,
        "integrity_issue_count": integrity_issue_count,
        "missing_required_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": body.get("receipt_hashes", {}),
        "receipt_hash_count": int(body.get("receipt_hash_count", 0) or 0),
        "timeline_event_hashes": body.get("timeline_event_hashes", []),
        "timeline_event_count": int(body.get("timeline_event_count", 0) or 0),
        "ledger_event_hashes": body.get("ledger_event_hashes", []),
        "ledger_event_count": int(body.get("ledger_event_count", 0) or 0),
        "accepted_post_cycle_hashes": body.get("accepted_post_cycle_hashes", {}),
        "source_card_ids": body.get("source_card_ids", []),
        "source_anchor_hash_count": int(body.get("source_anchor_hash_count", 0) or 0),
        "selected_skill_tag": body.get("selected_skill_tag", "general_python"),
        "help_level": safe_help_level(str(body.get("help_level", "A2"))),
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "final_manual_review_console_hash": body.get("final_manual_review_console_hash", ""),
        "final_review_ledger_integrity_gate_hash": body.get("final_review_ledger_integrity_gate_hash", ""),
        "final_review_receipt_ledger_hash": body.get("final_review_receipt_ledger_hash", ""),
        "final_manual_review_action_lock_hash": body.get("final_manual_review_action_lock_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_safe_action_lock_action(
    console_view: dict[str, Any],
    gate_view: dict[str, Any],
    ledger_view: dict[str, Any],
) -> str:
    console_recommendation = console_view.get("final_manual_review_console_recommendation", "keep_final_console_open")
    gate_recommendation = gate_view.get("final_review_ledger_integrity_gate_recommendation", "keep_integrity_gate_open")
    ledger_recommendation = ledger_view.get("final_review_receipt_ledger_recommendation", "keep_final_ledger_open")
    if (
        console_recommendation == "reject_final_console"
        or gate_recommendation == "reject_integrity_chain"
        or ledger_recommendation == "reject_final_ledger"
    ):
        return "return_to_final_console_or_integrity_gate"
    if console_recommendation == "ready_for_manual_console_review" and gate_recommendation == "ready_for_manual_integrity_review":
        return "present_locked_hash_only_action_review_to_human"
    if console_recommendation == "request_integrity_reconciliation" or gate_recommendation == "request_hash_reconciliation":
        return "reconcile_final_review_hashes_before_action_review"
    return "keep_action_locked_and_continue_manual_review"


def final_manual_review_action_lock_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "final_manual_review_action_lock_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "final_manual_review_action_lock_recommendation": summary.get(
            "final_manual_review_action_lock_recommendation",
            "keep_action_locked",
        ),
        "final_manual_review_action_lock_hash": summary.get("final_manual_review_action_lock_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-final-manual-review-action-lock")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
