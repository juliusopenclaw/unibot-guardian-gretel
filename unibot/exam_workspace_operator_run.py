from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_launch_flow import build_exam_workspace_launch_flow_dry_run
from .materials import build_material_manifest, sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_index import build_private_tutor_index_dry_run


EXAM_WORKSPACE_OPERATOR_RUN_SCHEMA_VERSION = "unibot-exam-workspace-operator-run-v1"
EXAM_WORKSPACE_OPERATOR_RUN_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-operator-run-release-review-board-claim-alignment-v1"
)
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


def build_exam_workspace_operator_run_release_claim_alignment(
    ready_report: dict[str, Any] | None = None,
    repeat_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ready_report is None or repeat_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_operator_run_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            manifest_path = temp_root / "private_manifest.json"
            index_path = temp_root / "private_tutor_index.json"
            index_journal_path = temp_root / "index_journal.jsonl"
            write_synthetic_operator_fixture(materials_root)
            write_synthetic_operator_manifest(manifest_path)
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )
            common_kwargs = {
                "base_path": str(materials_root),
                "review_policy": "local_private_tutor",
                "decision_record": synthetic_operator_decision_record(),
                "private_manifest_path": manifest_path,
                "tutor_index_path": index_path,
                "tutor_index_journal_path": index_journal_path,
                "focus_query": "pandas boxplot",
                "query": "synthetic private operator question",
                "requested_help_level": "A2",
                "student_reflection": "I checked my own prediction before opening the workspace.",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                "public_safe": True,
            }
            ready_report = ready_report or build_exam_workspace_operator_run_dry_run(
                **common_kwargs,
                cell_source="own_frame = None\n# local checkpoint only\n",
                cell_index=1,
                cell_id="synthetic-private-operator-cell",
            )
            repeat_report = repeat_report or build_exam_workspace_operator_run_dry_run(
                **common_kwargs,
                cell_source="# final answer: complete solution\n",
                cell_index=2,
                cell_id="synthetic-private-repeat-cell",
            )

    sections = [
        {
            "section_id": "operator_start_view_trace",
            "summary_claim": "operator run merges launch, checkpoint, tutor, ledger, and export evidence into one dry-run start view",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["exam_workspace_operator_run", "exam_workspace_launch", "exam_workspace_run"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "individual_confirmation_trace",
            "summary_claim": "operator run requires individual confirmation before local write steps and defaults to dry-run",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["exam_workspace_operator_run", "exam_workspace_run_history", "review_board_packet"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "repeat_task_boundary_trace",
            "summary_claim": "operator run stops when a notebook checkpoint contains final-solution exposure",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["exam_workspace_operator_run", "notebook_checkpoint", "study_session"],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "operator run does not publish raw notebook data, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["exam_workspace_operator_run", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    view = (
        ready_report.get("start_exam_workspace_view", {})
        if isinstance(ready_report.get("start_exam_workspace_view"), dict)
        else {}
    )
    confirmations = (
        ready_report.get("operator_confirmation_matrix", {})
        if isinstance(ready_report.get("operator_confirmation_matrix"), dict)
        else {}
    )
    confirmation_steps = confirmations.get("steps", {}) if isinstance(confirmations.get("steps"), dict) else {}
    receipt = ready_report.get("dry_run_receipt", {}) if isinstance(ready_report.get("dry_run_receipt"), dict) else {}
    checkpoint = (
        ready_report.get("local_notebook_checkpoint", {})
        if isinstance(ready_report.get("local_notebook_checkpoint"), dict)
        else {}
    )
    workspace = (
        ready_report.get("exam_workspace_run_summary", {})
        if isinstance(ready_report.get("exam_workspace_run_summary"), dict)
        else {}
    )
    ledger = (
        ready_report.get("help_ledger_preview", {})
        if isinstance(ready_report.get("help_ledger_preview"), dict)
        else {}
    )
    export = ready_report.get("export_receipt", {}) if isinstance(ready_report.get("export_receipt"), dict) else {}
    repeat_checkpoint = (
        repeat_report.get("local_notebook_checkpoint", {})
        if isinstance(repeat_report.get("local_notebook_checkpoint"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
        "raw confirmation text returned",
        "raw notebook code returned",
        "raw cell text returned",
        "raw notebook returned",
        "local path returned",
        "unconfirmed local write",
        "final solution acceptance",
        "complete code outsourcing",
        "inserted values",
        "final interpretation",
        "automatic grading",
        "proctoring",
        "KI-detection evidence",
        "Eigenleistung percentage claim",
        "cloud processing",
        "exam deployment",
        "exam clearance",
    ]
    boundary = str(ready_report.get("execution_boundary", ""))
    markdown = str(ready_report.get("start_exam_workspace_markdown", ""))
    contracts = {
        "operator_ready_public_safe": ready_report.get("public_safety_status") == "pass",
        "repeat_boundary_public_safe": repeat_report.get("public_safety_status") == "pass",
        "start_view_hash_only_ready": ready_report.get("status") == "exam_workspace_operator_dry_run_ready"
        and view.get("status") == "ready_to_start_dry_run"
        and view.get("raw_query_returned") is False
        and view.get("raw_cell_returned") is False
        and view.get("notebook_code_returned") is False
        and view.get("local_paths_returned") is False
        and bool(receipt.get("receipt_id"))
        and checkpoint.get("status") == "notebook_checkpoint_ready"
        and bool(checkpoint.get("notebook_work_sha256"))
        and workspace.get("status") == "exam_workspace_dry_run_ready"
        and workspace.get("tutor_status") == "allowed"
        and workspace.get("study_receipt_status") == "ok_study_session_receipt",
        "individual_confirmations_default_to_dry_run": confirmations.get("status") == "all_steps_dry_run"
        and confirmations.get("default_policy") == "dry_run_until_individual_operator_confirmation"
        and confirmations.get("local_writes_requested") is False
        and confirmations.get("raw_confirmation_text_returned") is False
        and int(confirmations.get("confirmed_count", -1) or 0) == 0
        and int(confirmations.get("write_step_count", 0) or 0) == 6
        and all(step.get("confirmed") is False for step in confirmation_steps.values())
        and all(step.get("requires_individual_confirmation") is True for step in confirmation_steps.values()),
        "receipt_and_export_not_exam_clearance": receipt.get("status") == "ready_for_human_review_not_exam_clearance"
        and receipt.get("not_cleared_receipt") is True
        and receipt.get("exam_deployment_status") == "not_cleared"
        and receipt.get("human_reviewable_independence_evidence") is True
        and export.get("not_cleared_receipt") is True
        and export.get("human_reviewable_independence_evidence") is True
        and ready_report.get("exam_deployment_status") == "not_cleared",
        "help_ledger_preview_not_written": ledger.get("status") == "preview_ready"
        and ledger.get("general_help_ledger_written") is False
        and ledger.get("exam_ledger_written") is False
        and ledger.get("raw_query_returned") is False
        and ledger.get("raw_response_returned") is False
        and ledger.get("local_path_returned") is False,
        "repeat_task_stops_operator_start": repeat_report.get("status") == "exam_workspace_operator_repeat_task_required"
        and repeat_report.get("start_exam_workspace_view", {}).get("status") == "repeat_task_required_before_start"
        and repeat_checkpoint.get("status") == "notebook_checkpoint_repeat_task_required"
        and repeat_report.get("exam_workspace_run_summary", {}).get("status") == "not_started_checkpoint_not_ready",
        "markdown_boundary_mentions_no_high_stakes_claims": "A0-A2 only" in markdown
        and "no solutions" in markdown
        and "grading" in markdown
        and "proctoring" in markdown
        and "AI detection" in markdown
        and "exam clearance" in markdown,
        "public_outputs_hide_private_operator_data": ready_report.get("raw_query_returned") is False
        and ready_report.get("raw_text_returned") is False
        and ready_report.get("raw_cell_returned") is False
        and ready_report.get("raw_notebook_returned") is False
        and ready_report.get("notebook_code_returned") is False
        and ready_report.get("local_paths_returned") is False
        and "never returns" in boundary
        and "raw queries" in boundary
        and "notebook code" in boundary
        and "local paths" in boundary,
        "high_stakes_actions_not_started": ready_report.get("automatic_grading_started") is False
        and ready_report.get("proctoring_started") is False
        and ready_report.get("ai_detection_started") is False
        and ready_report.get("exam_clearance_claimed") is False
        and ready_report.get("exam_deployment_status") == "not_cleared",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "ready_status": ready_report.get("status"),
        "repeat_status": repeat_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-operator-run-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_OPERATOR_RUN_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "operator_status": ready_report.get("status"),
        "operator_public_safety_status": ready_report.get("public_safety_status"),
        "repeat_status": repeat_report.get("status"),
        "repeat_public_safety_status": repeat_report.get("public_safety_status"),
        "exam_deployment_status": ready_report.get("exam_deployment_status"),
        "view_status": view.get("status"),
        "receipt_status": receipt.get("status"),
        "receipt_not_cleared": bool(receipt.get("not_cleared_receipt", False)),
        "confirmation_status": confirmations.get("status"),
        "confirmed_count": confirmations.get("confirmed_count", 0),
        "write_step_count": confirmations.get("write_step_count", 0),
        "local_writes_requested": bool(confirmations.get("local_writes_requested", False)),
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_hash_present": bool(checkpoint.get("notebook_work_sha256")),
        "workspace_status": workspace.get("status"),
        "tutor_status": workspace.get("tutor_status"),
        "study_receipt_status": workspace.get("study_receipt_status"),
        "help_ledger_preview_status": ledger.get("status"),
        "general_help_ledger_written": bool(ledger.get("general_help_ledger_written", False)),
        "exam_ledger_written": bool(ledger.get("exam_ledger_written", False)),
        "export_status": export.get("status"),
        "export_not_cleared_receipt": bool(export.get("not_cleared_receipt", False)),
        "repeat_checkpoint_status": repeat_checkpoint.get("status"),
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": blocked_claims,
        "public_safety_status": scan["status"],
        "policy": (
            "Exam workspace operator run is a human-facing dry-run control surface. It may summarize launch, "
            "checkpoint, tutor, ledger, export, and individual confirmation state, but it does not return raw "
            "private data, perform unconfirmed local writes, grade, proctor, detect AI use, claim Eigenleistung "
            "percentages, or clear exams."
        ),
    }


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


def write_synthetic_operator_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes debugging boxplot",
        encoding="utf-8",
    )


def synthetic_operator_manifest_record() -> dict[str, Any]:
    return {
        "material_id": "synthetic-operator-pandas-notebook",
        "title": "Synthetic operator pandas notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["pandas", "boxplots", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "synthetic week 01",
        "sha256": sha256_text("synthetic operator pandas notebook reviewed locally"),
    }


def write_synthetic_operator_manifest(path: Path) -> None:
    manifest = build_material_manifest([synthetic_operator_manifest_record()])
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def synthetic_operator_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic operator run decision",
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
