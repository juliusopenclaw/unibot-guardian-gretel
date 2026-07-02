from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_notebook_checkpoint import build_exam_notebook_checkpoint_adapter_dry_run
from .exam_workspace_run import build_exam_workspace_run_dry_run
from .material_coverage_run import build_course_material_coverage_run
from .materials import sha256_text
from .public_safety import scan_text


EXAM_WORKSPACE_LAUNCH_FLOW_SCHEMA_VERSION = "unibot-exam-workspace-launch-flow-v1"
LAUNCH_ENDPOINT = "/api/unibot/exam-workspace/launch-flow/dry-run"
WORKSPACE_RUN_ENDPOINT = "/api/unibot/exam-workspace/run-dry-run"
ALLOWED_LAUNCH_HELP_LEVELS = {"A0", "A1", "A2"}


def build_exam_workspace_launch_flow_dry_run(
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
    ledger_path: str | Path | None = None,
    focus_query: str = "",
    query: str = "",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_source: str = "",
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    checkpoint_journal_path: str | Path | None = None,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    operator_confirmed_checkpoint_store: bool = False,
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
        focus_query=focus_query or query,
        public_safe=public_safe,
    )
    start_point = coverage.get("next_exam_workspace_start_point", {})
    if not isinstance(start_point, dict):
        start_point = {}
    skill_row = selected_skill_row(coverage, start_point)
    coverage_summary = launch_coverage_summary(coverage, start_point, skill_row)

    if start_point.get("status") != "ready":
        report = launch_waiting_report(
            safe_id=safe_id,
            coverage_summary=coverage_summary,
            start_point=start_point,
            coverage=coverage,
            public_safe=public_safe,
        )
        return report

    help_level, coerced_help_level = coerce_launch_help_level(
        requested_help_level,
        fallback=str(start_point.get("recommended_help_level", "A2")),
    )
    query_template = str(start_point.get("query_template", "")).strip() or (
        f"Welche Quelle und welche eigene Vorhersage pruefe ich zuerst fuer {start_point.get('title', 'diesen Skill')}?"
    )
    actual_query = str(query or "").strip() or query_template
    reflection = str(student_reflection or "").strip() or (
        "Ich pruefe zuerst meine eigene Vorhersage und halte den kleinsten Notebook-Checkpoint fest."
    )
    task_id = str(start_point.get("notebook_exercise_task_id", "") or "launch-notebook-checkpoint")
    skill_tag = str(start_point.get("skill_tag", ""))
    cell_id = f"launch-{sha256_text(f'{safe_id}:{skill_tag}:{task_id}')[:12]}"
    notebook = launch_notebook_shell(safe_id=safe_id, skill_tag=skill_tag, task_id=task_id)
    source_card_ids = safe_source_card_ids(skill_row)
    local_checkpoint = build_local_checkpoint_summary()
    checkpoint_hash_override = ""
    workspace_cell_source = ""
    workspace_cell_index = 1
    workspace_cell_id = cell_id
    workspace_cell_type = "code"
    if cell_source or notebook_checkpoint:
        checkpoint_adapter = build_exam_notebook_checkpoint_adapter_dry_run(
            course_id=safe_id,
            task_id=task_id,
            skill_tag=skill_tag,
            source_card_ids=source_card_ids,
            cell_source=cell_source,
            notebook_checkpoint=notebook_checkpoint,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            requested_help_level=help_level,
            prediction_present=bool((study_receipt or {}).get("prediction_present") or query or focus_query),
            retrieval_response_present=True,
            notebook_action_present=True,
            reflection_present=bool((study_receipt or {}).get("reflection_present") or student_reflection),
            student_reflection=student_reflection,
            checkpoint_journal_path=checkpoint_journal_path,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            public_safe=public_safe,
        )
        local_checkpoint = launch_checkpoint_summary(checkpoint_adapter)
        checkpoint_status = str(checkpoint_adapter.get("status", "unknown"))
        if checkpoint_status != "notebook_checkpoint_ready":
            return launch_checkpoint_not_ready_report(
                safe_id=safe_id,
                coverage_summary=coverage_summary,
                start_point=start_point,
                local_checkpoint=local_checkpoint,
                checkpoint_adapter=checkpoint_adapter,
                public_safe=public_safe,
            )
        checkpoint_hash_override = str(
            checkpoint_adapter.get("notebook_checkpoint", {}).get("notebook_work_sha256", "")
        )
        workspace_cell_source = str(cell_source or "")
        workspace_cell_index = int(checkpoint_adapter.get("notebook_checkpoint", {}).get("cell_index", 0) or 0)
        workspace_cell_id = str(checkpoint_adapter.get("notebook_checkpoint", {}).get("checkpoint_id", cell_id))
        workspace_cell_type = str(checkpoint_adapter.get("notebook_checkpoint", {}).get("cell_type", cell_type or "code"))
    launch_study_receipt = launch_study_receipt_payload(
        study_receipt,
        task_id=task_id,
        skill_tag=skill_tag,
        source_card_ids=source_card_ids,
    )

    workspace_run = build_exam_workspace_run_dry_run(
        actual_query,
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
        requested_help_level=help_level,
        exam_status=exam_status,
        notebook=notebook,
        notebook_filename="unibot_exam_workspace_launch.ipynb",
        cell_index=workspace_cell_index,
        cell_id=workspace_cell_id,
        cell_type=workspace_cell_type,
        cell_source=workspace_cell_source,
        notebook_work_sha256_override=checkpoint_hash_override,
        material_files=[],
        student_reflection=reflection,
        study_receipt=launch_study_receipt,
        operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
        operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
        public_safe=public_safe,
    )

    checkpoint = workspace_run.get("notebook_checkpoint", {}) if isinstance(workspace_run.get("notebook_checkpoint"), dict) else {}
    report = {
        "schema_version": EXAM_WORKSPACE_LAUNCH_FLOW_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_launch_flow_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": launch_status(workspace_run),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Material-coverage to exam-workspace launch flow. It selects the next reviewed skill, prepares an "
            "A2 query template, creates a hash-only notebook cell checkpoint, previews Help-Ledger evidence, "
            "and returns an export receipt. Standard is dry-run; local writes require operator confirmations. "
            "It never returns raw course text, raw queries, notebook code, local paths, complete solutions, "
            "inserted values, final interpretation, grading, proctoring, AI detection, or exam clearance."
        ),
        "coverage_summary": coverage_summary,
        "launch_configuration": {
            "launch_endpoint": LAUNCH_ENDPOINT,
            "workspace_endpoint_used": WORKSPACE_RUN_ENDPOINT,
            "skill_tag": start_point.get("skill_tag", ""),
            "title": start_point.get("title", ""),
            "help_level": help_level,
            "requested_help_level_coerced": coerced_help_level,
            "query_template": query_template,
            "query_template_hash": sha256_text(query_template),
            "actual_query_hash": sha256_text(actual_query),
            "actual_query_returned": False,
            "source_anchor_hint": {
                "source_anchor_count": start_point.get("source_anchor_count", 0),
                "source_card_ids": source_card_ids,
                "source_anchor_ids_returned": False,
            },
            "notebook_cell_checkpoint": {
                "cell_task_id": checkpoint.get("cell_task_id", ""),
                "cell_id_hash": checkpoint.get("cell_id_hash", sha256_text(cell_id)),
                "cell_index": checkpoint.get("cell_index", 1),
                "cell_type": checkpoint.get("cell_type", "code"),
                "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
                "raw_notebook_returned": False,
                "notebook_code_returned": False,
                "local_path_returned": False,
            },
            "local_notebook_checkpoint": local_checkpoint,
            "operator_confirmations": workspace_run.get("operator_confirmations", {}),
            "requires_operator_confirmation_for_writes": True,
        },
        "local_notebook_checkpoint": local_checkpoint,
        "exam_workspace_run_summary": workspace_run_summary(workspace_run),
        "help_ledger_preview": help_ledger_preview(workspace_run),
        "export_receipt": workspace_run.get("export_package_summary", {}),
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
            "Real exam authority clearance stays outside UniBot. UniBot reminds the operator and remains not_cleared."
        ),
        "next_actions": launch_next_actions(workspace_run),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def selected_skill_row(coverage: dict[str, Any], start_point: dict[str, Any]) -> dict[str, Any]:
    skill_tag = str(start_point.get("skill_tag", ""))
    for row in coverage.get("skill_coverage", []) or []:
        if isinstance(row, dict) and row.get("skill_tag") == skill_tag:
            return row
    return {}


def launch_coverage_summary(
    coverage: dict[str, Any],
    start_point: dict[str, Any],
    skill_row: dict[str, Any],
) -> dict[str, Any]:
    summary = coverage.get("coverage_summary", {}) if isinstance(coverage.get("coverage_summary"), dict) else {}
    return {
        "status": coverage.get("status", "unknown"),
        "material_status": coverage.get("material_summary", {}).get("intake_status", "unknown")
        if isinstance(coverage.get("material_summary"), dict)
        else "unknown",
        "ready_skill_count": summary.get("exam_workspace_ready_skill_count", 0),
        "skill_count": summary.get("skill_count", 0),
        "ocr_gap_count": summary.get("ocr_gap_count", 0),
        "video_gap_count": summary.get("video_gap_count", 0),
        "start_point": {
            "status": start_point.get("status", "unknown"),
            "skill_tag": start_point.get("skill_tag", ""),
            "title": start_point.get("title", ""),
            "recommended_help_level": start_point.get("recommended_help_level", "A2"),
            "source_anchor_count": start_point.get("source_anchor_count", skill_row.get("source_anchor_count", 0)),
            "notebook_exercise_task_id": start_point.get("notebook_exercise_task_id", ""),
            "recommended_endpoint": LAUNCH_ENDPOINT if start_point.get("status") == "ready" else "",
            "workspace_endpoint": start_point.get("recommended_endpoint", WORKSPACE_RUN_ENDPOINT),
            "exam_deployment_status": "not_cleared",
        },
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def launch_waiting_report(
    *,
    safe_id: str,
    coverage_summary: dict[str, Any],
    start_point: dict[str, Any],
    coverage: dict[str, Any],
    public_safe: bool,
) -> dict[str, Any]:
    report = {
        "schema_version": EXAM_WORKSPACE_LAUNCH_FLOW_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_launch_flow_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "exam_workspace_launch_waiting_for_material_coverage",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Coverage-selected exam-workspace launch dry-run. It does not open a workspace until a reviewed "
            "skill has private tutor anchors and a notebook checkpoint. It returns only metadata and safe next steps."
        ),
        "coverage_summary": coverage_summary,
        "launch_configuration": {
            "launch_endpoint": LAUNCH_ENDPOINT,
            "workspace_endpoint_used": "",
            "skill_tag": start_point.get("skill_tag", ""),
            "help_level": "A2",
            "query_template": "",
            "query_template_hash": "",
            "actual_query_hash": "",
            "actual_query_returned": False,
            "source_anchor_hint": {
                "source_anchor_count": 0,
                "source_card_ids": [],
                "source_anchor_ids_returned": False,
            },
            "notebook_cell_checkpoint": {
                "status": "not_started_waiting_for_coverage",
                "raw_notebook_returned": False,
                "notebook_code_returned": False,
                "local_path_returned": False,
            },
            "operator_confirmations": {
                "exam_workspace_run": False,
                "manifest_apply": False,
                "tutor_index_build": False,
                "help_ledger_append": False,
                "exam_ledger_append": False,
            },
            "requires_operator_confirmation_for_writes": True,
        },
        "exam_workspace_run_summary": {"status": "not_started_waiting_for_material_coverage"},
        "help_ledger_preview": {
            "status": "not_started_waiting_for_material_coverage",
            "ledger_written": False,
            "raw_query_returned": False,
            "raw_response_returned": False,
            "local_path_returned": False,
        },
        "export_receipt": {
            "status": "not_started_waiting_for_material_coverage",
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
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
            "Real exam authority clearance stays outside UniBot. UniBot reminds the operator and remains not_cleared."
        ),
        "next_actions": list(coverage.get("next_actions", []) or [])[:5]
        + ["Rerun the launch flow after material coverage reports a ready exam-workspace start point."],
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def launch_checkpoint_not_ready_report(
    *,
    safe_id: str,
    coverage_summary: dict[str, Any],
    start_point: dict[str, Any],
    local_checkpoint: dict[str, Any],
    checkpoint_adapter: dict[str, Any],
    public_safe: bool,
) -> dict[str, Any]:
    adapter_status = str(checkpoint_adapter.get("status", "unknown"))
    report = {
        "schema_version": EXAM_WORKSPACE_LAUNCH_FLOW_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_launch_flow_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": f"exam_workspace_launch_{adapter_status}",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Coverage-selected exam-workspace launch stopped at the local notebook checkpoint adapter. "
            "The report keeps only hashes, validation state, and safe next steps."
        ),
        "coverage_summary": coverage_summary,
        "launch_configuration": {
            "launch_endpoint": LAUNCH_ENDPOINT,
            "workspace_endpoint_used": "",
            "skill_tag": start_point.get("skill_tag", ""),
            "help_level": "A2",
            "actual_query_returned": False,
            "source_anchor_hint": {
                "source_anchor_count": start_point.get("source_anchor_count", 0),
                "source_card_ids": local_checkpoint.get("source_card_ids", []),
                "source_anchor_ids_returned": False,
            },
            "notebook_cell_checkpoint": local_checkpoint.get("notebook_checkpoint", {}),
            "local_notebook_checkpoint": local_checkpoint,
            "requires_operator_confirmation_for_writes": True,
        },
        "local_notebook_checkpoint": local_checkpoint,
        "exam_workspace_run_summary": {"status": "not_started_checkpoint_not_ready"},
        "help_ledger_preview": checkpoint_adapter.get("help_ledger_preview", {}),
        "export_receipt": {
            "status": "not_started_checkpoint_not_ready",
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
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
            "Real exam authority clearance stays outside UniBot. UniBot reminds the operator and remains not_cleared."
        ),
        "next_actions": list(checkpoint_adapter.get("next_actions", []) or [])[:5],
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def coerce_launch_help_level(requested: str, *, fallback: str) -> tuple[str, bool]:
    candidate = str(requested or fallback or "A2").strip().upper()
    if candidate in ALLOWED_LAUNCH_HELP_LEVELS:
        return candidate, False
    fallback_candidate = str(fallback or "A2").strip().upper()
    if fallback_candidate in ALLOWED_LAUNCH_HELP_LEVELS:
        return fallback_candidate, True
    return "A2", True


def launch_notebook_shell(*, safe_id: str, skill_tag: str, task_id: str) -> dict[str, Any]:
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"unibot": {"role": "launch-note"}},
                "source": ["# UniBot Exam Workspace Launch\n", "A0-A2 checkpoint shell.\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"unibot": {"role": "own-checkpoint", "skill_tag_hash": sha256_text(skill_tag)[:16]}},
                "outputs": [],
                "source": [],
            },
        ],
        "metadata": {
            "unibot": {
                "course_id_hash": sha256_text(safe_id)[:16],
                "task_id_hash": sha256_text(task_id)[:16],
                "exam_workspace_launch": True,
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def safe_source_card_ids(skill_row: dict[str, Any]) -> list[str]:
    source_card_ids = skill_row.get("source_card_ids", []) if isinstance(skill_row, dict) else []
    if not isinstance(source_card_ids, list):
        return []
    return [str(item) for item in source_card_ids[:8]]


def build_local_checkpoint_summary() -> dict[str, Any]:
    return {
        "status": "not_provided_using_launch_shell",
        "checkpoint_id": "",
        "notebook_work_sha256": "",
        "study_receipt_status": "not_provided",
        "help_ledger_preview_status": "not_provided",
        "checkpoint_journal_written": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_path_returned": False,
    }


def launch_checkpoint_summary(adapter: dict[str, Any]) -> dict[str, Any]:
    checkpoint = adapter.get("notebook_checkpoint", {}) if isinstance(adapter.get("notebook_checkpoint"), dict) else {}
    receipt = adapter.get("study_receipt_summary", {}) if isinstance(adapter.get("study_receipt_summary"), dict) else {}
    ledger = adapter.get("help_ledger_preview", {}) if isinstance(adapter.get("help_ledger_preview"), dict) else {}
    journal = adapter.get("checkpoint_journal_summary", {}) if isinstance(adapter.get("checkpoint_journal_summary"), dict) else {}
    return {
        "status": adapter.get("status", "unknown"),
        "checkpoint_id": checkpoint.get("checkpoint_id", ""),
        "task_id": checkpoint.get("task_id", ""),
        "skill_tag": checkpoint.get("skill_tag", ""),
        "cell_index": checkpoint.get("cell_index", 0),
        "cell_type": checkpoint.get("cell_type", "code"),
        "cell_source_sha256": checkpoint.get("cell_source_sha256", ""),
        "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
        "study_receipt_status": receipt.get("status", "unknown"),
        "help_ledger_preview_status": ledger.get("status", "unknown"),
        "checkpoint_journal_written": bool(journal.get("checkpoint_journal_written", False)),
        "source_card_ids": list(ledger.get("source_card_ids", []) or [])[:8],
        "solution_marker_detected": bool(adapter.get("solution_marker_detected", False)),
        "raw_cell_privacy_flags": list(adapter.get("raw_cell_privacy_flags", []) or []),
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_path_returned": False,
    }


def launch_study_receipt_payload(
    study_receipt: dict[str, Any] | None,
    *,
    task_id: str,
    skill_tag: str,
    source_card_ids: list[str],
) -> dict[str, Any]:
    base = {
        "task_id": task_id,
        "skill_tag": skill_tag,
        "source_card_ids": source_card_ids,
        "prediction_present": True,
        "notebook_action_present": True,
        "reflection_present": True,
        "help_level": "A2",
    }
    if study_receipt:
        base.update(
            {
                key: value
                for key, value in study_receipt.items()
                if key not in {"solution", "final_answer", "raw_private_text", "raw_course_text", "local_path"}
            }
        )
    return base


def workspace_run_summary(workspace_run: dict[str, Any]) -> dict[str, Any]:
    session = workspace_run.get("session_summary", {}) if isinstance(workspace_run.get("session_summary"), dict) else {}
    materials = (
        workspace_run.get("material_freeze_summary", {})
        if isinstance(workspace_run.get("material_freeze_summary"), dict)
        else {}
    )
    notebook = workspace_run.get("notebook_checkpoint", {}) if isinstance(workspace_run.get("notebook_checkpoint"), dict) else {}
    tutor = workspace_run.get("tutor_sidecar", {}) if isinstance(workspace_run.get("tutor_sidecar"), dict) else {}
    receipt = (
        workspace_run.get("private_tutor_use_flow_summary", {}).get("study_receipt_validation", {})
        if isinstance(workspace_run.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    ledger = (
        workspace_run.get("exam_ledger_append_summary", {})
        if isinstance(workspace_run.get("exam_ledger_append_summary"), dict)
        else {}
    )
    effective_status = effective_workspace_status(workspace_run)
    return {
        "status": effective_status,
        "raw_workspace_status": workspace_run.get("status", "unknown"),
        "session_status": session.get("status", "unknown"),
        "material_freeze_status": materials.get("status", "unknown"),
        "notebook_run_status": notebook.get("run_status", "unknown"),
        "notebook_cell_task_id": notebook.get("cell_task_id", ""),
        "tutor_status": tutor.get("status", "unknown"),
        "effective_help_level": tutor.get("effective_help_level", "A2"),
        "source_anchor_count": tutor.get("source_anchor_count", 0),
        "study_receipt_status": receipt.get("status", "unknown"),
        "exam_ledger_status": ledger.get("status", "unknown"),
        "exam_ledger_written": bool(ledger.get("ledger_written", False)),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def help_ledger_preview(workspace_run: dict[str, Any]) -> dict[str, Any]:
    tutor_flow = (
        workspace_run.get("private_tutor_use_flow_summary", {})
        if isinstance(workspace_run.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    general_ledger = tutor_flow.get("ledger_append", {}) if isinstance(tutor_flow.get("ledger_append"), dict) else {}
    exam_ledger = (
        workspace_run.get("exam_ledger_append_summary", {})
        if isinstance(workspace_run.get("exam_ledger_append_summary"), dict)
        else {}
    )
    sidecar = workspace_run.get("tutor_sidecar", {}) if isinstance(workspace_run.get("tutor_sidecar"), dict) else {}
    return {
        "status": "preview_ready" if workspace_run.get("status") else "unknown",
        "general_help_ledger_status": general_ledger.get("status", "unknown"),
        "general_help_ledger_written": bool(general_ledger.get("ledger_written", False)),
        "exam_ledger_status": exam_ledger.get("status", "unknown"),
        "exam_ledger_written": bool(exam_ledger.get("ledger_written", False)),
        "event_hash": exam_ledger.get("event_hash", general_ledger.get("event_hash", "")),
        "help_level": exam_ledger.get("help_level", sidecar.get("effective_help_level", "A2")),
        "source_anchor_count": sidecar.get("source_anchor_count", 0),
        "source_card_ids": list(sidecar.get("source_card_ids", []) or [])[:8],
        "raw_query_returned": False,
        "raw_response_returned": False,
        "local_path_returned": False,
        "eigenleistung_percentage_claimed": False,
    }


def launch_status(workspace_run: dict[str, Any]) -> str:
    status = effective_workspace_status(workspace_run)
    if status == "blocked_public_safety":
        return "blocked_public_safety"
    if str(status).startswith("exam_workspace_tutor_"):
        return f"exam_workspace_launch_{status}"
    if status == "exam_workspace_waiting_for_tutor_flow":
        return "exam_workspace_launch_waiting_for_tutor_flow"
    if status == "exam_workspace_study_receipt_needs_evidence":
        return "exam_workspace_launch_needs_study_receipt_evidence"
    if status == "exam_workspace_ready_with_exam_ledger":
        return "exam_workspace_launch_ready_with_exam_ledger"
    if status == "exam_workspace_dry_run_ready":
        return "exam_workspace_launch_dry_run_ready"
    return "exam_workspace_launch_review_required"


def launch_next_actions(workspace_run: dict[str, Any]) -> list[str]:
    if effective_workspace_status(workspace_run) in {"exam_workspace_dry_run_ready", "exam_workspace_ready_with_exam_ledger"}:
        return [
            "Review the A2 launch template, notebook checkpoint, Help-Ledger preview, and export receipt.",
            "Keep the default dry-run posture; set operator confirmations only for local writes after review.",
            "Real exam authority clearance remains a real-world reminder and UniBot stays not_cleared.",
        ]
    return list(workspace_run.get("next_actions", []) or [])[:5]


def effective_workspace_status(workspace_run: dict[str, Any]) -> str:
    raw_status = str(workspace_run.get("status", "unknown"))
    if raw_status == "blocked_public_safety":
        return raw_status
    tutor = workspace_run.get("tutor_sidecar", {}) if isinstance(workspace_run.get("tutor_sidecar"), dict) else {}
    tutor_flow = (
        workspace_run.get("private_tutor_use_flow_summary", {})
        if isinstance(workspace_run.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    receipt = tutor_flow.get("study_receipt_validation", {}) if isinstance(tutor_flow.get("study_receipt_validation"), dict) else {}
    ledger = (
        workspace_run.get("exam_ledger_append_summary", {})
        if isinstance(workspace_run.get("exam_ledger_append_summary"), dict)
        else {}
    )
    if tutor.get("status") == "allowed" and receipt.get("status") == "ok_study_session_receipt":
        if ledger.get("ledger_written"):
            return "exam_workspace_ready_with_exam_ledger"
        return "exam_workspace_dry_run_ready"
    return raw_status


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-workspace-launch-flow")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
