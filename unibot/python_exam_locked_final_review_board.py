from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_final_manual_review_action_lock import safe_final_manual_review_console
from .python_exam_final_manual_review_console import safe_final_review_ledger_integrity_gate
from .python_exam_final_review_ledger_integrity_gate import safe_final_review_receipt_ledger
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level


PYTHON_EXAM_LOCKED_FINAL_REVIEW_BOARD_SCHEMA_VERSION = "unibot-python-exam-locked-final-review-board-v1"
PYTHON_EXAM_LOCKED_FINAL_REVIEW_BOARD_ENDPOINT = (
    "/api/unibot/course/python-exam-locked-final-review-board"
)

LOCKED_FINAL_REVIEW_BOARD_RECOMMENDATIONS = {
    "keep_final_board_open",
    "request_manual_reconciliation",
    "ready_for_human_final_board_review",
    "reject_final_board",
}


def build_python_exam_locked_final_review_board(
    *,
    python_exam_final_manual_review_action_lock: dict[str, Any] | None = None,
    python_exam_final_manual_review_console: dict[str, Any] | None = None,
    python_exam_final_review_ledger_integrity_gate: dict[str, Any] | None = None,
    python_exam_manual_final_review_receipt_ledger: dict[str, Any] | None = None,
    python_exam_draft_package_review_console: dict[str, Any] | None = None,
    python_exam_human_handoff_packet: dict[str, Any] | None = None,
    python_exam_full_local_rehearsal_pack: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    lock_view = safe_final_manual_review_action_lock(
        python_exam_final_manual_review_action_lock
        if isinstance(python_exam_final_manual_review_action_lock, dict)
        else {}
    )
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
    draft_view = safe_draft_package_review_console(
        python_exam_draft_package_review_console if isinstance(python_exam_draft_package_review_console, dict) else {}
    )
    handoff_view = safe_human_handoff_packet(
        python_exam_human_handoff_packet if isinstance(python_exam_human_handoff_packet, dict) else {}
    )
    rehearsal_view = safe_full_local_rehearsal_pack(
        python_exam_full_local_rehearsal_pack if isinstance(python_exam_full_local_rehearsal_pack, dict) else {}
    )
    selected = str(
        selected_skill_tag
        or lock_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
        or gate_view.get("selected_skill_tag", "")
        or ledger_view.get("selected_skill_tag", "")
        or rehearsal_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = locked_final_review_board_body(
        selected_skill_tag=selected,
        lock_view=lock_view,
        console_view=console_view,
        gate_view=gate_view,
        ledger_view=ledger_view,
        draft_view=draft_view,
        handoff_view=handoff_view,
        rehearsal_view=rehearsal_view,
    )
    summary = locked_final_review_board_summary(body)
    receipt = locked_final_review_board_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_LOCKED_FINAL_REVIEW_BOARD_SCHEMA_VERSION,
        "artifact_type": "python_exam_locked_final_review_board",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_locked_final_review_board_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Locked Final Review Board. It consumes only Final Manual Review Action Lock, "
            "Final Manual Review Console, Final Review Ledger Integrity Gate, Manual Final Review Receipt "
            "Ledger, Draft Package Review Console, Human Handoff Packet, and Full Local Rehearsal Pack "
            "metadata to present one final human review board. It shows lock, console, gate, ledger, draft, "
            "handoff, and rehearsal status, open hash issues, missing and mismatched hashes, receipt hashes, "
            "timeline and ledger event hashes, skill tag, help level, Source-Card anchors, accepted post-cycle "
            "hashes, and exactly one next safe human review action. It creates no export, writes nothing, "
            "starts no local action, archives nothing, submits nothing, authorizes nothing, and never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "locked_final_review_board_endpoint": PYTHON_EXAM_LOCKED_FINAL_REVIEW_BOARD_ENDPOINT,
        "selected_skill_tag": selected,
        "locked_final_review_board_summary": summary,
        "locked_final_review_board_body": body,
        "locked_final_review_board_recommendation": summary["locked_final_review_board_recommendation"],
        "locked_final_review_board_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Locked Final Review Board bleibt not_cleared."
        ),
        "next_actions": [
            f"Locked final review board recommendation: {summary['locked_final_review_board_recommendation']}.",
            f"Next safe human review action: {summary['next_safe_human_review_action']}.",
            "Keep export creation, archiving, submission, authorization, local writes, raw notebook work, scoring, and exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_final_manual_review_action_lock(lock: dict[str, Any]) -> dict[str, Any]:
    summary = (
        lock.get("final_manual_review_action_lock_summary", {})
        if isinstance(lock.get("final_manual_review_action_lock_summary"), dict)
        else {}
    )
    body = (
        lock.get("final_manual_review_action_lock_body", {})
        if isinstance(lock.get("final_manual_review_action_lock_body"), dict)
        else {}
    )
    receipt = (
        lock.get("final_manual_review_action_lock_receipt", {})
        if isinstance(lock.get("final_manual_review_action_lock_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(lock.get("status", "missing")),
        "selected_skill_tag": str(lock.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "final_manual_review_action_lock_recommendation": str(
            lock.get("final_manual_review_action_lock_recommendation")
            or summary.get("final_manual_review_action_lock_recommendation", "keep_action_locked")
        ),
        "final_manual_review_console_recommendation": str(
            summary.get("final_manual_review_console_recommendation")
            or body.get("final_manual_review_console_recommendation", "")
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
        "action_lock_receipt_hash": str(receipt.get("receipt_hash", "")),
        "final_manual_review_action_lock_hash": str(
            summary.get("final_manual_review_action_lock_hash")
            or body.get("final_manual_review_action_lock_hash", "")
        ),
        "final_manual_review_console_hash": str(
            summary.get("final_manual_review_console_hash") or body.get("final_manual_review_console_hash", "")
        ),
        "final_review_ledger_integrity_gate_hash": str(
            summary.get("final_review_ledger_integrity_gate_hash")
            or body.get("final_review_ledger_integrity_gate_hash", "")
        ),
        "final_review_receipt_ledger_hash": str(
            summary.get("final_review_receipt_ledger_hash") or body.get("final_review_receipt_ledger_hash", "")
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


def safe_draft_package_review_console(draft_console: dict[str, Any]) -> dict[str, Any]:
    summary = (
        draft_console.get("review_summary", {})
        if isinstance(draft_console.get("review_summary"), dict)
        else {}
    )
    integrity = (
        draft_console.get("package_integrity", {})
        if isinstance(draft_console.get("package_integrity"), dict)
        else {}
    )
    return {
        "status": str(draft_console.get("status", "missing")),
        "draft_review_status": str(summary.get("status", draft_console.get("status", "missing"))),
        "draft_present_status": str(summary.get("draft_present_status", draft_console.get("draft_present_status", ""))),
        "draft_package_hash": str(summary.get("draft_package_hash") or integrity.get("draft_package_hash", "")),
        "file_hash_integrity_status": str(summary.get("file_hash_integrity_status") or integrity.get("status", "")),
        "missing_required_hashes": [
            str(item) for item in (integrity.get("missing_file_hashes", []) or [])
        ][:12],
        "mismatched_hashes": [
            str(item) for item in (integrity.get("mismatched_file_hashes", []) or [])
        ][:12],
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_human_handoff_packet(handoff: dict[str, Any]) -> dict[str, Any]:
    summary = handoff.get("handoff_summary", {}) if isinstance(handoff.get("handoff_summary"), dict) else {}
    copy_view = handoff.get("copy_export_view", {}) if isinstance(handoff.get("copy_export_view"), dict) else {}
    return {
        "status": str(handoff.get("status", "missing")),
        "human_handoff_status": str(summary.get("status", handoff.get("status", "missing"))),
        "draft_package_id": str(summary.get("draft_package_id", "")),
        "file_hash_integrity_status": str(summary.get("file_hash_integrity_status", "")),
        "notebook_checkpoint_hash_present": bool(summary.get("notebook_checkpoint_hash_present", False)),
        "handoff_markdown_hash": str(copy_view.get("markdown_hash", "")),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_full_local_rehearsal_pack(rehearsal: dict[str, Any]) -> dict[str, Any]:
    summary = (
        rehearsal.get("rehearsal_summary", {})
        if isinstance(rehearsal.get("rehearsal_summary"), dict)
        else {}
    )
    source = (
        rehearsal.get("source_anchor_metadata", {})
        if isinstance(rehearsal.get("source_anchor_metadata"), dict)
        else {}
    )
    evidence = rehearsal.get("evidence_chain", {}) if isinstance(rehearsal.get("evidence_chain"), dict) else {}
    return {
        "status": str(rehearsal.get("status", "missing")),
        "rehearsal_status": str(summary.get("status", rehearsal.get("status", "missing"))),
        "selected_skill_tag": str(rehearsal.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "ready_step_count": int(summary.get("ready_step_count", 0) or 0),
        "attention_step_count": int(summary.get("attention_step_count", 0) or 0),
        "missing_step_count": int(summary.get("missing_step_count", 0) or 0),
        "human_handoff_status": str(summary.get("human_handoff_status", "")),
        "evidence_preview_status": str(summary.get("evidence_preview_status", "")),
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(source.get("source_anchor_count", 0) or 0),
        "human_handoff_markdown_hash": str(evidence.get("human_handoff_markdown_hash", "")),
        "evidence_preview_receipt_hash": str(evidence.get("evidence_preview_receipt_hash", "")),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "exam_deployment_status": "not_cleared",
    }


def locked_final_review_board_body(
    *,
    selected_skill_tag: str,
    lock_view: dict[str, Any],
    console_view: dict[str, Any],
    gate_view: dict[str, Any],
    ledger_view: dict[str, Any],
    draft_view: dict[str, Any],
    handoff_view: dict[str, Any],
    rehearsal_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(lock_view.get("receipt_hashes", {}) or {})
    if lock_view.get("action_lock_receipt_hash"):
        receipt_hashes["final_manual_review_action_lock_receipt_hash"] = lock_view.get("action_lock_receipt_hash", "")
    if console_view.get("console_receipt_hash"):
        receipt_hashes["final_manual_review_console_receipt_hash"] = console_view.get("console_receipt_hash", "")
    if gate_view.get("integrity_gate_receipt_hash"):
        receipt_hashes["integrity_gate_receipt_hash"] = gate_view.get("integrity_gate_receipt_hash", "")
    if ledger_view.get("final_review_receipt_ledger_receipt_hash"):
        receipt_hashes["final_review_receipt_ledger_receipt_hash"] = ledger_view.get(
            "final_review_receipt_ledger_receipt_hash",
            "",
        )
    if handoff_view.get("handoff_markdown_hash"):
        receipt_hashes["human_handoff_markdown_hash"] = handoff_view.get("handoff_markdown_hash", "")
    if rehearsal_view.get("evidence_preview_receipt_hash"):
        receipt_hashes["rehearsal_evidence_preview_receipt_hash"] = rehearsal_view.get(
            "evidence_preview_receipt_hash",
            "",
        )
    missing_hashes = sorted(
        {
            str(item)
            for item in (
                list(lock_view.get("missing_required_hashes", []) or [])
                + list(console_view.get("missing_required_hashes", []) or [])
                + list(gate_view.get("missing_required_hashes", []) or [])
                + list(ledger_view.get("missing_required_hashes", []) or [])
                + list(draft_view.get("missing_required_hashes", []) or [])
            )
            if str(item)
        }
    )[:12]
    mismatched_hashes = sorted(
        {
            str(item)
            for item in (
                list(lock_view.get("mismatched_hashes", []) or [])
                + list(console_view.get("mismatched_hashes", []) or [])
                + list(gate_view.get("mismatched_hashes", []) or [])
                + list(draft_view.get("mismatched_hashes", []) or [])
            )
            if str(item)
        }
    )[:12]
    accepted_hashes = (
        lock_view.get("accepted_post_cycle_hashes")
        or console_view.get("accepted_post_cycle_hashes")
        or gate_view.get("accepted_post_cycle_hashes")
        or ledger_view.get("accepted_post_cycle_hashes")
        or {}
    )
    timeline_event_hashes = (
        lock_view.get("timeline_event_hashes")
        or console_view.get("timeline_event_hashes")
        or gate_view.get("timeline_event_hashes")
        or ledger_view.get("timeline_event_hashes")
        or []
    )
    ledger_event_hashes = (
        lock_view.get("ledger_event_hashes")
        or console_view.get("ledger_event_hashes")
        or gate_view.get("ledger_event_hashes")
        or ledger_view.get("ledger_event_hashes")
        or []
    )
    source_card_ids = (
        lock_view.get("source_card_ids")
        or console_view.get("source_card_ids")
        or gate_view.get("source_card_ids")
        or ledger_view.get("source_card_ids")
        or rehearsal_view.get("source_card_ids")
        or []
    )
    integrity_issue_count = max(
        int(lock_view.get("integrity_issue_count", 0) or 0),
        int(console_view.get("integrity_issue_count", 0) or 0),
        int(gate_view.get("chain_issue_count", 0) or 0),
    )
    board_seed = {
        "lock_recommendation": lock_view.get("final_manual_review_action_lock_recommendation", ""),
        "console_recommendation": console_view.get("final_manual_review_console_recommendation", ""),
        "gate_recommendation": gate_view.get("final_review_ledger_integrity_gate_recommendation", ""),
        "ledger_recommendation": ledger_view.get("final_review_receipt_ledger_recommendation", ""),
        "draft_status": draft_view.get("draft_review_status", ""),
        "handoff_status": handoff_view.get("human_handoff_status", ""),
        "rehearsal_status": rehearsal_view.get("rehearsal_status", ""),
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
        "status": "python_exam_locked_final_review_board_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "final_manual_review_action_lock_recommendation": lock_view.get(
            "final_manual_review_action_lock_recommendation",
            "keep_action_locked",
        ),
        "final_manual_review_console_recommendation": console_view.get(
            "final_manual_review_console_recommendation",
            lock_view.get("final_manual_review_console_recommendation", ""),
        ),
        "final_review_ledger_integrity_gate_recommendation": gate_view.get(
            "final_review_ledger_integrity_gate_recommendation",
            lock_view.get("final_review_ledger_integrity_gate_recommendation", ""),
        ),
        "final_review_receipt_ledger_recommendation": ledger_view.get(
            "final_review_receipt_ledger_recommendation",
            lock_view.get("final_review_receipt_ledger_recommendation", ""),
        ),
        "draft_review_status": draft_view.get("draft_review_status", "missing"),
        "human_handoff_status": handoff_view.get("human_handoff_status", "missing"),
        "full_local_rehearsal_status": rehearsal_view.get("rehearsal_status", "missing"),
        "integrity_issue_count": integrity_issue_count,
        "missing_required_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": receipt_hashes,
        "receipt_hash_count": len([value for value in receipt_hashes.values() if value]),
        "timeline_event_hashes": [str(item) for item in (timeline_event_hashes or [])][:12],
        "timeline_event_count": int(lock_view.get("timeline_event_count", console_view.get("timeline_event_count", 0)) or 0),
        "ledger_event_hashes": [str(item) for item in (ledger_event_hashes or [])][:12],
        "ledger_event_count": int(lock_view.get("ledger_event_count", console_view.get("ledger_event_count", 0)) or 0),
        "accepted_post_cycle_hashes": accepted_hashes,
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(
            lock_view.get("source_anchor_hash_count")
            or console_view.get("source_anchor_hash_count")
            or gate_view.get("source_anchor_hash_count")
            or ledger_view.get("source_anchor_hash_count")
            or rehearsal_view.get("source_anchor_hash_count")
            or 0
        ),
        "help_level": safe_help_level(
            str(lock_view.get("help_level") or console_view.get("help_level") or gate_view.get("help_level") or "A2")
        ),
        "final_manual_review_action_lock_hash": lock_view.get("final_manual_review_action_lock_hash", ""),
        "final_manual_review_console_hash": lock_view.get("final_manual_review_console_hash")
        or console_view.get("final_manual_review_console_hash", ""),
        "final_review_ledger_integrity_gate_hash": lock_view.get("final_review_ledger_integrity_gate_hash")
        or gate_view.get("final_review_ledger_integrity_gate_hash", ""),
        "final_review_receipt_ledger_hash": lock_view.get("final_review_receipt_ledger_hash")
        or ledger_view.get("final_review_receipt_ledger_hash", ""),
        "draft_package_hash": draft_view.get("draft_package_hash", ""),
        "human_handoff_markdown_hash": handoff_view.get("handoff_markdown_hash", "")
        or rehearsal_view.get("human_handoff_markdown_hash", ""),
        "locked_final_review_board_hash": sha256_text(
            json.dumps(board_seed, sort_keys=True, ensure_ascii=False)
        ),
        "next_safe_human_review_action": next_safe_locked_board_action(lock_view, draft_view, handoff_view, rehearsal_view),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def locked_final_review_board_summary(body: dict[str, Any]) -> dict[str, Any]:
    lock_recommendation = body.get("final_manual_review_action_lock_recommendation", "keep_action_locked")
    console_recommendation = body.get("final_manual_review_console_recommendation", "")
    gate_recommendation = body.get("final_review_ledger_integrity_gate_recommendation", "")
    ledger_recommendation = body.get("final_review_receipt_ledger_recommendation", "")
    draft_status = body.get("draft_review_status", "missing")
    handoff_status = body.get("human_handoff_status", "missing")
    rehearsal_status = body.get("full_local_rehearsal_status", "missing")
    integrity_issue_count = int(body.get("integrity_issue_count", 0) or 0)
    missing_hashes = body.get("missing_required_hashes", []) or []
    mismatched_hashes = body.get("mismatched_hashes", []) or []
    ready_inputs = (
        lock_recommendation == "ready_for_manual_action_review"
        and console_recommendation == "ready_for_manual_console_review"
        and gate_recommendation == "ready_for_manual_integrity_review"
        and ledger_recommendation == "ready_for_manual_final_ledger_review"
        and draft_status == "python_exam_draft_package_review_console_ready"
        and handoff_status == "python_exam_human_handoff_packet_ready"
        and rehearsal_status == "python_exam_full_local_rehearsal_pack_ready"
        and integrity_issue_count == 0
        and not missing_hashes
        and not mismatched_hashes
        and bool(body.get("receipt_hash_count", 0))
    )
    if lock_recommendation == "reject_action_path":
        recommendation = "reject_final_board"
        reason = "final_action_path_rejected"
    elif ready_inputs:
        recommendation = "ready_for_human_final_board_review"
        reason = "locked_final_board_ready_for_human_review"
    elif lock_recommendation == "request_manual_reconciliation" or mismatched_hashes:
        recommendation = "request_manual_reconciliation"
        reason = "manual_reconciliation_required_before_final_board_review"
    else:
        recommendation = "keep_final_board_open"
        reason = "final_board_still_open"
    return {
        "status": "python_exam_locked_final_review_board_ready",
        "locked_final_review_board_recommendation": recommendation,
        "locked_final_review_board_reason": reason,
        "allowed_locked_final_review_board_recommendations": sorted(
            LOCKED_FINAL_REVIEW_BOARD_RECOMMENDATIONS
        ),
        "final_manual_review_action_lock_recommendation": lock_recommendation,
        "final_manual_review_console_recommendation": console_recommendation,
        "final_review_ledger_integrity_gate_recommendation": gate_recommendation,
        "final_review_receipt_ledger_recommendation": ledger_recommendation,
        "draft_review_status": draft_status,
        "human_handoff_status": handoff_status,
        "full_local_rehearsal_status": rehearsal_status,
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
        "final_manual_review_action_lock_hash": body.get("final_manual_review_action_lock_hash", ""),
        "final_manual_review_console_hash": body.get("final_manual_review_console_hash", ""),
        "final_review_ledger_integrity_gate_hash": body.get("final_review_ledger_integrity_gate_hash", ""),
        "final_review_receipt_ledger_hash": body.get("final_review_receipt_ledger_hash", ""),
        "draft_package_hash": body.get("draft_package_hash", ""),
        "human_handoff_markdown_hash": body.get("human_handoff_markdown_hash", ""),
        "locked_final_review_board_hash": body.get("locked_final_review_board_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def next_safe_locked_board_action(
    lock_view: dict[str, Any],
    draft_view: dict[str, Any],
    handoff_view: dict[str, Any],
    rehearsal_view: dict[str, Any],
) -> str:
    lock_recommendation = lock_view.get("final_manual_review_action_lock_recommendation", "keep_action_locked")
    if lock_recommendation == "reject_action_path":
        return "return_to_action_lock_or_final_review_console"
    if lock_recommendation == "request_manual_reconciliation":
        return "reconcile_locked_final_review_hashes_before_board_review"
    if (
        lock_recommendation == "ready_for_manual_action_review"
        and draft_view.get("draft_review_status") == "python_exam_draft_package_review_console_ready"
        and handoff_view.get("human_handoff_status") == "python_exam_human_handoff_packet_ready"
        and rehearsal_view.get("rehearsal_status") == "python_exam_full_local_rehearsal_pack_ready"
    ):
        return "present_locked_final_review_board_to_human_reviewer"
    return "keep_final_board_open_and_continue_manual_review"


def locked_final_review_board_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "locked_final_review_board_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "locked_final_review_board_recommendation": summary.get(
            "locked_final_review_board_recommendation",
            "keep_final_board_open",
        ),
        "locked_final_review_board_hash": summary.get("locked_final_review_board_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-locked-final-review-board")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
