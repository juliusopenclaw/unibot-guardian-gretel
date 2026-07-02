from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_drill_loop_progress_journal import (
    build_progress_resume_state,
    read_python_exam_drill_loop_progress_journal,
)


PYTHON_EXAM_RESUME_LAUNCHER_SCHEMA_VERSION = "unibot-python-exam-resume-launcher-v1"
PYTHON_EXAM_RESUME_LAUNCHER_ENDPOINT = "/api/unibot/course/python-exam-resume-launcher"
CONTROL_PANEL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-control-panel"
COURSE_DASHBOARD_ENDPOINT = "/api/unibot/course/exam-coverage-dashboard"


def build_python_exam_resume_launcher(
    *,
    python_exam_drill_loop_progress_journal: dict[str, Any] | None = None,
    progress_journal_summary: dict[str, Any] | None = None,
    progress_journal_path: str | Path | None = None,
    previous_records: list[dict[str, Any]] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    context = progress_context(
        progress_journal=python_exam_drill_loop_progress_journal,
        progress_summary=progress_journal_summary,
        progress_journal_path=progress_journal_path,
        previous_records=previous_records,
        selected_skill_tag=selected_skill_tag,
    )
    decision = resume_decision(context)
    prefill = control_panel_prefill(context=context, decision=decision)
    payload = {
        "schema_version": PYTHON_EXAM_RESUME_LAUNCHER_SCHEMA_VERSION,
        "artifact_type": "python_exam_resume_launcher",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Resume Launcher. It reads only Drill Loop Progress Journal resume metadata and prepares "
            "the next safe Control Panel or skill-dashboard action. It uses only resume state, skill tag, "
            "microtask hash, checkpoint hash, Source-Card anchors, A0-A2 help level, receipts, and not_cleared "
            "metadata. It never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, "
            "automatic grading, or exam clearance."
        ),
        "resume_launcher_endpoint": PYTHON_EXAM_RESUME_LAUNCHER_ENDPOINT,
        "resume_source": context["source"],
        "resume_decision": decision,
        "control_panel_prefill": prefill,
        "resume_state": context["resume_state"],
        "latest_progress_entry": context["latest_entry"],
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
        "storage_policy": (
            "Resume launcher returns only hash-based prefill metadata and never writes local files by itself."
        ),
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Resume Launcher bleibt not_cleared."
        ),
        "next_actions": next_actions(decision),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def progress_context(
    *,
    progress_journal: dict[str, Any] | None,
    progress_summary: dict[str, Any] | None,
    progress_journal_path: str | Path | None,
    previous_records: list[dict[str, Any]] | None,
    selected_skill_tag: str,
) -> dict[str, Any]:
    records = [item for item in (previous_records or []) if isinstance(item, dict)]
    source = "previous_records"
    journal = progress_journal if isinstance(progress_journal, dict) else {}
    summary = progress_summary if isinstance(progress_summary, dict) else {}
    if journal:
        source = "progress_journal_report"
        preview = journal.get("preview_record") if isinstance(journal.get("preview_record"), dict) else None
        stored = journal.get("stored_record") if isinstance(journal.get("stored_record"), dict) else None
        record = stored or preview
        if isinstance(record, dict):
            records.append(record)
    if summary and isinstance(summary.get("resume_state"), dict):
        source = "progress_journal_summary"
    if progress_journal_path:
        source = "progress_journal_path"
        records.extend(read_python_exam_drill_loop_progress_journal(progress_journal_path).get("records", []))
    accepted = [record for record in records if isinstance(record, dict) and record.get("status") == "accepted"]
    latest = {}
    if accepted and isinstance(accepted[-1].get("entry"), dict):
        latest = safe_latest_entry(accepted[-1]["entry"])
    elif journal and isinstance(journal.get("journal_entry_preview"), dict):
        latest = safe_latest_entry(journal["journal_entry_preview"])
    resume = (
        dict(summary.get("resume_state", {}))
        if summary and isinstance(summary.get("resume_state"), dict) and not accepted
        else build_progress_resume_state(records)
    )
    skill_tag = str(latest.get("skill_tag") or selected_skill_tag or "")
    if not skill_tag and isinstance(resume.get("completed_skill_tags"), list) and resume["completed_skill_tags"]:
        skill_tag = str(resume["completed_skill_tags"][-1])
    return {
        "source": source,
        "record_count": len(records),
        "accepted_record_count": len(accepted),
        "resume_state": safe_resume_state(resume),
        "latest_entry": latest,
        "selected_skill_tag": skill_tag or "general_python",
    }


def safe_latest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(entry.get("skill_tag", "")),
        "microtask_hash": str(entry.get("microtask_hash", "")),
        "checkpoint_hash": str(entry.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (entry.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(entry.get("source_anchor_count", len(entry.get("source_card_ids", []) or [])) or 0),
        "help_level": safe_help_level(str(entry.get("help_level", "A2"))),
        "help_ledger_event_hash": str(entry.get("help_ledger_event_hash", "")),
        "carryover_session_receipt_id": str(entry.get("carryover_session_receipt_id", "")),
        "review_loop_receipt_id": str(entry.get("review_loop_receipt_id", "")),
        "control_panel_receipt_id": str(entry.get("control_panel_receipt_id", "")),
        "next_step_action": safe_resume_action(str(entry.get("next_step_action", ""))),
        "next_step_status": str(entry.get("next_step_status", "")),
        "next_task_hash": str(entry.get("next_task_hash", "")),
        "reflection_status": str(entry.get("reflection_status", "missing")),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "score_returned": False,
        "grade_returned": False,
    }


def safe_resume_state(resume_state: dict[str, Any]) -> dict[str, Any]:
    action = safe_resume_action(str(resume_state.get("resume_action", "")))
    return {
        "status": str(resume_state.get("status", "empty")),
        "record_count": int(resume_state.get("record_count", 0) or 0),
        "accepted_record_count": int(resume_state.get("accepted_record_count", 0) or 0),
        "blocked_record_count": int(resume_state.get("blocked_record_count", 0) or 0),
        "last_safe_microtask_hash": str(resume_state.get("last_safe_microtask_hash", "")),
        "last_checkpoint_hash": str(resume_state.get("last_checkpoint_hash", "")),
        "next_microtask_hash": str(resume_state.get("next_microtask_hash", "")),
        "open_repeat_task_hash": str(resume_state.get("open_repeat_task_hash", "")),
        "completed_skill_tags": [str(item) for item in (resume_state.get("completed_skill_tags", []) or [])],
        "resume_action": action,
        "reflection_status": str(resume_state.get("reflection_status", "missing")),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def resume_decision(context: dict[str, Any]) -> dict[str, Any]:
    resume = context["resume_state"]
    latest = context["latest_entry"]
    action = safe_resume_action(str(resume.get("resume_action") or latest.get("next_step_action") or ""))
    if action == "run_next_microtask":
        task_hash = str(resume.get("next_microtask_hash") or latest.get("next_task_hash") or "")
        status = "python_exam_resume_launcher_next_microtask_ready" if task_hash else "python_exam_resume_launcher_attention"
        route = "control_panel"
    elif action == "repeat_current_microtask":
        task_hash = str(resume.get("open_repeat_task_hash") or resume.get("last_safe_microtask_hash") or latest.get("microtask_hash") or "")
        status = "python_exam_resume_launcher_repeat_microtask_ready" if task_hash else "python_exam_resume_launcher_attention"
        route = "control_panel"
    elif action == "return_to_skill_dashboard":
        task_hash = ""
        status = "python_exam_resume_launcher_return_to_skill_dashboard_ready"
        route = "skill_dashboard"
    else:
        action = "start_first_microtask"
        task_hash = ""
        status = "python_exam_resume_launcher_first_microtask_ready"
        route = "control_panel"
    seed = {
        "source": context["source"],
        "skill_tag": context["selected_skill_tag"],
        "action": action,
        "task_hash": task_hash,
        "checkpoint_hash": resume.get("last_checkpoint_hash", ""),
    }
    decision_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": status,
        "action": action,
        "route": route,
        "selected_skill_tag": context["selected_skill_tag"],
        "selected_task_hash": task_hash,
        "checkpoint_hash": str(resume.get("last_checkpoint_hash", "")),
        "help_level": safe_help_level(str(latest.get("help_level", "A2"))),
        "decision_hash": decision_hash,
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def control_panel_prefill(*, context: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    latest = context["latest_entry"]
    endpoint = CONTROL_PANEL_ENDPOINT if decision["route"] == "control_panel" else COURSE_DASHBOARD_ENDPOINT
    prefill_seed = {
        "endpoint": endpoint,
        "selected_skill_tag": decision.get("selected_skill_tag", ""),
        "selected_task_hash": decision.get("selected_task_hash", ""),
        "checkpoint_hash": decision.get("checkpoint_hash", ""),
        "help_level": decision.get("help_level", "A2"),
        "action": decision.get("action", ""),
        "source_card_ids": latest.get("source_card_ids", []),
    }
    return {
        "status": "prefill_ready",
        "endpoint": endpoint,
        "method": "POST",
        "action": decision.get("action", ""),
        "selected_skill_tag": decision.get("selected_skill_tag", ""),
        "selected_task_hash": decision.get("selected_task_hash", ""),
        "last_checkpoint_hash": decision.get("checkpoint_hash", ""),
        "source_card_ids": latest.get("source_card_ids", []),
        "source_anchor_count": latest.get("source_anchor_count", 0),
        "requested_help_level": decision.get("help_level", "A2"),
        "operator_confirmations_default": "all_false_dry_run",
        "prefill_hash": sha256_text(json.dumps(prefill_seed, sort_keys=True, ensure_ascii=False)),
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def safe_resume_action(action: str) -> str:
    value = str(action or "").strip()
    if value in {"run_next_microtask", "repeat_current_microtask", "return_to_skill_dashboard", "start_first_microtask"}:
        return value
    return "start_first_microtask"


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def next_actions(decision: dict[str, Any]) -> list[str]:
    action = decision.get("action")
    if action == "run_next_microtask":
        return [
            "Open the Control Panel with the next microtask hash prefilled.",
            "Keep the next run dry-run unless a local write is individually confirmed.",
            "Continue storing only hashes, receipts, A0-A2 help level, and not_cleared metadata.",
        ]
    if action == "repeat_current_microtask":
        return [
            "Repeat the current microtask through the Control Panel because the journal requests recovery.",
            "Use a fresh local notebook checkpoint and keep raw notebook work local.",
            "Do not infer scores, grades, rankings, percentages, or final interpretations.",
        ]
    if action == "return_to_skill_dashboard":
        return [
            "Return to the Course Exam Coverage Dashboard and select the next source-grounded skill.",
            "Keep the previous skill loop as complete metadata only.",
            "Keep exam_deployment_status not_cleared.",
        ]
    return [
        "Start the first safe microtask for the selected skill through the Control Panel.",
        "Create a local notebook checkpoint before appending progress.",
        "Keep A0-A2 and not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-resume-launcher")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
