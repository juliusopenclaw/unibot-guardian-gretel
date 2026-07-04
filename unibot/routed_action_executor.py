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
ROUTED_ACTION_EXECUTOR_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-routed-action-executor-workspace-card-execution-alignment-v1"
)
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
    report["workspace_card_execution_alignment"] = build_routed_action_executor_workspace_card_alignment(report)
    attach_public_scan(report, public_safe=public_safe)
    return report


def routed_action_executor_hash(executor_report: dict[str, Any] | None = None) -> str:
    report = executor_report if isinstance(executor_report, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": report.get("schema_version", ""),
                "artifact_type": report.get("artifact_type", ""),
                "status": report.get("status", ""),
                "course_id": report.get("course_id", ""),
                "exam_deployment_status": report.get("exam_deployment_status", ""),
                "selected_skill": report.get("selected_skill", {}),
                "selected_route": report.get("selected_route", {}),
                "executed_endpoint": report.get("executed_endpoint", ""),
                "execution_result_summary": report.get("execution_result_summary", {}),
                "operator_confirmation_summary": report.get("operator_confirmation_summary", {}),
                "public_safety_status": report.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def routed_action_executor_receipt_hash(executor_report: dict[str, Any] | None = None) -> str:
    report = executor_report if isinstance(executor_report, dict) else {}
    receipt = report.get("executor_receipt", {}) if isinstance(report.get("executor_receipt"), dict) else {}
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "receipt_hash": receipt.get("receipt_hash", ""),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "execution_result_hash": report.get("execution_result_summary", {}).get("result_hash", "")
                if isinstance(report.get("execution_result_summary"), dict)
                else "",
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_routed_action_executor_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic routed action executor workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic routed action executor prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_routed_action_executor_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_execution_before_local_write_or_public_claim",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__ROUTED_ACTION_EXECUTOR_RECEIPT_HASH__",
            "checkpoint_hash": "__ROUTED_ACTION_EXECUTOR_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_routed_action_executor_workspace_card(
    workspace_card: dict[str, Any],
    *,
    executor_hash: str = "",
    receipt_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if executor_hash and checkpoint_hash == "__ROUTED_ACTION_EXECUTOR_HASH__":
        checkpoint_hash = executor_hash
    if receipt_hash and task_hash == "__ROUTED_ACTION_EXECUTOR_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_routed_action_executor_gate")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def build_routed_action_executor_workspace_card_alignment(
    routed_action_executor: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = routed_action_executor if isinstance(routed_action_executor, dict) else {}
    route = report.get("selected_route", {}) if isinstance(report.get("selected_route"), dict) else {}
    result = (
        report.get("execution_result_summary", {})
        if isinstance(report.get("execution_result_summary"), dict)
        else {}
    )
    receipt = report.get("executor_receipt", {}) if isinstance(report.get("executor_receipt"), dict) else {}
    confirmations = (
        report.get("operator_confirmation_summary", {})
        if isinstance(report.get("operator_confirmation_summary"), dict)
        else {}
    )
    executor_hash = routed_action_executor_hash(report)
    receipt_hash = routed_action_executor_receipt_hash(report)
    workspace_card = safe_routed_action_executor_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_routed_action_executor_workspace_card(),
        executor_hash=executor_hash,
        receipt_hash=receipt_hash,
    )
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    raw_flag_names = [
        "raw_query_returned",
        "raw_text_returned",
        "raw_cell_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
    ]
    high_stakes_flag_names = [
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]
    contracts = {
        "executor_public_safe": report.get("public_safety_status") == "pass",
        "executor_ready": report.get("status") == "routed_action_executor_ready",
        "selected_route_present": bool(route.get("route_id"))
        and bool(route.get("endpoint"))
        and route.get("exam_deployment_status") == "not_cleared",
        "execution_result_ready": bool(result.get("artifact_type"))
        and bool(result.get("status"))
        and bool(result.get("result_hash"))
        and result.get("exam_deployment_status") == "not_cleared",
        "receipt_ready_not_clearance": receipt.get("status") == "executor_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and bool(receipt.get("receipt_hash"))
        and receipt.get("not_cleared_receipt") is True,
        "local_write_boundary_preserved": result.get("local_write_started") is False
        and confirmations.get("dry_run_by_default") is True
        and confirmations.get("local_write_confirmations_are_explicit") is True,
        "no_clearance_or_deployment_claim": report.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(report.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names)
        and all(result.get(flag, False) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(report.get(flag) is False for flag in high_stakes_flag_names)
        and all(result.get(flag, False) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_routed_action_executor_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == executor_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "routed_action_executor",
        "exam_run_packet",
        "exam_packet_timeline",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": ROUTED_ACTION_EXECUTOR_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "routed_action_executor_hash": executor_hash,
        "routed_action_executor_receipt_hash": receipt_hash,
        "executor_status": report.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "route_id": route.get("route_id", "missing"),
        "executed_endpoint": report.get("executed_endpoint", ""),
        "executed_artifact_type": result.get("artifact_type", "missing"),
        "executed_status": result.get("status", "missing"),
        "executed_result_hash_present": bool(result.get("result_hash")),
        "local_write_started": bool(result.get("local_write_started", True)),
        "dry_run_by_default": bool(confirmations.get("dry_run_by_default", False)),
        "local_write_confirmations_are_explicit": bool(
            confirmations.get("local_write_confirmations_are_explicit", False)
        ),
        "exam_deployment_status": report.get("exam_deployment_status", "missing"),
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "human_review_required",
            "public_safety_required",
            "operator_confirmation_required_for_local_write",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "autonomous publication",
            "approval claim",
            "exam clearance claim",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
        "contracts": contracts,
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_operator_prefill_hash_present": workspace_card["task_hash"] != ""
        and workspace_card["checkpoint_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_routed_action_executor_gate_linked": contracts[
            "workspace_card_routed_action_executor_gate_linked"
        ],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Routed action executor claims are hash-only review aids for selected route, dry-run execution "
            "metadata, result/receipt hashes, and local-write boundaries; they do not authorize publication, "
            "provider calls, grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "routed-action-executor-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_routed_action_executor_inputs() -> dict[str, Any]:
    route = {
        "skill_tag": "python_lists",
        "route_id": "review_open_operator_confirmations",
        "action_label": "Review open operator confirmations",
        "endpoint": "/api/unibot/exam-workspace/run-history-export-review",
        "dry_run_by_default": True,
        "requested_help_level": "A2",
        "requires_operator_confirmation_for_local_writes": True,
        "open_operator_confirmation_count": 0,
        "exam_deployment_status": "not_cleared",
    }
    report = build_routed_action_executor(
        selected_skill_tag="python_lists",
        selected_route=route,
        public_safe=True,
    )
    return {"routed_action_executor": report}


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
