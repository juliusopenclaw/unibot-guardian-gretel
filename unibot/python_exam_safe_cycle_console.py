from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_SAFE_CYCLE_CONSOLE_SCHEMA_VERSION = "unibot-python-exam-safe-cycle-console-v1"
PYTHON_EXAM_SAFE_CYCLE_CONSOLE_ENDPOINT = "/api/unibot/course/python-exam-safe-cycle-console"


def build_python_exam_safe_cycle_console(
    *,
    python_exam_active_study_loop_dashboard: dict[str, Any] | None = None,
    python_exam_active_study_guided_runner: dict[str, Any] | None = None,
    python_exam_guided_action_execution_bridge: dict[str, Any] | None = None,
    python_exam_drill_loop_control_panel: dict[str, Any] | None = None,
    python_exam_drill_loop_progress_journal: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    dashboard = python_exam_active_study_loop_dashboard if isinstance(python_exam_active_study_loop_dashboard, dict) else {}
    guided = python_exam_active_study_guided_runner if isinstance(python_exam_active_study_guided_runner, dict) else {}
    bridge = python_exam_guided_action_execution_bridge if isinstance(python_exam_guided_action_execution_bridge, dict) else {}
    control = python_exam_drill_loop_control_panel if isinstance(python_exam_drill_loop_control_panel, dict) else {}
    progress = python_exam_drill_loop_progress_journal if isinstance(python_exam_drill_loop_progress_journal, dict) else {}
    selected = effective_selected_skill(selected_skill_tag, bridge, guided, dashboard, control, progress)
    preview = safe_cycle_preview(bridge)
    row = safe_dashboard_row(dashboard, selected)
    receipts = cycle_receipts(guided=guided, bridge=bridge, control=control, progress=progress, row=row)
    matrix = safe_operator_matrix(bridge.get("operator_confirmation_matrix", {}))
    summary = cycle_summary(
        selected_skill_tag=selected,
        dashboard=dashboard,
        guided=guided,
        bridge=bridge,
        control=control,
        progress=progress,
        preview=preview,
        matrix=matrix,
    )
    payload = {
        "schema_version": PYTHON_EXAM_SAFE_CYCLE_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "python_exam_safe_cycle_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_safe_cycle_console_ready" if summary["ready"] else "python_exam_safe_cycle_console_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Safe Cycle Console. It merges Guided Runner, Guided Action Execution Bridge, Drill Loop "
            "Control Panel, Progress Journal, and Active Study Dashboard into one current metadata-only work-cycle "
            "view. It shows selected skill, next safe action, Control-Panel or Dashboard-Return preview, task and "
            "checkpoint hashes, Source-Card anchors, A0-A2 help level, Help-Ledger, Review, Progress receipts, "
            "operator-confirmation matrix, cycle status, and next safe user action. It never writes by default and "
            "never returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, "
            "or exam clearance."
        ),
        "safe_cycle_console_endpoint": PYTHON_EXAM_SAFE_CYCLE_CONSOLE_ENDPOINT,
        "selected_skill_tag": selected,
        "safe_cycle_summary": summary,
        "current_cycle_view": {
            "selected_skill_tag": selected,
            "next_safe_action": summary["next_safe_action"],
            "cycle_status": summary["cycle_status"],
            "preview": preview,
            "dashboard_row": row,
            "receipts": receipts,
            "operator_confirmation_matrix": matrix,
            "a0_a2_only": True,
            "dry_run_default": True,
            "local_writes_requested": False,
            "not_cleared_receipt": True,
            "exam_deployment_status": "not_cleared",
        },
        "source_reports": {
            "dashboard_status": dashboard.get("status", "missing"),
            "guided_runner_status": guided.get("status", "missing"),
            "execution_bridge_status": bridge.get("status", "missing"),
            "control_panel_status": control.get("status", "missing"),
            "progress_journal_status": progress.get("status", "missing"),
        },
        "safe_cycle_receipt": safe_cycle_receipt(summary, preview, receipts, matrix),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Safe Cycle Console bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_cycle_preview(bridge: dict[str, Any]) -> dict[str, Any]:
    source = {}
    if isinstance(bridge.get("control_panel_cycle_preview"), dict) and bridge.get("control_panel_cycle_preview"):
        source = bridge["control_panel_cycle_preview"]
    elif isinstance(bridge.get("dashboard_return_preview"), dict) and bridge.get("dashboard_return_preview"):
        source = bridge["dashboard_return_preview"]
    return {
        "status": str(source.get("status", "missing")),
        "ready": bool(source.get("ready", False)),
        "route": str(source.get("route", "missing")),
        "action": safe_action(str(source.get("action", ""))),
        "endpoint": str(source.get("endpoint", "")),
        "selected_skill_tag": str(source.get("selected_skill_tag", "")),
        "selected_task_hash": str(source.get("selected_task_hash", "")),
        "checkpoint_hash": str(source.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(source.get("help_level", "A2"))),
        "progress_journal_preview_status": str(source.get("progress_journal_preview_status", "missing")),
        "progress_journal_written": False,
        "preview_hash": str(source.get("preview_hash", "")),
        "operator_confirmations_default": "all_false_dry_run",
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_dashboard_row(dashboard: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    rows = [item for item in (dashboard.get("skill_loop_dashboard", []) or []) if isinstance(item, dict)]
    selected = next((row for row in rows if row.get("skill_tag") == selected_skill_tag), rows[0] if rows else {})
    return {
        "skill_tag": str(selected.get("skill_tag", selected_skill_tag)),
        "workspace_readiness": str(selected.get("workspace_readiness", "unknown")),
        "drill_status": str(selected.get("drill_status", "missing")),
        "source_coverage_status": str(selected.get("source_coverage_status", "unknown")),
        "next_safe_action": safe_action(str(selected.get("next_safe_action", ""))),
        "last_safe_microtask_hash": str(selected.get("last_safe_microtask_hash", "")),
        "next_microtask_hash": str(selected.get("next_microtask_hash", "")),
        "open_repeat_task_hash": str(selected.get("open_repeat_task_hash", "")),
        "completed_skill_loop": bool(selected.get("completed_skill_loop", False)),
        "help_level": safe_help_level(str(selected.get("help_level", "A2"))),
        "source_card_ids": [str(item) for item in (selected.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(selected.get("source_anchor_count", 0) or 0),
        "checkpoint_hash": str(selected.get("checkpoint_hash", "")),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def cycle_receipts(
    *,
    guided: dict[str, Any],
    bridge: dict[str, Any],
    control: dict[str, Any],
    progress: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    entry = progress.get("journal_entry_preview", {}) if isinstance(progress.get("journal_entry_preview"), dict) else {}
    return {
        "guided_runner_receipt_id": nested(guided, "guided_runner_receipt", "receipt_id") or "",
        "execution_bridge_receipt_id": nested(bridge, "execution_bridge_receipt", "receipt_id") or "",
        "control_panel_receipt_id": nested(control, "control_panel_receipt", "receipt_id") or row.get("control_panel_receipt_id", ""),
        "progress_entry_hash": entry.get("entry_hash", ""),
        "progress_record_status": nested(progress, "append_summary", "record_status") or "",
        "progress_journal_written": False,
        "help_ledger_event_hash": row.get("help_ledger_event_hash") or entry.get("help_ledger_event_hash", ""),
        "review_loop_receipt_id": row.get("review_loop_receipt_id") or entry.get("review_loop_receipt_id", ""),
        "carryover_session_receipt_id": row.get("carryover_session_receipt_id") or entry.get("carryover_session_receipt_id", ""),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def safe_operator_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    steps = []
    for item in (matrix.get("steps", []) or []):
        if isinstance(item, dict):
            steps.append(
                {
                    "step_id": str(item.get("step_id", "")),
                    "required_before_write": bool(item.get("required_before_write", True)),
                    "confirmed": False,
                    "write_started": False,
                }
            )
    if not steps:
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


def cycle_summary(
    *,
    selected_skill_tag: str,
    dashboard: dict[str, Any],
    guided: dict[str, Any],
    bridge: dict[str, Any],
    control: dict[str, Any],
    progress: dict[str, Any],
    preview: dict[str, Any],
    matrix: dict[str, Any],
) -> dict[str, Any]:
    ready = (
        dashboard.get("status") == "python_exam_active_study_loop_dashboard_ready"
        and guided.get("status") == "python_exam_active_study_guided_runner_ready"
        and bridge.get("status") == "python_exam_guided_action_execution_bridge_ready"
        and preview.get("ready") is True
        and matrix.get("confirmed_count") == 0
    )
    return {
        "selected_skill_tag": selected_skill_tag,
        "cycle_status": "safe_cycle_ready_for_operator_review" if ready else "safe_cycle_attention",
        "ready": ready,
        "next_safe_action": preview.get("action", "review_skill_readiness"),
        "route": preview.get("route", "missing"),
        "endpoint": preview.get("endpoint", ""),
        "preview_status": preview.get("status", "missing"),
        "selected_task_hash": preview.get("selected_task_hash", ""),
        "checkpoint_hash": preview.get("checkpoint_hash", ""),
        "source_card_count": len(preview.get("source_card_ids", []) or []),
        "help_level": preview.get("help_level", "A2"),
        "dashboard_status": dashboard.get("status", "missing"),
        "guided_runner_status": guided.get("status", "missing"),
        "execution_bridge_status": bridge.get("status", "missing"),
        "control_panel_status": control.get("status", "missing"),
        "progress_journal_status": progress.get("status", "missing"),
        "operator_confirmation_status": matrix.get("status", "all_steps_dry_run"),
        "confirmed_local_write_count": 0,
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_cycle_receipt(
    summary: dict[str, Any],
    preview: dict[str, Any],
    receipts: dict[str, Any],
    matrix: dict[str, Any],
) -> dict[str, Any]:
    receipt_hash = sha256_text(
        json.dumps(
            {"summary": summary, "preview": preview, "receipts": receipts, "matrix": matrix},
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    return {
        "status": "safe_cycle_console_receipt_ready_not_exam_clearance",
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
                ("safe_cycle_summary", "selected_skill_tag"),
                ("execution_bridge_summary", "selected_skill_tag"),
                ("guided_runner_summary", "selected_skill_tag"),
                ("active_study_summary", "selected_skill_tag"),
                ("control_panel_summary", "selected_skill_tag"),
                ("journal_entry_preview", "skill_tag"),
            ]:
                value = nested(report, *path)
                if value:
                    return str(value)
    return "general_python"


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
    if summary.get("route") == "control_panel":
        return [
            "Review the Safe Cycle Console and open the Control Panel preview.",
            "Run notebook work locally; store only hashes after explicit confirmation.",
            "Append Progress Journal only after human review; stay A0-A2 and not_cleared.",
        ]
    return [
        "Review the dashboard return preview and select the next safe Python skill.",
        "Keep receipts metadata-only and local writes unstarted.",
        "Stay not_cleared until real-world authorization is handled outside UniBot.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-safe-cycle-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
