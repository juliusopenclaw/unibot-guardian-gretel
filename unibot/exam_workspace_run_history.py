from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_session_console import build_exam_workspace_session_console
from .materials import sha256_text
from .public_safety import scan_text


EXAM_WORKSPACE_RUN_HISTORY_SCHEMA_VERSION = "unibot-exam-workspace-run-history-v1"
RUN_HISTORY_ENDPOINT = "/api/unibot/exam-workspace/run-history-export-review"


def build_exam_workspace_run_history_export_review(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    build_current_console: bool = False,
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
    ledger_path: str | Path | None = None,
    focus_query: str = "",
    query: str = "",
    selected_skill_tag: str = "",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    cell_source: str = "",
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    checkpoint_journal_path: str | Path | None = None,
    repeat_run_index: int = 1,
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    reports = [item for item in (console_reports or []) if isinstance(item, dict)]
    receipt_records = [item for item in (console_receipts or []) if isinstance(item, dict)]
    if build_current_console or not reports and not receipt_records:
        current = build_exam_workspace_session_console(
            course_id=safe_id,
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
            ledger_path=ledger_path,
            focus_query=focus_query,
            query=query,
            selected_skill_tag=selected_skill_tag,
            requested_help_level=requested_help_level,
            exam_status=exam_status,
            student_reflection=student_reflection,
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
            cell_source=cell_source,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            checkpoint_journal_path=checkpoint_journal_path,
            repeat_run_index=repeat_run_index,
            previous_console_receipts=receipt_records,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
            operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
            operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
            operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
            operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
            public_safe=public_safe,
        )
        reports.append(current)

    entries = build_history_entries(reports=reports, receipts=receipt_records)
    package = export_review_package(entries)
    review_receipt = export_review_receipt(safe_id, package, entries)
    report = {
        "schema_version": EXAM_WORKSPACE_RUN_HISTORY_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_run_history_export_review",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": history_status(entries),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Exam Workspace Run History and Export Review. It aggregates hash-only Session Console receipts into "
            "a human-reviewable package: skill, checkpoint hashes, help-level profile, Help-Ledger preview, "
            "blockers, operator confirmations, export receipt, and reflection status. It never returns raw queries, "
            "course raw text, notebook code, local paths, values, final interpretations, grading, proctoring, AI "
            "detection, or exam clearance."
        ),
        "run_history": entries,
        "history_summary": history_summary(entries),
        "export_review_package": package,
        "export_review_receipt": review_receipt,
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; History und Export Review bleiben not_cleared."
        ),
        "next_actions": history_next_actions(entries),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_history_entries(*, reports: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for report in reports:
        console = report.get("session_console", {}) if isinstance(report.get("session_console"), dict) else {}
        receipt = report.get("session_console_receipt", {}) if isinstance(report.get("session_console_receipt"), dict) else {}
        selected = console.get("selected_skill", {}) if isinstance(console.get("selected_skill"), dict) else {}
        checkpoint = console.get("notebook_checkpoint", {}) if isinstance(console.get("notebook_checkpoint"), dict) else {}
        tutor = console.get("tutor_state", {}) if isinstance(console.get("tutor_state"), dict) else {}
        ledger = console.get("help_ledger_preview", {}) if isinstance(console.get("help_ledger_preview"), dict) else {}
        export = console.get("export_receipt", {}) if isinstance(console.get("export_receipt"), dict) else {}
        confirmations = console.get("operator_confirmations", {}) if isinstance(console.get("operator_confirmations"), dict) else {}
        entry = {
            "entry_type": "session_console_report",
            "receipt_id": receipt.get("receipt_id", ""),
            "receipt_hash": receipt.get("receipt_hash", ""),
            "repeat_run_index": receipt.get("repeat_run_index", console.get("repeat_dry_run", {}).get("repeat_run_index", 1)),
            "skill_tag": receipt.get("selected_skill_tag", selected.get("skill_tag", "")),
            "checkpoint_hash": receipt.get("notebook_work_sha256", checkpoint.get("notebook_work_sha256", "")),
            "help_level": tutor.get("effective_help_level", "A2"),
            "tutor_status": tutor.get("tutor_status", "unknown"),
            "study_receipt_status": tutor.get("study_receipt_status", "unknown"),
            "reflection_status": reflection_status(tutor.get("study_receipt_status", "")),
            "help_ledger_preview": {
                "status": ledger.get("status", "unknown"),
                "help_level": ledger.get("help_level", tutor.get("effective_help_level", "A2")),
                "event_hash": ledger.get("event_hash", ""),
                "general_help_ledger_written": bool(ledger.get("general_help_ledger_written", False)),
                "exam_ledger_written": bool(ledger.get("exam_ledger_written", False)),
                "raw_help_text_returned": False,
            },
            "local_cycle_operator_workspace_card": safe_workspace_card_view(
                console.get("local_cycle_operator_workspace_card", {})
            ),
            "blockers": blockers_from_console(report, console),
            "operator_confirmations": {
                "status": confirmations.get("status", "unknown"),
                "confirmed_count": confirmations.get("confirmed_count", 0),
                "write_step_count": confirmations.get("write_step_count", 0),
                "open_steps": list(confirmations.get("open_steps", []) or [])[:8],
                "local_writes_requested": bool(confirmations.get("local_writes_requested", False)),
            },
            "export_receipt": {
                "status": export.get("status", "unknown"),
                "package_id": export.get("package_id", ""),
                "not_cleared_receipt": bool(export.get("not_cleared_receipt", True)),
                "human_reviewable_independence_evidence": bool(export.get("human_reviewable_independence_evidence", False)),
                "raw_export_returned": False,
            },
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        }
        entries.append(entry)

    for receipt in receipts:
        entries.append(
            {
                "entry_type": "session_console_receipt",
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", receipt.get("receipt_id", "")),
                "repeat_run_index": receipt.get("repeat_run_index", 1),
                "skill_tag": receipt.get("selected_skill_tag", ""),
                "checkpoint_hash": receipt.get("notebook_work_sha256", ""),
                "help_level": "",
                "tutor_status": "not_in_receipt",
                "study_receipt_status": "not_in_receipt",
                "reflection_status": "hash_only_receipt_no_reflection_detail",
                "help_ledger_preview": {"status": "not_in_receipt", "raw_help_text_returned": False},
                "blockers": [],
                "operator_confirmations": {"status": "not_in_receipt", "open_steps": []},
                "export_receipt": {"status": "not_in_receipt", "not_cleared_receipt": True, "raw_export_returned": False},
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    entries.sort(key=lambda item: (int(item.get("repeat_run_index", 1) or 1), str(item.get("receipt_id", ""))))
    return entries[:24]


def blockers_from_console(report: dict[str, Any], console: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    status = str(report.get("status", ""))
    if "repeat_task_required" in status:
        blockers.append("repeat_task_required")
    if "waiting_for_required_evidence" in status:
        blockers.append("required_evidence_missing")
    confirmations = console.get("operator_confirmations", {}) if isinstance(console.get("operator_confirmations"), dict) else {}
    open_steps = [str(item) for item in confirmations.get("open_steps", []) or []]
    if open_steps:
        blockers.append("operator_confirmations_open")
    return blockers[:8]


def reflection_status(study_receipt_status: str) -> str:
    if str(study_receipt_status) == "ok_study_session_receipt":
        return "reflection_evidence_present"
    if study_receipt_status:
        return f"reflection_review_needed:{study_receipt_status}"
    return "reflection_status_unknown"


def history_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    skill_tags = sorted({str(item.get("skill_tag", "")) for item in entries if item.get("skill_tag")})
    checkpoint_hashes = [str(item.get("checkpoint_hash", "")) for item in entries if item.get("checkpoint_hash")]
    help_levels: dict[str, int] = {}
    blockers: dict[str, int] = {}
    workspace_cards: dict[str, int] = {}
    confirmed = 0
    open_steps = 0
    for item in entries:
        help_level = str(item.get("help_level", ""))
        if help_level:
            help_levels[help_level] = help_levels.get(help_level, 0) + 1
        confirmations = item.get("operator_confirmations", {}) if isinstance(item.get("operator_confirmations"), dict) else {}
        confirmed += int(confirmations.get("confirmed_count", 0) or 0)
        open_steps += len(confirmations.get("open_steps", []) or [])
        workspace_card = item.get("local_cycle_operator_workspace_card", {}) if isinstance(item.get("local_cycle_operator_workspace_card"), dict) else {}
        workspace_status = str(workspace_card.get("status", ""))
        if workspace_status:
            workspace_cards[workspace_status] = workspace_cards.get(workspace_status, 0) + 1
        for blocker in item.get("blockers", []) or []:
            blockers[str(blocker)] = blockers.get(str(blocker), 0) + 1
    return {
        "run_count": len(entries),
        "skill_tags": skill_tags,
        "checkpoint_hash_count": len(checkpoint_hashes),
        "checkpoint_hashes": checkpoint_hashes[:12],
        "help_level_profile": help_levels,
        "blocker_profile": blockers,
        "workspace_card_profile": workspace_cards,
        "confirmed_operator_step_count": confirmed,
        "open_operator_step_count": open_steps,
        "raw_history_returned": False,
    }


def export_review_package(entries: list[dict[str, Any]]) -> dict[str, Any]:
    summary = history_summary(entries)
    return {
        "status": "export_review_ready" if entries else "export_review_waiting_for_session_history",
        "exam_deployment_status": "not_cleared",
        "review_items": {
            "skills": summary["skill_tags"],
            "checkpoint_hashes": summary["checkpoint_hashes"],
            "help_level_profile": summary["help_level_profile"],
            "blocker_profile": summary["blocker_profile"],
            "operator_confirmation_profile": {
                "confirmed_step_count": summary["confirmed_operator_step_count"],
                "open_step_count": summary["open_operator_step_count"],
            },
            "workspace_card_profile": summary["workspace_card_profile"],
            "reflection_statuses": sorted({str(item.get("reflection_status", "")) for item in entries if item.get("reflection_status")}),
            "export_receipts": [
                {
                    "status": item.get("export_receipt", {}).get("status", "unknown")
                    if isinstance(item.get("export_receipt"), dict)
                    else "unknown",
                    "package_id": item.get("export_receipt", {}).get("package_id", "")
                    if isinstance(item.get("export_receipt"), dict)
                    else "",
                    "not_cleared_receipt": item.get("export_receipt", {}).get("not_cleared_receipt", True)
                    if isinstance(item.get("export_receipt"), dict)
                    else True,
                }
                for item in entries[:12]
            ],
        },
        "human_reviewable_independence_evidence": bool(entries),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
    }


def export_review_receipt(course_id: str, package: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    seed = {
        "course_id": course_id,
        "package": package,
        "entry_hashes": [item.get("receipt_hash", item.get("receipt_id", "")) for item in entries],
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "export_review_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "run_count": len(entries),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def history_status(entries: list[dict[str, Any]]) -> str:
    return "exam_workspace_run_history_export_review_ready" if entries else "exam_workspace_run_history_waiting_for_session_history"


def history_next_actions(entries: list[dict[str, Any]]) -> list[str]:
    if not entries:
        return ["Run the Session Console for a selected skill, then rebuild the export review."]
    return [
        "Review checkpoint hashes, help-level profile, blockers, confirmations, export receipt, and reflection status.",
        "Repeat dry-runs as needed; keep exam_deployment_status not_cleared until real-world clearance is handled outside UniBot.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-workspace-run-history-export-review")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


def safe_workspace_card_view(workspace_card: dict[str, Any]) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    review = workspace_card.get("readiness_review", {}) if isinstance(workspace_card.get("readiness_review"), dict) else {}
    handoff = workspace_card.get("readiness_handoff", {}) if isinstance(workspace_card.get("readiness_handoff"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(summary.get("recommendation_reason", review.get("recommendation_reason", "missing_start_packet"))),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
    }
