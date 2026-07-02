from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_chain_snapshot, safe_help_level
from .python_exam_local_cycle_operator_workspace_card import safe_local_cycle_workspace_card
from .python_exam_manual_cycle_launch_receipt import safe_manual_confirmation_console


PYTHON_EXAM_MANUAL_CYCLE_EVIDENCE_BINDER_SCHEMA_VERSION = "unibot-python-exam-manual-cycle-evidence-binder-v1"
PYTHON_EXAM_MANUAL_CYCLE_EVIDENCE_BINDER_ENDPOINT = "/api/unibot/course/python-exam-manual-cycle-evidence-binder"

BINDER_REVIEW_ACTIONS = {
    "continue_confirmation_review",
    "ready_for_human_manual_cycle_review",
    "refresh_launch_receipt",
    "refresh_manual_confirmation_console",
    "abort_manual_cycle_review",
}


def build_python_exam_manual_cycle_evidence_binder(
    *,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    python_exam_local_cycle_chain_snapshot: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    launch_receipt = python_exam_manual_cycle_launch_receipt if isinstance(python_exam_manual_cycle_launch_receipt, dict) else {}
    manual_console = (
        python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    )
    chain_snapshot = (
        python_exam_local_cycle_chain_snapshot if isinstance(python_exam_local_cycle_chain_snapshot, dict) else {}
    )
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    readiness_review = (
        python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    )
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    chain_view = safe_chain_snapshot(chain_snapshot)
    workspace_view = safe_local_cycle_workspace_card(workspace_card)
    review_view = safe_readiness_review(readiness_review)
    selected = str(
        selected_skill_tag
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
        or chain_view.get("selected_skill_tag", "")
        or workspace_view.get("selected_skill_tag", "")
        or review_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"

    evidence = binder_evidence(
        launch_view=launch_view,
        console_view=console_view,
        chain_view=chain_view,
        workspace_view=workspace_view,
        review_view=review_view,
    )
    summary = binder_summary(selected_skill_tag=selected, launch_view=launch_view, evidence=evidence)
    receipt = evidence_binder_receipt(summary, evidence)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_CYCLE_EVIDENCE_BINDER_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_cycle_evidence_binder",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_cycle_evidence_binder_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Cycle Evidence Binder. It binds the Manual Cycle Launch Receipt, Manual "
            "Confirmation Console, Chain Snapshot, Operator Workspace Card, and Readiness Review into one "
            "hash-only stop-go evidence packet before or after a human-run local cycle review. It executes "
            "nothing, writes nothing, and exposes only launch decision, confirmation hashes, Source-Card "
            "anchors, task/checkpoint hashes, Help-Ledger preview hash, receipt hashes, and one next safe "
            "review action. It never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, rankings, grades, proctoring, AI detection, automatic "
            "grading, or exam clearance claims."
        ),
        "manual_cycle_evidence_binder_endpoint": PYTHON_EXAM_MANUAL_CYCLE_EVIDENCE_BINDER_ENDPOINT,
        "selected_skill_tag": selected,
        "binder_summary": summary,
        "next_safe_review_action": summary["next_safe_review_action"],
        "manual_cycle_evidence": evidence,
        "manual_cycle_evidence_binder_receipt": receipt,
        "cycle_review_window": {
            "pre_cycle_chain_bound": bool(summary["launch_receipt_present"] and evidence["chain_snapshot_hash"]),
            "post_cycle_receipt_expected_after_human_action": True,
            "post_cycle_receipt_hash": "",
            "post_cycle_execution_claimed": False,
            "local_execution_started": False,
            "local_writes_requested": False,
            "exam_deployment_status": "not_cleared",
        },
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Evidence Binder bleibt not_cleared."
        ),
        "next_actions": [
            f"Next safe review action: {summary['next_safe_review_action']}.",
            "Use this binder as hash-only evidence; keep any manual local work outside this artifact.",
            "After a real human-run local cycle, attach only a reviewed post-cycle receipt hash in a later binder.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_launch_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    summary = receipt.get("launch_receipt_summary", {}) if isinstance(receipt.get("launch_receipt_summary"), dict) else {}
    metadata = receipt.get("launch_metadata", {}) if isinstance(receipt.get("launch_metadata"), dict) else {}
    confirmation = receipt.get("confirmation_review", {}) if isinstance(receipt.get("confirmation_review"), dict) else {}
    launch_receipt = (
        receipt.get("manual_cycle_launch_receipt", {})
        if isinstance(receipt.get("manual_cycle_launch_receipt"), dict)
        else {}
    )
    return {
        "status": str(receipt.get("status", "missing")),
        "selected_skill_tag": str(receipt.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "launch_decision": str(receipt.get("launch_decision") or summary.get("launch_decision", "refresh_manual_console")),
        "launch_decision_reason": str(summary.get("launch_decision_reason", "")),
        "manual_confirmation_action": str(summary.get("manual_confirmation_action", "")),
        "open_confirmation_count": int(summary.get("open_confirmation_count", confirmation.get("open_confirmation_count", 0)) or 0),
        "confirmed_count": int(summary.get("confirmed_count", confirmation.get("confirmed_count", 0)) or 0),
        "task_hash": str(metadata.get("task_hash", summary.get("task_hash", ""))),
        "checkpoint_hash": str(metadata.get("checkpoint_hash", summary.get("checkpoint_hash", ""))),
        "source_card_ids": [str(item) for item in (metadata.get("source_card_ids", summary.get("source_card_ids", [])) or [])][:8],
        "source_anchor_count": int(metadata.get("source_anchor_count", summary.get("source_anchor_count", 0)) or 0),
        "help_level": safe_help_level(str(metadata.get("help_level", summary.get("help_level", "A2")))),
        "operator_run_prefill_hash": str(metadata.get("operator_run_prefill_hash", summary.get("operator_run_prefill_hash", ""))),
        "gate_receipt_hash": str(metadata.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(metadata.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(metadata.get("start_receipt_hash", "")),
        "chain_snapshot_hash": str(metadata.get("chain_snapshot_hash", "")),
        "chain_snapshot_receipt_hash": str(metadata.get("chain_snapshot_receipt_hash", "")),
        "manual_confirmation_console_receipt_hash": str(metadata.get("manual_confirmation_console_receipt_hash", "")),
        "help_ledger_preview_hash": str(metadata.get("help_ledger_preview_hash", "")),
        "launch_receipt_hash": str(launch_receipt.get("receipt_hash", "")),
        "not_cleared_receipt": bool(launch_receipt.get("not_cleared_receipt", False)),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def safe_readiness_review(review: dict[str, Any]) -> dict[str, Any]:
    summary = review.get("readiness_review_summary", {}) if isinstance(review.get("readiness_review_summary"), dict) else {}
    receipt = (
        review.get("local_cycle_readiness_review_receipt", {})
        if isinstance(review.get("local_cycle_readiness_review_receipt"), dict)
        else {}
    )
    return {
        "status": str(review.get("status", "missing")),
        "selected_skill_tag": str(review.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "recommendation": str(review.get("readiness_review_recommendation") or summary.get("recommendation", "keep_blocked")),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "gate_receipt_hash": str(summary.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(summary.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(summary.get("start_receipt_hash", "")),
        "review_receipt_hash": str(receipt.get("receipt_hash", "")),
        "exam_deployment_status": "not_cleared",
    }


def binder_evidence(
    *,
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
    chain_view: dict[str, Any],
    workspace_view: dict[str, Any],
    review_view: dict[str, Any],
) -> dict[str, Any]:
    open_hashes = first_list(console_view, key="open_confirmation_hashes")
    confirmed_hashes = first_list(console_view, key="confirmed_hashes")
    return {
        "launch_decision": launch_view.get("launch_decision", "refresh_manual_console"),
        "launch_decision_reason": launch_view.get("launch_decision_reason", ""),
        "manual_confirmation_action": first_value(launch_view, console_view, key="manual_confirmation_action")
        or console_view.get("next_manual_confirmation_action", ""),
        "open_confirmation_count": first_int(launch_view, console_view, chain_view, key="open_confirmation_count"),
        "confirmed_count": first_int(launch_view, console_view, chain_view, key="confirmed_count"),
        "open_confirmation_hashes": open_hashes[:12],
        "confirmed_hashes": confirmed_hashes[:12],
        "task_hash": first_value(launch_view, console_view, chain_view, workspace_view, review_view, key="task_hash"),
        "checkpoint_hash": first_value(launch_view, console_view, chain_view, workspace_view, review_view, key="checkpoint_hash"),
        "source_card_ids": first_list(launch_view, console_view, chain_view, workspace_view, review_view, key="source_card_ids")[:8],
        "source_anchor_count": first_int(launch_view, console_view, chain_view, workspace_view, review_view, key="source_anchor_count"),
        "help_level": safe_help_level(
            first_value(launch_view, console_view, chain_view, workspace_view, review_view, key="help_level") or "A2"
        ),
        "help_ledger_preview_hash": first_value(launch_view, chain_view, workspace_view, key="help_ledger_preview_hash"),
        "gate_receipt_hash": first_value(launch_view, console_view, review_view, key="gate_receipt_hash"),
        "decision_receipt_hash": first_value(launch_view, console_view, review_view, key="decision_receipt_hash"),
        "start_receipt_hash": first_value(launch_view, console_view, review_view, key="start_receipt_hash"),
        "chain_snapshot_hash": first_value(launch_view, chain_view, console_view, key="chain_snapshot_hash")
        or chain_view.get("snapshot_hash", ""),
        "chain_snapshot_receipt_hash": first_value(launch_view, console_view, key="chain_snapshot_receipt_hash"),
        "manual_confirmation_console_receipt_hash": first_value(
            launch_view, console_view, key="manual_confirmation_console_receipt_hash"
        ),
        "operator_run_prefill_hash": first_value(launch_view, key="operator_run_prefill_hash"),
        "launch_receipt_hash": launch_view.get("launch_receipt_hash", ""),
        "readiness_review_receipt_hash": review_view.get("review_receipt_hash", ""),
        "a0_a2_only": all(
            level in {"A0", "A1", "A2"}
            for level in [
                launch_view.get("help_level", "A2"),
                console_view.get("help_level", "A2"),
                chain_view.get("help_level", "A2"),
                workspace_view.get("help_level", "A2"),
                review_view.get("help_level", "A2"),
            ]
        ),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def binder_summary(*, selected_skill_tag: str, launch_view: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    launch_present = launch_view.get("status") == "python_exam_manual_cycle_launch_receipt_ready"
    launch_hash_present = bool(evidence.get("launch_receipt_hash"))
    required_hashes_present = all(
        bool(evidence.get(key))
        for key in [
            "task_hash",
            "checkpoint_hash",
            "gate_receipt_hash",
            "decision_receipt_hash",
            "start_receipt_hash",
            "chain_snapshot_hash",
            "manual_confirmation_console_receipt_hash",
            "operator_run_prefill_hash",
            "launch_receipt_hash",
        ]
    )
    if not launch_present or not launch_hash_present:
        action = "refresh_launch_receipt"
        reason = "launch_receipt_missing_or_unhashed"
    elif evidence.get("launch_decision") == "refresh_manual_console":
        action = "refresh_manual_confirmation_console"
        reason = "launch_receipt_requests_manual_console_refresh"
    elif evidence.get("launch_decision") == "abort_manual_cycle_review" or not evidence.get("a0_a2_only", False):
        action = "abort_manual_cycle_review"
        reason = "launch_receipt_or_help_level_not_safe"
    elif evidence.get("launch_decision") == "ready_for_manual_local_cycle" and required_hashes_present:
        action = "ready_for_human_manual_cycle_review"
        reason = "hash_only_stop_go_chain_ready_for_human_review"
    else:
        action = "continue_confirmation_review"
        reason = "confirmation_review_or_hash_metadata_still_open"
    return {
        "status": "python_exam_manual_cycle_evidence_binder_ready",
        "selected_skill_tag": selected_skill_tag,
        "launch_receipt_present": launch_present,
        "required_hashes_present": required_hashes_present,
        "launch_decision": evidence.get("launch_decision", "refresh_manual_console"),
        "next_safe_review_action": action,
        "next_safe_review_reason": reason,
        "allowed_next_safe_review_actions": sorted(BINDER_REVIEW_ACTIONS),
        "open_confirmation_count": int(evidence.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(evidence.get("confirmed_count", 0) or 0),
        "task_hash": evidence.get("task_hash", ""),
        "checkpoint_hash": evidence.get("checkpoint_hash", ""),
        "source_card_ids": list(evidence.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(evidence.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(evidence.get("help_level", "A2"))),
        "help_ledger_preview_hash": evidence.get("help_ledger_preview_hash", ""),
        "gate_receipt_hash": evidence.get("gate_receipt_hash", ""),
        "decision_receipt_hash": evidence.get("decision_receipt_hash", ""),
        "start_receipt_hash": evidence.get("start_receipt_hash", ""),
        "chain_snapshot_hash": evidence.get("chain_snapshot_hash", ""),
        "launch_receipt_hash": evidence.get("launch_receipt_hash", ""),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def evidence_binder_receipt(summary: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "evidence": evidence,
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_cycle_evidence_binder_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "next_safe_review_action": summary.get("next_safe_review_action", "refresh_launch_receipt"),
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-cycle-evidence-binder")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
