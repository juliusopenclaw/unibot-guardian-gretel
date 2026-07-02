from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_operator_workspace_card import safe_handoff_view, safe_local_cycle_workspace_card
from .python_exam_local_cycle_readiness_handoff import safe_review_view


PYTHON_EXAM_LOCAL_CYCLE_MANUAL_CONFIRMATION_CONSOLE_SCHEMA_VERSION = (
    "unibot-python-exam-local-cycle-manual-confirmation-console-v1"
)
PYTHON_EXAM_LOCAL_CYCLE_MANUAL_CONFIRMATION_CONSOLE_ENDPOINT = (
    "/api/unibot/course/python-exam-local-cycle-manual-confirmation-console"
)

NEXT_MANUAL_CONFIRMATION_ACTIONS = {
    "review_missing_confirmation",
    "confirm_hash_metadata_manually",
    "refresh_start_packet_review",
    "continue_to_manual_local_cycle",
}


def build_python_exam_local_cycle_manual_confirmation_console(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    chain_snapshot = python_exam_local_cycle_chain_snapshot if isinstance(python_exam_local_cycle_chain_snapshot, dict) else {}
    review_view = safe_review_view(review)
    handoff_view = safe_handoff_view(handoff)
    workspace_view = safe_local_cycle_workspace_card(workspace_card)
    chain_view = safe_chain_snapshot(chain_snapshot)
    start_view = safe_start_packet_view(review)
    selected = str(
        selected_skill_tag
        or review_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
        or workspace_view.get("selected_skill_tag", "")
        or chain_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    open_cards = confirmation_cards(start_view.get("open_confirmations", []), card_state="open")
    confirmed_cards = confirmation_cards(start_view.get("confirmed_hash_metadata", []), card_state="confirmed")
    matrix = confirmation_matrix(open_cards=open_cards, confirmed_cards=confirmed_cards)
    summary = console_summary(
        selected_skill_tag=selected,
        review_view=review_view,
        handoff_view=handoff_view,
        workspace_view=workspace_view,
        chain_view=chain_view,
        start_view=start_view,
        matrix=matrix,
    )
    payload = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_MANUAL_CONFIRMATION_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_manual_confirmation_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Manual Confirmation Console. It consumes the Readiness Review, Handoff, "
            "Operator Workspace Card, and Chain Snapshot to show open and confirmed operator confirmations side "
            "by side. It exposes only hash metadata, receipt hashes, Source-Card anchors, checkpoint hashes, "
            "A0-A2 help level, and one next safe manual action. It executes nothing, writes nothing, and never "
            "returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or exam "
            "clearance claims."
        ),
        "manual_confirmation_console_endpoint": PYTHON_EXAM_LOCAL_CYCLE_MANUAL_CONFIRMATION_CONSOLE_ENDPOINT,
        "selected_skill_tag": selected,
        "console_summary": summary,
        "next_manual_confirmation_action": summary["next_manual_confirmation_action"],
        "confirmation_matrix": matrix,
        "open_confirmation_cards": open_cards,
        "confirmed_hash_metadata_cards": confirmed_cards,
        "source_checkpoint_metadata": source_checkpoint_metadata(start_view, review_view, handoff_view, workspace_view, chain_view),
        "receipt_hashes": receipt_hashes(review, handoff, workspace_card, chain_snapshot, start_view, chain_view),
        "manual_confirmation_console_receipt": manual_confirmation_console_receipt(summary, matrix),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Manual Confirmation Console bleibt not_cleared."
        ),
        "next_actions": [
            f"Next manual action: {summary['next_manual_confirmation_action']}.",
            "Review hash metadata manually before any local cycle action.",
            "Keep local execution outside this console and keep exam_deployment_status not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_start_packet_view(review: dict[str, Any]) -> dict[str, Any]:
    packet = review.get("local_cycle_start_packet", {}) if isinstance(review.get("local_cycle_start_packet"), dict) else {}
    return {
        "status": str(packet.get("status", "missing")),
        "selected_skill_tag": str(packet.get("selected_skill_tag", "")),
        "start_status": str(packet.get("start_status", "missing")),
        "task_hash": str(packet.get("task_hash", "")),
        "checkpoint_hash": str(packet.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (packet.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(packet.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(packet.get("help_level", "A2"))),
        "gate_receipt_hash": str(packet.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(packet.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(packet.get("start_receipt_hash", "")),
        "open_confirmation_count": int(packet.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(packet.get("confirmed_count", 0) or 0),
        "open_confirmations": list(packet.get("open_confirmations", []) or [])[:8],
        "confirmed_hash_metadata": list(packet.get("confirmed_hash_metadata", []) or [])[:8],
        "blocked_for_confirmation": bool(packet.get("blocked_for_confirmation", False)),
        "ready_for_manual_local_cycle_review": bool(packet.get("ready_for_manual_local_cycle_review", False)),
        "exam_deployment_status": "not_cleared",
    }


def safe_chain_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("chain_snapshot_summary", {}) if isinstance(snapshot.get("chain_snapshot_summary"), dict) else {}
    return {
        "status": snapshot.get("status", "missing"),
        "selected_skill_tag": str(snapshot.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "chain_present": bool(summary.get("chain_present", False)),
        "chain_hash_complete": bool(summary.get("chain_hash_complete", False)),
        "chain_ready_for_manual_local_cycle_review": bool(
            summary.get("chain_ready_for_manual_local_cycle_review", False)
        ),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "snapshot_hash": str(snapshot.get("snapshot_hash", summary.get("snapshot_hash", ""))),
        "review_receipt_hash": str(summary.get("review_receipt_hash", "")),
        "handoff_receipt_hash": str(summary.get("handoff_receipt_hash", "")),
        "workspace_card_hash": str(summary.get("workspace_card_hash", "")),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", "")),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "open_confirmation_count": int(summary.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def confirmation_cards(items: list[Any], *, card_state: str) -> list[dict[str, Any]]:
    cards = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        card = {
            "card_state": card_state,
            "sequence_index": index,
            "step_id": str(item.get("step_id", "")),
            "action": str(item.get("action", "")),
            "card_hash": str(item.get("card_hash", "")),
            "selected_task_hash": str(item.get("selected_task_hash", "")),
            "checkpoint_hash": str(item.get("checkpoint_hash", "")),
            "help_level": safe_help_level(str(item.get("help_level", "A2"))),
            "operator_confirmed": bool(item.get("operator_confirmed", card_state == "confirmed")),
            "write_started": False,
            "not_cleared_receipt": True,
            "exam_deployment_status": "not_cleared",
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        }
        card["confirmation_card_hash"] = sha256_text(json.dumps(card, sort_keys=True, ensure_ascii=False))
        cards.append(card)
    return cards


def confirmation_matrix(*, open_cards: list[dict[str, Any]], confirmed_cards: list[dict[str, Any]]) -> dict[str, Any]:
    open_count = len(open_cards)
    confirmed_count = len(confirmed_cards)
    return {
        "status": "manual_confirmation_review_ready",
        "open_count": open_count,
        "confirmed_count": confirmed_count,
        "total_count": open_count + confirmed_count,
        "open_step_ids": [card.get("step_id", "") for card in open_cards],
        "confirmed_step_ids": [card.get("step_id", "") for card in confirmed_cards],
        "open_card_hashes": [card.get("card_hash", "") for card in open_cards],
        "confirmed_card_hashes": [card.get("card_hash", "") for card in confirmed_cards],
        "a0_a2_only": all(card.get("help_level") in {"A0", "A1", "A2"} for card in open_cards + confirmed_cards),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def console_summary(
    *,
    selected_skill_tag: str,
    review_view: dict[str, Any],
    handoff_view: dict[str, Any],
    workspace_view: dict[str, Any],
    chain_view: dict[str, Any],
    start_view: dict[str, Any],
    matrix: dict[str, Any],
) -> dict[str, Any]:
    hash_complete = hashes_complete(start_view, review_view, handoff_view, workspace_view, chain_view)
    chain_usable = chain_view.get("chain_present") and chain_view.get("chain_hash_complete")
    open_count = int(matrix.get("open_count", 0) or 0)
    confirmed_count = int(matrix.get("confirmed_count", 0) or 0)
    if not hash_complete or not chain_usable:
        action = "refresh_start_packet_review"
        reason = "missing_start_packet_or_chain_hash_metadata"
    elif open_count > 0:
        action = "review_missing_confirmation"
        reason = "open_operator_confirmations_present"
    elif confirmed_count <= 0:
        action = "confirm_hash_metadata_manually"
        reason = "no_confirmed_hash_metadata_present"
    else:
        action = "continue_to_manual_local_cycle"
        reason = "all_confirmations_hash_metadata_present"
    status = (
        "python_exam_local_cycle_manual_confirmation_console_ready"
        if action != "refresh_start_packet_review"
        else "python_exam_local_cycle_manual_confirmation_console_attention"
    )
    return {
        "status": status,
        "selected_skill_tag": selected_skill_tag,
        "next_manual_confirmation_action": action,
        "next_manual_confirmation_reason": reason,
        "allowed_next_manual_confirmation_actions": sorted(NEXT_MANUAL_CONFIRMATION_ACTIONS),
        "readiness_review_status": review_view.get("status", "missing"),
        "readiness_recommendation": review_view.get("recommendation", "keep_blocked"),
        "handoff_status": handoff_view.get("status", "missing"),
        "operator_workspace_card_status": workspace_view.get("status", "missing"),
        "chain_snapshot_status": chain_view.get("status", "missing"),
        "start_status": start_view.get("start_status", "missing"),
        "hash_metadata_complete": bool(hash_complete),
        "chain_hash_complete": bool(chain_view.get("chain_hash_complete", False)),
        "open_confirmation_count": open_count,
        "confirmed_count": confirmed_count,
        "task_hash": first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="task_hash"),
        "checkpoint_hash": first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="checkpoint_hash"),
        "source_card_ids": list(
            first_list(start_view, review_view, handoff_view, workspace_view, chain_view, key="source_card_ids")
        )[:8],
        "source_anchor_count": first_int(start_view, review_view, handoff_view, workspace_view, chain_view, key="source_anchor_count"),
        "help_level": safe_help_level(first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="help_level") or "A2"),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def hashes_complete(*views: dict[str, Any]) -> bool:
    task_hash = first_value(*views, key="task_hash")
    checkpoint_hash = first_value(*views, key="checkpoint_hash")
    source_anchor_count = first_int(*views, key="source_anchor_count")
    gate_hash = first_value(*views, key="gate_receipt_hash")
    decision_hash = first_value(*views, key="decision_receipt_hash")
    start_hash = first_value(*views, key="start_receipt_hash")
    chain_hash = first_value(*views, key="snapshot_hash")
    return all([task_hash, checkpoint_hash, gate_hash, decision_hash, start_hash, chain_hash]) and source_anchor_count > 0


def source_checkpoint_metadata(
    start_view: dict[str, Any],
    review_view: dict[str, Any],
    handoff_view: dict[str, Any],
    workspace_view: dict[str, Any],
    chain_view: dict[str, Any],
) -> dict[str, Any]:
    return {
        "selected_skill_tag": first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="selected_skill_tag"),
        "task_hash": first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="task_hash"),
        "checkpoint_hash": first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="checkpoint_hash"),
        "source_card_ids": list(first_list(start_view, review_view, handoff_view, workspace_view, chain_view, key="source_card_ids"))[:8],
        "source_anchor_count": first_int(start_view, review_view, handoff_view, workspace_view, chain_view, key="source_anchor_count"),
        "help_level": safe_help_level(first_value(start_view, review_view, handoff_view, workspace_view, chain_view, key="help_level") or "A2"),
        "a0_a2_only": True,
        "exam_deployment_status": "not_cleared",
    }


def receipt_hashes(
    review: dict[str, Any],
    handoff: dict[str, Any],
    workspace_card: dict[str, Any],
    chain_snapshot: dict[str, Any],
    start_view: dict[str, Any],
    chain_view: dict[str, Any],
) -> dict[str, Any]:
    review_receipt = review.get("readiness_review_receipt", {}) if isinstance(review.get("readiness_review_receipt"), dict) else {}
    handoff_receipt = handoff.get("handoff_receipt", {}) if isinstance(handoff.get("handoff_receipt"), dict) else {}
    workspace_ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    chain_receipt = (
        chain_snapshot.get("chain_snapshot_receipt", {})
        if isinstance(chain_snapshot.get("chain_snapshot_receipt"), dict)
        else {}
    )
    return {
        "gate_receipt_hash": str(start_view.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(start_view.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(start_view.get("start_receipt_hash", "")),
        "readiness_review_receipt_hash": str(review_receipt.get("receipt_hash", "")),
        "handoff_receipt_hash": str(handoff_receipt.get("receipt_hash", "")),
        "workspace_help_ledger_preview_hash": str(workspace_ledger.get("preview_hash", chain_view.get("help_ledger_preview_hash", ""))),
        "chain_snapshot_hash": str(chain_view.get("snapshot_hash", "")),
        "chain_snapshot_receipt_hash": str(chain_receipt.get("receipt_hash", "")),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def manual_confirmation_console_receipt(summary: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "open_card_hashes": matrix.get("open_card_hashes", []),
        "confirmed_card_hashes": matrix.get("confirmed_card_hashes", []),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_confirmation_console_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "next_manual_confirmation_action": summary.get("next_manual_confirmation_action", "refresh_start_packet_review"),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def first_value(*views: dict[str, Any], key: str) -> str:
    for view in views:
        value = view.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def first_list(*views: dict[str, Any], key: str) -> list[str]:
    for view in views:
        value = view.get(key)
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return []


def first_int(*views: dict[str, Any], key: str) -> int:
    for view in views:
        value = view.get(key)
        if value:
            return int(value or 0)
    return 0


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-manual-confirmation-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
