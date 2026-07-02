from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_GUIDED_ACTION_EXECUTION_BRIDGE_SCHEMA_VERSION = "unibot-python-exam-guided-action-execution-bridge-v1"
PYTHON_EXAM_GUIDED_ACTION_EXECUTION_BRIDGE_ENDPOINT = "/api/unibot/course/python-exam-guided-action-execution-bridge"
CONTROL_PANEL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-control-panel"
ACTIVE_STUDY_DASHBOARD_ENDPOINT = "/api/unibot/course/python-exam-active-study-loop-dashboard"
COURSE_DASHBOARD_ENDPOINT = "/api/unibot/course/exam-coverage-dashboard"
PROGRESS_JOURNAL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-progress-journal"


def build_python_exam_guided_action_execution_bridge(
    *,
    python_exam_active_study_guided_runner: dict[str, Any] | None = None,
    python_exam_drill_loop_control_panel: dict[str, Any] | None = None,
    python_exam_drill_loop_progress_journal: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    guided = python_exam_active_study_guided_runner if isinstance(python_exam_active_study_guided_runner, dict) else {}
    control = python_exam_drill_loop_control_panel if isinstance(python_exam_drill_loop_control_panel, dict) else {}
    progress = python_exam_drill_loop_progress_journal if isinstance(python_exam_drill_loop_progress_journal, dict) else {}
    card = safe_action_card(guided.get("guided_action_card", {}) if isinstance(guided.get("guided_action_card"), dict) else {})
    selected = selected_skill_tag or card.get("selected_skill_tag") or nested(guided, "guided_runner_summary", "selected_skill_tag") or "general_python"
    preview = execution_preview(card=card, control=control, progress=progress, selected_skill_tag=str(selected))
    summary = bridge_summary(guided=guided, preview=preview, selected_skill_tag=str(selected))
    payload = {
        "schema_version": PYTHON_EXAM_GUIDED_ACTION_EXECUTION_BRIDGE_SCHEMA_VERSION,
        "artifact_type": "python_exam_guided_action_execution_bridge",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_guided_action_execution_bridge_ready" if summary["ready"] else "python_exam_guided_action_execution_bridge_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Guided Action Execution Bridge. It translates one Guided Runner dry-run Action Card into "
            "a concrete metadata-only next-cycle preview: Control Panel Preview for run_next_microtask, "
            "repeat_current_microtask, or start_first_microtask, and Dashboard Return Preview for "
            "return_to_skill_dashboard or review_skill_readiness. It uses only Action Card fields, skill tag, "
            "task/checkpoint hashes, Source-Card anchors, A0-A2 help level, receipts, Progress Journal preview "
            "metadata, and operator-confirmation status. It never writes by default and never returns raw queries, "
            "course raw text, notebook code, local paths, values, solutions, final interpretations, scores, "
            "percentages, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "execution_bridge_endpoint": PYTHON_EXAM_GUIDED_ACTION_EXECUTION_BRIDGE_ENDPOINT,
        "selected_skill_tag": str(selected),
        "execution_bridge_summary": summary,
        "input_action_card": card,
        "control_panel_cycle_preview": preview if preview["route"] == "control_panel" else {},
        "dashboard_return_preview": preview if preview["route"] != "control_panel" else {},
        "operator_confirmation_matrix": operator_confirmation_matrix(),
        "execution_bridge_receipt": bridge_receipt(summary, preview),
        "dry_run_default": True,
        "local_writes_requested": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Execution Bridge bleibt not_cleared."
        ),
        "next_actions": next_actions(summary, preview),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_action_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": str(card.get("status", "missing")),
        "ready": bool(card.get("ready", False)),
        "action": safe_action(str(card.get("action", ""))),
        "route": safe_route(str(card.get("route", "")), str(card.get("action", ""))),
        "method": "POST",
        "endpoint": safe_endpoint(str(card.get("endpoint", "")), str(card.get("action", ""))),
        "selected_skill_tag": str(card.get("selected_skill_tag", "")),
        "selected_task_hash": str(card.get("selected_task_hash", "")),
        "last_safe_microtask_hash": str(card.get("last_safe_microtask_hash", "")),
        "checkpoint_hash": str(card.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (card.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(card.get("source_anchor_count", 0) or 0),
        "source_coverage_status": str(card.get("source_coverage_status", "unknown")),
        "help_level": safe_help_level(str(card.get("help_level", "A2"))),
        "allowed_help_levels": safe_help_levels(card.get("allowed_help_levels", [])),
        "help_ledger_event_hash": str(card.get("help_ledger_event_hash", "")),
        "carryover_session_receipt_id": str(card.get("carryover_session_receipt_id", "")),
        "review_loop_receipt_id": str(card.get("review_loop_receipt_id", "")),
        "control_panel_receipt_id": str(card.get("control_panel_receipt_id", "")),
        "dashboard_prefill_hash": str(card.get("dashboard_prefill_hash", "")),
        "resume_decision_hash": str(card.get("resume_decision_hash", "")),
        "operator_confirmations_default": "all_false_dry_run",
        "dry_run_default": True,
        "local_writes_requested": False,
        "a0_a2_only": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def execution_preview(
    *,
    card: dict[str, Any],
    control: dict[str, Any],
    progress: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    action = card.get("action", "review_skill_readiness")
    if action in {"run_next_microtask", "repeat_current_microtask", "start_first_microtask"}:
        return control_panel_preview(card=card, control=control, progress=progress, selected_skill_tag=selected_skill_tag)
    return dashboard_return_preview(card=card, progress=progress, selected_skill_tag=selected_skill_tag)


def control_panel_preview(
    *,
    card: dict[str, Any],
    control: dict[str, Any],
    progress: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    action = card.get("action", "start_first_microtask")
    selected_task_hash = str(card.get("selected_task_hash", ""))
    ready = bool(card.get("ready")) and (bool(selected_task_hash) or action == "start_first_microtask")
    seed = preview_seed(card=card, selected_skill_tag=selected_skill_tag, endpoint=CONTROL_PANEL_ENDPOINT)
    return {
        "status": "control_panel_execution_preview_ready" if ready else "control_panel_execution_preview_attention",
        "ready": ready,
        "route": "control_panel",
        "action": action,
        "method": "POST",
        "endpoint": CONTROL_PANEL_ENDPOINT,
        "selected_skill_tag": selected_skill_tag,
        "selected_task_hash": selected_task_hash,
        "checkpoint_hash": card.get("checkpoint_hash", ""),
        "source_card_ids": card.get("source_card_ids", []),
        "source_anchor_count": card.get("source_anchor_count", 0),
        "help_level": card.get("help_level", "A2"),
        "allowed_help_levels": card.get("allowed_help_levels", ["A0", "A1", "A2"]),
        "control_panel_status": control.get("status", "missing"),
        "control_panel_receipt_id": card.get("control_panel_receipt_id") or nested(control, "control_panel_receipt", "receipt_id") or "",
        "progress_journal_preview_status": progress.get("status", "missing"),
        "progress_journal_written": False,
        "progress_journal_endpoint": PROGRESS_JOURNAL_ENDPOINT,
        "preview_hash": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False)),
        "operator_confirmations_default": "all_false_dry_run",
        "local_writes_requested": False,
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "solutions_returned": False,
        "score_returned": False,
        "grade_returned": False,
    }


def dashboard_return_preview(*, card: dict[str, Any], progress: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    action = card.get("action", "review_skill_readiness")
    endpoint = COURSE_DASHBOARD_ENDPOINT if action == "return_to_skill_dashboard" else ACTIVE_STUDY_DASHBOARD_ENDPOINT
    seed = preview_seed(card=card, selected_skill_tag=selected_skill_tag, endpoint=endpoint)
    return {
        "status": "dashboard_return_preview_ready",
        "ready": True,
        "route": "skill_dashboard",
        "action": action,
        "method": "POST",
        "endpoint": endpoint,
        "selected_skill_tag": selected_skill_tag,
        "selected_task_hash": "",
        "checkpoint_hash": card.get("checkpoint_hash", ""),
        "source_card_ids": card.get("source_card_ids", []),
        "source_anchor_count": card.get("source_anchor_count", 0),
        "help_level": card.get("help_level", "A2"),
        "progress_journal_preview_status": progress.get("status", "missing"),
        "progress_journal_written": False,
        "preview_hash": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False)),
        "operator_confirmations_default": "all_false_dry_run",
        "local_writes_requested": False,
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "solutions_returned": False,
        "score_returned": False,
        "grade_returned": False,
    }


def preview_seed(*, card: dict[str, Any], selected_skill_tag: str, endpoint: str) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        "selected_skill_tag": selected_skill_tag,
        "action": card.get("action", ""),
        "selected_task_hash": card.get("selected_task_hash", ""),
        "checkpoint_hash": card.get("checkpoint_hash", ""),
        "source_card_ids": card.get("source_card_ids", []),
        "help_level": card.get("help_level", "A2"),
    }


def bridge_summary(*, guided: dict[str, Any], preview: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    return {
        "selected_skill_tag": selected_skill_tag,
        "guided_runner_status": guided.get("status", "missing"),
        "action": preview.get("action", "review_skill_readiness"),
        "route": preview.get("route", "skill_dashboard"),
        "endpoint": preview.get("endpoint", ACTIVE_STUDY_DASHBOARD_ENDPOINT),
        "selected_task_hash": preview.get("selected_task_hash", ""),
        "checkpoint_hash": preview.get("checkpoint_hash", ""),
        "source_card_count": len(preview.get("source_card_ids", []) or []),
        "help_level": preview.get("help_level", "A2"),
        "preview_status": preview.get("status", "missing"),
        "ready": bool(preview.get("ready")),
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "confirmed_local_write_count": 0,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def operator_confirmation_matrix() -> dict[str, Any]:
    steps = [
        {"step_id": "checkpoint_store", "required_before_write": True, "confirmed": False, "write_started": False},
        {"step_id": "progress_journal_append", "required_before_write": True, "confirmed": False, "write_started": False},
        {"step_id": "workspace_local_write", "required_before_write": True, "confirmed": False, "write_started": False},
        {"step_id": "export_write", "required_before_write": True, "confirmed": False, "write_started": False},
    ]
    return {
        "status": "all_steps_dry_run",
        "confirmed_count": 0,
        "local_writes_requested": False,
        "steps": steps,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def bridge_receipt(summary: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "preview": preview}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "guided_action_execution_bridge_receipt_ready_not_exam_clearance",
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


def safe_route(route: str, action: str) -> str:
    if route in {"control_panel", "skill_dashboard"}:
        return route
    return "control_panel" if safe_action(action) in {"run_next_microtask", "repeat_current_microtask", "start_first_microtask"} else "skill_dashboard"


def safe_endpoint(endpoint: str, action: str) -> str:
    if endpoint in {CONTROL_PANEL_ENDPOINT, ACTIVE_STUDY_DASHBOARD_ENDPOINT, COURSE_DASHBOARD_ENDPOINT}:
        return endpoint
    if safe_action(action) in {"run_next_microtask", "repeat_current_microtask", "start_first_microtask"}:
        return CONTROL_PANEL_ENDPOINT
    if safe_action(action) == "return_to_skill_dashboard":
        return COURSE_DASHBOARD_ENDPOINT
    return ACTIVE_STUDY_DASHBOARD_ENDPOINT


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def safe_help_levels(values: Any) -> list[str]:
    text = " ".join(str(item) for item in (values or []))
    levels = [level for level in ["A0", "A1", "A2"] if level in text]
    return levels or ["A0", "A1", "A2"]


def next_actions(summary: dict[str, Any], preview: dict[str, Any]) -> list[str]:
    if summary.get("route") == "control_panel":
        return [
            "Open the Control Panel preview using the selected task hash.",
            "Run notebook work locally and store only hashes after explicit operator confirmation.",
            "Append the Progress Journal only after review; stay A0-A2 and not_cleared.",
        ]
    return [
        "Return to the skill dashboard preview and choose the next ready Python exam skill.",
        "Keep completed work as receipts and hashes only.",
        "Stay dry-run by default and not_cleared.",
    ]


def nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-guided-action-execution-bridge")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
