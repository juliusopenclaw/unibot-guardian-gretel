from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_SCHEMA_VERSION = "unibot-python-exam-local-cycle-readiness-review-v1"
PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-readiness-review"


def build_python_exam_local_cycle_readiness_review(
    *,
    python_exam_local_cycle_start_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    packet = python_exam_local_cycle_start_packet if isinstance(python_exam_local_cycle_start_packet, dict) else {}
    start_view = safe_start_packet(packet)
    selected = str(selected_skill_tag or start_view.get("selected_skill_tag", "") or "").strip()
    if not selected:
        selected = "general_python"
    summary = readiness_review_summary(selected_skill_tag=selected, start_view=start_view, packet=packet)
    packet_view = {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": start_view.get("selected_skill_tag", selected),
        "start_status": start_view.get("start_status", "missing"),
        "blocked_reason": start_view.get("blocked_reason", ""),
        "next_safe_action": start_view.get("next_safe_action", "review_skill_readiness"),
        "next_safe_user_action": start_view.get("next_safe_user_action", "review_confirmed_start_packet"),
        "task_hash": start_view.get("task_hash", ""),
        "checkpoint_hash": start_view.get("checkpoint_hash", ""),
        "source_card_ids": list(start_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(start_view.get("source_anchor_count", 0) or 0),
        "help_level": start_view.get("help_level", "A2"),
        "gate_receipt_id": start_view.get("gate_receipt_id", ""),
        "gate_receipt_hash": start_view.get("gate_receipt_hash", ""),
        "decision_receipt_id": start_view.get("decision_receipt_id", ""),
        "decision_receipt_hash": start_view.get("decision_receipt_hash", ""),
        "start_receipt_id": start_view.get("start_receipt_id", ""),
        "start_receipt_hash": start_view.get("start_receipt_hash", ""),
        "open_confirmation_count": int(start_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(start_view.get("confirmed_count", 0) or 0),
        "blocked_for_confirmation": bool(start_view.get("blocked_for_confirmation", False)),
        "ready_for_manual_local_cycle_review": bool(start_view.get("ready_for_manual_local_cycle_review", False)),
        "open_confirmations": list(start_view.get("open_confirmations", []) or [])[:8],
        "confirmed_hash_metadata": list(start_view.get("confirmed_hash_metadata", []) or [])[:8],
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }
    report = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_readiness_review",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Readiness Review. It consumes the Local Cycle Start Packet and produces a "
            "human-reviewable recommendation about whether the local cycle stays blocked_for_confirmation, needs "
            "missing confirmation review, or is ready for manual local cycle review after full human confirmation. "
            "It only uses metadata, hashes, Source-Card anchors, task and checkpoint hashes, gate/decision/start "
            "receipt hashes, A0-A2 help level, and confirmation counts. It never executes a local action, writes "
            "anything, or returns raw queries, course raw text, notebook code, local paths, values, solutions, "
            "final interpretations, scores, rankings, grades, proctoring, AI detection, automatic grading, or "
            "exam clearance claims."
        ),
        "local_cycle_readiness_review_endpoint": PYTHON_EXAM_LOCAL_CYCLE_READINESS_REVIEW_ENDPOINT,
        "selected_skill_tag": selected,
        "local_cycle_start_packet_status": start_view.get("status", "missing"),
        "local_cycle_start_packet": packet_view,
        "readiness_review_summary": summary,
        "readiness_review_recommendation": summary["recommendation"],
        "readiness_review_reason": summary["recommendation_reason"],
        "readiness_review_checks": {
            "packet_present": summary["packet_present"],
            "hash_metadata_complete": summary["hash_metadata_complete"],
            "blocked_for_confirmation": summary["blocked_for_confirmation"],
            "request_missing_confirmation_review": summary["request_missing_confirmation_review"],
            "ready_for_manual_local_cycle_review": summary["ready_for_manual_local_cycle_review"],
            "keep_blocked": summary["keep_blocked"],
        },
        "readiness_review_receipt": readiness_review_receipt(summary, packet_view),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Readiness Review bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def safe_start_packet(packet: dict[str, Any]) -> dict[str, Any]:
    summary = packet.get("local_cycle_start_summary", {}) if isinstance(packet.get("local_cycle_start_summary"), dict) else {}
    start = packet.get("start_packet", {}) if isinstance(packet.get("start_packet"), dict) else {}
    receipt = packet.get("local_cycle_start_receipt", {}) if isinstance(packet.get("local_cycle_start_receipt"), dict) else {}
    open_confirmations = safe_confirmation_items(start.get("open_confirmations", []) if isinstance(start.get("open_confirmations"), list) else [])
    confirmed_hash_metadata = safe_confirmation_items(
        start.get("confirmed_hash_metadata", []) if isinstance(start.get("confirmed_hash_metadata"), list) else []
    )
    start_status = str(summary.get("start_status") or start.get("start_status") or "missing")
    selected = str(summary.get("selected_skill_tag") or start.get("selected_skill_tag") or packet.get("selected_skill_tag", "")).strip()
    return {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": selected,
        "start_status": start_status,
        "blocked_reason": str(summary.get("blocked_reason") or start.get("blocked_reason") or ""),
        "next_safe_action": safe_action(str(summary.get("next_safe_action") or start.get("next_safe_action") or "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action") or start.get("next_safe_user_action") or ""),
        "task_hash": str(summary.get("selected_task_hash") or start.get("task_hash") or ""),
        "checkpoint_hash": str(summary.get("checkpoint_hash") or start.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (start.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(start.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(summary.get("help_level") or start.get("help_level") or "A2")),
        "gate_receipt_id": str(summary.get("gate_receipt_id") or start.get("gate_receipt_id") or ""),
        "gate_receipt_hash": str(start.get("gate_receipt_hash") or ""),
        "decision_receipt_id": str(summary.get("decision_receipt_id") or start.get("decision_receipt_id") or ""),
        "decision_receipt_hash": str(start.get("decision_receipt_hash") or ""),
        "start_receipt_id": str(receipt.get("receipt_id", "")),
        "start_receipt_hash": str(receipt.get("receipt_hash", "")),
        "open_confirmation_count": len(open_confirmations),
        "confirmed_count": len(confirmed_hash_metadata),
        "open_confirmations": open_confirmations,
        "confirmed_hash_metadata": confirmed_hash_metadata,
        "blocked_for_confirmation": start_status == "blocked_for_confirmation",
        "ready_for_manual_local_cycle_review": start_status == "ready_after_human_confirmation",
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_confirmation_items(items: list[Any]) -> list[dict[str, Any]]:
    safe = []
    for item in items:
        if not isinstance(item, dict):
            continue
        safe.append(
            {
                "step_id": str(item.get("step_id", "")),
                "action": str(item.get("action", "")),
                "card_hash": str(item.get("card_hash", "")),
                "selected_task_hash": str(item.get("selected_task_hash", "")),
                "checkpoint_hash": str(item.get("checkpoint_hash", "")),
                "help_level": safe_help_level(str(item.get("help_level", "A2"))),
                "operator_confirmed": bool(item.get("operator_confirmed", False)),
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
            }
        )
    return safe


def readiness_review_summary(*, selected_skill_tag: str, start_view: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    packet_present = start_view.get("status") != "missing"
    required_hashes = [
        str(start_view.get("task_hash", "")),
        str(start_view.get("checkpoint_hash", "")),
        str(start_view.get("gate_receipt_hash", "")),
        str(start_view.get("decision_receipt_hash", "")),
        str(start_view.get("start_receipt_hash", "")),
    ]
    has_required_hashes = all(required_hashes) and bool(start_view.get("selected_skill_tag"))
    has_anchor_metadata = int(start_view.get("source_anchor_count", 0) or 0) > 0 and bool(start_view.get("source_card_ids", []))
    help_level = str(start_view.get("help_level", "A2"))
    help_level_safe = help_level in {"A0", "A1", "A2"}
    start_status = str(start_view.get("start_status", "missing"))
    open_confirmation_count = int(start_view.get("open_confirmation_count", 0) or 0)
    confirmed_count = int(start_view.get("confirmed_count", 0) or 0)
    blocked_for_confirmation = bool(start_view.get("blocked_for_confirmation", False))
    request_missing_confirmation_review = open_confirmation_count > 0
    ready_for_manual_local_cycle_review = (
        start_status == "ready_after_human_confirmation"
        and confirmed_count > 0
        and open_confirmation_count == 0
        and has_required_hashes
        and has_anchor_metadata
        and help_level_safe
    )
    keep_blocked = not packet_present or not has_required_hashes or not has_anchor_metadata or not help_level_safe or (
        not request_missing_confirmation_review and not ready_for_manual_local_cycle_review
    )
    if not packet_present:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_start_packet"
    elif not has_required_hashes:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_hash_metadata"
    elif not has_anchor_metadata:
        recommendation = "keep_blocked"
        recommendation_reason = "missing_source_anchor_metadata"
    elif not help_level_safe:
        recommendation = "keep_blocked"
        recommendation_reason = "unsupported_help_level"
    elif request_missing_confirmation_review:
        recommendation = "request_missing_confirmation_review"
        recommendation_reason = "open_confirmations_present"
    elif ready_for_manual_local_cycle_review:
        recommendation = "ready_for_manual_local_cycle_review"
        recommendation_reason = "full_human_confirmation_present"
    else:
        recommendation = "keep_blocked"
        recommendation_reason = "start_packet_not_ready"
    return {
        "status": "python_exam_local_cycle_readiness_review_ready" if packet_present else "python_exam_local_cycle_readiness_review_attention",
        "selected_skill_tag": selected_skill_tag,
        "packet_status": start_view.get("status", "missing"),
        "start_status": start_status,
        "blocked_reason": str(start_view.get("blocked_reason", "")),
        "blocked_for_confirmation": blocked_for_confirmation,
        "request_missing_confirmation_review": recommendation == "request_missing_confirmation_review",
        "ready_for_manual_local_cycle_review": recommendation == "ready_for_manual_local_cycle_review",
        "keep_blocked": recommendation == "keep_blocked",
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "open_confirmation_count": open_confirmation_count,
        "confirmed_count": confirmed_count,
        "task_hash": str(start_view.get("task_hash", "")),
        "checkpoint_hash": str(start_view.get("checkpoint_hash", "")),
        "gate_receipt_id": str(start_view.get("gate_receipt_id", "")),
        "gate_receipt_hash": str(start_view.get("gate_receipt_hash", "")),
        "decision_receipt_id": str(start_view.get("decision_receipt_id", "")),
        "decision_receipt_hash": str(start_view.get("decision_receipt_hash", "")),
        "start_receipt_id": str(start_view.get("start_receipt_id", "")),
        "start_receipt_hash": str(start_view.get("start_receipt_hash", "")),
        "source_card_ids": list(start_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(start_view.get("source_anchor_count", 0) or 0),
        "help_level": help_level,
        "next_safe_action": str(start_view.get("next_safe_action", "")),
        "next_safe_user_action": str(start_view.get("next_safe_user_action", "")),
        "hash_metadata_complete": has_required_hashes and has_anchor_metadata and help_level_safe,
        "packet_present": packet_present,
        "exam_deployment_status": "not_cleared",
    }


def readiness_review_receipt(summary: dict[str, Any], packet_view: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps({"summary": summary, "packet_view": packet_view}, sort_keys=True, ensure_ascii=False)
    )
    return {
        "status": "local_cycle_readiness_review_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def safe_action(action: str) -> str:
    if action in {
        "run_next_microtask",
        "repeat_current_microtask",
        "start_first_microtask",
        "return_to_skill_dashboard",
        "review_skill_readiness",
    }:
        return action
    return "review_skill_readiness"


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        f"Recommendation: {summary['recommendation']}.",
        "Keep the review read-only; do not start any local write from this packet.",
        "Use the result as the human-checkpoint before the next local exam work cycle.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-readiness-review")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
