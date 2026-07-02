from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_GUIDED_LOOP_CONTROL_SURFACE_SCHEMA_VERSION = "unibot-python-exam-guided-loop-control-surface-v1"
PYTHON_EXAM_GUIDED_LOOP_CONTROL_SURFACE_ENDPOINT = "/api/unibot/course/python-exam-guided-loop-control-surface"


def build_python_exam_guided_loop_control_surface(
    *,
    python_exam_gap_coach_guided_rehearsal_loop: dict[str, Any] | None = None,
    python_exam_rehearsal_playback_gap_coach: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    operator_confirmed_dry_run_request: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    loop = python_exam_gap_coach_guided_rehearsal_loop if isinstance(python_exam_gap_coach_guided_rehearsal_loop, dict) else {}
    coach = python_exam_rehearsal_playback_gap_coach if isinstance(python_exam_rehearsal_playback_gap_coach, dict) else {}
    summary = safe_dict(loop.get("guided_loop_summary"))
    step = safe_dict(loop.get("guided_step"))
    prefill = safe_dict(loop.get("safe_prefill") or step.get("safe_prefill"))
    skill_tag = effective_skill_tag(selected_skill_tag, loop, coach)
    action_key = str(summary.get("next_safe_action_key") or loop.get("requested_action_key") or step.get("action_key") or "resolve_missing_artifact")
    route = str(summary.get("route") or step.get("route") or "")
    endpoint = str(summary.get("endpoint") or step.get("endpoint") or prefill.get("endpoint") or "")
    source = source_anchor_status(loop, coach, prefill)
    checkpoint = checkpoint_status(loop, coach, prefill)
    confirmations = operator_confirmation_status(loop, coach)
    help_status = a0_a2_help_status(loop, coach)
    evidence = evidence_status(loop, coach)
    clicks = control_clicks(
        action_key=action_key,
        route=route,
        endpoint=endpoint,
        prefill=prefill,
        confirmations=confirmations,
        operator_confirmed_dry_run_request=operator_confirmed_dry_run_request,
    )
    control_summary = {
        "selected_skill_tag": skill_tag,
        "guided_loop_status": loop.get("status", "missing"),
        "action_key": action_key,
        "route": route,
        "endpoint": endpoint,
        "guided_step_status": step.get("status", "missing"),
        "prefill_hash": prefill.get("prefill_hash", ""),
        "source_anchor_count": source["source_anchor_count"],
        "checkpoint_hash_count": checkpoint["checkpoint_hash_count"],
        "open_operator_confirmation_count": confirmations["open_operator_confirmation_count"],
        "help_status": help_status["status"],
        "evidence_preview_status": evidence["evidence_preview_status"],
        "human_handoff_status": evidence["human_handoff_status"],
        "next_safe_click": next_safe_click(action_key),
        "dry_run_request_status": (
            "dry_run_request_confirmed_for_next_call" if operator_confirmed_dry_run_request else "dry_run_request_prepared_not_executed"
        ),
        "ready": bool(loop and step.get("ready", False) is not False and prefill.get("prefill_hash")),
        "dry_run_default": True,
        "local_writes_requested": False,
        "exam_deployment_status": "not_cleared",
    }
    payload = {
        "schema_version": PYTHON_EXAM_GUIDED_LOOP_CONTROL_SURFACE_SCHEMA_VERSION,
        "artifact_type": "python_exam_guided_loop_control_surface",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "python_exam_guided_loop_control_surface_ready"
            if control_summary["ready"]
            else "python_exam_guided_loop_control_surface_attention"
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Guided Loop Control Surface. It renders the current Gap-Coach Guided Rehearsal Loop "
            "as one human-checkable control surface: action key, route, endpoint, prefill hash, Source-Card "
            "anchors, notebook checkpoint hashes, open operator confirmations, A0-A2 help profile, evidence "
            "status, Human Handoff status, and next safe click. It prepares metadata-only dry-run requests but "
            "does not execute local writes; every write-capable step remains behind explicit operator "
            "confirmation. It never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, rankings, grades, proctoring, AI detection, automatic "
            "grading, or exam clearance claims."
        ),
        "control_surface_endpoint": PYTHON_EXAM_GUIDED_LOOP_CONTROL_SURFACE_ENDPOINT,
        "selected_skill_tag": skill_tag,
        "control_summary": control_summary,
        "current_guided_step_card": current_step_card(step, prefill, action_key, route, endpoint),
        "control_clicks": clicks,
        "source_anchor_status": source,
        "notebook_checkpoint_status": checkpoint,
        "operator_confirmation_status": confirmations,
        "a0_a2_help_status": help_status,
        "evidence_status": evidence,
        "surface_receipt": surface_receipt(control_summary, clicks, source, checkpoint, confirmations, evidence),
        "dry_run_default": True,
        "dry_run_request_prepared": True,
        "dry_run_request_executed_by_surface": False,
        "local_writes_requested": False,
        "local_writes_executed_by_surface": False,
        "local_execution_started": False,
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmations": {
            "checkpoint_store": False,
            "progress_journal_append": False,
            "workspace_local_write": False,
            "export_write": False,
            "human_handoff_write": False,
        },
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Guided Loop Control Surface bleibt not_cleared."
        ),
        "next_actions": [
            f"Review next safe click: {control_summary['next_safe_click']}.",
            "Use the prepared dry-run request only after human review of the visible metadata.",
            "Keep local writes behind explicit operator confirmation and keep exam_deployment_status not_cleared.",
        ],
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def current_step_card(step: dict[str, Any], prefill: dict[str, Any], action_key: str, route: str, endpoint: str) -> dict[str, Any]:
    return {
        "status": step.get("status", "missing"),
        "action_key": action_key,
        "route": route,
        "endpoint": endpoint,
        "method": "POST",
        "prefill_hash": prefill.get("prefill_hash", ""),
        "ready": bool(step.get("ready", False)),
        "dry_run_default": True,
        "local_writes_requested": False,
        "operator_confirmation_required_for_local_write": True,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
    }


def control_clicks(
    *,
    action_key: str,
    route: str,
    endpoint: str,
    prefill: dict[str, Any],
    confirmations: dict[str, Any],
    operator_confirmed_dry_run_request: bool,
) -> list[dict[str, Any]]:
    primary = {
        "click_id": next_safe_click(action_key),
        "label": click_label(action_key),
        "action_key": action_key,
        "route": route,
        "endpoint": endpoint,
        "method": "POST",
        "enabled": bool(endpoint and prefill.get("prefill_hash")),
        "prefill_hash": prefill.get("prefill_hash", ""),
        "dry_run_request_status": (
            "confirmed_for_next_dry_run_request" if operator_confirmed_dry_run_request else "prepared_not_executed"
        ),
        "requires_operator_confirmation_for_local_writes": True,
        "open_operator_confirmation_count": confirmations["open_operator_confirmation_count"],
        "dry_run_default": True,
        "local_write_executed": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }
    review = {
        "click_id": "review_visible_metadata",
        "label": "Review visible metadata",
        "action_key": "review_metadata",
        "route": "metadata_review",
        "endpoint": "",
        "method": "NONE",
        "enabled": True,
        "prefill_hash": prefill.get("prefill_hash", ""),
        "dry_run_default": True,
        "local_write_executed": False,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }
    return [review, primary]


def source_anchor_status(loop: dict[str, Any], coach: dict[str, Any], prefill: dict[str, Any]) -> dict[str, Any]:
    drill = safe_dict(loop.get("a0_a2_drill_card"))
    source_cards = [item for item in (loop.get("source_checkpoint_review_cards", []) or []) if isinstance(item, dict)]
    first_source = source_cards[0] if source_cards else {}
    source_ids = first_list(
        prefill.get("source_card_ids"),
        drill.get("source_card_ids"),
        first_source.get("source_card_ids"),
        nested(coach, "source_anchor_metadata", "source_card_ids"),
    )
    source_anchor_count = first_int(
        prefill.get("source_anchor_count"),
        drill.get("source_anchor_count"),
        first_source.get("source_anchor_count"),
        nested(coach, "source_anchor_metadata", "source_anchor_count"),
        nested(loop, "guided_loop_summary", "source_anchor_count"),
    )
    return {
        "status": "source_anchor_present" if source_anchor_count > 0 or source_ids else "source_anchor_missing",
        "source_card_ids": source_ids[:8],
        "source_anchor_count": source_anchor_count,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def checkpoint_status(loop: dict[str, Any], coach: dict[str, Any], prefill: dict[str, Any]) -> dict[str, Any]:
    drill = safe_dict(loop.get("a0_a2_drill_card"))
    source_cards = [item for item in (loop.get("source_checkpoint_review_cards", []) or []) if isinstance(item, dict)]
    checkpoint_card = source_cards[1] if len(source_cards) > 1 else {}
    latest = first_text(
        prefill.get("checkpoint_hash"),
        drill.get("latest_notebook_checkpoint_hash"),
        checkpoint_card.get("latest_notebook_checkpoint_hash"),
        nested(coach, "notebook_checkpoint_metadata", "latest_notebook_checkpoint_hash"),
    )
    count = first_int(
        prefill.get("checkpoint_hash_count"),
        checkpoint_card.get("checkpoint_hash_count"),
        nested(coach, "notebook_checkpoint_metadata", "checkpoint_hash_count"),
        1 if latest else 0,
    )
    return {
        "status": "checkpoint_hash_present" if latest or count > 0 else "checkpoint_hash_missing",
        "latest_notebook_checkpoint_hash": latest,
        "checkpoint_hash_count": count,
        "exam_deployment_status": "not_cleared",
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def operator_confirmation_status(loop: dict[str, Any], coach: dict[str, Any]) -> dict[str, Any]:
    summary = safe_dict(loop.get("guided_loop_summary"))
    cards = [item for item in (loop.get("operator_confirmation_review_cards", []) or []) if isinstance(item, dict)]
    open_count = first_int(
        summary.get("open_operator_confirmation_count"),
        nested(coach, "operator_confirmation_status", "open_operator_confirmation_count"),
        len(cards),
    )
    return {
        "status": "operator_confirmations_open" if open_count else "operator_confirmations_reviewed_or_not_required",
        "open_operator_confirmation_count": open_count,
        "review_card_count": len(cards),
        "operator_confirmed_count": len([item for item in cards if item.get("operator_confirmed") is True]),
        "local_writes_require_confirmation": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def a0_a2_help_status(loop: dict[str, Any], coach: dict[str, Any]) -> dict[str, Any]:
    drill = safe_dict(loop.get("a0_a2_drill_card"))
    profile = first_dict(drill.get("current_help_profile"), nested(coach, "a0_a2_help_status", "profile"))
    nonstandard = sum(int(count or 0) for level, count in profile.items() if str(level) not in {"A0", "A1", "A2"})
    status = str(nested(coach, "a0_a2_help_status", "status") or "a0_a2_only")
    return {
        "status": "a0_a2_only" if status == "a0_a2_only" and nonstandard == 0 else "a0_a2_review_attention",
        "profile": profile,
        "allowed_help_boundary": "A0-A2",
        "nonstandard_help_event_count": nonstandard,
        "exam_deployment_status": "not_cleared",
    }


def evidence_status(loop: dict[str, Any], coach: dict[str, Any]) -> dict[str, Any]:
    handoff = safe_dict(loop.get("human_review_packet_card"))
    return {
        "evidence_preview_status": first_text(
            handoff.get("evidence_preview_status"),
            nested(coach, "evidence_playback", "evidence_preview_status"),
            "missing",
        ),
        "evidence_preview_receipt_id": first_text(
            handoff.get("evidence_preview_receipt_id"),
            nested(coach, "evidence_playback", "evidence_preview_receipt_id"),
        ),
        "human_handoff_status": first_text(
            handoff.get("human_handoff_status"),
            nested(coach, "evidence_playback", "human_handoff_status"),
            "missing",
        ),
        "human_handoff_markdown_hash": first_text(
            handoff.get("human_handoff_markdown_hash"),
            nested(coach, "evidence_playback", "human_handoff_markdown_hash"),
        ),
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def surface_receipt(*parts: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps(parts, sort_keys=True, ensure_ascii=False))
    return {
        "status": "python_exam_guided_loop_control_surface_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def next_safe_click(action_key: str) -> str:
    return {
        "resolve_missing_artifact": "review_missing_artifact_card",
        "resolve_source_gap": "review_source_checkpoint_cards",
        "review_operator_confirmation": "review_operator_confirmation_cards",
        "continue_a0_a2_drill": "prepare_a0_a2_drill_dry_run",
        "ready_to_rehearse_again": "prepare_full_rehearsal_dry_run",
        "ready_for_human_review_packet": "open_human_review_packet_metadata",
    }.get(action_key, "review_visible_metadata")


def click_label(action_key: str) -> str:
    return {
        "resolve_missing_artifact": "Review missing artifact",
        "resolve_source_gap": "Review source/checkpoint",
        "review_operator_confirmation": "Review confirmations",
        "continue_a0_a2_drill": "Prepare A0-A2 drill",
        "ready_to_rehearse_again": "Prepare rehearsal",
        "ready_for_human_review_packet": "Open human review metadata",
    }.get(action_key, "Review metadata")


def effective_skill_tag(selected: str, *artifacts: dict[str, Any]) -> str:
    if str(selected or "").strip():
        return str(selected).strip()
    for artifact in artifacts:
        for path in (
            ("selected_skill_tag",),
            ("guided_loop_summary", "selected_skill_tag"),
            ("playback_summary", "selected_skill_tag"),
        ):
            value = nested(artifact, *path)
            if isinstance(value, str) and value:
                return value
    return "python_lists"


def safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def first_int(*values: Any) -> int:
    for value in values:
        try:
            if value is not None and str(value) != "":
                return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def first_list(*values: Any) -> list[str]:
    for value in values:
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return []


def first_dict(*values: Any) -> dict[str, int]:
    for value in values:
        if isinstance(value, dict) and value:
            safe: dict[str, int] = {}
            for key, count in value.items():
                try:
                    safe[str(key)] = int(count or 0)
                except (TypeError, ValueError):
                    safe[str(key)] = 0
            return safe
    return {}


def nested(payload: Any, *path: str) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-guided-loop-control-surface")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
