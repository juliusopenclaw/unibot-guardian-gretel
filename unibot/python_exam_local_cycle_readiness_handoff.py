from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_SCHEMA_VERSION = "unibot-python-exam-local-cycle-readiness-handoff-v1"
PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_ENDPOINT = "/api/unibot/course/python-exam-local-cycle-readiness-handoff"
OPERATOR_RUN_ENDPOINT = "/api/unibot/exam-workspace/operator-run"


def build_python_exam_local_cycle_readiness_handoff(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_start_packet: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    review = python_exam_local_cycle_readiness_review if isinstance(python_exam_local_cycle_readiness_review, dict) else {}
    packet = python_exam_local_cycle_start_packet if isinstance(python_exam_local_cycle_start_packet, dict) else {}
    review_view = safe_review_view(review)
    packet_view = safe_packet_view(packet, review_view)
    selected = str(selected_skill_tag or review_view.get("selected_skill_tag", "") or packet_view.get("selected_skill_tag", "")).strip()
    if not selected:
        selected = "general_python"
    ready_for_operator_prefill = review_view["recommendation"] in {
        "request_missing_confirmation_review",
        "ready_for_manual_local_cycle_review",
    } and review_view["hash_metadata_complete"]
    summary = handoff_summary(
        selected_skill_tag=selected,
        review_view=review_view,
        packet_view=packet_view,
        ready_for_operator_prefill=ready_for_operator_prefill,
    )
    operator_prefill = build_operator_run_prefill(review_view, packet_view, ready_for_operator_prefill)
    manual_handoff = build_manual_local_cycle_handoff(review_view, packet_view, operator_prefill, ready_for_operator_prefill)
    payload = {
        "schema_version": PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_SCHEMA_VERSION,
        "artifact_type": "python_exam_local_cycle_readiness_handoff",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Local Cycle Readiness Handoff. It turns the Readiness Review into a safe operator "
            "prefill and a manual handoff packet for the next local cycle without executing anything. It consumes "
            "only metadata, hashes, Source-Card anchors, task/checkpoint hashes, the Readiness Review "
            "recommendation, and the Start Packet, then prepares an operator-run dry-run prefill. It never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance claims."
        ),
        "local_cycle_readiness_handoff_endpoint": PYTHON_EXAM_LOCAL_CYCLE_READINESS_HANDOFF_ENDPOINT,
        "selected_skill_tag": selected,
        "readiness_review_status": review_view["status"],
        "local_cycle_start_packet_status": packet_view["status"],
        "handoff_summary": summary,
        "operator_run_prefill": operator_prefill,
        "manual_local_cycle_handoff": manual_handoff,
        "handoff_receipt": handoff_receipt(summary, operator_prefill, manual_handoff),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Local Cycle Handoff bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_review_view(review: dict[str, Any]) -> dict[str, Any]:
    summary = review.get("readiness_review_summary", {}) if isinstance(review.get("readiness_review_summary"), dict) else {}
    checks = review.get("readiness_review_checks", {}) if isinstance(review.get("readiness_review_checks"), dict) else {}
    return {
        "status": review.get("status", "missing"),
        "selected_skill_tag": str(review.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "recommendation": str(review.get("readiness_review_recommendation", summary.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(review.get("readiness_review_reason", summary.get("recommendation_reason", "missing_start_packet"))),
        "packet_present": bool(summary.get("packet_present", False)),
        "hash_metadata_complete": bool(summary.get("hash_metadata_complete", False)),
        "blocked_for_confirmation": bool(summary.get("blocked_for_confirmation", False)),
        "request_missing_confirmation_review": bool(
            checks.get("request_missing_confirmation_review", summary.get("recommendation") == "request_missing_confirmation_review")
        ),
        "ready_for_manual_local_cycle_review": bool(
            checks.get("ready_for_manual_local_cycle_review", summary.get("recommendation") == "ready_for_manual_local_cycle_review")
        ),
        "keep_blocked": bool(checks.get("keep_blocked", summary.get("recommendation") == "keep_blocked")),
        "open_confirmation_count": int(summary.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(summary.get("confirmed_count", 0) or 0),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "gate_receipt_hash": str(summary.get("gate_receipt_hash", "")),
        "decision_receipt_hash": str(summary.get("decision_receipt_hash", "")),
        "start_receipt_hash": str(summary.get("start_receipt_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_level": str(summary.get("help_level", "A2")),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "exam_deployment_status": "not_cleared",
    }


def safe_packet_view(packet: dict[str, Any], review_view: dict[str, Any]) -> dict[str, Any]:
    start = packet.get("local_cycle_start_packet", {}) if isinstance(packet.get("local_cycle_start_packet"), dict) else {}
    packet_summary = packet.get("local_cycle_start_summary", {}) if isinstance(packet.get("local_cycle_start_summary"), dict) else {}
    if not start:
        start = packet.get("start_packet", {}) if isinstance(packet.get("start_packet"), dict) else {}
    selected_skill_tag = str(
        packet.get("selected_skill_tag")
        or start.get("selected_skill_tag")
        or packet_summary.get("selected_skill_tag")
        or review_view.get("selected_skill_tag", "")
    )
    return {
        "status": packet.get("status", "missing"),
        "selected_skill_tag": selected_skill_tag,
        "start_status": str(packet_summary.get("start_status") or start.get("start_status") or "missing"),
        "task_hash": str(packet_summary.get("selected_task_hash") or start.get("task_hash") or ""),
        "checkpoint_hash": str(packet_summary.get("checkpoint_hash") or start.get("checkpoint_hash") or ""),
        "source_card_ids": [str(item) for item in (start.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(start.get("source_anchor_count", 0) or 0),
        "help_level": str(packet_summary.get("help_level") or start.get("help_level") or "A2"),
        "gate_receipt_id": str(packet_summary.get("gate_receipt_id") or start.get("gate_receipt_id") or ""),
        "gate_receipt_hash": str(packet_summary.get("gate_receipt_hash") or start.get("gate_receipt_hash") or ""),
        "decision_receipt_id": str(packet_summary.get("decision_receipt_id") or start.get("decision_receipt_id") or ""),
        "decision_receipt_hash": str(packet_summary.get("decision_receipt_hash") or start.get("decision_receipt_hash") or ""),
        "start_receipt_id": str(packet_summary.get("start_receipt_id") or start.get("start_receipt_id") or ""),
        "start_receipt_hash": str(packet_summary.get("start_receipt_hash") or start.get("start_receipt_hash") or ""),
        "open_confirmation_count": int(packet_summary.get("open_confirmation_count") or start.get("open_confirmation_count") or 0),
        "confirmed_count": int(packet_summary.get("confirmed_count") or start.get("confirmed_count") or 0),
        "open_confirmations": list(packet_summary.get("open_confirmations", start.get("open_confirmations", [])) or [])[:8],
        "confirmed_hash_metadata": list(packet_summary.get("confirmed_hash_metadata", start.get("confirmed_hash_metadata", [])) or [])[:8],
        "exam_deployment_status": "not_cleared",
    }


def build_operator_run_prefill(review_view: dict[str, Any], packet_view: dict[str, Any], ready: bool) -> dict[str, Any]:
    prefill_seed = {
        "endpoint": OPERATOR_RUN_ENDPOINT,
        "selected_skill_tag": packet_view.get("selected_skill_tag", review_view.get("selected_skill_tag", "")),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "source_card_ids": packet_view.get("source_card_ids", []),
        "source_anchor_count": packet_view.get("source_anchor_count", 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "start_status": packet_view.get("start_status", "missing"),
    }
    return {
        "status": "prefill_ready" if ready else "prefill_attention",
        "endpoint": OPERATOR_RUN_ENDPOINT,
        "method": "POST",
        "selected_skill_tag": prefill_seed["selected_skill_tag"],
        "task_hash": prefill_seed["task_hash"],
        "checkpoint_hash": prefill_seed["checkpoint_hash"],
        "source_card_ids": list(prefill_seed.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(prefill_seed.get("source_anchor_count", 0) or 0),
        "requested_help_level": "A2",
        "operator_confirmations_default": "all_false_dry_run",
        "ready_for_manual_local_cycle_review": ready,
        "dry_run_default": True,
        "local_writes_requested": False,
        "prefill_hash": sha256_text(json.dumps(prefill_seed, sort_keys=True, ensure_ascii=False)),
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def build_manual_local_cycle_handoff(
    review_view: dict[str, Any],
    packet_view: dict[str, Any],
    operator_prefill: dict[str, Any],
    ready: bool,
) -> dict[str, Any]:
    return {
        "status": "manual_local_cycle_handoff_ready" if ready else "manual_local_cycle_handoff_attention",
        "selected_skill_tag": packet_view.get("selected_skill_tag", review_view.get("selected_skill_tag", "")),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "recommendation_reason": review_view.get("recommendation_reason", "missing_start_packet"),
        "next_operator_action": (
            "open_operator_run_prefill" if ready else "resolve_readiness_review_attention"
        ),
        "operator_run_endpoint": OPERATOR_RUN_ENDPOINT,
        "operator_run_prefill_hash": operator_prefill.get("prefill_hash", ""),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def handoff_summary(
    *,
    selected_skill_tag: str,
    review_view: dict[str, Any],
    packet_view: dict[str, Any],
    ready_for_operator_prefill: bool,
) -> dict[str, Any]:
    packet_present = bool(review_view.get("packet_present", False))
    hash_complete = bool(review_view.get("hash_metadata_complete", False))
    if not packet_present:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "missing_start_packet"
    elif not hash_complete:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "missing_hash_metadata"
    elif ready_for_operator_prefill:
        status = "python_exam_local_cycle_readiness_handoff_ready"
        reason = review_view.get("recommendation_reason", "open_confirmations_present")
    else:
        status = "python_exam_local_cycle_readiness_handoff_attention"
        reason = "review_not_ready_for_prefill"
    return {
        "status": status,
        "selected_skill_tag": selected_skill_tag,
        "readiness_review_status": review_view.get("status", "missing"),
        "start_packet_status": packet_view.get("status", "missing"),
        "recommendation": review_view.get("recommendation", "keep_blocked"),
        "recommendation_reason": reason,
        "ready_for_operator_prefill": ready_for_operator_prefill,
        "operator_run_endpoint": OPERATOR_RUN_ENDPOINT,
        "operator_run_method": "POST",
        "task_hash": packet_view.get("task_hash", ""),
        "checkpoint_hash": packet_view.get("checkpoint_hash", ""),
        "open_confirmation_count": int(review_view.get("open_confirmation_count", 0) or 0),
        "confirmed_count": int(review_view.get("confirmed_count", 0) or 0),
        "help_level": packet_view.get("help_level", review_view.get("help_level", "A2")),
        "source_card_ids": list(packet_view.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": int(packet_view.get("source_anchor_count", 0) or 0),
        "manual_handoff_ready": ready_for_operator_prefill,
        "operator_prefill_ready": ready_for_operator_prefill,
        "next_safe_action": (
            "Open the operator-run prefill and review the confirmed or missing confirmations."
            if ready_for_operator_prefill
            else "Resolve readiness review attention items before prefilling operator-run."
        ),
        "exam_deployment_status": "not_cleared",
    }


def handoff_receipt(summary: dict[str, Any], operator_prefill: dict[str, Any], manual_handoff: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps({"summary": summary, "operator_prefill": operator_prefill, "manual_handoff": manual_handoff}, sort_keys=True, ensure_ascii=False)
    )
    return {
        "status": "local_cycle_readiness_handoff_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "python_exam_local_cycle_readiness_handoff_ready":
        return [
            "Open the operator-run prefill and keep confirmations explicit.",
            "Review the manual handoff packet before any local write.",
            "Keep the operator-run dry-run by default and stay not_cleared.",
        ]
    return [
        "Resolve readiness review attention items before using the handoff.",
        "Keep the handoff metadata-only and do not start local writes.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-local-cycle-readiness-handoff")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
