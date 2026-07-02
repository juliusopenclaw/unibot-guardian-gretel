from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_locked_final_review_board import (
    safe_final_manual_review_action_lock,
    safe_full_local_rehearsal_pack,
)


PYTHON_EXAM_LOCKED_FINAL_REVIEW_GAP_RESOLVER_SCHEMA_VERSION = (
    "unibot-python-exam-locked-final-review-gap-resolver-v1"
)
PYTHON_EXAM_LOCKED_FINAL_REVIEW_GAP_RESOLVER_ENDPOINT = (
    "/api/unibot/course/python-exam-locked-final-review-gap-resolver"
)

LOCKED_FINAL_REVIEW_GAP_RESOLVER_RECOMMENDATIONS = {
    "keep_gap_resolver_open",
    "request_manual_reconciliation",
    "ready_for_manual_rehearsal_recheck",
    "reject_gap_resolution",
}


def build_python_exam_locked_final_review_gap_resolver(
    *,
    python_exam_locked_final_review_board: dict[str, Any] | None = None,
    python_exam_final_manual_review_action_lock: dict[str, Any] | None = None,
    python_exam_full_local_rehearsal_pack: dict[str, Any] | None = None,
    python_exam_rehearsal_playback_gap_coach: dict[str, Any] | None = None,
    python_exam_guided_loop_control_surface: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    board_view = safe_locked_final_review_board(
        python_exam_locked_final_review_board if isinstance(python_exam_locked_final_review_board, dict) else {}
    )
    lock_view = safe_final_manual_review_action_lock(
        python_exam_final_manual_review_action_lock
        if isinstance(python_exam_final_manual_review_action_lock, dict)
        else {}
    )
    rehearsal_view = safe_full_local_rehearsal_pack(
        python_exam_full_local_rehearsal_pack if isinstance(python_exam_full_local_rehearsal_pack, dict) else {}
    )
    gap_coach_view = safe_rehearsal_playback_gap_coach(
        python_exam_rehearsal_playback_gap_coach
        if isinstance(python_exam_rehearsal_playback_gap_coach, dict)
        else {}
    )
    control_view = safe_guided_loop_control_surface(
        python_exam_guided_loop_control_surface if isinstance(python_exam_guided_loop_control_surface, dict) else {}
    )
    selected = str(
        selected_skill_tag
        or board_view.get("selected_skill_tag", "")
        or lock_view.get("selected_skill_tag", "")
        or rehearsal_view.get("selected_skill_tag", "")
        or gap_coach_view.get("selected_skill_tag", "")
        or control_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    body = locked_final_review_gap_resolver_body(
        selected_skill_tag=selected,
        board_view=board_view,
        lock_view=lock_view,
        rehearsal_view=rehearsal_view,
        gap_coach_view=gap_coach_view,
        control_view=control_view,
    )
    summary = locked_final_review_gap_resolver_summary(body)
    receipt = locked_final_review_gap_resolver_receipt(summary)
    payload = {
        "schema_version": PYTHON_EXAM_LOCKED_FINAL_REVIEW_GAP_RESOLVER_SCHEMA_VERSION,
        "artifact_type": "python_exam_locked_final_review_gap_resolver",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_locked_final_review_gap_resolver_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Locked Final Review Gap Resolver. It consumes only Locked Final Review Board, "
            "Final Manual Review Action Lock, Full Local Rehearsal Pack, Rehearsal Playback Gap Coach, and "
            "Guided Loop Control Surface metadata to translate open board issues into one safe human follow-up "
            "card. It shows board recommendation, lock recommendation, open hash issues, missing and mismatched "
            "hashes, affected review layer, receipt hashes, timeline and ledger event hashes, skill tag, help "
            "level, Source-Card anchors, rehearsal and gap-coach status, and one prioritized non-executing "
            "repair card. It creates no export, writes nothing, starts no local action, archives nothing, "
            "submits nothing, authorizes nothing, and never returns raw queries, course raw text, notebook code, "
            "local paths, values, solutions, final interpretations, scores, rankings, grades, proctoring, AI "
            "detection, automatic grading, or exam clearance claims."
        ),
        "locked_final_review_gap_resolver_endpoint": PYTHON_EXAM_LOCKED_FINAL_REVIEW_GAP_RESOLVER_ENDPOINT,
        "selected_skill_tag": selected,
        "locked_final_review_gap_resolver_summary": summary,
        "locked_final_review_gap_resolver_body": body,
        "locked_final_review_gap_resolver_recommendation": summary[
            "locked_final_review_gap_resolver_recommendation"
        ],
        "prioritized_repair_card": body["prioritized_repair_card"],
        "locked_final_review_gap_resolver_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Locked Final Review Gap Resolver bleibt not_cleared."
        ),
        "next_actions": [
            f"Locked final review gap resolver recommendation: {summary['locked_final_review_gap_resolver_recommendation']}.",
            f"Next safe human review action: {summary['next_safe_human_review_action']}.",
            "Use the repair card as a human review prompt only; keep every write/export/archive/submission outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_locked_final_review_board(board: dict[str, Any]) -> dict[str, Any]:
    summary = (
        board.get("locked_final_review_board_summary", {})
        if isinstance(board.get("locked_final_review_board_summary"), dict)
        else {}
    )
    body = (
        board.get("locked_final_review_board_body", {})
        if isinstance(board.get("locked_final_review_board_body"), dict)
        else {}
    )
    receipt = (
        board.get("locked_final_review_board_receipt", {})
        if isinstance(board.get("locked_final_review_board_receipt"), dict)
        else {}
    )
    receipt_hashes = summary.get("receipt_hashes") or body.get("receipt_hashes", {})
    if not isinstance(receipt_hashes, dict):
        receipt_hashes = {}
    accepted_hashes = summary.get("accepted_post_cycle_hashes") or body.get("accepted_post_cycle_hashes", {})
    if not isinstance(accepted_hashes, dict):
        accepted_hashes = {}
    return {
        "status": str(board.get("status", "missing")),
        "selected_skill_tag": str(board.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "locked_final_review_board_recommendation": str(
            board.get("locked_final_review_board_recommendation")
            or summary.get("locked_final_review_board_recommendation", "keep_final_board_open")
        ),
        "final_manual_review_action_lock_recommendation": str(
            summary.get("final_manual_review_action_lock_recommendation")
            or body.get("final_manual_review_action_lock_recommendation", "")
        ),
        "draft_review_status": str(summary.get("draft_review_status") or body.get("draft_review_status", "")),
        "human_handoff_status": str(summary.get("human_handoff_status") or body.get("human_handoff_status", "")),
        "full_local_rehearsal_status": str(
            summary.get("full_local_rehearsal_status") or body.get("full_local_rehearsal_status", "")
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
        "board_receipt_hash": str(receipt.get("receipt_hash", "")),
        "locked_final_review_board_hash": str(
            summary.get("locked_final_review_board_hash") or body.get("locked_final_review_board_hash", "")
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
        "exam_deployment_status": "not_cleared",
    }


def safe_rehearsal_playback_gap_coach(coach: dict[str, Any]) -> dict[str, Any]:
    summary = coach.get("playback_summary", {}) if isinstance(coach.get("playback_summary"), dict) else {}
    gaps = coach.get("gap_profile", {}) if isinstance(coach.get("gap_profile"), dict) else {}
    receipt = coach.get("playback_receipt", {}) if isinstance(coach.get("playback_receipt"), dict) else {}
    source = coach.get("source_anchor_metadata", {}) if isinstance(coach.get("source_anchor_metadata"), dict) else {}
    help_status = coach.get("a0_a2_help_status", {}) if isinstance(coach.get("a0_a2_help_status"), dict) else {}
    evidence = coach.get("evidence_playback", {}) if isinstance(coach.get("evidence_playback"), dict) else {}
    return {
        "status": str(coach.get("status", "missing")),
        "selected_skill_tag": str(coach.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "next_safe_action_key": str(coach.get("next_safe_action_key") or summary.get("next_safe_action_key", "")),
        "gap_coach_status": str(coach.get("status", "missing")),
        "missing_or_attention_count": int(gaps.get("missing_or_attention_count", 0) or 0),
        "operator_confirmation_gap": bool(gaps.get("operator_confirmation_gap", False)),
        "source_gap": bool(gaps.get("source_gap", False)),
        "notebook_checkpoint_gap": bool(gaps.get("notebook_checkpoint_gap", False)),
        "a0_a2_profile_gap": bool(gaps.get("a0_a2_profile_gap", False)),
        "ready_for_human_review_packet": bool(gaps.get("ready_for_human_review_packet", False)),
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(source.get("source_anchor_count", 0) or 0),
        "help_level": "A2" if str(help_status.get("status", "")) == "a0_a2_only" else "A2",
        "evidence_preview_status": str(evidence.get("evidence_preview_status", "")),
        "human_handoff_status": str(evidence.get("human_handoff_status", "")),
        "human_handoff_markdown_hash": str(evidence.get("human_handoff_markdown_hash", "")),
        "gap_coach_receipt_hash": str(receipt.get("receipt_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_guided_loop_control_surface(surface: dict[str, Any]) -> dict[str, Any]:
    summary = surface.get("control_summary", {}) if isinstance(surface.get("control_summary"), dict) else {}
    receipt = surface.get("surface_receipt", {}) if isinstance(surface.get("surface_receipt"), dict) else {}
    source = surface.get("source_anchor_status", {}) if isinstance(surface.get("source_anchor_status"), dict) else {}
    checkpoint = surface.get("notebook_checkpoint_status", {}) if isinstance(surface.get("notebook_checkpoint_status"), dict) else {}
    confirmations = (
        surface.get("operator_confirmation_status", {})
        if isinstance(surface.get("operator_confirmation_status"), dict)
        else {}
    )
    return {
        "status": str(surface.get("status", "missing")),
        "selected_skill_tag": str(surface.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "guided_loop_control_status": str(surface.get("status", "missing")),
        "action_key": str(summary.get("action_key", "")),
        "next_safe_click": str(summary.get("next_safe_click", "")),
        "prefill_hash": str(summary.get("prefill_hash", "")),
        "source_anchor_hash_count": int(source.get("source_anchor_count", 0) or 0),
        "checkpoint_hash_count": int(checkpoint.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(confirmations.get("open_operator_confirmation_count", 0) or 0),
        "surface_receipt_hash": str(receipt.get("receipt_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def locked_final_review_gap_resolver_body(
    *,
    selected_skill_tag: str,
    board_view: dict[str, Any],
    lock_view: dict[str, Any],
    rehearsal_view: dict[str, Any],
    gap_coach_view: dict[str, Any],
    control_view: dict[str, Any],
) -> dict[str, Any]:
    receipt_hashes = dict(board_view.get("receipt_hashes", {}) or {})
    for key, value in {
        "locked_final_review_board_receipt_hash": board_view.get("board_receipt_hash", ""),
        "gap_coach_receipt_hash": gap_coach_view.get("gap_coach_receipt_hash", ""),
        "guided_loop_control_surface_receipt_hash": control_view.get("surface_receipt_hash", ""),
    }.items():
        if value:
            receipt_hashes[key] = value
    missing_hashes = [str(item) for item in (board_view.get("missing_required_hashes", []) or [])][:12]
    mismatched_hashes = [str(item) for item in (board_view.get("mismatched_hashes", []) or [])][:12]
    affected_layer = affected_review_layer(board_view, gap_coach_view, control_view)
    repair_card = prioritized_repair_card(
        affected_layer=affected_layer,
        board_view=board_view,
        lock_view=lock_view,
        rehearsal_view=rehearsal_view,
        gap_coach_view=gap_coach_view,
        control_view=control_view,
        missing_hashes=missing_hashes,
        mismatched_hashes=mismatched_hashes,
    )
    timeline_event_hashes = board_view.get("timeline_event_hashes", []) or []
    ledger_event_hashes = board_view.get("ledger_event_hashes", []) or []
    source_card_ids = board_view.get("source_card_ids") or gap_coach_view.get("source_card_ids") or rehearsal_view.get("source_card_ids") or []
    resolver_seed = {
        "board_recommendation": board_view.get("locked_final_review_board_recommendation", ""),
        "lock_recommendation": lock_view.get("final_manual_review_action_lock_recommendation", ""),
        "integrity_issue_count": board_view.get("integrity_issue_count", 0),
        "missing_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "affected_layer": affected_layer,
        "repair_card": repair_card,
        "receipt_hashes": receipt_hashes,
        "selected_skill_tag": selected_skill_tag,
        "exam_deployment_status": "not_cleared",
    }
    return {
        "status": "python_exam_locked_final_review_gap_resolver_body_ready",
        "selected_skill_tag": selected_skill_tag,
        "locked_final_review_board_recommendation": board_view.get(
            "locked_final_review_board_recommendation",
            "keep_final_board_open",
        ),
        "final_manual_review_action_lock_recommendation": lock_view.get(
            "final_manual_review_action_lock_recommendation",
            board_view.get("final_manual_review_action_lock_recommendation", ""),
        ),
        "full_local_rehearsal_status": rehearsal_view.get("rehearsal_status", "missing"),
        "gap_coach_status": gap_coach_view.get("gap_coach_status", "missing"),
        "guided_loop_control_status": control_view.get("guided_loop_control_status", "missing"),
        "gap_coach_next_safe_action_key": gap_coach_view.get("next_safe_action_key", ""),
        "guided_loop_next_safe_click": control_view.get("next_safe_click", ""),
        "affected_review_layer": affected_layer,
        "integrity_issue_count": int(board_view.get("integrity_issue_count", 0) or 0),
        "missing_required_hashes": missing_hashes,
        "mismatched_hashes": mismatched_hashes,
        "receipt_hashes": receipt_hashes,
        "receipt_hash_count": len([value for value in receipt_hashes.values() if value]),
        "timeline_event_hashes": [str(item) for item in timeline_event_hashes][:12],
        "timeline_event_count": int(board_view.get("timeline_event_count", 0) or 0),
        "ledger_event_hashes": [str(item) for item in ledger_event_hashes][:12],
        "ledger_event_count": int(board_view.get("ledger_event_count", 0) or 0),
        "accepted_post_cycle_hashes": board_view.get("accepted_post_cycle_hashes", {}),
        "source_card_ids": [str(item) for item in (source_card_ids or [])][:8],
        "source_anchor_hash_count": int(
            board_view.get("source_anchor_hash_count")
            or gap_coach_view.get("source_anchor_hash_count")
            or control_view.get("source_anchor_hash_count")
            or rehearsal_view.get("source_anchor_hash_count")
            or 0
        ),
        "help_level": safe_help_level(str(board_view.get("help_level") or gap_coach_view.get("help_level") or "A2")),
        "locked_final_review_board_hash": board_view.get("locked_final_review_board_hash", ""),
        "final_manual_review_action_lock_hash": lock_view.get("final_manual_review_action_lock_hash", ""),
        "prioritized_repair_card": repair_card,
        "next_safe_human_review_action": repair_card["next_safe_human_review_action"],
        "locked_final_review_gap_resolver_hash": sha256_text(
            json.dumps(resolver_seed, sort_keys=True, ensure_ascii=False)
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


def affected_review_layer(
    board_view: dict[str, Any],
    gap_coach_view: dict[str, Any],
    control_view: dict[str, Any],
) -> str:
    if board_view.get("locked_final_review_board_recommendation") == "reject_final_board":
        return "locked_final_review_board"
    if board_view.get("mismatched_hashes"):
        return "hash_reconciliation"
    if "notebook_checkpoint_hash" in (board_view.get("missing_required_hashes", []) or []):
        return "notebook_checkpoint_hash"
    if gap_coach_view.get("operator_confirmation_gap") or control_view.get("open_operator_confirmation_count", 0) > 0:
        return "operator_confirmation_review"
    if gap_coach_view.get("source_gap") or gap_coach_view.get("notebook_checkpoint_gap"):
        return "source_checkpoint_review"
    if board_view.get("integrity_issue_count", 0) > 0:
        return "final_review_hash_chain"
    return "manual_rehearsal_recheck"


def prioritized_repair_card(
    *,
    affected_layer: str,
    board_view: dict[str, Any],
    lock_view: dict[str, Any],
    rehearsal_view: dict[str, Any],
    gap_coach_view: dict[str, Any],
    control_view: dict[str, Any],
    missing_hashes: list[str],
    mismatched_hashes: list[str],
) -> dict[str, Any]:
    if board_view.get("locked_final_review_board_recommendation") == "reject_final_board":
        action = "return_to_locked_final_review_board"
        rationale = "final_board_rejected"
    elif mismatched_hashes or board_view.get("locked_final_review_board_recommendation") == "request_manual_reconciliation":
        action = "manual_hash_reconciliation_review"
        rationale = "hash_reconciliation_required"
    elif board_view.get("locked_final_review_board_recommendation") == "ready_for_human_final_board_review":
        action = "manual_rehearsal_recheck"
        rationale = "board_ready_for_human_recheck"
    elif affected_layer == "operator_confirmation_review":
        action = "review_operator_confirmation_cards"
        rationale = "operator_confirmation_gap"
    elif affected_layer == "notebook_checkpoint_hash":
        action = "review_notebook_checkpoint_hash_chain"
        rationale = "notebook_checkpoint_hash_missing"
    else:
        action = "continue_manual_final_review"
        rationale = "board_open_with_hash_issues"
    return {
        "status": "repair_card_ready",
        "affected_review_layer": affected_layer,
        "repair_action": action,
        "rationale": rationale,
        "board_recommendation": board_view.get("locked_final_review_board_recommendation", "keep_final_board_open"),
        "lock_recommendation": lock_view.get("final_manual_review_action_lock_recommendation", "keep_action_locked"),
        "rehearsal_status": rehearsal_view.get("rehearsal_status", "missing"),
        "gap_coach_action_key": gap_coach_view.get("next_safe_action_key", ""),
        "guided_loop_next_safe_click": control_view.get("next_safe_click", ""),
        "missing_hashes": missing_hashes[:8],
        "mismatched_hashes": mismatched_hashes[:8],
        "next_safe_human_review_action": action,
        "dry_run_default": True,
        "local_writes_requested": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def locked_final_review_gap_resolver_summary(body: dict[str, Any]) -> dict[str, Any]:
    board_recommendation = body.get("locked_final_review_board_recommendation", "keep_final_board_open")
    lock_recommendation = body.get("final_manual_review_action_lock_recommendation", "keep_action_locked")
    mismatched_hashes = body.get("mismatched_hashes", []) or []
    missing_hashes = body.get("missing_required_hashes", []) or []
    if board_recommendation == "reject_final_board" or lock_recommendation == "reject_action_path":
        recommendation = "reject_gap_resolution"
        reason = "locked_final_review_path_rejected"
    elif board_recommendation == "request_manual_reconciliation" or lock_recommendation == "request_manual_reconciliation" or mismatched_hashes:
        recommendation = "request_manual_reconciliation"
        reason = "manual_hash_reconciliation_required"
    elif board_recommendation == "ready_for_human_final_board_review" and not missing_hashes:
        recommendation = "ready_for_manual_rehearsal_recheck"
        reason = "ready_for_human_rehearsal_recheck"
    else:
        recommendation = "keep_gap_resolver_open"
        reason = "gap_resolver_still_open"
    return {
        "status": "python_exam_locked_final_review_gap_resolver_ready",
        "locked_final_review_gap_resolver_recommendation": recommendation,
        "locked_final_review_gap_resolver_reason": reason,
        "allowed_locked_final_review_gap_resolver_recommendations": sorted(
            LOCKED_FINAL_REVIEW_GAP_RESOLVER_RECOMMENDATIONS
        ),
        "locked_final_review_board_recommendation": board_recommendation,
        "final_manual_review_action_lock_recommendation": lock_recommendation,
        "full_local_rehearsal_status": body.get("full_local_rehearsal_status", ""),
        "gap_coach_status": body.get("gap_coach_status", ""),
        "guided_loop_control_status": body.get("guided_loop_control_status", ""),
        "gap_coach_next_safe_action_key": body.get("gap_coach_next_safe_action_key", ""),
        "guided_loop_next_safe_click": body.get("guided_loop_next_safe_click", ""),
        "affected_review_layer": body.get("affected_review_layer", ""),
        "integrity_issue_count": int(body.get("integrity_issue_count", 0) or 0),
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
        "prioritized_repair_card": body.get("prioritized_repair_card", {}),
        "next_safe_human_review_action": body.get("next_safe_human_review_action", ""),
        "locked_final_review_board_hash": body.get("locked_final_review_board_hash", ""),
        "final_manual_review_action_lock_hash": body.get("final_manual_review_action_lock_hash", ""),
        "locked_final_review_gap_resolver_hash": body.get("locked_final_review_gap_resolver_hash", ""),
        "dry_run_default": True,
        "export_created": False,
        "export_authorized": False,
        "archive_created": False,
        "submission_started": False,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def locked_final_review_gap_resolver_receipt(summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"summary": summary, "exam_deployment_status": "not_cleared"}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "locked_final_review_gap_resolver_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "locked_final_review_gap_resolver_recommendation": summary.get(
            "locked_final_review_gap_resolver_recommendation",
            "keep_gap_resolver_open",
        ),
        "locked_final_review_gap_resolver_hash": summary.get("locked_final_review_gap_resolver_hash", ""),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-locked-final-review-gap-resolver")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
