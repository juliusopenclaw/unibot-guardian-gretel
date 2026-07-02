from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_drill_loop_control_panel import build_python_exam_drill_loop_control_panel, nested


PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_SCHEMA_VERSION = "unibot-python-exam-drill-loop-progress-journal-v1"
PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-progress-journal"
DEFAULT_PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_PATH = (
    Path.home() / ".unibot_guardian" / "python_exam_drill_loop_progress.jsonl"
)


def resolve_python_exam_drill_loop_progress_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_PATH


def build_python_exam_drill_loop_progress_journal(
    *,
    python_exam_drill_loop_control_panel: dict[str, Any] | None = None,
    progress_journal_path: str | Path | None = None,
    previous_records: list[dict[str, Any]] | None = None,
    operator_confirmed_progress_journal_append: bool = False,
    public_safe: bool = True,
    **control_panel_kwargs: Any,
) -> dict[str, Any]:
    panel = (
        python_exam_drill_loop_control_panel
        if isinstance(python_exam_drill_loop_control_panel, dict)
        else build_python_exam_drill_loop_control_panel(public_safe=public_safe, **control_panel_kwargs)
    )
    record = sanitize_python_exam_drill_loop_progress_record(panel)
    confirmed = bool(operator_confirmed_progress_journal_append)
    accepted = record.get("status") == "accepted"
    will_write = bool(confirmed and accepted)
    append_status = "stored" if will_write else "write_preview_ready"
    if confirmed and not accepted:
        append_status = "blocked_record_not_accepted"

    existing_records = read_python_exam_drill_loop_progress_journal(progress_journal_path).get("records", [])
    supplied_records = [item for item in (previous_records or []) if isinstance(item, dict)]
    projected_records = [*existing_records, *supplied_records]
    if will_write:
        target = resolve_python_exam_drill_loop_progress_journal_path(progress_journal_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        projected_records.append(record)
    elif record.get("status") == "accepted":
        projected_records.append(record)

    entry = record.get("entry", {}) if isinstance(record.get("entry"), dict) else {}
    resume = build_progress_resume_state(projected_records)
    payload = {
        "schema_version": PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_loop_progress_journal",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": append_status,
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Drill Loop Progress Journal. It previews or appends hash-only drill-loop progress records "
            "from the Control Panel for resume/recovery. Entries store only skill tag, microtask hash, checkpoint "
            "hash, Source-Card anchors, A0-A2 help level, Help-Ledger event hash, Carryover receipt, Review Loop "
            "receipt, next-step action, reflection status, and not_cleared receipt. It never returns raw queries, "
            "course raw text, notebook code, local paths, values, solutions, final interpretations, scores, "
            "percentages, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "progress_journal_endpoint": PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_ENDPOINT,
        "journal_written": will_write,
        "dry_run_default": True,
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmed_progress_journal_append": confirmed,
        "local_writes_requested": confirmed,
        "append_summary": {
            "status": append_status,
            "record_status": record.get("status", "blocked"),
            "journal_written": will_write,
            "record_id": record.get("record_id", ""),
            "entry_hash": entry.get("entry_hash", ""),
            "skill_tag": entry.get("skill_tag", ""),
            "next_step_action": entry.get("next_step_action", ""),
            "not_cleared_receipt": True,
            "local_path_returned": False,
        },
        "journal_entry_preview": entry,
        "stored_record": record if will_write else None,
        "preview_record": record if not will_write else None,
        "resume_state": resume,
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
            "local jsonl progress journal; API output returns only metadata, hashes, receipts, A0-A2 help level, "
            "reflection status, resume state, and not_cleared status; no raw text, notebook code, values, or paths"
        ),
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Progress Journal bleibt not_cleared."
        ),
        "next_actions": next_actions(append_status, resume),
    }
    attach_public_scan(payload, public_safe=public_safe, source_name="python-exam-drill-loop-progress-journal")
    return payload


def sanitize_python_exam_drill_loop_progress_record(control_panel: dict[str, Any] | None) -> dict[str, Any]:
    panel = control_panel if isinstance(control_panel, dict) else {}
    summary = panel.get("control_panel_summary", {}) if isinstance(panel.get("control_panel_summary"), dict) else {}
    evidence = panel.get("session_evidence_summary", {}) if isinstance(panel.get("session_evidence_summary"), dict) else {}
    next_step = panel.get("next_step_recommendation", {}) if isinstance(panel.get("next_step_recommendation"), dict) else {}
    artifacts = panel.get("control_panel_artifacts", {}) if isinstance(panel.get("control_panel_artifacts"), dict) else {}
    review_loop = artifacts.get("drill_session_review_loop", {}) if isinstance(artifacts.get("drill_session_review_loop"), dict) else {}
    receipt = panel.get("control_panel_receipt", {}) if isinstance(panel.get("control_panel_receipt"), dict) else {}
    issues: list[str] = []
    if panel.get("artifact_type") != "python_exam_drill_loop_control_panel":
        issues.append("control_panel_artifact_type_invalid")
    if panel.get("status") != "python_exam_drill_loop_control_panel_ready":
        issues.append("control_panel_must_be_ready")
    if panel.get("exam_deployment_status") != "not_cleared":
        issues.append("exam_deployment_must_remain_not_cleared")
    if panel.get("public_safety_status") not in {"pass", "local_private_mode"}:
        issues.append("control_panel_public_safety_must_pass")
    help_level = str(evidence.get("help_level") or next_step.get("help_level") or "A2").upper()
    if help_level not in {"A0", "A1", "A2"}:
        issues.append("help_level_must_be_a0_a2")
        help_level = "A2"
    for flag in [
        "raw_query_returned",
        "raw_text_returned",
        "raw_cell_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
        "values_returned",
        "solutions_returned",
        "final_interpretations_returned",
        "score_returned",
        "percentage_returned",
        "ranking_returned",
        "grade_returned",
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]:
        if panel.get(flag) is True:
            issues.append(f"{flag}_must_be_false")

    entry_seed = {
        "skill_tag": summary.get("selected_skill_tag") or evidence.get("skill_tag") or "",
        "microtask_hash": evidence.get("microtask_hash") or summary.get("current_task_hash") or "",
        "checkpoint_hash": evidence.get("checkpoint_hash") or summary.get("checkpoint_hash") or "",
        "source_card_ids": [str(item) for item in (evidence.get("source_card_ids", []) or [])][:8],
        "help_level": help_level,
        "help_ledger_event_hash": evidence.get("help_ledger_event_hash") or "",
        "carryover_session_receipt_id": evidence.get("carryover_session_receipt_id") or "",
        "review_loop_receipt_id": nested(review_loop, "review_loop_receipt", "receipt_id") or "",
        "control_panel_receipt_id": receipt.get("receipt_id", ""),
        "next_step_action": next_step.get("action") or summary.get("next_step_action") or "missing",
        "next_step_status": next_step.get("status") or summary.get("next_step_status") or "missing",
        "next_task_hash": next_step.get("next_task_hash") or summary.get("next_task_hash") or "",
        "reflection_status": evidence.get("reflection_status") or summary.get("reflection_status") or "missing",
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }
    entry_hash = sha256_text(json.dumps(entry_seed, sort_keys=True, ensure_ascii=False))
    entry = {
        **entry_seed,
        "entry_hash": entry_hash,
        "source_anchor_count": len(entry_seed["source_card_ids"]),
        "raw_query_stored": False,
        "raw_text_stored": False,
        "notebook_code_stored": False,
        "local_path_stored": False,
        "score_stored": False,
        "grade_stored": False,
        "exam_clearance_stored": False,
        "issues": sorted(set(issues)),
    }
    record_hash = sha256_text(json.dumps(entry, sort_keys=True, ensure_ascii=False))
    record = {
        "schema_version": PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_loop_progress_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted" if not entry["issues"] else "blocked",
        "record_id": record_hash[:20],
        "record_hash": record_hash,
        "entry": entry,
        "storage_policy": (
            "local-only jsonl; stores skill tag, microtask/checkpoint/source-card hashes, A0-A2 level, receipts, "
            "reflection status, next action, and not_cleared status only"
        ),
    }
    attach_public_scan(record, public_safe=True, source_name="python-exam-drill-loop-progress-journal-record")
    if record.get("public_safety_status") != "pass":
        record["status"] = "blocked"
        record["entry"]["issues"] = sorted(set(record["entry"]["issues"] + ["public_safety_must_pass"]))
    return record


def read_python_exam_drill_loop_progress_journal(
    path: str | Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    journal_path = resolve_python_exam_drill_loop_progress_journal_path(path)
    if not journal_path.exists():
        return {"status": "empty", "count": 0, "records": []}
    rows = []
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    if limit is not None:
        rows = rows[-max(0, int(limit)) :]
    return {"status": "ok", "count": len(rows), "records": rows}


def summarize_python_exam_drill_loop_progress_journal(path: str | Path | None = None) -> dict[str, Any]:
    journal = read_python_exam_drill_loop_progress_journal(path)
    records = [record for record in journal.get("records", []) if isinstance(record, dict)]
    summary = {
        "schema_version": PYTHON_EXAM_DRILL_LOOP_PROGRESS_JOURNAL_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_loop_progress_journal_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": journal.get("status", "empty"),
        "resume_state": build_progress_resume_state(records),
        "exam_deployment_status": "not_cleared",
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
        "storage_policy": "summary excludes raw queries, course raw text, notebook code, values, solutions, and paths",
    }
    attach_public_scan(summary, public_safe=True, source_name="python-exam-drill-loop-progress-journal-summary")
    return summary


def build_progress_resume_state(records: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [record for record in records if isinstance(record, dict) and record.get("status") == "accepted"]
    entries = [record.get("entry", {}) for record in accepted if isinstance(record.get("entry"), dict)]
    latest = entries[-1] if entries else {}
    next_action = str(latest.get("next_step_action") or "start_first_microtask")
    open_repeat = latest.get("microtask_hash", "") if next_action == "repeat_current_microtask" else ""
    next_microtask = latest.get("next_task_hash", "") if next_action == "run_next_microtask" else ""
    completed = []
    for entry in entries:
        if entry.get("next_step_action") == "return_to_skill_dashboard" and entry.get("skill_tag") not in completed:
            completed.append(entry.get("skill_tag"))
    return {
        "status": "resume_ready" if entries else "empty",
        "record_count": len(records),
        "accepted_record_count": len(accepted),
        "blocked_record_count": len(records) - len(accepted),
        "last_safe_microtask_hash": latest.get("microtask_hash", ""),
        "last_checkpoint_hash": latest.get("checkpoint_hash", ""),
        "next_microtask_hash": next_microtask,
        "open_repeat_task_hash": open_repeat,
        "completed_skill_tags": completed,
        "resume_action": next_action,
        "reflection_status": latest.get("reflection_status", "missing") if latest else "missing",
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def next_actions(append_status: str, resume_state: dict[str, Any]) -> list[str]:
    if append_status == "write_preview_ready":
        return [
            "Review the Progress Journal preview before confirming any local append.",
            "Use the resume state to continue with the next microtask or repeat the current one.",
            "Keep A0-A2, metadata-only evidence, and not_cleared.",
        ]
    if append_status == "stored":
        return [
            f"Resume with action: {resume_state.get('resume_action', 'review')}.",
            "Continue the next Drill Loop cycle through the Control Panel.",
            "Keep raw notebook work local and export only hashes, receipts, and safe metadata.",
        ]
    return [
        "Fix the Control Panel readiness or public-safety issue before appending the Progress Journal.",
        "Do not infer scores, grades, rankings, percentages, or exam clearance.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
