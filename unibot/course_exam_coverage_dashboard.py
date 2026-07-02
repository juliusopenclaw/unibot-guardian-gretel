from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .material_coverage_run import build_course_material_coverage_run
from .materials import sha256_text
from .public_safety import scan_text


COURSE_EXAM_COVERAGE_DASHBOARD_SCHEMA_VERSION = "unibot-course-exam-coverage-dashboard-v1"
COURSE_EXAM_COVERAGE_DASHBOARD_ENDPOINT = "/api/unibot/course/exam-coverage-dashboard"


def build_course_exam_coverage_dashboard(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_manifest_path: str | Path | None = None,
    manifest_apply_journal_path: str | Path | None = None,
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    focus_query: str = "",
    selected_skill_tag: str = "",
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    run_history_report: dict[str, Any] | None = None,
    build_current_console: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    coverage = build_course_material_coverage_run(
        safe_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        receipt_journal_path=receipt_journal_path,
        private_manifest_path=private_manifest_path,
        manifest_apply_journal_path=manifest_apply_journal_path,
        tutor_index_path=tutor_index_path,
        tutor_index_journal_path=tutor_index_journal_path,
        focus_query=focus_query or selected_skill_tag,
        public_safe=public_safe,
    )
    safe_console_reports = [item for item in (console_reports or []) if isinstance(item, dict)]
    safe_console_receipts = [item for item in (console_receipts or []) if isinstance(item, dict)]
    if isinstance(run_history_report, dict):
        history = run_history_report
    elif build_current_console or safe_console_reports or safe_console_receipts:
        history = build_exam_workspace_run_history_export_review(
            course_id=safe_id,
            console_reports=safe_console_reports,
            console_receipts=safe_console_receipts,
            build_current_console=build_current_console,
            base_path=base_path,
            max_files=max_files,
            review_policy=review_policy,
            decision_record=decision_record,
            decision_record_journal_path=decision_record_journal_path,
            receipts=receipts,
            receipt_journal_path=receipt_journal_path,
            private_manifest_path=private_manifest_path,
            manifest_apply_journal_path=manifest_apply_journal_path,
            tutor_index_path=tutor_index_path,
            tutor_index_journal_path=tutor_index_journal_path,
            focus_query=focus_query,
            selected_skill_tag=selected_skill_tag,
            public_safe=public_safe,
        )
    else:
        history = empty_history_report(safe_id)
    rows = build_dashboard_rows(
        skill_coverage=[item for item in coverage.get("skill_coverage", []) if isinstance(item, dict)],
        run_history=[item for item in history.get("run_history", []) if isinstance(item, dict)],
    )
    summary = dashboard_summary(coverage=coverage, history=history, rows=rows)
    report = {
        "schema_version": COURSE_EXAM_COVERAGE_DASHBOARD_SCHEMA_VERSION,
        "artifact_type": "course_exam_coverage_dashboard",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "course_exam_coverage_dashboard_ready",
        "dashboard_title": "Course Exam Coverage Dashboard",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Course Exam Coverage Dashboard. It merges material coverage, Exam-Skill readiness, Session Console "
            "receipts, and Run-History Export Review into a compact per-skill overview. It is dry-run and "
            "metadata-only: no raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "coverage_summary": coverage.get("coverage_summary", {}),
        "dashboard_summary": summary,
        "skill_dashboard": rows,
        "run_history_summary": history.get("history_summary", {}),
        "export_review_summary": safe_export_review_summary(history.get("export_review_package", {})),
        "coverage_receipt": {
            "status": "dashboard_receipt_ready_not_exam_clearance",
            "receipt_id": dashboard_receipt_id(summary=summary, rows=rows, history=history),
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "ledger_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; dieses Dashboard bleibt technisch nutzbar und not_cleared."
        ),
        "next_actions": dashboard_next_actions(rows),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_dashboard_rows(*, skill_coverage: list[dict[str, Any]], run_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in run_history:
        tag = str(entry.get("skill_tag", ""))
        if tag:
            entries_by_skill[tag].append(entry)

    rows = []
    for skill in skill_coverage:
        tag = str(skill.get("skill_tag", ""))
        entries = entries_by_skill.get(tag, [])
        help_profile = help_level_profile(entries)
        open_steps = open_operator_steps(entries)
        checkpoint_hashes = latest_checkpoint_hashes(entries)
        rows.append(
            {
                "skill_tag": tag,
                "title": skill.get("title", ""),
                "exam_task_type": skill.get("exam_task_type", ""),
                "workspace_readiness": skill.get("exam_workspace_readiness", "unknown"),
                "source_anchor_count": int(skill.get("source_anchor_count", 0) or 0),
                "source_card_ids": list(skill.get("source_card_ids", []) or [])[:8],
                "reviewed_notebook_anchor_count": int(skill.get("reviewed_notebook_anchor_count", 0) or 0),
                "ocr_gap_count": int(skill.get("ocr_gap_count", 0) or 0),
                "video_transcription_gap_count": int(skill.get("video_transcription_gap_count", 0) or 0),
                "coverage_gap_status": coverage_gap_status(skill),
                "latest_checkpoint_hashes": checkpoint_hashes,
                "checkpoint_hash_count": len(checkpoint_hashes),
                "help_level_profile": help_profile,
                "open_operator_confirmation_count": len(open_steps),
                "open_operator_confirmations": open_steps[:8],
                "next_safe_step": next_safe_step(skill, entries, open_steps),
                "allowed_exam_help": allowed_a0_a2(skill),
                "exam_deployment_status": "not_cleared",
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    return rows


def empty_history_report(course_id: str) -> dict[str, Any]:
    return {
        "artifact_type": "exam_workspace_run_history_export_review",
        "course_id": course_id,
        "status": "exam_workspace_run_history_waiting_for_session_history",
        "exam_deployment_status": "not_cleared",
        "run_history": [],
        "history_summary": {
            "run_count": 0,
            "skill_tags": [],
            "checkpoint_hash_count": 0,
            "checkpoint_hashes": [],
            "help_level_profile": {},
            "blocker_profile": {},
            "confirmed_operator_step_count": 0,
            "open_operator_step_count": 0,
            "raw_history_returned": False,
        },
        "export_review_package": {
            "status": "export_review_waiting_for_session_history",
            "human_reviewable_independence_evidence": False,
            "review_items": {
                "reflection_statuses": [],
                "operator_confirmation_profile": {"confirmed_step_count": 0, "open_step_count": 0},
            },
        },
        "export_review_receipt": {"status": "waiting_for_session_history", "receipt_hash": ""},
    }


def latest_checkpoint_hashes(entries: list[dict[str, Any]]) -> list[str]:
    hashes = []
    for entry in sorted(entries, key=lambda item: int(item.get("repeat_run_index", 0) or 0), reverse=True):
        checkpoint_hash = str(entry.get("checkpoint_hash", ""))
        if checkpoint_hash and checkpoint_hash not in hashes:
            hashes.append(checkpoint_hash)
    return hashes[:4]


def help_level_profile(entries: list[dict[str, Any]]) -> dict[str, int]:
    profile: dict[str, int] = {}
    for entry in entries:
        level = str(entry.get("help_level", ""))
        if level:
            profile[level] = profile.get(level, 0) + 1
    return profile


def open_operator_steps(entries: list[dict[str, Any]]) -> list[str]:
    steps = []
    for entry in entries:
        confirmations = entry.get("operator_confirmations", {}) if isinstance(entry.get("operator_confirmations"), dict) else {}
        for step in confirmations.get("open_steps", []) or []:
            step_text = str(step)
            if step_text and step_text not in steps:
                steps.append(step_text)
    return steps


def coverage_gap_status(skill: dict[str, Any]) -> str:
    if int(skill.get("source_anchor_count", 0) or 0) <= 0:
        return "needs_source_anchor_review"
    if int(skill.get("reviewed_notebook_anchor_count", 0) or 0) <= 0:
        return "needs_notebook_anchor_review"
    if int(skill.get("video_transcription_gap_count", 0) or 0) > 0:
        return "video_transcription_pending"
    if int(skill.get("ocr_gap_count", 0) or 0) > 0:
        return "ocr_pending"
    return "coverage_ready_for_dry_run"


def next_safe_step(skill: dict[str, Any], entries: list[dict[str, Any]], open_steps: list[str]) -> str:
    if open_steps:
        return "review open operator confirmations before any local write"
    if not entries and skill.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run":
        return "start Session Console dry-run for this skill with A0-A2 help"
    if entries:
        return "review latest checkpoint hash, help-level profile, and export receipt"
    return str(skill.get("next_step", "review coverage state"))


def allowed_a0_a2(skill: dict[str, Any]) -> list[str]:
    allowed = [str(item) for item in (skill.get("allowed_exam_help", []) or [])]
    safe = [item for item in allowed if item.startswith(("A0", "A1", "A2"))]
    return safe or ["A0", "A1", "A2"]


def dashboard_summary(*, coverage: dict[str, Any], history: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    coverage_summary = coverage.get("coverage_summary", {}) if isinstance(coverage.get("coverage_summary"), dict) else {}
    history_summary = history.get("history_summary", {}) if isinstance(history.get("history_summary"), dict) else {}
    return {
        "skill_count": len(rows),
        "workspace_ready_skill_count": int(coverage_summary.get("exam_workspace_ready_skill_count", 0) or 0),
        "skills_with_history_count": len([row for row in rows if row.get("checkpoint_hash_count", 0)]),
        "source_anchor_count": sum(int(row.get("source_anchor_count", 0) or 0) for row in rows),
        "ocr_gap_count": int(coverage_summary.get("ocr_gap_count", 0) or 0),
        "video_gap_count": int(coverage_summary.get("video_gap_count", 0) or 0),
        "checkpoint_hash_count": int(history_summary.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": sum(int(row.get("open_operator_confirmation_count", 0) or 0) for row in rows),
        "help_level_profile": dict(history_summary.get("help_level_profile", {}) or {}),
        "exam_deployment_status": "not_cleared",
    }


def safe_export_review_summary(package: dict[str, Any]) -> dict[str, Any]:
    review = package.get("review_items", {}) if isinstance(package.get("review_items"), dict) else {}
    profile = review.get("operator_confirmation_profile", {}) if isinstance(review.get("operator_confirmation_profile"), dict) else {}
    return {
        "status": package.get("status", "unknown"),
        "human_reviewable_independence_evidence": bool(package.get("human_reviewable_independence_evidence", False)),
        "reflection_statuses": list(review.get("reflection_statuses", []) or [])[:8],
        "confirmed_operator_step_count": int(profile.get("confirmed_step_count", 0) or 0),
        "open_operator_step_count": int(profile.get("open_step_count", 0) or 0),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def dashboard_receipt_id(*, summary: dict[str, Any], rows: list[dict[str, Any]], history: dict[str, Any]) -> str:
    seed = {
        "summary": summary,
        "skill_tags": [row.get("skill_tag", "") for row in rows],
        "history_receipt": history.get("export_review_receipt", {}).get("receipt_hash", "")
        if isinstance(history.get("export_review_receipt"), dict)
        else "",
    }
    return sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))[:20]


def dashboard_next_actions(rows: list[dict[str, Any]]) -> list[str]:
    open_confirmation_rows = [row for row in rows if row.get("open_operator_confirmation_count", 0)]
    if open_confirmation_rows:
        return [
            "Review open operator confirmations before any local write.",
            "Use Session Console or Run-History Export Review for the selected skill; keep A0-A2 and not_cleared.",
        ]
    ready_without_history = [
        row
        for row in rows
        if row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run" and not row.get("checkpoint_hash_count")
    ]
    if ready_without_history:
        tag = ready_without_history[0].get("skill_tag", "selected_skill")
        return [f"Start a Session Console dry-run for {tag} with A0-A2 help, then rebuild the dashboard."]
    return ["Review per-skill next safe steps and continue material or notebook-anchor readiness work."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "course-exam-coverage-dashboard")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
