from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_chain_snapshot, safe_help_level
from .python_exam_local_cycle_operator_workspace_card import safe_handoff_view, safe_local_cycle_workspace_card


PYTHON_EXAM_MANUAL_CYCLE_LAUNCH_RECEIPT_SCHEMA_VERSION = "unibot-python-exam-manual-cycle-launch-receipt-v1"
PYTHON_EXAM_MANUAL_CYCLE_LAUNCH_RECEIPT_ENDPOINT = "/api/unibot/course/python-exam-manual-cycle-launch-receipt"

LAUNCH_RECEIPT_DECISIONS = {
    "stay_in_confirmation_review",
    "ready_for_manual_local_cycle",
    "refresh_manual_console",
    "abort_manual_cycle_review",
}


def build_python_exam_manual_cycle_launch_receipt(
    *,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    console = python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    chain_snapshot = python_exam_local_cycle_chain_snapshot if isinstance(python_exam_local_cycle_chain_snapshot, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    handoff = python_exam_local_cycle_readiness_handoff if isinstance(python_exam_local_cycle_readiness_handoff, dict) else {}
    console_view = safe_manual_confirmation_console(console)
    chain_view = safe_chain_snapshot(chain_snapshot)
    workspace_view = safe_local_cycle_workspace_card(workspace_card)
    handoff_view = safe_handoff_view(handoff or workspace_card.get("readiness_handoff", {}))
    prefill_view = safe_operator_prefill(workspace_card, handoff)
    selected = str(
        selected_skill_tag
        or console_view.get("selected_skill_tag", "")
        or chain_view.get("selected_skill_tag", "")
        or workspace_view.get("selected_skill_tag", "")
        or handoff_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    receipt_summary = launch_receipt_summary(
        selected_skill_tag=selected,
        console_view=console_view,
        chain_view=chain_view,
        workspace_view=workspace_view,
        handoff_view=handoff_view,
        prefill_view=prefill_view,
    )
    metadata = launch_metadata(console_view, chain_view, workspace_view, handoff_view, prefill_view)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_CYCLE_LAUNCH_RECEIPT_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_cycle_launch_receipt",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": receipt_summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Cycle Launch Receipt. It records the reviewed Manual Confirmation Console, Chain "
            "Snapshot, Operator Workspace Card, and Operator-Run Prefill before any manual local cycle action. It "
            "only exposes hashes, receipt metadata, Source-Card anchors, task/checkpoint hashes, A0-A2 help level, "
            "and one launch decision. It executes nothing, writes nothing, and never returns raw queries, course "
            "raw text, notebook code, local paths, values, solutions, final interpretations, scores, rankings, "
            "grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_cycle_launch_receipt_endpoint": PYTHON_EXAM_MANUAL_CYCLE_LAUNCH_RECEIPT_ENDPOINT,
        "selected_skill_tag": selected,
        "launch_receipt_summary": receipt_summary,
        "launch_decision": receipt_summary["launch_decision"],
        "launch_metadata": metadata,
        "confirmation_review": {
            "manual_confirmation_console_status": console_view.get("status", "missing"),
            "manual_confirmation_action": console_view.get("next_manual_confirmation_action", "refresh_start_packet_review"),
            "open_confirmation_count": int(console_view.get("open_confirmation_count", 0) or 0),
            "confirmed_count": int(console_view.get("confirmed_count", 0) or 0),
            "open_confirmation_hashes": list(console_view.get("open_confirmation_hashes", []) or [])[:12],
            "confirmed_hashes": list(console_view.get("confirmed_hashes", []) or [])[:12],
            "manual_confirmation_console_receipt_hash": console_view.get("manual_confirmation_console_receipt_hash", ""),
            "not_cleared_receipt": True,
            "exam_deployment_status": "not_cleared",
        },
        "operator_run_prefill": prefill_view,
        "manual_cycle_launch_receipt": manual_cycle_launch_receipt(receipt_summary, metadata, console_view, prefill_view),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Manual Cycle Launch Receipt bleibt not_cleared."
        ),
        "next_actions": [
            f"Launch decision: {receipt_summary['launch_decision']}.",
            "Use this only as a human-reviewable launch receipt; do not execute local work from the receipt.",
            "Keep any real manual local action outside this artifact and keep exam_deployment_status not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_manual_confirmation_console(console: dict[str, Any]) -> dict[str, Any]:
    summary = console.get("console_summary", {}) if isinstance(console.get("console_summary"), dict) else {}
    matrix = console.get("confirmation_matrix", {}) if isinstance(console.get("confirmation_matrix"), dict) else {}
    metadata = console.get("source_checkpoint_metadata", {}) if isinstance(console.get("source_checkpoint_metadata"), dict) else {}
    receipt_hashes = console.get("receipt_hashes", {}) if isinstance(console.get("receipt_hashes"), dict) else {}
    receipt = (
        console.get("manual_confirmation_console_receipt", {})
        if isinstance(console.get("manual_confirmation_console_receipt"), dict)
        else {}
    )
    return {
        "status": console.get("status", "missing"),
        "selected_skill_tag": str(console.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "next_manual_confirmation_action": str(
            console.get("next_manual_confirmation_action")
            or summary.get("next_manual_confirmation_action")
            or "refresh_start_packet_review"
        ),
        "next_manual_confirmation_reason": str(summary.get("next_manual_confirmation_reason", "")),
        "hash_metadata_complete": bool(summary.get("hash_metadata_complete", False)),
        "chain_hash_complete": bool(summary.get("chain_hash_complete", False)),
        "open_confirmation_count": int(matrix.get("open_count", summary.get("open_confirmation_count", 0)) or 0),
        "confirmed_count": int(matrix.get("confirmed_count", summary.get("confirmed_count", 0)) or 0),
        "open_confirmation_hashes": [str(item) for item in (matrix.get("open_card_hashes", []) or [])][:12],
        "confirmed_hashes": [str(item) for item in (matrix.get("confirmed_card_hashes", []) or [])][:12],
        "task_hash": str(metadata.get("task_hash", summary.get("task_hash", ""))),
        "checkpoint_hash": str(metadata.get("checkpoint_hash", summary.get("checkpoint_hash", ""))),
        "source_card_ids": [str(item) for item in (metadata.get("source_card_ids", summary.get("source_card_ids", [])) or [])][:8],
        "source_anchor_count": int(metadata.get("source_anchor_count", summary.get("source_anchor_count", 0)) or 0),
        "help_level": safe_help_level(str(metadata.get("help_level", summary.get("help_level", "A2")))),
        "gate_receipt_hash": str(receipt_hashes.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(receipt_hashes.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(receipt_hashes.get("start_receipt_hash", "")),
        "chain_snapshot_hash": str(receipt_hashes.get("chain_snapshot_hash", "")),
        "chain_snapshot_receipt_hash": str(receipt_hashes.get("chain_snapshot_receipt_hash", "")),
        "manual_confirmation_console_receipt_hash": str(receipt.get("receipt_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_operator_prefill(workspace_card: dict[str, Any], handoff: dict[str, Any]) -> dict[str, Any]:
    prefill = {}
    if isinstance(workspace_card.get("operator_run_prefill"), dict):
        prefill = workspace_card.get("operator_run_prefill", {})
    elif isinstance(handoff.get("operator_run_prefill"), dict):
        prefill = handoff.get("operator_run_prefill", {})
    return {
        "status": str(prefill.get("status", "missing")),
        "endpoint": str(prefill.get("endpoint", "")),
        "method": str(prefill.get("method", "POST")),
        "selected_skill_tag": str(prefill.get("selected_skill_tag", "")),
        "task_hash": str(prefill.get("task_hash", "")),
        "checkpoint_hash": str(prefill.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (prefill.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(prefill.get("source_anchor_count", 0) or 0),
        "requested_help_level": safe_help_level(str(prefill.get("requested_help_level", "A2"))),
        "prefill_hash": str(prefill.get("prefill_hash", "")),
        "dry_run_default": True,
        "local_writes_requested": False,
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def launch_receipt_summary(
    *,
    selected_skill_tag: str,
    console_view: dict[str, Any],
    chain_view: dict[str, Any],
    workspace_view: dict[str, Any],
    handoff_view: dict[str, Any],
    prefill_view: dict[str, Any],
) -> dict[str, Any]:
    console_ready = console_view.get("status") == "python_exam_local_cycle_manual_confirmation_console_ready"
    chain_ready = bool(chain_view.get("chain_present", False) and chain_view.get("chain_hash_complete", False))
    workspace_ready = workspace_view.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
    prefill_ready = bool(prefill_view.get("prefill_hash") and prefill_view.get("status") == "prefill_ready")
    help_safe = console_view.get("help_level", "A2") in {"A0", "A1", "A2"} and prefill_view.get(
        "requested_help_level", "A2"
    ) in {"A0", "A1", "A2"}
    manual_action = str(console_view.get("next_manual_confirmation_action", "refresh_start_packet_review"))
    open_count = int(console_view.get("open_confirmation_count", 0) or 0)
    confirmed_count = int(console_view.get("confirmed_count", 0) or 0)
    if not console_ready or manual_action == "refresh_start_packet_review":
        launch_decision = "refresh_manual_console"
        reason = "manual_confirmation_console_needs_refresh"
    elif not chain_ready or not workspace_ready or not prefill_ready or not help_safe:
        launch_decision = "abort_manual_cycle_review"
        reason = "launch_metadata_incomplete_or_unsafe"
    elif manual_action in {"review_missing_confirmation", "confirm_hash_metadata_manually"} or open_count > 0:
        launch_decision = "stay_in_confirmation_review"
        reason = "manual_confirmation_review_not_finished"
    elif manual_action == "continue_to_manual_local_cycle" and confirmed_count > 0:
        launch_decision = "ready_for_manual_local_cycle"
        reason = "confirmed_hash_metadata_ready_for_manual_local_cycle"
    else:
        launch_decision = "abort_manual_cycle_review"
        reason = "unsupported_manual_confirmation_action"
    return {
        "status": "python_exam_manual_cycle_launch_receipt_ready",
        "selected_skill_tag": selected_skill_tag,
        "launch_decision": launch_decision,
        "launch_decision_reason": reason,
        "allowed_launch_decisions": sorted(LAUNCH_RECEIPT_DECISIONS),
        "manual_confirmation_console_status": console_view.get("status", "missing"),
        "manual_confirmation_action": manual_action,
        "chain_snapshot_status": chain_view.get("status", "missing"),
        "operator_workspace_card_status": workspace_view.get("status", "missing"),
        "handoff_status": handoff_view.get("status", "missing"),
        "operator_prefill_status": prefill_view.get("status", "missing"),
        "open_confirmation_count": open_count,
        "confirmed_count": confirmed_count,
        "task_hash": first_value(console_view, chain_view, workspace_view, prefill_view, key="task_hash"),
        "checkpoint_hash": first_value(console_view, chain_view, workspace_view, prefill_view, key="checkpoint_hash"),
        "source_card_ids": first_list(console_view, chain_view, workspace_view, prefill_view, key="source_card_ids")[:8],
        "source_anchor_count": first_int(console_view, chain_view, workspace_view, prefill_view, key="source_anchor_count"),
        "help_level": safe_help_level(first_value(console_view, chain_view, workspace_view, prefill_view, key="help_level") or prefill_view.get("requested_help_level", "A2")),
        "operator_run_prefill_hash": prefill_view.get("prefill_hash", ""),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def launch_metadata(
    console_view: dict[str, Any],
    chain_view: dict[str, Any],
    workspace_view: dict[str, Any],
    handoff_view: dict[str, Any],
    prefill_view: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task_hash": first_value(console_view, chain_view, workspace_view, prefill_view, key="task_hash"),
        "checkpoint_hash": first_value(console_view, chain_view, workspace_view, prefill_view, key="checkpoint_hash"),
        "source_card_ids": first_list(console_view, chain_view, workspace_view, prefill_view, key="source_card_ids")[:8],
        "source_anchor_count": first_int(console_view, chain_view, workspace_view, prefill_view, key="source_anchor_count"),
        "help_level": safe_help_level(first_value(console_view, chain_view, workspace_view, prefill_view, key="help_level") or prefill_view.get("requested_help_level", "A2")),
        "operator_run_endpoint": prefill_view.get("endpoint") or handoff_view.get("operator_run_endpoint", ""),
        "operator_run_method": prefill_view.get("method") or handoff_view.get("operator_run_method", "POST"),
        "operator_run_prefill_hash": prefill_view.get("prefill_hash", ""),
        "gate_receipt_hash": console_view.get("gate_receipt_hash", ""),
        "decision_receipt_hash": console_view.get("decision_receipt_hash", ""),
        "start_receipt_hash": console_view.get("start_receipt_hash", ""),
        "chain_snapshot_hash": chain_view.get("snapshot_hash") or console_view.get("chain_snapshot_hash", ""),
        "chain_snapshot_receipt_hash": console_view.get("chain_snapshot_receipt_hash", ""),
        "manual_confirmation_console_receipt_hash": console_view.get("manual_confirmation_console_receipt_hash", ""),
        "help_ledger_preview_hash": chain_view.get("help_ledger_preview_hash", workspace_view.get("help_ledger_preview_hash", "")),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def manual_cycle_launch_receipt(
    summary: dict[str, Any],
    metadata: dict[str, Any],
    console_view: dict[str, Any],
    prefill_view: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "metadata": metadata,
        "open_hashes": console_view.get("open_confirmation_hashes", []),
        "confirmed_hashes": console_view.get("confirmed_hashes", []),
        "prefill_hash": prefill_view.get("prefill_hash", ""),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_cycle_launch_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "launch_decision": summary.get("launch_decision", "refresh_manual_console"),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
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


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-cycle-launch-receipt")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
