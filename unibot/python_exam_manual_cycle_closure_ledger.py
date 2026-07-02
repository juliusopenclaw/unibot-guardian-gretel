from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_evidence_binder import safe_launch_receipt
from .python_exam_manual_cycle_launch_receipt import safe_manual_confirmation_console
from .python_exam_manual_post_cycle_receipt_intake import safe_evidence_binder


PYTHON_EXAM_MANUAL_CYCLE_CLOSURE_LEDGER_SCHEMA_VERSION = "unibot-python-exam-manual-cycle-closure-ledger-v1"
PYTHON_EXAM_MANUAL_CYCLE_CLOSURE_LEDGER_ENDPOINT = "/api/unibot/course/python-exam-manual-cycle-closure-ledger"

CLOSURE_LEDGER_DECISIONS = {
    "keep_cycle_open",
    "request_post_cycle_hash_review",
    "close_cycle_for_human_review",
    "reject_cycle_closure",
}


def build_python_exam_manual_cycle_closure_ledger(
    *,
    python_exam_manual_post_cycle_receipt_intake: dict[str, Any] | None = None,
    python_exam_manual_cycle_evidence_binder: dict[str, Any] | None = None,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    post_cycle_intake = (
        python_exam_manual_post_cycle_receipt_intake
        if isinstance(python_exam_manual_post_cycle_receipt_intake, dict)
        else {}
    )
    evidence_binder = (
        python_exam_manual_cycle_evidence_binder if isinstance(python_exam_manual_cycle_evidence_binder, dict) else {}
    )
    launch_receipt = python_exam_manual_cycle_launch_receipt if isinstance(python_exam_manual_cycle_launch_receipt, dict) else {}
    manual_console = (
        python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    )
    intake_view = safe_post_cycle_intake(post_cycle_intake)
    binder_view = safe_evidence_binder(evidence_binder)
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    selected = str(
        selected_skill_tag
        or intake_view.get("selected_skill_tag", "")
        or binder_view.get("selected_skill_tag", "")
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"
    summary = closure_summary(
        selected_skill_tag=selected,
        intake_view=intake_view,
        binder_view=binder_view,
        launch_view=launch_view,
        console_view=console_view,
    )
    ledger_entries = closure_ledger_entries(summary, intake_view, binder_view, launch_view, console_view)
    receipt = closure_ledger_receipt(summary, ledger_entries)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_CYCLE_CLOSURE_LEDGER_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_cycle_closure_ledger",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_cycle_closure_ledger_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Cycle Closure Ledger. It consumes only Manual Post-Cycle Receipt Intake, "
            "Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata to close or keep open "
            "a human-reviewable local cycle. It exposes only hash metadata, Source-Card anchors, task/checkpoint "
            "hashes, Help-Ledger hash, operator reflection hash, intake recommendation, and one ledger decision. "
            "It executes nothing, writes nothing, and never returns raw queries, course raw text, notebook code, "
            "local paths, values, solutions, final interpretations, scores, rankings, grades, proctoring, AI "
            "detection, automatic grading, or exam clearance claims."
        ),
        "manual_cycle_closure_ledger_endpoint": PYTHON_EXAM_MANUAL_CYCLE_CLOSURE_LEDGER_ENDPOINT,
        "selected_skill_tag": selected,
        "closure_summary": summary,
        "closure_ledger_decision": summary["closure_ledger_decision"],
        "closure_ledger_entries": ledger_entries,
        "manual_cycle_closure_ledger_receipt": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Closure Ledger bleibt not_cleared."
        ),
        "next_actions": [
            f"Closure ledger decision: {summary['closure_ledger_decision']}.",
            "Use this ledger only as a human-reviewable cycle closure record.",
            "Keep raw notebook work, values, local files, scoring, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_post_cycle_intake(intake: dict[str, Any]) -> dict[str, Any]:
    summary = (
        intake.get("post_cycle_intake_summary", {}) if isinstance(intake.get("post_cycle_intake_summary"), dict) else {}
    )
    metadata = (
        intake.get("post_cycle_hash_metadata", {}) if isinstance(intake.get("post_cycle_hash_metadata"), dict) else {}
    )
    receipt = (
        intake.get("manual_post_cycle_receipt_intake", {})
        if isinstance(intake.get("manual_post_cycle_receipt_intake"), dict)
        else {}
    )
    return {
        "status": str(intake.get("status", "missing")),
        "selected_skill_tag": str(intake.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "post_cycle_review_recommendation": str(
            intake.get("post_cycle_review_recommendation")
            or summary.get("post_cycle_review_recommendation", "keep_post_cycle_review_open")
        ),
        "post_cycle_review_reason": str(summary.get("post_cycle_review_reason", "")),
        "binder_next_safe_review_action": str(summary.get("binder_next_safe_review_action", "")),
        "launch_decision": str(summary.get("launch_decision", "")),
        "manual_confirmation_action": str(summary.get("manual_confirmation_action", "")),
        "metadata_status": str(summary.get("metadata_status", metadata.get("status", "post_cycle_hash_metadata_missing"))),
        "missing_required_hashes": [str(item) for item in (summary.get("missing_required_hashes", []) or [])][:12],
        "forbidden_metadata_keys": [str(item) for item in (summary.get("forbidden_metadata_keys", []) or [])][:12],
        "invalid_hash_fields": [str(item) for item in (summary.get("invalid_hash_fields", []) or [])][:12],
        "task_hash": str(summary.get("task_hash") or metadata.get("task_hash", "")),
        "pre_cycle_task_hash": str(summary.get("pre_cycle_task_hash", "")),
        "notebook_checkpoint_hash": str(summary.get("notebook_checkpoint_hash") or metadata.get("notebook_checkpoint_hash", "")),
        "help_ledger_entry_hash": str(summary.get("help_ledger_entry_hash") or metadata.get("help_ledger_entry_hash", "")),
        "operator_reflection_hash": str(summary.get("operator_reflection_hash") or metadata.get("operator_reflection_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or metadata.get("source_card_ids", []) or [])][:8],
        "source_anchor_hash_count": int(summary.get("source_anchor_hash_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level", "A2"))),
        "binder_receipt_hash": str(summary.get("binder_receipt_hash", "")),
        "launch_receipt_hash": str(summary.get("launch_receipt_hash", "")),
        "post_cycle_receipt_hash": str(summary.get("post_cycle_receipt_hash") or metadata.get("post_cycle_receipt_hash", "")),
        "human_confirmation_hash": str(summary.get("human_confirmation_hash") or metadata.get("human_confirmation_hash", "")),
        "intake_receipt_hash": str(receipt.get("receipt_hash", "")),
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", False)),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def closure_summary(
    *,
    selected_skill_tag: str,
    intake_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
) -> dict[str, Any]:
    recommendation = intake_view.get("post_cycle_review_recommendation", "keep_post_cycle_review_open")
    intake_present = intake_view.get("status") == "python_exam_manual_post_cycle_receipt_intake_ready"
    if not intake_present or recommendation == "keep_post_cycle_review_open":
        decision = "keep_cycle_open"
        reason = "post_cycle_intake_missing_or_open"
    elif recommendation == "request_missing_post_cycle_hashes":
        decision = "request_post_cycle_hash_review"
        reason = "post_cycle_hash_review_missing_required_hashes"
    elif recommendation == "reject_post_cycle_receipt":
        decision = "reject_cycle_closure"
        reason = "post_cycle_intake_rejected_receipt"
    elif recommendation == "accept_hash_only_post_cycle_receipt_for_human_review":
        decision = "close_cycle_for_human_review"
        reason = "hash_only_cycle_ready_for_human_closure_review"
    else:
        decision = "reject_cycle_closure"
        reason = "unsupported_post_cycle_intake_recommendation"
    accepted_hashes = accepted_post_cycle_hashes(intake_view) if decision == "close_cycle_for_human_review" else {}
    return {
        "status": "python_exam_manual_cycle_closure_ledger_ready",
        "selected_skill_tag": selected_skill_tag,
        "closure_ledger_decision": decision,
        "closure_ledger_reason": reason,
        "allowed_closure_ledger_decisions": sorted(CLOSURE_LEDGER_DECISIONS),
        "post_cycle_review_recommendation": recommendation,
        "post_cycle_review_reason": intake_view.get("post_cycle_review_reason", ""),
        "pre_cycle_stop_go_action": binder_view.get("next_safe_review_action", ""),
        "launch_decision": launch_view.get("launch_decision", binder_view.get("launch_decision", "")),
        "manual_confirmation_action": console_view.get("next_manual_confirmation_action", ""),
        "open_confirmation_count": int(console_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(console_view.get("confirmed_count", 0) or 0),
        "missing_required_hashes": list(intake_view.get("missing_required_hashes", []) or [])[:12],
        "forbidden_metadata_keys": list(intake_view.get("forbidden_metadata_keys", []) or [])[:12],
        "invalid_hash_fields": list(intake_view.get("invalid_hash_fields", []) or [])[:12],
        "accepted_post_cycle_hashes": accepted_hashes,
        "task_hash": intake_view.get("task_hash") or binder_view.get("task_hash", ""),
        "pre_cycle_task_hash": intake_view.get("pre_cycle_task_hash") or binder_view.get("task_hash", ""),
        "checkpoint_hash": binder_view.get("checkpoint_hash", ""),
        "notebook_checkpoint_hash": intake_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_hash": intake_view.get("help_ledger_entry_hash") or binder_view.get("help_ledger_preview_hash", ""),
        "operator_reflection_hash": intake_view.get("operator_reflection_hash", ""),
        "source_card_ids": list(intake_view.get("source_card_ids") or binder_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": int(intake_view.get("source_anchor_hash_count", 0) or 0),
        "help_level": safe_help_level(str(intake_view.get("help_level") or binder_view.get("help_level", "A2"))),
        "binder_receipt_hash": intake_view.get("binder_receipt_hash") or binder_view.get("binder_receipt_hash", ""),
        "launch_receipt_hash": intake_view.get("launch_receipt_hash") or launch_view.get("launch_receipt_hash", ""),
        "post_cycle_receipt_hash": intake_view.get("post_cycle_receipt_hash", ""),
        "intake_receipt_hash": intake_view.get("intake_receipt_hash", ""),
        "next_safe_review_action": next_safe_review_action(decision),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def accepted_post_cycle_hashes(intake_view: dict[str, Any]) -> dict[str, str]:
    return {
        "notebook_checkpoint_hash": intake_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_entry_hash": intake_view.get("help_ledger_entry_hash", ""),
        "task_hash": intake_view.get("task_hash", ""),
        "operator_reflection_hash": intake_view.get("operator_reflection_hash", ""),
        "post_cycle_receipt_hash": intake_view.get("post_cycle_receipt_hash", ""),
        "human_confirmation_hash": intake_view.get("human_confirmation_hash", ""),
    }


def next_safe_review_action(decision: str) -> str:
    if decision == "close_cycle_for_human_review":
        return "review_closed_cycle_evidence_with_human"
    if decision == "request_post_cycle_hash_review":
        return "collect_missing_post_cycle_hash_metadata"
    if decision == "reject_cycle_closure":
        return "return_to_post_cycle_receipt_intake_review"
    return "continue_manual_cycle_review"


def closure_ledger_entries(
    summary: dict[str, Any],
    intake_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
) -> list[dict[str, Any]]:
    seeds = [
        {
            "entry_id": "pre_cycle_stop_go_chain",
            "status": binder_view.get("status", "missing"),
            "review_action": binder_view.get("next_safe_review_action", ""),
            "binder_receipt_hash": summary.get("binder_receipt_hash", ""),
            "launch_receipt_hash": summary.get("launch_receipt_hash", ""),
        },
        {
            "entry_id": "manual_confirmation_state",
            "status": console_view.get("status", "missing"),
            "manual_confirmation_action": summary.get("manual_confirmation_action", ""),
            "open_confirmation_count": summary.get("open_confirmation_count", 0),
            "confirmed_count": summary.get("confirmed_count", 0),
        },
        {
            "entry_id": "post_cycle_receipt_intake",
            "status": intake_view.get("status", "missing"),
            "recommendation": summary.get("post_cycle_review_recommendation", ""),
            "intake_receipt_hash": summary.get("intake_receipt_hash", ""),
            "missing_required_hashes": summary.get("missing_required_hashes", []),
        },
        {
            "entry_id": "cycle_closure_decision",
            "status": summary.get("closure_ledger_decision", "keep_cycle_open"),
            "reason": summary.get("closure_ledger_reason", ""),
            "next_safe_review_action": summary.get("next_safe_review_action", ""),
            "help_level": summary.get("help_level", "A2"),
        },
    ]
    entries = []
    for seed in seeds:
        entry_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
        entry = dict(seed)
        entry.update(
            {
                "entry_hash": entry_hash,
                "not_cleared_receipt": True,
                "local_writes_requested": False,
                "local_execution_started": False,
                "raw_text_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
                "exam_deployment_status": "not_cleared",
            }
        )
        entries.append(entry)
    return entries


def closure_ledger_receipt(summary: dict[str, Any], ledger_entries: list[dict[str, Any]]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "ledger_entry_hashes": [entry.get("entry_hash", "") for entry in ledger_entries],
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_cycle_closure_ledger_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "closure_ledger_decision": summary.get("closure_ledger_decision", "keep_cycle_open"),
        "not_cleared_receipt": True,
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-cycle-closure-ledger")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
