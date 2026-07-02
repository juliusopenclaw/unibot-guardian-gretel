from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_operator_workspace_card import safe_handoff_view, safe_local_cycle_workspace_card
from .python_exam_local_cycle_readiness_handoff import safe_review_view


PYTHON_EXAM_LOCAL_CYCLE_CHAIN_SNAPSHOT_SCHEMA_VERSION = "unibot-python-exam-local-cycle-chain-snapshot-v1"
PYTHON_EXAM_LOCAL_CYCLE_CHAIN_SNAPSHOT_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-chain-snapshot"


def build_python_exam_local_cycle_chain_snapshot(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card if isinstance(python_exam_local_cycle_operator_workspace_card, dict) else {}
    )
    review_view = safe_review_view(review)
    handoff_view = safe_handoff_view(handoff)
    workspace_view = safe_local_cycle_workspace_card(workspace_card)
    selected = str(
        selected_skill_tag
        or review_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
        or workspace_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    summary = chain_snapshot_summary(
        selected_skill_tag=selected,
        review=review,
        review_view=review_view,
        handoff=handoff,
        handoff_view=handoff_view,
        workspace_view=workspace_view,
    )
    payload = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_CHAIN_SNAPSHOT_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_chain_snapshot",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Chain Snapshot. It compacts the Readiness Review, Readiness Handoff, and "
            "Local Cycle Operator Workspace Card into one hash-only evidence chain. It exposes only metadata, "
            "hashes, Source-Card anchors, task/checkpoint hashes, Gate/Decision/Start receipt hashes, "
            "Help-Ledger preview hashes, and next safe actions. It never returns raw queries, course raw text, "
            "notebook code, local paths, values, solutions, final interpretations, scores, rankings, grades, "
            "proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "local_cycle_chain_snapshot_endpoint": PYTHON_EXAM_LOCAL_CYCLE_CHAIN_SNAPSHOT_ENDPOINT,
        "selected_skill_tag": selected,
        "local_cycle_readiness_review": review_view,
        "local_cycle_readiness_handoff": handoff_view,
        "local_cycle_operator_workspace_card": workspace_view,
        "chain_snapshot_summary": summary,
        "snapshot_hash": summary["snapshot_hash"],
        "chain_steps": chain_steps(review, review_view, handoff, handoff_view, workspace_view),
        "chain_snapshot_receipt": chain_snapshot_receipt(summary, review, handoff, workspace_card),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Chain Snapshot bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def chain_snapshot_summary(
    *,
    selected_skill_tag: str,
    review: dict[str, Any],
    review_view: dict[str, Any],
    handoff: dict[str, Any],
    handoff_view: dict[str, Any],
    workspace_view: dict[str, Any],
) -> dict[str, Any]:
    review_present = review_view.get("status") != "missing"
    handoff_present = handoff_view.get("status") != "missing"
    workspace_present = workspace_view.get("status") != "missing"
    review_hash = review_receipt_hash(review)
    handoff_hash = handoff_receipt_hash(handoff)
    workspace_hash = workspace_ledger_hash(workspace_view)
    chain_hash_complete = bool(review_hash and handoff_hash and workspace_hash)
    chain_present = review_present and handoff_present and workspace_present
    ready_for_prefill = bool(handoff_view.get("ready_for_operator_prefill", False))
    chain_ready = chain_present and chain_hash_complete and ready_for_prefill
    status = "python_exam_local_cycle_chain_snapshot_ready" if chain_ready else "python_exam_local_cycle_chain_snapshot_attention"
    seed = {
        "selected_skill_tag": selected_skill_tag,
        "review_receipt_hash": review_hash,
        "handoff_receipt_hash": handoff_hash,
        "workspace_card_hash": workspace_hash,
        "review_status": review_view.get("status", ""),
        "handoff_status": handoff_view.get("status", ""),
        "workspace_status": workspace_view.get("status", ""),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "ready_for_operator_prefill": ready_for_prefill,
        "help_level": workspace_view.get("help_level", review_view.get("help_level", "A2")),
    }
    snapshot_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": status,
        "selected_skill_tag": selected_skill_tag,
        "chain_present": chain_present,
        "chain_hash_complete": chain_hash_complete,
        "chain_ready_for_manual_local_cycle_review": bool(review_view.get("ready_for_manual_local_cycle_review", False)),
        "review_status": review_view.get("status", "missing"),
        "review_recommendation": review_view.get("recommendation", "keep_blocked"),
        "review_reason": review_view.get("recommendation_reason", "missing_start_packet"),
        "handoff_status": handoff_view.get("status", "missing"),
        "ready_for_operator_prefill": ready_for_prefill,
        "workspace_card_status": workspace_view.get("status", "missing"),
        "help_ledger_preview_status": workspace_view.get("help_ledger_preview_status", "missing"),
        "next_safe_action": workspace_view.get("next_safe_action", review_view.get("next_safe_action", "")),
        "next_safe_user_action": workspace_view.get("next_safe_user_action", review_view.get("next_safe_user_action", "")),
        "task_hash": workspace_view.get("task_hash", review_view.get("task_hash", "")),
        "checkpoint_hash": workspace_view.get("checkpoint_hash", review_view.get("checkpoint_hash", "")),
        "source_card_ids": list(workspace_view.get("source_card_ids", review_view.get("source_card_ids", [])) or [])[:8],
        "source_anchor_count": int(workspace_view.get("source_anchor_count", review_view.get("source_anchor_count", 0)) or 0),
        "help_level": workspace_view.get("help_level", review_view.get("help_level", "A2")),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "gate_receipt_hash": review_view.get("gate_receipt_hash", ""),
        "decision_receipt_hash": review_view.get("decision_receipt_hash", ""),
        "start_receipt_hash": review_view.get("start_receipt_hash", ""),
        "operator_run_endpoint": handoff_view.get("operator_run_endpoint", ""),
        "operator_run_prefill_hash": handoff_view.get("prefill_hash", ""),
        "help_ledger_preview_hash": workspace_view.get("help_ledger_preview_hash", ""),
        "review_receipt_hash": review_hash,
        "handoff_receipt_hash": handoff_hash,
        "workspace_card_hash": workspace_hash,
        "snapshot_hash": snapshot_hash,
        "chain_step_count": 3,
        "exam_deployment_status": "not_cleared",
    }


def chain_steps(
    review: dict[str, Any],
    review_view: dict[str, Any],
    handoff: dict[str, Any],
    handoff_view: dict[str, Any],
    workspace_view: dict[str, Any],
) -> list[dict[str, Any]]:
    steps = [
        {
            "step_id": "readiness_review",
            "artifact_type": "python_exam_local_cycle_readiness_review",
            "status": review_view.get("status", "missing"),
            "step_hash": sha256_text(
                json.dumps(
                    {
                        "review_receipt_hash": review_receipt_hash(review),
                        "recommendation": review_view.get("recommendation", "keep_blocked"),
                        "review_reason": review_view.get("recommendation_reason", "missing_start_packet"),
                        "open_confirmation_count": review_view.get("open_confirmation_count", 0),
                        "confirmed_count": review_view.get("confirmed_count", 0),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
            ),
            "receipt_hash": review_receipt_hash(review),
            "help_level": review_view.get("help_level", "A2"),
            "raw_text_returned": False,
        },
        {
            "step_id": "readiness_handoff",
            "artifact_type": "python_exam_local_cycle_readiness_handoff",
            "status": handoff_view.get("status", "missing"),
            "step_hash": sha256_text(
                json.dumps(
                    {
                        "handoff_receipt_hash": handoff_receipt_hash(handoff),
                        "ready_for_operator_prefill": handoff_view.get("ready_for_operator_prefill", False),
                        "operator_run_prefill_hash": handoff_view.get("prefill_hash", ""),
                        "next_safe_action": handoff_view.get("next_safe_action", ""),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
            ),
            "receipt_hash": handoff_receipt_hash(handoff),
            "help_level": handoff_view.get("help_level", "A2"),
            "raw_text_returned": False,
        },
        {
            "step_id": "operator_workspace_card",
            "artifact_type": "python_exam_local_cycle_operator_workspace_card",
            "status": workspace_view.get("status", "missing"),
            "step_hash": sha256_text(
                json.dumps(
                    {
                        "workspace_card_hash": workspace_ledger_hash(workspace_view),
                        "help_ledger_preview_status": workspace_view.get("help_ledger_preview_status", ""),
                        "next_safe_action": workspace_view.get("next_safe_action", ""),
                        "help_level": workspace_view.get("help_level", "A2"),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
            ),
            "receipt_hash": workspace_ledger_hash(workspace_view),
            "help_level": workspace_view.get("help_level", "A2"),
            "raw_text_returned": False,
        },
    ]
    return steps


def chain_snapshot_receipt(
    summary: dict[str, Any],
    review: dict[str, Any],
    handoff: dict[str, Any],
    workspace_card: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "review_receipt_hash": review_receipt_hash(review),
        "handoff_receipt_hash": handoff_receipt_hash(handoff),
        "workspace_card_hash": workspace_ledger_hash(safe_local_cycle_workspace_card(workspace_card)),
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "local_cycle_chain_snapshot_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "step_count": 3,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def review_receipt_hash(review: dict[str, Any]) -> str:
    receipt = review.get("readiness_review_receipt", {}) if isinstance(review.get("readiness_review_receipt"), dict) else {}
    return str(receipt.get("receipt_hash", ""))


def handoff_receipt_hash(handoff: dict[str, Any]) -> str:
    receipt = handoff.get("handoff_receipt", {}) if isinstance(handoff.get("handoff_receipt"), dict) else {}
    return str(receipt.get("receipt_hash", ""))


def workspace_ledger_hash(workspace_view: dict[str, Any]) -> str:
    help_ledger_preview = workspace_view.get("help_ledger_preview", {}) if isinstance(workspace_view.get("help_ledger_preview"), dict) else {}
    return str(workspace_view.get("help_ledger_preview_hash") or help_ledger_preview.get("preview_hash", ""))


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review the local cycle chain snapshot."),
        "Use the chain snapshot only as hash-only evidence and keep exam_deployment_status not_cleared.",
        "Handle real-world exam clearance outside UniBot.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-chain-snapshot")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
