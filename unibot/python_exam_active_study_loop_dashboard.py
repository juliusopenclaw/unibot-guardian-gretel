from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_ACTIVE_STUDY_LOOP_DASHBOARD_SCHEMA_VERSION = "unibot-python-exam-active-study-loop-dashboard-v1"
PYTHON_EXAM_ACTIVE_STUDY_LOOP_DASHBOARD_ENDPOINT = "/api/unibot/course/python-exam-active-study-loop-dashboard"


def build_python_exam_active_study_loop_dashboard(
    *,
    course_exam_coverage_dashboard: dict[str, Any] | None = None,
    python_exam_tutor_drill_pack: dict[str, Any] | None = None,
    python_exam_drill_loop_control_panel: dict[str, Any] | None = None,
    python_exam_drill_loop_progress_journal: dict[str, Any] | None = None,
    python_exam_resume_launcher: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    coverage = course_exam_coverage_dashboard if isinstance(course_exam_coverage_dashboard, dict) else {}
    pack = python_exam_tutor_drill_pack if isinstance(python_exam_tutor_drill_pack, dict) else {}
    control = python_exam_drill_loop_control_panel if isinstance(python_exam_drill_loop_control_panel, dict) else {}
    journal = python_exam_drill_loop_progress_journal if isinstance(python_exam_drill_loop_progress_journal, dict) else {}
    launcher = python_exam_resume_launcher if isinstance(python_exam_resume_launcher, dict) else {}
    selected = effective_selected_skill(selected_skill_tag, launcher, journal, control, pack, coverage)
    rows = active_skill_rows(
        coverage=coverage,
        pack=pack,
        control=control,
        journal=journal,
        launcher=launcher,
        selected_skill_tag=selected,
    )
    summary = active_summary(rows=rows, selected_skill_tag=selected, launcher=launcher)
    payload = {
        "schema_version": PYTHON_EXAM_ACTIVE_STUDY_LOOP_DASHBOARD_SCHEMA_VERSION,
        "artifact_type": "python_exam_active_study_loop_dashboard",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_active_study_loop_dashboard_ready" if rows else "python_exam_active_study_loop_dashboard_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Active Study Loop Dashboard. It merges Progress Journal, Resume Launcher, Drill Loop "
            "Control Panel, Course Exam Coverage Dashboard, and Source-Grounded Tutor Drill Pack into one "
            "metadata-only per-skill overview. It shows readiness, last safe microtask, next microtask/repeat/"
            "return status, Source-Card coverage, A0-A2 help level, checkpoint, ledger, review receipts, open "
            "repeats, completed skill loops, and the next safe action. It never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, "
            "rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "active_study_loop_endpoint": PYTHON_EXAM_ACTIVE_STUDY_LOOP_DASHBOARD_ENDPOINT,
        "selected_skill_tag": selected,
        "active_study_summary": summary,
        "skill_loop_dashboard": rows,
        "source_reports": {
            "coverage_status": coverage.get("status", "missing"),
            "drill_pack_status": pack.get("status", "missing"),
            "control_panel_status": control.get("status", "missing"),
            "progress_journal_status": journal.get("status", "missing"),
            "resume_launcher_status": launcher.get("status", "missing"),
        },
        "active_study_loop_receipt": active_receipt(summary, rows),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Active Study Loop Dashboard bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def active_skill_rows(
    *,
    coverage: dict[str, Any],
    pack: dict[str, Any],
    control: dict[str, Any],
    journal: dict[str, Any],
    launcher: dict[str, Any],
    selected_skill_tag: str,
) -> list[dict[str, Any]]:
    coverage_rows = [safe_coverage_row(item) for item in (coverage.get("skill_dashboard", []) or []) if isinstance(item, dict)]
    drill_rows = [safe_drill_row(item) for item in (pack.get("skill_drills", []) or []) if isinstance(item, dict)]
    rows_by_skill: dict[str, dict[str, Any]] = {}
    for row in coverage_rows:
        rows_by_skill[row["skill_tag"]] = row
    for drill in drill_rows:
        rows_by_skill.setdefault(drill["skill_tag"], minimal_coverage_row(drill["skill_tag"]))
        rows_by_skill[drill["skill_tag"]]["drill"] = drill
    if selected_skill_tag and selected_skill_tag not in rows_by_skill:
        rows_by_skill[selected_skill_tag] = minimal_coverage_row(selected_skill_tag)

    progress_entry = journal.get("journal_entry_preview", {}) if isinstance(journal.get("journal_entry_preview"), dict) else {}
    resume_state = launcher.get("resume_state", {}) if isinstance(launcher.get("resume_state"), dict) else {}
    decision = launcher.get("resume_decision", {}) if isinstance(launcher.get("resume_decision"), dict) else {}
    prefill = launcher.get("control_panel_prefill", {}) if isinstance(launcher.get("control_panel_prefill"), dict) else {}
    control_summary = control.get("control_panel_summary", {}) if isinstance(control.get("control_panel_summary"), dict) else {}
    control_receipt = control.get("control_panel_receipt", {}) if isinstance(control.get("control_panel_receipt"), dict) else {}
    completed_tags = [str(item) for item in (resume_state.get("completed_skill_tags", []) or [])]

    rows = []
    for tag in sorted(rows_by_skill, key=lambda value: (0 if value == selected_skill_tag else 1, value)):
        base = rows_by_skill[tag]
        drill = base.get("drill", {})
        selected = tag == selected_skill_tag
        entry = progress_entry if progress_entry.get("skill_tag") == tag else {}
        launcher_applies = selected and decision.get("selected_skill_tag") == tag
        resume_action = decision.get("action", "start_first_microtask") if launcher_applies else "review_skill_readiness"
        last_safe_microtask_hash = entry.get("microtask_hash", "") if selected else ""
        checkpoint_hash = entry.get("checkpoint_hash") or (control_summary.get("checkpoint_hash", "") if selected else "")
        next_microtask_hash = decision.get("selected_task_hash", "") if launcher_applies and resume_action == "run_next_microtask" else ""
        open_repeat_task_hash = decision.get("selected_task_hash", "") if launcher_applies and resume_action == "repeat_current_microtask" else ""
        completed = tag in completed_tags or (launcher_applies and resume_action == "return_to_skill_dashboard")
        next_action = next_safe_action(
            workspace_readiness=base.get("workspace_readiness", "unknown"),
            drill_status=drill.get("status", "missing"),
            resume_action=resume_action,
            selected=selected,
            completed=completed,
        )
        rows.append(
            {
                "skill_tag": tag,
                "title": base.get("title", tag),
                "selected": selected,
                "workspace_readiness": base.get("workspace_readiness", "unknown"),
                "drill_status": drill.get("status", "missing"),
                "source_card_ids": entry.get("source_card_ids") or drill.get("source_card_ids") or base.get("source_card_ids", []),
                "source_anchor_count": int(entry.get("source_anchor_count") or base.get("source_anchor_count", 0) or 0),
                "reviewed_notebook_anchor_count": int(base.get("reviewed_notebook_anchor_count", 0) or 0),
                "source_coverage_status": source_coverage_status(base, drill),
                "microtask_count": int(drill.get("microtask_count", 0) or 0),
                "last_safe_microtask_hash": last_safe_microtask_hash,
                "next_microtask_hash": next_microtask_hash,
                "open_repeat_task_hash": open_repeat_task_hash,
                "completed_skill_loop": completed,
                "resume_action": resume_action,
                "next_safe_action": next_action,
                "help_level": entry.get("help_level") or prefill.get("requested_help_level") or "A2",
                "allowed_help_levels": safe_help_levels(drill.get("allowed_help_levels") or base.get("allowed_exam_help", [])),
                "checkpoint_hash": checkpoint_hash,
                "help_ledger_event_hash": entry.get("help_ledger_event_hash", ""),
                "carryover_session_receipt_id": entry.get("carryover_session_receipt_id", ""),
                "review_loop_receipt_id": entry.get("review_loop_receipt_id", ""),
                "control_panel_receipt_id": entry.get("control_panel_receipt_id") or (control_receipt.get("receipt_id", "") if selected else ""),
                "prefill_hash": prefill.get("prefill_hash", "") if launcher_applies else "",
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
                "score_returned": False,
                "grade_returned": False,
            }
        )
    return rows


def safe_coverage_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(row.get("skill_tag", "")),
        "title": str(row.get("title", row.get("skill_tag", ""))),
        "workspace_readiness": str(row.get("workspace_readiness", "unknown")),
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(row.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(row.get("reviewed_notebook_anchor_count", 0) or 0),
        "allowed_exam_help": [str(item) for item in (row.get("allowed_exam_help", []) or [])],
    }


def safe_drill_row(drill: dict[str, Any]) -> dict[str, Any]:
    source = drill.get("source_anchor_metadata", {}) if isinstance(drill.get("source_anchor_metadata"), dict) else {}
    return {
        "skill_tag": str(drill.get("skill_tag", "")),
        "title": str(drill.get("title", drill.get("skill_tag", ""))),
        "status": str(drill.get("status", "missing")),
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "microtask_count": len(drill.get("microtasks", []) or []),
        "allowed_help_levels": safe_help_levels(drill.get("allowed_help_levels", [])),
    }


def minimal_coverage_row(skill_tag: str) -> dict[str, Any]:
    return {
        "skill_tag": str(skill_tag),
        "title": str(skill_tag),
        "workspace_readiness": "unknown",
        "source_card_ids": [],
        "source_anchor_count": 0,
        "reviewed_notebook_anchor_count": 0,
        "allowed_exam_help": ["A0", "A1", "A2"],
    }


def active_summary(*, rows: list[dict[str, Any]], selected_skill_tag: str, launcher: dict[str, Any]) -> dict[str, Any]:
    selected_row = next((row for row in rows if row.get("selected")), rows[0] if rows else {})
    return {
        "skill_count": len(rows),
        "selected_skill_tag": selected_skill_tag,
        "workspace_ready_skill_count": len(
            [row for row in rows if row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run"]
        ),
        "active_resume_action": nested(launcher, "resume_decision", "action") or selected_row.get("resume_action", ""),
        "next_safe_action": selected_row.get("next_safe_action", "review_skill_readiness"),
        "open_repeat_count": len([row for row in rows if row.get("open_repeat_task_hash")]),
        "completed_skill_loop_count": len([row for row in rows if row.get("completed_skill_loop")]),
        "source_anchor_count": sum(int(row.get("source_anchor_count", 0) or 0) for row in rows),
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def source_coverage_status(base: dict[str, Any], drill: dict[str, Any]) -> str:
    if int(base.get("source_anchor_count", 0) or 0) <= 0 and int(drill.get("source_anchor_count", 0) or 0) <= 0:
        return "needs_source_anchor_review"
    if int(base.get("reviewed_notebook_anchor_count", 0) or 0) <= 0:
        return "needs_notebook_anchor_review"
    return "source_coverage_ready"


def next_safe_action(
    *,
    workspace_readiness: str,
    drill_status: str,
    resume_action: str,
    selected: bool,
    completed: bool,
) -> str:
    if completed:
        return "return_to_skill_dashboard"
    if selected and resume_action in {"run_next_microtask", "repeat_current_microtask", "start_first_microtask"}:
        return resume_action
    if workspace_readiness == "ready_for_exam_workspace_dry_run" and drill_status == "drill_ready":
        return "start_first_microtask"
    return "review_skill_readiness"


def active_receipt(summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "rows": rows}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "active_study_loop_dashboard_receipt_ready_not_exam_clearance",
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
                ("resume_decision", "selected_skill_tag"),
                ("journal_entry_preview", "skill_tag"),
                ("control_panel_summary", "selected_skill_tag"),
                ("selected_skill_tag",),
            ]:
                value = nested(report, *path)
                if value:
                    return str(value)
    return "general_python"


def safe_help_levels(values: Any) -> list[str]:
    text = " ".join(str(item) for item in (values or []))
    levels = [level for level in ["A0", "A1", "A2"] if level in text]
    return levels or ["A0", "A1", "A2"]


def next_actions(summary: dict[str, Any]) -> list[str]:
    action = summary.get("next_safe_action")
    if action == "run_next_microtask":
        return [
            "Open the Resume Launcher prefilled Control Panel for the next microtask.",
            "Keep notebook work local and append progress only with operator confirmation.",
            "Stay A0-A2 and not_cleared.",
        ]
    if action == "repeat_current_microtask":
        return [
            "Repeat the current microtask with a fresh local checkpoint.",
            "Use only hash-based evidence and do not infer grades or final interpretations.",
        ]
    if action == "return_to_skill_dashboard":
        return [
            "Return to the skill dashboard and select the next ready course skill.",
            "Keep completed loops as metadata-only review evidence.",
        ]
    return [
        "Review source coverage and drill readiness before starting the next microtask.",
        "Keep the dashboard dry-run, metadata-only, and not_cleared.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-active-study-loop-dashboard")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
