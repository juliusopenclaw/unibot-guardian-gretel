from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_exam_coverage_dashboard import build_course_exam_coverage_dashboard
from .course_per_skill_action_router import build_course_per_skill_action_router
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction_manifest_apply import build_private_manifest_apply_dry_run
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .exam_workspace_session_console import build_exam_workspace_session_console
from .material_coverage_run import build_course_material_coverage_run
from .materials import sha256_text
from .private_extraction_runner import run_private_extraction_batch
from .public_safety import scan_text
from .study_session import build_course_study_session_plan
from .tutor_index import build_private_tutor_index_dry_run
from .video_transcription_runner import run_video_transcription_batch


ROUTED_ACTION_EXECUTOR_SCHEMA_VERSION = "unibot-routed-action-executor-v1"
ROUTED_ACTION_EXECUTOR_ENDPOINT = "/api/unibot/course/routed-action-executor"


def build_routed_action_executor(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    selected_skill_tag: str = "",
    focus_query: str = "",
    router_report: dict[str, Any] | None = None,
    selected_route: dict[str, Any] | None = None,
    dashboard_report: dict[str, Any] | None = None,
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
    private_output_dir: str | Path | None = None,
    checkpoint_journal_path: str | Path | None = None,
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    run_history_report: dict[str, Any] | None = None,
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
    repeat_run_index: int = 1,
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    operator_confirmed_private_extraction_run: bool = False,
    operator_confirmed_video_transcription_run: bool = False,
    max_jobs: int = 0,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    safe_console_reports = [item for item in (console_reports or []) if isinstance(item, dict)]
    safe_console_receipts = [item for item in (console_receipts or []) if isinstance(item, dict)]
    router = router_report if isinstance(router_report, dict) else build_course_per_skill_action_router(
        course_id=safe_id,
        selected_skill_tag=selected_skill_tag,
        focus_query=focus_query or query,
        dashboard_report=dashboard_report,
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
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        run_history_report=run_history_report,
        build_current_console=False,
        public_safe=public_safe,
    )
    route = selected_route if isinstance(selected_route, dict) else router.get("selected_route", {})
    route_id = str(route.get("route_id", "waiting_for_skill_selection"))
    endpoint = str(route.get("endpoint", ""))
    skill_tag = str(route.get("skill_tag") or selected_skill_tag or router.get("selected_skill", {}).get("skill_tag", ""))
    execution = execute_selected_route(
        course_id=safe_id,
        route_id=route_id,
        endpoint=endpoint,
        skill_tag=skill_tag,
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
        private_output_dir=private_output_dir,
        checkpoint_journal_path=checkpoint_journal_path,
        console_reports=safe_console_reports,
        console_receipts=safe_console_receipts,
        query=query or focus_query or skill_tag,
        requested_help_level=safe_help_level(requested_help_level or route.get("requested_help_level", "A2")),
        exam_status=exam_status,
        student_reflection=student_reflection,
        study_receipt=study_receipt,
        notebook_checkpoint=notebook_checkpoint,
        cell_source=cell_source,
        cell_index=cell_index,
        cell_id=cell_id,
        cell_type=cell_type,
        repeat_run_index=repeat_run_index,
        operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
        operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
        operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
        operator_confirmed_private_extraction_run=operator_confirmed_private_extraction_run,
        operator_confirmed_video_transcription_run=operator_confirmed_video_transcription_run,
        max_jobs=max_jobs,
        public_safe=public_safe,
    )
    result_summary = summarize_execution_result(execution)
    receipt = executor_receipt(safe_id, route, result_summary)
    report = {
        "schema_version": ROUTED_ACTION_EXECUTOR_SCHEMA_VERSION,
        "artifact_type": "routed_action_executor",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": executor_status(route_id, execution),
        "executor_title": "Routed Action Executor",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Routed Action Executor. It executes the selected Per-Skill Action Router route as a controlled "
            "dry-run by default and returns only a public-safe summary plus receipt. Write-capable routes remain "
            "behind explicit operator confirmations. It never returns raw queries, course raw text, notebook code, "
            "local paths, values, solutions, final interpretations, proctoring, AI detection, automatic assessment, "
            "or exam clearance."
        ),
        "selected_skill": {
            "skill_tag": skill_tag,
            "exam_deployment_status": "not_cleared",
        },
        "selected_route": safe_route(route),
        "executed_endpoint": endpoint,
        "execution_result_summary": result_summary,
        "executor_receipt": receipt,
        "operator_confirmation_summary": operator_confirmation_summary(
            checkpoint=operator_confirmed_checkpoint_store,
            workspace=operator_confirmed_exam_workspace_run,
            manifest=operator_confirmed_manifest_apply,
            index=operator_confirmed_tutor_index_build,
            help_ledger=operator_confirmed_help_ledger_append,
            exam_ledger=operator_confirmed_exam_ledger_append,
            private_extraction=operator_confirmed_private_extraction_run,
            video_transcription=operator_confirmed_video_transcription_run,
        ),
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; der Executor bleibt dry-run-by-default und not_cleared."
        ),
        "next_actions": executor_next_actions(route_id, execution),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def execute_selected_route(
    *,
    course_id: str,
    route_id: str,
    endpoint: str,
    skill_tag: str,
    base_path: str | None,
    max_files: int,
    review_policy: str,
    decision_record: dict[str, Any] | None,
    decision_record_journal_path: str | Path | None,
    receipts: list[dict[str, Any]] | None,
    receipt_journal_path: str | Path | None,
    private_manifest_path: str | Path | None,
    manifest_apply_journal_path: str | Path | None,
    tutor_index_path: str | Path | None,
    tutor_index_journal_path: str | Path | None,
    ledger_path: str | Path | None,
    private_output_dir: str | Path | None,
    checkpoint_journal_path: str | Path | None,
    console_reports: list[dict[str, Any]],
    console_receipts: list[dict[str, Any]],
    query: str,
    requested_help_level: str,
    exam_status: str,
    student_reflection: str,
    study_receipt: dict[str, Any] | None,
    notebook_checkpoint: dict[str, Any] | None,
    cell_source: str,
    cell_index: int,
    cell_id: str,
    cell_type: str,
    repeat_run_index: int,
    operator_confirmed_checkpoint_store: bool,
    operator_confirmed_exam_workspace_run: bool,
    operator_confirmed_manifest_apply: bool,
    operator_confirmed_tutor_index_build: bool,
    operator_confirmed_help_ledger_append: bool,
    operator_confirmed_exam_ledger_append: bool,
    operator_confirmed_private_extraction_run: bool,
    operator_confirmed_video_transcription_run: bool,
    max_jobs: int,
    public_safe: bool,
) -> dict[str, Any]:
    if endpoint == "/api/unibot/exam-workspace/session-console":
        return build_exam_workspace_session_console(
            course_id=course_id,
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
            focus_query=skill_tag,
            query=query,
            selected_skill_tag=skill_tag,
            requested_help_level=requested_help_level,
            exam_status=exam_status,
            student_reflection=student_reflection,
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=cell_source,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            checkpoint_journal_path=checkpoint_journal_path,
            repeat_run_index=max(int(repeat_run_index or 1), next_repeat_index(console_receipts)),
            previous_console_receipts=console_receipts,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
            operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
            operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
            operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
            operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/exam-workspace/run-history-export-review":
        return build_exam_workspace_run_history_export_review(
            course_id=course_id,
            console_reports=console_reports,
            console_receipts=console_receipts,
            build_current_console=False,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/exam-coverage-dashboard":
        return build_course_exam_coverage_dashboard(
            course_id=course_id,
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
            focus_query=skill_tag,
            selected_skill_tag=skill_tag,
            console_reports=console_reports,
            console_receipts=console_receipts,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/material-coverage/run":
        return build_course_material_coverage_run(
            course_id,
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
            focus_query=skill_tag,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/extraction-manifest/apply-dry-run":
        return build_private_manifest_apply_dry_run(
            course_id,
            base_path=base_path,
            max_files=max_files,
            review_policy=review_policy,
            decision_record=decision_record,
            decision_record_journal_path=decision_record_journal_path,
            receipts=receipts,
            receipt_journal_path=receipt_journal_path,
            private_manifest_path=private_manifest_path,
            manifest_apply_journal_path=manifest_apply_journal_path,
            operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/tutor-index/dry-run":
        return build_private_tutor_index_dry_run(
            course_id,
            private_manifest_path=private_manifest_path,
            tutor_index_path=tutor_index_path,
            tutor_index_journal_path=tutor_index_journal_path,
            operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/study-session-plan":
        return build_course_study_session_plan(
            course_id,
            base_path=base_path,
            max_files=max_files,
            review_policy=review_policy,
            decision_record=decision_record,
            receipts=receipts,
            focus_query=skill_tag,
            max_items=1,
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/private-extraction/run-batch":
        if not operator_confirmed_private_extraction_run:
            return write_capable_route_waiting(
                artifact_type="course_private_extraction_run",
                route_id=route_id,
                endpoint=endpoint,
                required_confirmation="operator_confirmed_private_extraction_run",
            )
        return run_private_extraction_batch(
            course_id,
            base_path=base_path,
            max_files=max_files,
            review_policy=review_policy,
            decision_record=decision_record,
            decision_record_journal_path=decision_record_journal_path,
            receipt_journal_path=receipt_journal_path,
            private_output_dir=private_output_dir,
            max_jobs=max(0, int(max_jobs or 0)),
            job_types=["ocr"],
            public_safe=public_safe,
        )
    if endpoint == "/api/unibot/course/video-transcription/run-batch":
        if not operator_confirmed_video_transcription_run:
            return write_capable_route_waiting(
                artifact_type="course_video_transcription_run",
                route_id=route_id,
                endpoint=endpoint,
                required_confirmation="operator_confirmed_video_transcription_run",
            )
        return run_video_transcription_batch(
            course_id,
            base_path=base_path,
            max_files=max_files,
            review_policy=review_policy,
            decision_record=decision_record,
            receipt_journal_path=receipt_journal_path,
            private_output_dir=private_output_dir,
            max_jobs=max(0, int(max_jobs or 0)),
            public_safe=public_safe,
        )
    return {
        "artifact_type": "routed_action_execution_not_supported",
        "status": "unsupported_route",
        "route_id": route_id,
        "endpoint": endpoint,
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def write_capable_route_waiting(*, artifact_type: str, route_id: str, endpoint: str, required_confirmation: str) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "status": "dry_run_waiting_for_operator_confirmation",
        "route_id": route_id,
        "endpoint": endpoint,
        "required_confirmation": required_confirmation,
        "exam_deployment_status": "not_cleared",
        "dry_run_by_default": True,
        "local_write_started": False,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def summarize_execution_result(execution: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "artifact_type": execution.get("artifact_type", "unknown"),
        "status": execution.get("status", "unknown"),
        "exam_deployment_status": execution.get("exam_deployment_status", "not_cleared"),
        "public_safety_status": execution.get("public_safety_status", "unknown"),
        "receipt": safe_receipt_from_execution(execution),
        "counts": safe_counts_from_execution(execution),
        "local_write_started": bool(execution.get("local_write_started", False)),
        "raw_query_returned": bool(execution.get("raw_query_returned", False)),
        "raw_text_returned": bool(execution.get("raw_text_returned", False)),
        "raw_cell_returned": bool(execution.get("raw_cell_returned", False)),
        "raw_notebook_returned": bool(execution.get("raw_notebook_returned", False)),
        "notebook_code_returned": bool(execution.get("notebook_code_returned", False)),
        "local_paths_returned": bool(execution.get("local_paths_returned", False)),
        "automatic_grading_started": bool(execution.get("automatic_grading_started", False)),
        "proctoring_started": bool(execution.get("proctoring_started", False)),
        "ai_detection_started": bool(execution.get("ai_detection_started", False)),
        "exam_clearance_claimed": bool(execution.get("exam_clearance_claimed", False)),
    }
    summary["result_hash"] = sha256_text(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    return summary


def safe_receipt_from_execution(execution: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "session_console_receipt",
        "export_review_receipt",
        "coverage_receipt",
        "dry_run_receipt",
        "run_receipt",
        "receipt",
    ):
        receipt = execution.get(key)
        if isinstance(receipt, dict):
            return {
                "status": receipt.get("status", "unknown"),
                "receipt_id": receipt.get("receipt_id", receipt.get("package_id", "")),
                "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", True)),
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
    return {"status": "no_receipt_in_result", "not_cleared_receipt": True}


def safe_counts_from_execution(execution: dict[str, Any]) -> dict[str, Any]:
    counts = execution.get("counts") if isinstance(execution.get("counts"), dict) else {}
    if not counts and isinstance(execution.get("dashboard_summary"), dict):
        counts = execution.get("dashboard_summary", {})
    if not counts and isinstance(execution.get("history_summary"), dict):
        counts = execution.get("history_summary", {})
    allowed = {}
    for key, value in counts.items():
        if isinstance(value, (int, float, str, bool)) and "path" not in str(key).lower():
            allowed[str(key)] = value
    return allowed


def next_repeat_index(console_receipts: list[dict[str, Any]]) -> int:
    repeats = [int(item.get("repeat_run_index", 0) or 0) for item in console_receipts if isinstance(item, dict)]
    return max(repeats or [0]) + 1


def safe_help_level(level: str) -> str:
    prefix = str(level or "A2")[:2]
    return prefix if prefix in {"A0", "A1", "A2"} else "A2"


def safe_route(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": route.get("skill_tag", ""),
        "route_id": route.get("route_id", "unknown"),
        "action_label": route.get("action_label", ""),
        "endpoint": route.get("endpoint", ""),
        "dry_run_by_default": bool(route.get("dry_run_by_default", True)),
        "requested_help_level": safe_help_level(str(route.get("requested_help_level", "A2"))),
        "requires_operator_confirmation_for_local_writes": bool(
            route.get("requires_operator_confirmation_for_local_writes", True)
        ),
        "open_operator_confirmation_count": int(route.get("open_operator_confirmation_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def executor_receipt(course_id: str, route: dict[str, Any], result_summary: dict[str, Any]) -> dict[str, Any]:
    seed = {"course_id": course_id, "route": safe_route(route), "result": result_summary}
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "executor_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def operator_confirmation_summary(**flags: bool) -> dict[str, Any]:
    confirmed = {key: bool(value) for key, value in flags.items()}
    return {
        "confirmed_steps": [key for key, value in confirmed.items() if value],
        "confirmed_count": len([value for value in confirmed.values() if value]),
        "dry_run_by_default": True,
        "local_write_confirmations_are_explicit": True,
    }


def executor_status(route_id: str, execution: dict[str, Any]) -> str:
    if route_id == "waiting_for_skill_selection":
        return "routed_action_executor_waiting_for_skill"
    if execution.get("status") == "unsupported_route":
        return "routed_action_executor_unsupported_route"
    return "routed_action_executor_ready"


def executor_next_actions(route_id: str, execution: dict[str, Any]) -> list[str]:
    if execution.get("status") == "dry_run_waiting_for_operator_confirmation":
        return [f"Review the dry-run route, then set {execution.get('required_confirmation')} only if local writes are intended."]
    if route_id == "review_open_operator_confirmations":
        return ["Review Run-History output and confirm or leave local write steps dry-run."]
    if route_id in {"start_session_console_dry_run", "repeat_session_console_or_review_history"}:
        return ["Review the Session Console receipt, then refresh the Course Exam Coverage Dashboard."]
    return ["Review the routed dry-run summary and continue with the next safe router step."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "routed-action-executor")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
