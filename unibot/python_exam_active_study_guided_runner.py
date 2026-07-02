from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_ACTIVE_STUDY_GUIDED_RUNNER_SCHEMA_VERSION = "unibot-python-exam-active-study-guided-runner-v1"
PYTHON_EXAM_ACTIVE_STUDY_GUIDED_RUNNER_ENDPOINT = "/api/unibot/course/python-exam-active-study-guided-runner"
CONTROL_PANEL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-control-panel"
ACTIVE_STUDY_DASHBOARD_ENDPOINT = "/api/unibot/course/python-exam-active-study-loop-dashboard"
COURSE_DASHBOARD_ENDPOINT = "/api/unibot/course/exam-coverage-dashboard"


def build_python_exam_active_study_guided_runner(
    *,
    python_exam_active_study_loop_dashboard: dict[str, Any] | None = None,
    python_exam_resume_launcher: dict[str, Any] | None = None,
    python_exam_drill_loop_control_panel: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    requested_action: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    dashboard = python_exam_active_study_loop_dashboard if isinstance(python_exam_active_study_loop_dashboard, dict) else {}
    launcher = python_exam_resume_launcher if isinstance(python_exam_resume_launcher, dict) else {}
    control = python_exam_drill_loop_control_panel if isinstance(python_exam_drill_loop_control_panel, dict) else {}
    selected = effective_selected_skill(selected_skill_tag, dashboard, launcher, control)
    row = selected_dashboard_row(dashboard, selected)
    action = safe_action(requested_action or row.get("next_safe_action") or nested(launcher, "resume_decision", "action"))
    card = guided_action_card(
        row=row,
        launcher=launcher,
        control=control,
        selected_skill_tag=selected,
        action=action,
    )
    summary = guided_summary(dashboard=dashboard, card=card, selected_skill_tag=selected)
    payload = {
        "schema_version": PYTHON_EXAM_ACTIVE_STUDY_GUIDED_RUNNER_SCHEMA_VERSION,
        "artifact_type": "python_exam_active_study_guided_runner",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_active_study_guided_runner_ready" if card["ready"] else "python_exam_active_study_guided_runner_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Active Study Guided Runner. It turns the selected Active Study Loop Dashboard row into "
            "one dry-run Action Card for run_next_microtask, repeat_current_microtask, start_first_microtask, "
            "return_to_skill_dashboard, or review_skill_readiness. It uses only skill tag, task/checkpoint hashes, "
            "Source-Card anchors, A0-A2 help level, dashboard receipts, Resume Launcher prefill metadata, Control "
            "Panel receipt metadata, operator-confirmation requirements, and not_cleared status. It never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "guided_runner_endpoint": PYTHON_EXAM_ACTIVE_STUDY_GUIDED_RUNNER_ENDPOINT,
        "selected_skill_tag": selected,
        "guided_runner_summary": summary,
        "guided_action_card": card,
        "control_panel_prefill": card["prefill"] if card["route"] == "control_panel" else {},
        "dashboard_return_prefill": card["prefill"] if card["route"] != "control_panel" else {},
        "guided_runner_receipt": guided_receipt(summary, card),
        "dry_run_default": True,
        "local_writes_requested": False,
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmations": {
            "checkpoint_store": False,
            "progress_journal_append": False,
            "workspace_local_write": False,
            "export_write": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Guided Runner bleibt not_cleared."
        ),
        "next_actions": next_actions(card),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def selected_dashboard_row(dashboard: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    rows = [item for item in (dashboard.get("skill_loop_dashboard", []) or []) if isinstance(item, dict)]
    for row in rows:
        if row.get("skill_tag") == selected_skill_tag and row.get("selected") is True:
            return safe_row(row)
    for row in rows:
        if row.get("skill_tag") == selected_skill_tag:
            return safe_row(row)
    for row in rows:
        if row.get("selected") is True:
            return safe_row(row)
    return {
        "skill_tag": selected_skill_tag or "general_python",
        "next_safe_action": "review_skill_readiness",
        "source_card_ids": [],
        "source_anchor_count": 0,
        "help_level": "A2",
        "allowed_help_levels": ["A0", "A1", "A2"],
        "exam_deployment_status": "not_cleared",
    }


def safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(row.get("skill_tag", "")),
        "workspace_readiness": str(row.get("workspace_readiness", "unknown")),
        "drill_status": str(row.get("drill_status", "missing")),
        "next_safe_action": safe_action(str(row.get("next_safe_action", ""))),
        "resume_action": safe_action(str(row.get("resume_action", ""))),
        "last_safe_microtask_hash": str(row.get("last_safe_microtask_hash", "")),
        "next_microtask_hash": str(row.get("next_microtask_hash", "")),
        "open_repeat_task_hash": str(row.get("open_repeat_task_hash", "")),
        "checkpoint_hash": str(row.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(row.get("source_anchor_count", 0) or 0),
        "source_coverage_status": str(row.get("source_coverage_status", "unknown")),
        "help_level": safe_help_level(str(row.get("help_level", "A2"))),
        "allowed_help_levels": safe_help_levels(row.get("allowed_help_levels", [])),
        "help_ledger_event_hash": str(row.get("help_ledger_event_hash", "")),
        "carryover_session_receipt_id": str(row.get("carryover_session_receipt_id", "")),
        "review_loop_receipt_id": str(row.get("review_loop_receipt_id", "")),
        "control_panel_receipt_id": str(row.get("control_panel_receipt_id", "")),
        "prefill_hash": str(row.get("prefill_hash", "")),
        "completed_skill_loop": bool(row.get("completed_skill_loop", False)),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def guided_action_card(
    *,
    row: dict[str, Any],
    launcher: dict[str, Any],
    control: dict[str, Any],
    selected_skill_tag: str,
    action: str,
) -> dict[str, Any]:
    route = "control_panel" if action in {"run_next_microtask", "repeat_current_microtask", "start_first_microtask"} else "skill_dashboard"
    endpoint = CONTROL_PANEL_ENDPOINT if route == "control_panel" else COURSE_DASHBOARD_ENDPOINT
    if action == "review_skill_readiness":
        endpoint = ACTIVE_STUDY_DASHBOARD_ENDPOINT
    selected_task_hash = task_hash_for_action(row, launcher, action)
    prefill = action_prefill(
        endpoint=endpoint,
        selected_skill_tag=selected_skill_tag,
        selected_task_hash=selected_task_hash,
        checkpoint_hash=row.get("checkpoint_hash", ""),
        help_level=safe_help_level(row.get("help_level", "A2")),
        source_card_ids=row.get("source_card_ids", []),
        action=action,
    )
    ready = action != "review_skill_readiness" or bool(selected_skill_tag)
    if action in {"run_next_microtask", "repeat_current_microtask"} and not selected_task_hash:
        ready = False
    return {
        "status": "guided_action_card_ready" if ready else "guided_action_card_attention",
        "ready": ready,
        "action": action,
        "route": route,
        "method": "POST",
        "endpoint": endpoint,
        "selected_skill_tag": selected_skill_tag,
        "selected_task_hash": selected_task_hash,
        "last_safe_microtask_hash": row.get("last_safe_microtask_hash", ""),
        "checkpoint_hash": row.get("checkpoint_hash", ""),
        "source_card_ids": row.get("source_card_ids", []),
        "source_anchor_count": row.get("source_anchor_count", 0),
        "source_coverage_status": row.get("source_coverage_status", "unknown"),
        "help_level": safe_help_level(row.get("help_level", "A2")),
        "allowed_help_levels": safe_help_levels(row.get("allowed_help_levels", [])),
        "help_ledger_event_hash": row.get("help_ledger_event_hash", ""),
        "carryover_session_receipt_id": row.get("carryover_session_receipt_id", ""),
        "review_loop_receipt_id": row.get("review_loop_receipt_id", ""),
        "control_panel_receipt_id": row.get("control_panel_receipt_id") or nested(control, "control_panel_receipt", "receipt_id") or "",
        "dashboard_prefill_hash": row.get("prefill_hash", ""),
        "resume_decision_hash": nested(launcher, "resume_decision", "decision_hash") or "",
        "prefill": prefill,
        "operator_confirmations_required": [
            "checkpoint_store",
            "progress_journal_append",
            "workspace_local_write",
        ],
        "operator_confirmations_default": "all_false_dry_run",
        "dry_run_default": True,
        "local_writes_requested": False,
        "a0_a2_only": True,
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


def action_prefill(
    *,
    endpoint: str,
    selected_skill_tag: str,
    selected_task_hash: str,
    checkpoint_hash: str,
    help_level: str,
    source_card_ids: list[str],
    action: str,
) -> dict[str, Any]:
    seed = {
        "endpoint": endpoint,
        "selected_skill_tag": selected_skill_tag,
        "selected_task_hash": selected_task_hash,
        "checkpoint_hash": checkpoint_hash,
        "help_level": help_level,
        "source_card_ids": source_card_ids,
        "action": action,
    }
    return {
        "status": "guided_prefill_ready",
        "endpoint": endpoint,
        "method": "POST",
        "action": action,
        "selected_skill_tag": selected_skill_tag,
        "selected_task_hash": selected_task_hash,
        "last_checkpoint_hash": checkpoint_hash,
        "source_card_ids": source_card_ids,
        "requested_help_level": help_level,
        "operator_confirmations_default": "all_false_dry_run",
        "prefill_hash": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False)),
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def task_hash_for_action(row: dict[str, Any], launcher: dict[str, Any], action: str) -> str:
    if action == "run_next_microtask":
        return str(row.get("next_microtask_hash") or nested(launcher, "resume_decision", "selected_task_hash") or "")
    if action == "repeat_current_microtask":
        return str(row.get("open_repeat_task_hash") or row.get("last_safe_microtask_hash") or "")
    return ""


def guided_summary(
    *,
    dashboard: dict[str, Any],
    card: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    active_summary = dashboard.get("active_study_summary", {}) if isinstance(dashboard.get("active_study_summary"), dict) else {}
    return {
        "selected_skill_tag": selected_skill_tag,
        "dashboard_status": dashboard.get("status", "missing"),
        "dashboard_skill_count": int(active_summary.get("skill_count", 0) or 0),
        "action": card.get("action", "review_skill_readiness"),
        "route": card.get("route", "skill_dashboard"),
        "endpoint": card.get("endpoint", ACTIVE_STUDY_DASHBOARD_ENDPOINT),
        "selected_task_hash": card.get("selected_task_hash", ""),
        "checkpoint_hash": card.get("checkpoint_hash", ""),
        "source_card_count": len(card.get("source_card_ids", []) or []),
        "help_level": card.get("help_level", "A2"),
        "a0_a2_only": True,
        "ready": bool(card.get("ready")),
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def guided_receipt(summary: dict[str, Any], card: dict[str, Any]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "card": card}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "active_study_guided_runner_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def effective_selected_skill(selected_skill_tag: str, *reports: Any) -> str:
    if selected_skill_tag:
        return str(selected_skill_tag)
    for report in reports:
        if isinstance(report, dict):
            for path in [
                ("selected_skill_tag",),
                ("active_study_summary", "selected_skill_tag"),
                ("resume_decision", "selected_skill_tag"),
                ("control_panel_summary", "selected_skill_tag"),
            ]:
                value = nested(report, *path)
                if value:
                    return str(value)
    return "general_python"


def safe_action(action: str | None) -> str:
    value = str(action or "").strip()
    if value in {
        "run_next_microtask",
        "repeat_current_microtask",
        "start_first_microtask",
        "return_to_skill_dashboard",
        "review_skill_readiness",
    }:
        return value
    return "review_skill_readiness"


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def safe_help_levels(values: Any) -> list[str]:
    text = " ".join(str(item) for item in (values or []))
    levels = [level for level in ["A0", "A1", "A2"] if level in text]
    return levels or ["A0", "A1", "A2"]


def next_actions(card: dict[str, Any]) -> list[str]:
    action = card.get("action")
    if action == "run_next_microtask":
        return [
            "Open the Control Panel Action Card for the next microtask hash.",
            "Keep notebook work local and confirm each local write separately.",
            "Append progress only after human review; stay A0-A2 and not_cleared.",
        ]
    if action == "repeat_current_microtask":
        return [
            "Repeat the current microtask with a fresh checkpoint hash.",
            "Use only the Action Card metadata and do not infer scores or final interpretations.",
        ]
    if action == "start_first_microtask":
        return [
            "Start the first safe microtask for this skill through the Control Panel prefill.",
            "Keep dry-run default and require operator confirmation for every local write.",
        ]
    if action == "return_to_skill_dashboard":
        return [
            "Return to the skill dashboard and pick the next ready Python exam skill.",
            "Keep the completed loop as receipt-only evidence.",
        ]
    return [
        "Review readiness and source coverage before starting a microtask.",
        "Keep all outputs metadata-only, dry-run, and not_cleared.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-active-study-guided-runner")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
