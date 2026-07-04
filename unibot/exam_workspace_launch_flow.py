from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_notebook_checkpoint import build_exam_notebook_checkpoint_adapter_dry_run
from .exam_workspace_run import build_exam_workspace_run_dry_run
from .material_coverage_run import build_course_material_coverage_run
from .materials import build_material_manifest, sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_index import build_private_tutor_index_dry_run


EXAM_WORKSPACE_LAUNCH_FLOW_SCHEMA_VERSION = "unibot-exam-workspace-launch-flow-v1"
EXAM_WORKSPACE_LAUNCH_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-launch-release-review-board-claim-alignment-v1"
)
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
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
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
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
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
            "local_cycle_operator_workspace_card": local_cycle_workspace_card,
            "requires_operator_confirmation_for_writes": True,
        },
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
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


def build_exam_workspace_launch_release_claim_alignment(
    launch_report: dict[str, Any] | None = None,
    blocked_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if launch_report is None or blocked_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_launch_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            materials_root.mkdir(parents=True)
            (materials_root / "pandas_intro.md").write_text(
                "pandas DataFrame read_csv columns dtypes debugging boxplot",
                encoding="utf-8",
            )
            manifest_path = temp_root / "private_manifest.json"
            tutor_index_path = temp_root / "private_tutor_index.json"
            tutor_index_journal_path = temp_root / "private_tutor_index_journal.jsonl"
            manifest = build_material_manifest([synthetic_launch_manifest_record()])
            manifest["artifact_type"] = "course_private_material_manifest"
            manifest["exam_deployment_status"] = "not_cleared"
            manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=tutor_index_path,
                tutor_index_journal_path=tutor_index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )
            common_kwargs = {
                "course_id": "exam-workspace-launch-alignment",
                "base_path": str(materials_root),
                "review_policy": "local_private_tutor",
                "decision_record": synthetic_launch_decision_record(),
                "private_manifest_path": manifest_path,
                "tutor_index_path": tutor_index_path,
                "tutor_index_journal_path": tutor_index_journal_path,
                "focus_query": "pandas boxplot",
                "query": "synthetic private launch query",
                "student_reflection": "I checked my own prediction before asking for source-anchored help.",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                "python_exam_local_cycle_operator_workspace_card": synthetic_launch_workspace_card(),
                "public_safe": True,
            }
            launch_report = launch_report or build_exam_workspace_launch_flow_dry_run(
                **common_kwargs,
                requested_help_level="A2",
                cell_source="own_frame_shape = (3, 2)\n",
                cell_index=1,
                cell_id="synthetic-private-launch-cell",
            )
            blocked_report = blocked_report or build_exam_workspace_launch_flow_dry_run(
                **common_kwargs,
                requested_help_level="A2",
                cell_source="# final answer: complete solution\n",
                cell_index=2,
                cell_id="synthetic-private-repeat-cell",
            )

    sections = [
        {
            "section_id": "notebook_checkpoint_trace",
            "summary_claim": "launch flow starts from a coverage-selected skill and links only hash-only notebook checkpoint evidence",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["exam_workspace_launch", "notebook_checkpoint", "study_session"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "private_tutor_use_trace",
            "summary_claim": "launch flow stays within private tutor use, study receipts, and source-anchored A0-A2 help",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "exam_workspace_launch",
                "python_exam_local_cycle_operator_workspace_card",
                "private_tutor_use_flow",
                "evaluation_packet",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "dry_run_boundary_trace",
            "summary_claim": "launch flow defaults to dry-run and requires operator review before local writes or any real exam posture",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "exam_workspace_launch",
                "python_exam_local_cycle_operator_workspace_card",
                "review_board_packet",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "launch flow does not publish raw code, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["exam_workspace_launch", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    launch_config = launch_report.get("launch_configuration", {}) if isinstance(launch_report.get("launch_configuration"), dict) else {}
    notebook_checkpoint = (
        launch_config.get("notebook_cell_checkpoint", {})
        if isinstance(launch_config.get("notebook_cell_checkpoint"), dict)
        else {}
    )
    local_checkpoint = (
        launch_report.get("local_notebook_checkpoint", {})
        if isinstance(launch_report.get("local_notebook_checkpoint"), dict)
        else {}
    )
    workspace_summary = (
        launch_report.get("exam_workspace_run_summary", {})
        if isinstance(launch_report.get("exam_workspace_run_summary"), dict)
        else {}
    )
    workspace_card = (
        launch_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(launch_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    launch_workspace_card = (
        launch_config.get("local_cycle_operator_workspace_card", {})
        if isinstance(launch_config.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    help_preview = (
        launch_report.get("help_ledger_preview", {})
        if isinstance(launch_report.get("help_ledger_preview"), dict)
        else {}
    )
    blocked_checkpoint = (
        blocked_report.get("local_notebook_checkpoint", {})
        if isinstance(blocked_report.get("local_notebook_checkpoint"), dict)
        else {}
    )
    blocked_claims = [
        "raw notebook code returned",
        "raw cell text returned",
        "raw notebook returned",
        "local path returned",
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
    boundary = str(launch_report.get("execution_boundary", ""))
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "launch_public_safe": launch_report.get("public_safety_status") == "pass",
        "blocked_launch_public_safe": blocked_report.get("public_safety_status") == "pass",
        "notebook_checkpoint_linked_hash_only": launch_report.get("status") == "exam_workspace_launch_dry_run_ready"
        and local_checkpoint.get("status") == "notebook_checkpoint_ready"
        and bool(local_checkpoint.get("notebook_work_sha256"))
        and bool(notebook_checkpoint.get("notebook_work_sha256"))
        and notebook_checkpoint.get("raw_notebook_returned") is False
        and notebook_checkpoint.get("notebook_code_returned") is False
        and notebook_checkpoint.get("local_path_returned") is False,
        "private_tutor_use_and_study_receipt_linked": workspace_summary.get("tutor_status") == "allowed"
        and workspace_summary.get("study_receipt_status") == "ok_study_session_receipt"
        and help_preview.get("status") == "preview_ready"
        and help_preview.get("general_help_ledger_written") is False
        and help_preview.get("exam_ledger_written") is False,
        "workspace_card_launch_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("selected_skill_tag") == launch_config.get("skill_tag")
        and workspace_card.get("not_cleared_receipt") is True
        and launch_workspace_card.get("status") == workspace_card.get("status")
        and launch_workspace_card.get("raw_workspace_card_returned") is False,
        "dry_run_operator_boundaries_hold": launch_config.get("requires_operator_confirmation_for_writes") is True
        and launch_report.get("exam_deployment_status") == "not_cleared"
        and launch_report.get("export_receipt", {}).get("not_cleared_receipt") is True
        and "Standard is dry-run" in boundary,
        "blocked_checkpoint_stops_launch": blocked_report.get("status")
        == "exam_workspace_launch_notebook_checkpoint_repeat_task_required"
        and blocked_report.get("exam_workspace_run_summary", {}).get("status") == "not_started_checkpoint_not_ready"
        and blocked_checkpoint.get("solution_marker_detected") is True,
        "public_outputs_hide_private_data": launch_report.get("raw_query_returned") is False
        and launch_report.get("raw_text_returned") is False
        and launch_report.get("raw_cell_returned") is False
        and launch_report.get("raw_notebook_returned") is False
        and launch_report.get("notebook_code_returned") is False
        and launch_report.get("local_paths_returned") is False,
        "high_stakes_actions_not_started": launch_report.get("automatic_grading_started") is False
        and launch_report.get("proctoring_started") is False
        and launch_report.get("ai_detection_started") is False
        and launch_report.get("exam_clearance_claimed") is False
        and launch_report.get("exam_deployment_status") == "not_cleared",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "launch_status": launch_report.get("status"),
        "blocked_status": blocked_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-launch-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_LAUNCH_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "launch_status": launch_report.get("status"),
        "launch_public_safety_status": launch_report.get("public_safety_status"),
        "launch_workspace_status": workspace_summary.get("status"),
        "blocked_launch_status": blocked_report.get("status"),
        "blocked_public_safety_status": blocked_report.get("public_safety_status"),
        "exam_deployment_status": launch_report.get("exam_deployment_status"),
        "checkpoint_status": local_checkpoint.get("status"),
        "checkpoint_hash_present": bool(local_checkpoint.get("notebook_work_sha256")),
        "study_receipt_status": workspace_summary.get("study_receipt_status"),
        "tutor_status": workspace_summary.get("tutor_status"),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "help_ledger_preview_status": help_preview.get("status"),
        "general_help_ledger_written": bool(help_preview.get("general_help_ledger_written", False)),
        "exam_ledger_written": bool(help_preview.get("exam_ledger_written", False)),
        "repeat_task_required": bool(blocked_checkpoint.get("solution_marker_detected", False)),
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
            "Exam workspace launch is a source-anchored dry-run entry point. It may prepare a private tutor session, "
            "hash-only notebook checkpoint, study receipt, and export receipt, but it does not return raw private data, "
            "grade, proctor, detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


def selected_skill_row(coverage: dict[str, Any], start_point: dict[str, Any]) -> dict[str, Any]:
    skill_tag = str(start_point.get("skill_tag", ""))
    for row in coverage.get("skill_coverage", []) or []:
        if isinstance(row, dict) and row.get("skill_tag") == skill_tag:
            return row
    return {}


def synthetic_launch_manifest_record() -> dict[str, Any]:
    return {
        "material_id": "synthetic-launch-notebook",
        "title": "Synthetic launch notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["pandas", "boxplots", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "synthetic week 01",
        "sha256": sha256_text("synthetic launch notebook reviewed locally"),
    }


def synthetic_launch_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic launch workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "boxplots",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic launch prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "boxplots",
            "next_safe_action": "open_launch_dry_run",
            "next_safe_user_action": "review_launch_checkpoint_before_any_local_write",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": preview_hash,
            "checkpoint_hash": preview_hash,
            "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def synthetic_launch_decision_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic launch flow decision",
    }


def safe_local_cycle_workspace_card(workspace_card: dict[str, Any]) -> dict[str, Any]:
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
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": str(summary.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


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
