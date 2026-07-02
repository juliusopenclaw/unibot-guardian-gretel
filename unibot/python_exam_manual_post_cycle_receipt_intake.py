from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_local_cycle_manual_confirmation_console import safe_help_level
from .python_exam_manual_cycle_evidence_binder import safe_launch_receipt
from .python_exam_manual_cycle_launch_receipt import safe_manual_confirmation_console


PYTHON_EXAM_MANUAL_POST_CYCLE_RECEIPT_INTAKE_SCHEMA_VERSION = (
    "unibot-python-exam-manual-post-cycle-receipt-intake-v1"
)
PYTHON_EXAM_MANUAL_POST_CYCLE_RECEIPT_INTAKE_ENDPOINT = (
    "/api/unibot/course/python-exam-manual-post-cycle-receipt-intake"
)

POST_CYCLE_RECOMMENDATIONS = {
    "keep_post_cycle_review_open",
    "request_missing_post_cycle_hashes",
    "accept_hash_only_post_cycle_receipt_for_human_review",
    "reject_post_cycle_receipt",
}

REQUIRED_POST_CYCLE_HASHES = [
    "notebook_checkpoint_hash",
    "help_ledger_entry_hash",
    "task_hash",
    "operator_reflection_hash",
]

FORBIDDEN_METADATA_KEYS = {
    "raw_query",
    "query",
    "prompt",
    "course_raw_text",
    "raw_text",
    "source_text",
    "notebook_code",
    "cell_code",
    "code",
    "local_path",
    "path",
    "file_path",
    "value",
    "values",
    "solution",
    "solutions",
    "final_interpretation",
    "final_interpretations",
    "score",
    "ranking",
    "grade",
    "proctoring",
    "ai_detection",
    "automatic_grading",
    "exam_clearance",
}

HASH_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{12,128}$")


def build_python_exam_manual_post_cycle_receipt_intake(
    *,
    python_exam_manual_cycle_evidence_binder: dict[str, Any] | None = None,
    python_exam_manual_cycle_launch_receipt: dict[str, Any] | None = None,
    python_exam_manual_confirmation_console: dict[str, Any] | None = None,
    post_cycle_hash_metadata: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    binder = python_exam_manual_cycle_evidence_binder if isinstance(python_exam_manual_cycle_evidence_binder, dict) else {}
    launch_receipt = python_exam_manual_cycle_launch_receipt if isinstance(python_exam_manual_cycle_launch_receipt, dict) else {}
    manual_console = (
        python_exam_manual_confirmation_console if isinstance(python_exam_manual_confirmation_console, dict) else {}
    )
    raw_metadata = post_cycle_hash_metadata if isinstance(post_cycle_hash_metadata, dict) else {}
    binder_view = safe_evidence_binder(binder)
    launch_view = safe_launch_receipt(launch_receipt)
    console_view = safe_manual_confirmation_console(manual_console)
    metadata_view = safe_post_cycle_hash_metadata(raw_metadata)
    selected = str(
        selected_skill_tag
        or binder_view.get("selected_skill_tag", "")
        or launch_view.get("selected_skill_tag", "")
        or console_view.get("selected_skill_tag", "")
    ).strip()
    if not selected:
        selected = "general_python"

    summary = post_cycle_intake_summary(
        selected_skill_tag=selected,
        binder_view=binder_view,
        launch_view=launch_view,
        console_view=console_view,
        metadata_view=metadata_view,
    )
    receipt = post_cycle_intake_receipt(summary, metadata_view, binder_view, launch_view)
    payload = {
        "schema_version": PYTHON_EXAM_MANUAL_POST_CYCLE_RECEIPT_INTAKE_SCHEMA_VERSION,
        "artifact_type": "python_exam_manual_post_cycle_receipt_intake",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_manual_post_cycle_receipt_intake_ready",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Manual Post-Cycle Receipt Intake. It accepts only hash metadata that a human provides "
            "after an explicitly human-run local cycle action. It consumes Manual Cycle Evidence Binder, Launch "
            "Receipt, Manual Confirmation Console, and optional post-cycle hashes, then returns one review "
            "recommendation. It executes nothing, writes nothing, and never returns raw queries, course raw text, "
            "notebook code, local paths, values, solutions, final interpretations, scores, rankings, grades, "
            "proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "manual_post_cycle_receipt_intake_endpoint": PYTHON_EXAM_MANUAL_POST_CYCLE_RECEIPT_INTAKE_ENDPOINT,
        "selected_skill_tag": selected,
        "post_cycle_intake_summary": summary,
        "post_cycle_review_recommendation": summary["post_cycle_review_recommendation"],
        "post_cycle_hash_metadata": metadata_view,
        "pre_cycle_evidence": {
            "binder_status": binder_view.get("status", "missing"),
            "binder_next_safe_review_action": binder_view.get("next_safe_review_action", "refresh_launch_receipt"),
            "binder_receipt_hash": binder_view.get("binder_receipt_hash", ""),
            "launch_decision": launch_view.get("launch_decision", "refresh_manual_console"),
            "launch_receipt_hash": launch_view.get("launch_receipt_hash", ""),
            "manual_confirmation_console_receipt_hash": console_view.get("manual_confirmation_console_receipt_hash", ""),
            "open_confirmation_count": int(console_view.get("open_confirmation_count", 0) or 0),
            "confirmed_count": int(console_view.get("confirmed_count", 0) or 0),
            "exam_deployment_status": "not_cleared",
        },
        "manual_post_cycle_receipt_intake": receipt,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Post-Cycle Receipt Intake bleibt not_cleared."
        ),
        "next_actions": [
            f"Post-cycle review recommendation: {summary['post_cycle_review_recommendation']}.",
            "Use this intake only for human-reviewable hash metadata from a manual local action.",
            "Keep any raw notebook work, values, local files, and real exam clearance outside this artifact.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_evidence_binder(binder: dict[str, Any]) -> dict[str, Any]:
    summary = binder.get("binder_summary", {}) if isinstance(binder.get("binder_summary"), dict) else {}
    evidence = binder.get("manual_cycle_evidence", {}) if isinstance(binder.get("manual_cycle_evidence"), dict) else {}
    receipt = (
        binder.get("manual_cycle_evidence_binder_receipt", {})
        if isinstance(binder.get("manual_cycle_evidence_binder_receipt"), dict)
        else {}
    )
    return {
        "status": str(binder.get("status", "missing")),
        "selected_skill_tag": str(binder.get("selected_skill_tag") or summary.get("selected_skill_tag", "")),
        "next_safe_review_action": str(
            binder.get("next_safe_review_action")
            or summary.get("next_safe_review_action", "refresh_launch_receipt")
        ),
        "launch_decision": str(summary.get("launch_decision") or evidence.get("launch_decision", "")),
        "task_hash": str(summary.get("task_hash") or evidence.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash") or evidence.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids") or evidence.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", evidence.get("source_anchor_count", 0)) or 0),
        "help_level": safe_help_level(str(summary.get("help_level") or evidence.get("help_level", "A2"))),
        "help_ledger_preview_hash": str(
            summary.get("help_ledger_preview_hash") or evidence.get("help_ledger_preview_hash", "")
        ),
        "binder_receipt_hash": str(receipt.get("receipt_hash", "")),
        "launch_receipt_hash": str(summary.get("launch_receipt_hash") or evidence.get("launch_receipt_hash", "")),
        "required_hashes_present": bool(summary.get("required_hashes_present", False)),
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def safe_post_cycle_hash_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    forbidden_keys = sorted(key for key in metadata if str(key).lower() in FORBIDDEN_METADATA_KEYS)
    hash_fields = {
        field: safe_hash(metadata.get(field))
        for field in [
            "notebook_checkpoint_hash",
            "help_ledger_entry_hash",
            "task_hash",
            "operator_reflection_hash",
            "post_cycle_receipt_hash",
            "human_confirmation_hash",
        ]
    }
    source_card_ids = [safe_identifier(item) for item in (metadata.get("source_card_ids", []) or [])]
    source_anchor_hashes = [safe_hash(item) for item in (metadata.get("source_anchor_hashes", []) or [])]
    source_card_ids = [item for item in source_card_ids if item][:8]
    source_anchor_hashes = [item for item in source_anchor_hashes if item][:12]
    try:
        source_anchor_count = int(metadata.get("source_anchor_count", len(source_anchor_hashes)) or 0)
    except (TypeError, ValueError):
        source_anchor_count = 0
    missing_required = [field for field in REQUIRED_POST_CYCLE_HASHES if not hash_fields.get(field)]
    invalid_hash_fields = [
        field
        for field in REQUIRED_POST_CYCLE_HASHES + ["post_cycle_receipt_hash", "human_confirmation_hash"]
        if metadata.get(field) and not hash_fields.get(field)
    ]
    return {
        "status": "post_cycle_hash_metadata_present" if metadata else "post_cycle_hash_metadata_missing",
        "notebook_checkpoint_hash": hash_fields["notebook_checkpoint_hash"],
        "help_ledger_entry_hash": hash_fields["help_ledger_entry_hash"],
        "task_hash": hash_fields["task_hash"],
        "operator_reflection_hash": hash_fields["operator_reflection_hash"],
        "post_cycle_receipt_hash": hash_fields["post_cycle_receipt_hash"],
        "human_confirmation_hash": hash_fields["human_confirmation_hash"],
        "source_card_ids": source_card_ids,
        "source_anchor_hashes": source_anchor_hashes,
        "source_anchor_count": source_anchor_count,
        "missing_required_hashes": missing_required,
        "invalid_hash_fields": invalid_hash_fields,
        "forbidden_metadata_keys": forbidden_keys,
        "hash_only": bool(metadata) and not forbidden_keys and not invalid_hash_fields,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def post_cycle_intake_summary(
    *,
    selected_skill_tag: str,
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
    console_view: dict[str, Any],
    metadata_view: dict[str, Any],
) -> dict[str, Any]:
    binder_ready = binder_view.get("status") == "python_exam_manual_cycle_evidence_binder_ready"
    pre_cycle_ready = binder_view.get("next_safe_review_action") == "ready_for_human_manual_cycle_review"
    rejected = bool(metadata_view.get("forbidden_metadata_keys") or metadata_view.get("invalid_hash_fields"))
    metadata_present = metadata_view.get("status") == "post_cycle_hash_metadata_present"
    missing_hashes = list(metadata_view.get("missing_required_hashes", []) or [])
    source_bound = bool(metadata_view.get("source_card_ids") or metadata_view.get("source_anchor_hashes"))
    task_matches = (
        not metadata_view.get("task_hash")
        or not binder_view.get("task_hash")
        or metadata_view.get("task_hash") == binder_view.get("task_hash")
    )
    if rejected:
        recommendation = "reject_post_cycle_receipt"
        reason = "post_cycle_metadata_contains_forbidden_or_invalid_fields"
    elif not binder_ready or not pre_cycle_ready:
        recommendation = "keep_post_cycle_review_open"
        reason = "pre_cycle_stop_go_chain_not_ready_for_post_cycle_intake"
    elif not metadata_present or missing_hashes or not source_bound:
        recommendation = "request_missing_post_cycle_hashes"
        reason = "post_cycle_hash_metadata_missing_or_incomplete"
    elif not task_matches:
        recommendation = "reject_post_cycle_receipt"
        reason = "post_cycle_task_hash_does_not_match_pre_cycle_binder"
    else:
        recommendation = "accept_hash_only_post_cycle_receipt_for_human_review"
        reason = "hash_only_post_cycle_receipt_ready_for_human_review"
    return {
        "status": "python_exam_manual_post_cycle_receipt_intake_ready",
        "selected_skill_tag": selected_skill_tag,
        "post_cycle_review_recommendation": recommendation,
        "post_cycle_review_reason": reason,
        "allowed_post_cycle_review_recommendations": sorted(POST_CYCLE_RECOMMENDATIONS),
        "binder_status": binder_view.get("status", "missing"),
        "binder_next_safe_review_action": binder_view.get("next_safe_review_action", "refresh_launch_receipt"),
        "launch_decision": launch_view.get("launch_decision", binder_view.get("launch_decision", "")),
        "manual_confirmation_action": console_view.get("next_manual_confirmation_action", ""),
        "metadata_status": metadata_view.get("status", "post_cycle_hash_metadata_missing"),
        "missing_required_hashes": missing_hashes,
        "forbidden_metadata_keys": list(metadata_view.get("forbidden_metadata_keys", []) or []),
        "invalid_hash_fields": list(metadata_view.get("invalid_hash_fields", []) or []),
        "task_hash": metadata_view.get("task_hash") or binder_view.get("task_hash", ""),
        "pre_cycle_task_hash": binder_view.get("task_hash", ""),
        "notebook_checkpoint_hash": metadata_view.get("notebook_checkpoint_hash", ""),
        "help_ledger_entry_hash": metadata_view.get("help_ledger_entry_hash", ""),
        "operator_reflection_hash": metadata_view.get("operator_reflection_hash", ""),
        "source_card_ids": list(metadata_view.get("source_card_ids", []) or binder_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_hash_count": len(metadata_view.get("source_anchor_hashes", []) or []),
        "help_level": safe_help_level(str(binder_view.get("help_level", "A2"))),
        "binder_receipt_hash": binder_view.get("binder_receipt_hash", ""),
        "launch_receipt_hash": launch_view.get("launch_receipt_hash", binder_view.get("launch_receipt_hash", "")),
        "post_cycle_receipt_hash": metadata_view.get("post_cycle_receipt_hash", ""),
        "human_confirmation_hash": metadata_view.get("human_confirmation_hash", ""),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
    }


def post_cycle_intake_receipt(
    summary: dict[str, Any],
    metadata_view: dict[str, Any],
    binder_view: dict[str, Any],
    launch_view: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "metadata": metadata_view,
        "binder_receipt_hash": binder_view.get("binder_receipt_hash", ""),
        "launch_receipt_hash": launch_view.get("launch_receipt_hash", ""),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "manual_post_cycle_receipt_intake_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "post_cycle_review_recommendation": summary.get("post_cycle_review_recommendation", "keep_post_cycle_review_open"),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_execution_started": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def safe_hash(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    clean = value.strip()
    if not clean or "/" in clean or "\\" in clean or "\n" in clean:
        return ""
    if not HASH_PATTERN.match(clean):
        return ""
    return clean


def safe_identifier(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    clean = value.strip()
    if not clean or "/" in clean or "\\" in clean or "\n" in clean:
        return ""
    if len(clean) > 80:
        return ""
    return clean


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-manual-post-cycle-receipt-intake")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
