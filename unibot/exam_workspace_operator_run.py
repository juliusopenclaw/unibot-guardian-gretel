from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_launch_flow import build_exam_workspace_launch_flow_dry_run
from .materials import sha256_text
from .public_safety import scan_text


EXAM_WORKSPACE_OPERATOR_RUN_SCHEMA_VERSION = "unibot-exam-workspace-operator-run-v1"
OPERATOR_RUN_ENDPOINT = "/api/unibot/exam-workspace/operator-run"


def build_exam_workspace_operator_run_dry_run(
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
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    launch = build_exam_workspace_launch_flow_dry_run(
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
        operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
        operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
        operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
        public_safe=public_safe,
    )
    confirmations = operator_confirmation_matrix(
        launch,
        checkpoint_store=operator_confirmed_checkpoint_store,
        exam_workspace_run=operator_confirmed_exam_workspace_run,
        manifest_apply=operator_confirmed_manifest_apply,
        tutor_index_build=operator_confirmed_tutor_index_build,
        help_ledger_append=operator_confirmed_help_ledger_append,
        exam_ledger_append=operator_confirmed_exam_ledger_append,
    )
    receipt = operator_receipt(launch=launch, confirmations=confirmations)
    view = start_exam_workspace_view(launch=launch, confirmations=confirmations, receipt=receipt)
    report = {
        "schema_version": EXAM_WORKSPACE_OPERATOR_RUN_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_operator_run_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": operator_status(launch, confirmations),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Operator-facing Start Exam Workspace receipt. It merges material coverage, local notebook checkpoint, "
            "A0-A2 tutor state, Help-Ledger preview, export receipt, and explicit operator confirmations into one "
            "human-readable dry-run view. Local writes happen only for individually confirmed steps. It never returns "
            "raw queries, raw cells, notebook code, local paths, complete solutions, inserted values, final "
            "interpretation, grading, proctoring, AI detection, or exam clearance."
        ),
        "operator_run_endpoint": OPERATOR_RUN_ENDPOINT,
        "start_exam_workspace_view": view,
        "start_exam_workspace_markdown": start_exam_workspace_markdown(view),
        "operator_confirmation_matrix": confirmations,
        "dry_run_receipt": receipt,
        "coverage_summary": launch.get("coverage_summary", {}),
        "local_notebook_checkpoint": launch.get("local_notebook_checkpoint", {}),
        "exam_workspace_run_summary": launch.get("exam_workspace_run_summary", {}),
        "help_ledger_preview": launch.get("help_ledger_preview", {}),
        "export_receipt": launch.get("export_receipt", {}),
        "launch_status": launch.get("status", "unknown"),
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
        "next_actions": operator_next_actions(launch, confirmations),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def operator_confirmation_matrix(
    launch: dict[str, Any],
    *,
    checkpoint_store: bool,
    exam_workspace_run: bool,
    manifest_apply: bool,
    tutor_index_build: bool,
    help_ledger_append: bool,
    exam_ledger_append: bool,
) -> dict[str, Any]:
    checkpoint = launch.get("local_notebook_checkpoint", {}) if isinstance(launch.get("local_notebook_checkpoint"), dict) else {}
    workspace = launch.get("exam_workspace_run_summary", {}) if isinstance(launch.get("exam_workspace_run_summary"), dict) else {}
    ledger = launch.get("help_ledger_preview", {}) if isinstance(launch.get("help_ledger_preview"), dict) else {}
    launch_config = launch.get("launch_configuration", {}) if isinstance(launch.get("launch_configuration"), dict) else {}
    lower_confirmations = (
        launch_config.get("operator_confirmations", {}) if isinstance(launch_config.get("operator_confirmations"), dict) else {}
    )
    steps = {
        "checkpoint_store": confirmation_step(
            confirmed=checkpoint_store,
            writes_local=True,
            label="Store hash-only notebook checkpoint event",
            status="stored" if checkpoint.get("checkpoint_journal_written") else "dry_run_not_written",
        ),
        "exam_workspace_run": confirmation_step(
            confirmed=exam_workspace_run or bool(lower_confirmations.get("exam_workspace_run", False)),
            writes_local=True,
            label="Start local exam workspace session, material freeze, notebook open, and cell checkpoint",
            status=workspace.get("session_status", "dry_run_not_started"),
        ),
        "manifest_apply": confirmation_step(
            confirmed=manifest_apply or bool(lower_confirmations.get("manifest_apply", False)),
            writes_local=True,
            label="Apply reviewed private manifest metadata if needed",
            status="confirmed" if manifest_apply else "dry_run_not_requested",
        ),
        "tutor_index_build": confirmation_step(
            confirmed=tutor_index_build or bool(lower_confirmations.get("tutor_index_build", False)),
            writes_local=True,
            label="Build or rebuild hash-only private tutor index if needed",
            status="confirmed" if tutor_index_build else "dry_run_not_requested",
        ),
        "help_ledger_append": confirmation_step(
            confirmed=help_ledger_append or bool(lower_confirmations.get("help_ledger_append", False)),
            writes_local=True,
            label="Append general Help-Ledger event",
            status=ledger.get("general_help_ledger_status", "dry_run_not_written"),
        ),
        "exam_ledger_append": confirmation_step(
            confirmed=exam_ledger_append or bool(lower_confirmations.get("exam_ledger_append", False)),
            writes_local=True,
            label="Append exam-gateway ledger event",
            status=ledger.get("exam_ledger_status", "dry_run_not_written"),
        ),
    }
    confirmed_count = len([item for item in steps.values() if item.get("confirmed")])
    return {
        "status": "operator_confirmations_present" if confirmed_count else "all_steps_dry_run",
        "confirmed_count": confirmed_count,
        "write_step_count": len(steps),
        "default_policy": "dry_run_until_individual_operator_confirmation",
        "steps": steps,
        "local_writes_requested": confirmed_count > 0,
        "raw_confirmation_text_returned": False,
    }


def confirmation_step(*, confirmed: bool, writes_local: bool, label: str, status: str) -> dict[str, Any]:
    return {
        "label": label,
        "confirmed": bool(confirmed),
        "writes_local": bool(writes_local),
        "status": status,
        "requires_individual_confirmation": True,
    }


def operator_receipt(*, launch: dict[str, Any], confirmations: dict[str, Any]) -> dict[str, Any]:
    coverage = launch.get("coverage_summary", {}) if isinstance(launch.get("coverage_summary"), dict) else {}
    start = coverage.get("start_point", {}) if isinstance(coverage.get("start_point"), dict) else {}
    checkpoint = launch.get("local_notebook_checkpoint", {}) if isinstance(launch.get("local_notebook_checkpoint"), dict) else {}
    workspace = launch.get("exam_workspace_run_summary", {}) if isinstance(launch.get("exam_workspace_run_summary"), dict) else {}
    ledger = launch.get("help_ledger_preview", {}) if isinstance(launch.get("help_ledger_preview"), dict) else {}
    export = launch.get("export_receipt", {}) if isinstance(launch.get("export_receipt"), dict) else {}
    seed = {
        "launch_status": launch.get("status", ""),
        "skill_tag": start.get("skill_tag", ""),
        "checkpoint_hash": checkpoint.get("notebook_work_sha256", ""),
        "workspace_status": workspace.get("status", ""),
        "ledger_hash": ledger.get("event_hash", ""),
        "export_package": export.get("package_id", ""),
        "confirmations": confirmations.get("confirmed_count", 0),
    }
    return {
        "status": "ready_for_human_review_not_exam_clearance",
        "receipt_id": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))[:20],
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "material_coverage_status": coverage.get("status", "unknown"),
        "start_point_status": start.get("status", "unknown"),
        "selected_skill_tag": start.get("skill_tag", ""),
        "notebook_checkpoint_status": checkpoint.get("status", "not_provided"),
        "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
        "tutor_status": workspace.get("tutor_status", "unknown"),
        "effective_help_level": workspace.get("effective_help_level", ledger.get("help_level", "A2")),
        "study_receipt_status": workspace.get("study_receipt_status", "unknown"),
        "help_ledger_preview_status": ledger.get("status", "unknown"),
        "export_status": export.get("status", "unknown"),
        "human_reviewable_independence_evidence": bool(export.get("human_reviewable_independence_evidence", False)),
        "operator_confirmation_status": confirmations.get("status", "unknown"),
        "raw_query_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_path_returned": False,
    }


def start_exam_workspace_view(
    *,
    launch: dict[str, Any],
    confirmations: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    coverage = launch.get("coverage_summary", {}) if isinstance(launch.get("coverage_summary"), dict) else {}
    start = coverage.get("start_point", {}) if isinstance(coverage.get("start_point"), dict) else {}
    checkpoint = launch.get("local_notebook_checkpoint", {}) if isinstance(launch.get("local_notebook_checkpoint"), dict) else {}
    workspace = launch.get("exam_workspace_run_summary", {}) if isinstance(launch.get("exam_workspace_run_summary"), dict) else {}
    ledger = launch.get("help_ledger_preview", {}) if isinstance(launch.get("help_ledger_preview"), dict) else {}
    export = launch.get("export_receipt", {}) if isinstance(launch.get("export_receipt"), dict) else {}
    return {
        "title": "Start Exam Workspace",
        "status": view_status(launch),
        "mode": "exam_controlled_gateway",
        "exam_deployment_status": "not_cleared",
        "sections": [
            view_section("Material Coverage", coverage.get("status", "unknown"), [
                f"ready skills: {coverage.get('ready_skill_count', 0)}/{coverage.get('skill_count', 0)}",
                f"selected skill: {start.get('skill_tag', '') or 'none'}",
            ]),
            view_section("Notebook Checkpoint", checkpoint.get("status", "not_provided"), [
                f"checkpoint id: {checkpoint.get('checkpoint_id', '') or 'not provided'}",
                f"work hash: {checkpoint.get('notebook_work_sha256', '') or 'missing'}",
            ]),
            view_section("Tutor Sidecar", workspace.get("tutor_status", "unknown"), [
                f"help level: {workspace.get('effective_help_level', ledger.get('help_level', 'A2'))}",
                f"source anchors: {workspace.get('source_anchor_count', ledger.get('source_anchor_count', 0))}",
            ]),
            view_section("Help Ledger Preview", ledger.get("status", "unknown"), [
                f"general ledger written: {bool(ledger.get('general_help_ledger_written', False))}",
                f"exam ledger written: {bool(ledger.get('exam_ledger_written', False))}",
            ]),
            view_section("Export Receipt", export.get("status", "unknown"), [
                f"not cleared: {bool(export.get('not_cleared_receipt', True))}",
                f"human reviewable: {bool(export.get('human_reviewable_independence_evidence', False))}",
            ]),
            view_section("Operator Confirmations", confirmations.get("status", "unknown"), [
                f"confirmed write steps: {confirmations.get('confirmed_count', 0)}/{confirmations.get('write_step_count', 0)}",
                "default: dry-run",
            ]),
        ],
        "receipt_id": receipt.get("receipt_id", ""),
        "raw_query_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def view_section(title: str, status: str, lines: list[str]) -> dict[str, Any]:
    return {"title": title, "status": status, "lines": lines[:4]}


def view_status(launch: dict[str, Any]) -> str:
    status = str(launch.get("status", "unknown"))
    if status in {"exam_workspace_launch_dry_run_ready", "exam_workspace_launch_ready_with_exam_ledger"}:
        return "ready_to_start_dry_run"
    if "repeat_task_required" in status:
        return "repeat_task_required_before_start"
    if "waiting" in status:
        return "waiting_for_required_evidence"
    return "review_required_before_start"


def start_exam_workspace_markdown(view: dict[str, Any]) -> str:
    lines = [
        "# Start Exam Workspace",
        f"Status: {view.get('status', 'unknown')}",
        f"Exam deployment: {view.get('exam_deployment_status', 'not_cleared')}",
        f"Receipt: {view.get('receipt_id', '')}",
        "",
    ]
    for section in view.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        lines.append(f"## {section.get('title', 'Section')}")
        lines.append(f"Status: {section.get('status', 'unknown')}")
        for item in section.get("lines", []) or []:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(
        [
            "Boundary: A0-A2 only; no solutions, raw cells, notebook code, local paths, grading, proctoring, AI detection, or exam clearance.",
        ]
    )
    return "\n".join(lines)


def operator_status(launch: dict[str, Any], confirmations: dict[str, Any]) -> str:
    launch_status = str(launch.get("status", "unknown"))
    if launch_status == "blocked_public_safety":
        return "blocked_public_safety"
    if "repeat_task_required" in launch_status:
        return "exam_workspace_operator_repeat_task_required"
    if "waiting" in launch_status:
        return "exam_workspace_operator_waiting_for_required_evidence"
    if launch_status in {"exam_workspace_launch_dry_run_ready", "exam_workspace_launch_ready_with_exam_ledger"}:
        if confirmations.get("local_writes_requested"):
            return "exam_workspace_operator_ready_with_confirmed_local_writes"
        return "exam_workspace_operator_dry_run_ready"
    return "exam_workspace_operator_review_required"


def operator_next_actions(launch: dict[str, Any], confirmations: dict[str, Any]) -> list[str]:
    status = operator_status(launch, confirmations)
    if status == "exam_workspace_operator_dry_run_ready":
        return [
            "Review the Start Exam Workspace receipt before enabling any local write confirmation.",
            "Use the dry-run receipt as the human-readable handoff; do not infer a grade or Eigenleistung percentage.",
            "Real exam authority clearance remains a real-world reminder and UniBot stays not_cleared.",
        ]
    if status == "exam_workspace_operator_ready_with_confirmed_local_writes":
        return [
            "Review the locally written receipt artifacts and export summary.",
            "Keep any additional write step individually confirmed and human-reviewed.",
            "Do not treat this as exam clearance; UniBot remains not_cleared.",
        ]
    return list(launch.get("next_actions", []) or [])[:5]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-workspace-operator-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
