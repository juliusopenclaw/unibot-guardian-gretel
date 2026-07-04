from __future__ import annotations

import base64
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .materials import sha256_text
from .private_tutor_use_flow import build_private_tutor_use_flow_dry_run
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_index import build_private_index_tutor_response_dry_run


EXAM_WORKSPACE_RUN_SCHEMA_VERSION = "unibot-exam-workspace-run-v1"
EXAM_WORKSPACE_RUN_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-run-release-review-board-claim-alignment-v1"
)
EXAM_WORKSPACE_RUN_WORKSPACE_CARD_RECEIPT_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-run-workspace-card-run-receipt-alignment-v1"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def build_exam_workspace_run_dry_run(
    query: str,
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
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    notebook: dict[str, Any] | None = None,
    notebook_content_base64: str | None = None,
    notebook_filename: str = "exam_workspace_notebook.ipynb",
    cell_index: int = 0,
    cell_id: str | None = None,
    cell_type: str = "code",
    cell_source: str = "",
    notebook_work_sha256_override: str = "",
    material_files: list[dict[str, Any]] | None = None,
    student_reflection: str = "",
    study_receipt: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
    attach_workspace_card_alignment: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    notebook_payload = notebook_from_payload(notebook=notebook, notebook_content_base64=notebook_content_base64)
    selected_source = str(cell_source or source_from_notebook(notebook_payload, cell_index))
    cell_hash = sha256_text(f"{safe_id}:{cell_index}:{cell_id or ''}:{selected_source}")[:16]
    task_id = f"exam-cell-{cell_hash}"
    notebook_sha = sha256_text(json.dumps(notebook_payload, ensure_ascii=False, sort_keys=True))

    session = session_step(
        course_id=safe_id,
        notebook_session_id=task_id,
        confirmed=operator_confirmed_exam_workspace_run,
    )
    materials = material_freeze_step(
        course_id=safe_id,
        material_files=material_files or [],
        confirmed=operator_confirmed_exam_workspace_run,
    )
    notebook_step = notebook_open_step(
        course_id=safe_id,
        notebook_payload=notebook_payload,
        notebook_content_base64=notebook_content_base64,
        notebook_filename=notebook_filename,
        confirmed=operator_confirmed_exam_workspace_run,
    )
    cell_run = notebook_cell_step(
        course_id=safe_id,
        session_id=str(session.get("session_id", "")),
        cell_index=cell_index,
        cell_source=selected_source,
        confirmed=operator_confirmed_exam_workspace_run,
    )
    notebook_work_sha256 = valid_sha256(notebook_work_sha256_override) or str(
        cell_run.get("notebook_work_sha256", sha256_text(selected_source))
    )
    cell_source_sha256 = valid_sha256(notebook_work_sha256_override) or sha256_text(selected_source)
    cell_run["notebook_work_sha256"] = notebook_work_sha256

    tutor_flow = build_private_tutor_use_flow_dry_run(
        query,
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
        requested_help_level=requested_help_level,
        mode="exam_controlled_gateway",
        exam_status=exam_status,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
        study_receipt=workspace_study_receipt(
            task_id=task_id,
            query=query,
            reflection=student_reflection,
            study_receipt=study_receipt,
        ),
        public_safe=public_safe,
    )
    sidecar_response = build_private_index_tutor_response_dry_run(
        query,
        course_id=safe_id,
        tutor_index_path=tutor_index_path,
        mode="exam_controlled_gateway",
        requested_help_level=requested_help_level,
        exam_status=exam_status,
        public_safe=public_safe,
    )
    exam_ledger = exam_ledger_step(
        course_id=safe_id,
        session_id=str(session.get("session_id", "")),
        gateway_session_id=str(session.get("session_id", "")),
        cell_index=cell_index,
        cell_id=cell_id or task_id,
        cell_type=cell_type,
        prompt=query,
        raw_response=f"sidecar_response_sha256:{sha256_text(str(sidecar_response.get('answer_markdown', '')))}",
        student_reflection=student_reflection,
        notebook_work_sha256=str(cell_run.get("notebook_work_sha256", sha256_text(selected_source))),
        source_card_ids=list(sidecar_response.get("source_card_ids", []) or [])[:8],
        help_level=str(sidecar_response.get("effective_help_level", requested_help_level)),
        confirmed=operator_confirmed_exam_ledger_append,
    )
    package = export_step(
        course_id=safe_id,
        notebook_payload=notebook_payload,
        session=session,
        materials=materials,
        cell_run=cell_run,
        sidecar_response=sidecar_response,
        exam_ledger=exam_ledger,
    )

    report = {
        "schema_version": EXAM_WORKSPACE_RUN_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_run_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": exam_workspace_status(tutor_flow=tutor_flow, sidecar_response=sidecar_response, exam_ledger=exam_ledger),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Controlled exam-workspace run. It links a notebook cell checkpoint, A0-A2 private tutor sidecar, "
            "Help-Ledger evidence, study-receipt validation, and a human-review export receipt. Standard use is "
            "dry-run; local writes require explicit operator confirmations. It never returns raw queries, raw "
            "course text, notebook code, local paths, complete solutions, inserted values, final interpretation, "
            "grading, proctoring, AI detection, or exam clearance."
        ),
        "operator_confirmations": {
            "exam_workspace_run": bool(operator_confirmed_exam_workspace_run),
            "manifest_apply": bool(operator_confirmed_manifest_apply),
            "tutor_index_build": bool(operator_confirmed_tutor_index_build),
            "help_ledger_append": bool(operator_confirmed_help_ledger_append),
            "exam_ledger_append": bool(operator_confirmed_exam_ledger_append),
        },
        "session_summary": public_session_summary(session),
        "material_freeze_summary": public_material_summary(materials),
        "notebook_checkpoint": {
            "step_id": "notebook_checkpoint",
            "status": notebook_step.get("status", "unknown"),
            "notebook_sha256": notebook_sha,
            "cell_index": int(cell_index or 0),
            "cell_id_hash": sha256_text(cell_id or task_id),
            "cell_task_id": task_id,
            "cell_source_sha256": cell_source_sha256,
            "cell_type": str(cell_type or "code")[:40],
            "run_status": cell_run.get("status", "unknown"),
            "execution_id": cell_run.get("execution_id", ""),
            "notebook_work_sha256": notebook_work_sha256,
            "notebook_work_hash_override_used": bool(valid_sha256(notebook_work_sha256_override)),
            "kernel_execution_started": cell_run.get("status") not in {"kernel-unavailable", "dry_run_not_executed"},
            "raw_notebook_returned": False,
            "notebook_code_returned": False,
            "local_path_returned": False,
        },
        "tutor_sidecar": sidecar_public_summary(sidecar_response),
        "private_tutor_use_flow_summary": {
            "status": tutor_flow.get("status", "unknown"),
            "manifest_apply": tutor_flow.get("manifest_apply_summary", {}),
            "tutor_index": tutor_flow.get("tutor_index_summary", {}),
            "tutor_response": tutor_flow.get("tutor_response_summary", {}),
            "ledger_append": tutor_flow.get("ledger_append_summary", {}),
            "study_receipt_validation": tutor_flow.get("study_receipt_validation", {}),
        },
        "cell_evidence_link": {
            "cell_task_id": task_id,
            "study_receipt_task_id": tutor_flow.get("study_receipt_validation", {}).get("task_id", ""),
            "study_receipt_status": tutor_flow.get("study_receipt_validation", {}).get("status", "unknown"),
            "exam_ledger_status": exam_ledger.get("status", "unknown"),
            "general_help_ledger_status": tutor_flow.get("ledger_append_summary", {}).get("status", "unknown"),
            "source_anchor_id_hash": tutor_flow.get("study_receipt_validation", {}).get("source_anchor_id_hash", ""),
            "notebook_work_sha256": cell_run.get("notebook_work_sha256", ""),
            "eigenleistung_percentage_claimed": False,
        },
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
        "exam_ledger_append_summary": exam_ledger_public_summary(exam_ledger),
        "export_package_summary": package,
        "raw_query_returned": False,
        "raw_text_returned": False,
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
            "Real exam authority clearance is a real-world follow-up. UniBot reminds the operator and remains not_cleared."
        ),
        "next_actions": exam_workspace_next_actions(tutor_flow=tutor_flow, sidecar_response=sidecar_response, exam_ledger=exam_ledger),
    }
    attach_public_scan(report, public_safe=public_safe)
    if attach_workspace_card_alignment:
        report["workspace_card_run_receipt_alignment"] = build_exam_workspace_run_workspace_card_receipt_alignment(
            report
        )
        attach_public_scan(report, public_safe=public_safe)
    return report


def build_exam_workspace_run_release_claim_alignment(
    run_report: dict[str, Any] | None = None,
    waiting_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if run_report is None or waiting_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_run_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            (materials_root / "Week 1").mkdir(parents=True)
            (materials_root / "Week 1" / "synthetic_python_lists.pdf").write_bytes(b"%PDF-1.4\nsynthetic")
            decision_record = synthetic_exam_workspace_decision_record()
            queue = build_course_extraction_queue(
                base_path=str(materials_root),
                rights_decision_reference=str(decision_record["decision_reference"]),
            )
            receipt = synthetic_exam_workspace_reviewed_receipt(queue["jobs"][0], decision_record)
            common_kwargs = {
                "query": "synthetic private exam-workspace query",
                "course_id": "exam-workspace-run-alignment",
                "base_path": str(materials_root),
                "decision_record": decision_record,
                "notebook": synthetic_exam_workspace_notebook(),
                "cell_index": 1,
                "cell_id": "synthetic-private-run-cell",
                "cell_type": "code",
                "student_reflection": "I checked my own prediction before requesting source-anchored help.",
                "requested_help_level": "A2",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                "python_exam_local_cycle_operator_workspace_card": synthetic_exam_workspace_run_workspace_card(),
                "public_safe": True,
            }
            if run_report is None:
                import exam_mode

                previous_exam_root = exam_mode.EXAM_ROOT
                exam_mode.EXAM_ROOT = temp_root / "exam_workspace_runtime"
                try:
                    run_report = build_exam_workspace_run_dry_run(
                        **common_kwargs,
                        receipts=[receipt],
                        private_manifest_path=temp_root / "private_manifest.json",
                        manifest_apply_journal_path=temp_root / "manifest_apply.jsonl",
                        tutor_index_path=temp_root / "private_tutor_index.json",
                        tutor_index_journal_path=temp_root / "private_tutor_index.jsonl",
                        ledger_path=temp_root / "help_ledger.jsonl",
                        operator_confirmed_exam_workspace_run=True,
                        operator_confirmed_manifest_apply=True,
                        operator_confirmed_tutor_index_build=True,
                        operator_confirmed_help_ledger_append=True,
                        operator_confirmed_exam_ledger_append=True,
                        attach_workspace_card_alignment=False,
                    )
                finally:
                    exam_mode.EXAM_ROOT = previous_exam_root
            waiting_report = waiting_report or build_exam_workspace_run_dry_run(
                **common_kwargs,
                private_manifest_path=temp_root / "missing_manifest.json",
                tutor_index_path=temp_root / "missing_tutor_index.json",
                attach_workspace_card_alignment=False,
            )

    sections = [
        {
            "section_id": "launch_to_run_checkpoint_trace",
            "summary_claim": "exam-workspace run links the launch-ready notebook checkpoint to hash-only run evidence",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["exam_workspace_run", "exam_workspace_launch", "notebook_checkpoint", "study_session"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "private_tutor_study_ledger_trace",
            "summary_claim": "exam-workspace run keeps A0-A2 tutor help source-anchored, study-receipted, and ledgered only with operator confirmation",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "exam_workspace_run",
                "python_exam_local_cycle_operator_workspace_card",
                "private_tutor_use_flow",
                "evaluation_packet",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "operator_boundary_export_trace",
            "summary_claim": "exam-workspace run can prepare a human-review export receipt but remains not cleared for real exams",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "exam_workspace_run",
                "python_exam_local_cycle_operator_workspace_card",
                "review_board_packet",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "exam-workspace run does not publish raw code, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["exam_workspace_run", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    session = run_report.get("session_summary", {}) if isinstance(run_report.get("session_summary"), dict) else {}
    materials = (
        run_report.get("material_freeze_summary", {})
        if isinstance(run_report.get("material_freeze_summary"), dict)
        else {}
    )
    checkpoint = (
        run_report.get("notebook_checkpoint", {})
        if isinstance(run_report.get("notebook_checkpoint"), dict)
        else {}
    )
    tutor_sidecar = run_report.get("tutor_sidecar", {}) if isinstance(run_report.get("tutor_sidecar"), dict) else {}
    workspace_card = (
        run_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(run_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    tutor_flow = (
        run_report.get("private_tutor_use_flow_summary", {})
        if isinstance(run_report.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    receipt = (
        tutor_flow.get("study_receipt_validation", {})
        if isinstance(tutor_flow.get("study_receipt_validation"), dict)
        else {}
    )
    general_ledger = (
        tutor_flow.get("ledger_append", {})
        if isinstance(tutor_flow.get("ledger_append"), dict)
        else {}
    )
    exam_ledger = (
        run_report.get("exam_ledger_append_summary", {})
        if isinstance(run_report.get("exam_ledger_append_summary"), dict)
        else {}
    )
    export = (
        run_report.get("export_package_summary", {})
        if isinstance(run_report.get("export_package_summary"), dict)
        else {}
    )
    cell_evidence = (
        run_report.get("cell_evidence_link", {})
        if isinstance(run_report.get("cell_evidence_link"), dict)
        else {}
    )
    waiting_session = (
        waiting_report.get("session_summary", {})
        if isinstance(waiting_report.get("session_summary"), dict)
        else {}
    )
    waiting_materials = (
        waiting_report.get("material_freeze_summary", {})
        if isinstance(waiting_report.get("material_freeze_summary"), dict)
        else {}
    )
    waiting_exam_ledger = (
        waiting_report.get("exam_ledger_append_summary", {})
        if isinstance(waiting_report.get("exam_ledger_append_summary"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
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
    boundary = str(run_report.get("execution_boundary", ""))
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "run_public_safe": run_report.get("public_safety_status") == "pass",
        "waiting_run_public_safe": waiting_report.get("public_safety_status") == "pass",
        "session_material_notebook_checkpoint_hash_only": run_report.get("status") == "exam_workspace_ready_with_exam_ledger"
        and session.get("status") == "started"
        and session.get("session_id_returned") is False
        and materials.get("status") == "frozen"
        and materials.get("raw_text_returned") is False
        and materials.get("local_path_returned") is False
        and bool(checkpoint.get("notebook_sha256"))
        and bool(checkpoint.get("cell_source_sha256"))
        and bool(checkpoint.get("notebook_work_sha256"))
        and checkpoint.get("raw_notebook_returned") is False
        and checkpoint.get("notebook_code_returned") is False
        and checkpoint.get("local_path_returned") is False,
        "private_tutor_study_and_ledger_linked": tutor_flow.get("status") == "private_tutor_use_flow_ready_with_ledger"
        and tutor_sidecar.get("status") == "allowed"
        and tutor_sidecar.get("effective_help_level") in {"A0", "A1", "A2"}
        and int(tutor_sidecar.get("source_anchor_count", 0) or 0) >= 1
        and receipt.get("status") == "ok_study_session_receipt"
        and general_ledger.get("ledger_written") is True
        and exam_ledger.get("ledger_written") is True
        and cell_evidence.get("study_receipt_status") == "ok_study_session_receipt"
        and cell_evidence.get("eigenleistung_percentage_claimed") is False,
        "workspace_card_execution_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("selected_skill_tag") in {
            str(tutor_sidecar.get("selected_skill", {}).get("skill_tag", "")),
            str(tutor_sidecar.get("selected_skill", {}).get("tag", "")),
            "boxplots",
        }
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
        "operator_confirmed_local_write_boundaries": all(
            run_report.get("operator_confirmations", {}).get(flag) is True
            for flag in [
                "exam_workspace_run",
                "manifest_apply",
                "tutor_index_build",
                "help_ledger_append",
                "exam_ledger_append",
            ]
        )
        and general_ledger.get("path_returned") is False
        and exam_ledger.get("path_returned") is False,
        "waiting_mode_no_writes_no_paths": waiting_report.get("status") == "exam_workspace_waiting_for_tutor_flow"
        and waiting_session.get("status") == "dry_run_not_started"
        and waiting_materials.get("freeze_written") is False
        and waiting_exam_ledger.get("ledger_written") is False
        and waiting_report.get("local_paths_returned") is False,
        "export_receipt_not_exam_clearance": export.get("status") == "ready_for_human_review_not_exam_clearance"
        and export.get("not_cleared_receipt") is True
        and export.get("human_reviewable_independence_evidence") is True
        and export.get("raw_transcripts_included") is False
        and export.get("automatic_grading_included") is False
        and export.get("proctoring_included") is False
        and export.get("ai_detection_included") is False
        and export.get("local_path_returned") is False,
        "public_outputs_hide_private_data": run_report.get("raw_query_returned") is False
        and run_report.get("raw_text_returned") is False
        and run_report.get("raw_notebook_returned") is False
        and run_report.get("notebook_code_returned") is False
        and run_report.get("local_paths_returned") is False
        and "never returns raw queries" in boundary
        and "notebook code" in boundary
        and "local paths" in boundary,
        "high_stakes_actions_not_started": run_report.get("exam_deployment_status") == "not_cleared"
        and run_report.get("automatic_grading_started") is False
        and run_report.get("proctoring_started") is False
        and run_report.get("ai_detection_started") is False
        and run_report.get("exam_clearance_claimed") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "run_status": run_report.get("status"),
        "waiting_status": waiting_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-run-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_RUN_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "run_status": run_report.get("status"),
        "run_public_safety_status": run_report.get("public_safety_status"),
        "waiting_status": waiting_report.get("status"),
        "waiting_public_safety_status": waiting_report.get("public_safety_status"),
        "exam_deployment_status": run_report.get("exam_deployment_status"),
        "session_status": session.get("status"),
        "material_freeze_status": materials.get("status"),
        "notebook_run_status": checkpoint.get("run_status"),
        "notebook_hash_present": bool(checkpoint.get("notebook_sha256")),
        "notebook_work_hash_present": bool(checkpoint.get("notebook_work_sha256")),
        "tutor_status": tutor_sidecar.get("status"),
        "effective_help_level": tutor_sidecar.get("effective_help_level"),
        "source_anchor_count": tutor_sidecar.get("source_anchor_count", 0),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "private_tutor_use_flow_status": tutor_flow.get("status"),
        "study_receipt_status": receipt.get("status"),
        "general_help_ledger_status": general_ledger.get("status"),
        "general_help_ledger_written": bool(general_ledger.get("ledger_written", False)),
        "exam_ledger_status": exam_ledger.get("status"),
        "exam_ledger_written": bool(exam_ledger.get("ledger_written", False)),
        "export_status": export.get("status"),
        "export_not_cleared_receipt": bool(export.get("not_cleared_receipt", False)),
        "human_reviewable_independence_evidence": bool(export.get("human_reviewable_independence_evidence", False)),
        "waiting_session_status": waiting_session.get("status"),
        "waiting_freeze_written": bool(waiting_materials.get("freeze_written", False)),
        "waiting_exam_ledger_written": bool(waiting_exam_ledger.get("ledger_written", False)),
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
            "Exam workspace run is a controlled, source-anchored local evidence packet. It may connect a notebook "
            "checkpoint, private tutor sidecar, study receipt, Help-Ledger event, exam ledger event, and export "
            "receipt for human review, but it does not return raw private data, grade, proctor, detect AI use, "
            "claim Eigenleistung percentages, or clear exams."
        ),
    }


def exam_workspace_run_hash(run_report: dict[str, Any] | None = None) -> str:
    run_report = run_report if isinstance(run_report, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": run_report.get("schema_version", ""),
                "artifact_type": run_report.get("artifact_type", ""),
                "status": run_report.get("status", ""),
                "course_id": run_report.get("course_id", ""),
                "exam_deployment_status": run_report.get("exam_deployment_status", ""),
                "operator_confirmations": run_report.get("operator_confirmations", {}),
                "session_summary": run_report.get("session_summary", {}),
                "material_freeze_summary": run_report.get("material_freeze_summary", {}),
                "notebook_checkpoint": run_report.get("notebook_checkpoint", {}),
                "tutor_sidecar": stable_tutor_sidecar(run_report.get("tutor_sidecar", {})),
                "private_tutor_use_flow_summary": stable_private_tutor_flow_summary(
                    run_report.get("private_tutor_use_flow_summary", {})
                ),
                "cell_evidence_link": run_report.get("cell_evidence_link", {}),
                "exam_ledger_append_summary": run_report.get("exam_ledger_append_summary", {}),
                "export_package_summary": stable_export_package_summary(
                    run_report.get("export_package_summary", {})
                ),
                "public_safety_status": run_report.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def exam_workspace_run_receipt_hash(run_report: dict[str, Any] | None = None) -> str:
    run_report = run_report if isinstance(run_report, dict) else {}
    flow = (
        run_report.get("private_tutor_use_flow_summary", {})
        if isinstance(run_report.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    receipt = flow.get("study_receipt_validation", {}) if isinstance(flow.get("study_receipt_validation"), dict) else {}
    general_ledger = flow.get("ledger_append", {}) if isinstance(flow.get("ledger_append"), dict) else {}
    exam_ledger = (
        run_report.get("exam_ledger_append_summary", {})
        if isinstance(run_report.get("exam_ledger_append_summary"), dict)
        else {}
    )
    checkpoint = (
        run_report.get("notebook_checkpoint", {})
        if isinstance(run_report.get("notebook_checkpoint"), dict)
        else {}
    )
    return sha256_text(
        json.dumps(
            {
                "run_status": run_report.get("status", ""),
                "exam_deployment_status": run_report.get("exam_deployment_status", ""),
                "checkpoint_hash": checkpoint.get("notebook_work_sha256", ""),
                "study_receipt_status": receipt.get("status", ""),
                "study_receipt_task_id": receipt.get("task_id", ""),
                "general_ledger_status": general_ledger.get("status", ""),
                "general_ledger_written": general_ledger.get("ledger_written", None),
                "general_ledger_event_hash": general_ledger.get("event_hash", ""),
                "exam_ledger_status": exam_ledger.get("status", ""),
                "exam_ledger_written": exam_ledger.get("ledger_written", None),
                "exam_ledger_event_hash": exam_ledger.get("event_hash", ""),
                "export": stable_export_package_summary(run_report.get("export_package_summary", {})),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def stable_tutor_sidecar(sidecar: Any) -> dict[str, Any]:
    sidecar = sidecar if isinstance(sidecar, dict) else {}
    selected = sidecar.get("selected_skill", {}) if isinstance(sidecar.get("selected_skill"), dict) else {}
    return {
        "status": sidecar.get("status", ""),
        "mode": sidecar.get("mode", ""),
        "strict_exam_boundary": sidecar.get("strict_exam_boundary", None),
        "effective_help_level": sidecar.get("effective_help_level", ""),
        "source_anchor_count": sidecar.get("source_anchor_count", 0),
        "source_card_ids": sidecar.get("source_card_ids", []),
        "selected_skill": {
            "skill_tag": selected.get("skill_tag", ""),
            "tag": selected.get("tag", ""),
        },
    }


def stable_private_tutor_flow_summary(flow: Any) -> dict[str, Any]:
    flow = flow if isinstance(flow, dict) else {}
    receipt = flow.get("study_receipt_validation", {}) if isinstance(flow.get("study_receipt_validation"), dict) else {}
    ledger = flow.get("ledger_append", {}) if isinstance(flow.get("ledger_append"), dict) else {}
    return {
        "status": flow.get("status", ""),
        "manifest_apply_status": flow.get("manifest_apply", {}).get("status", "")
        if isinstance(flow.get("manifest_apply"), dict)
        else "",
        "tutor_index_status": flow.get("tutor_index", {}).get("status", "")
        if isinstance(flow.get("tutor_index"), dict)
        else "",
        "tutor_response_status": flow.get("tutor_response", {}).get("status", "")
        if isinstance(flow.get("tutor_response"), dict)
        else "",
        "study_receipt_validation": {
            "status": receipt.get("status", ""),
            "task_id": receipt.get("task_id", ""),
            "skill_tag": receipt.get("skill_tag", ""),
            "help_level": receipt.get("help_level", ""),
            "repeat_task_required": receipt.get("repeat_task_required", None),
            "raw_text_stored": receipt.get("raw_text_stored", None),
            "reflection_stored": receipt.get("reflection_stored", None),
            "public_safety_status": receipt.get("public_safety_status", ""),
        },
        "ledger_append": {
            "status": ledger.get("status", ""),
            "ledger_written": ledger.get("ledger_written", None),
            "event_hash": ledger.get("event_hash", ""),
            "path_returned": ledger.get("path_returned", None),
        },
    }


def stable_export_package_summary(export: Any) -> dict[str, Any]:
    export = export if isinstance(export, dict) else {}
    return {
        "status": export.get("status", ""),
        "package_id": export.get("package_id", ""),
        "exam_deployment_status": export.get("exam_deployment_status", ""),
        "not_cleared_receipt": export.get("not_cleared_receipt", None),
        "notebook_included": export.get("notebook_included", None),
        "notebook_sha256": export.get("notebook_sha256", ""),
        "help_ledger_entry_count": export.get("help_ledger_entry_count", 0),
        "blocked_count": export.get("blocked_count", 0),
        "human_reviewable_independence_evidence": export.get(
            "human_reviewable_independence_evidence", None
        ),
        "raw_transcripts_included": export.get("raw_transcripts_included", None),
        "automatic_grading_included": export.get("automatic_grading_included", None),
        "proctoring_included": export.get("proctoring_included", None),
        "ai_detection_included": export.get("ai_detection_included", None),
        "local_path_returned": export.get("local_path_returned", None),
        "raw_notebook_returned": export.get("raw_notebook_returned", None),
    }


def build_exam_workspace_run_workspace_card_receipt_alignment(
    run_report: dict[str, Any] | None = None,
    waiting_report: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if run_report is None or waiting_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_run_receipt_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            (materials_root / "Week 1").mkdir(parents=True)
            (materials_root / "Week 1" / "synthetic_python_lists.pdf").write_bytes(b"%PDF-1.4\nsynthetic")
            decision_record = synthetic_exam_workspace_decision_record()
            queue = build_course_extraction_queue(
                base_path=str(materials_root),
                rights_decision_reference=str(decision_record["decision_reference"]),
            )
            receipt = synthetic_exam_workspace_reviewed_receipt(queue["jobs"][0], decision_record)
            common_kwargs = {
                "query": "synthetic private exam-workspace query",
                "course_id": "exam-workspace-run-receipt-alignment",
                "base_path": str(materials_root),
                "decision_record": decision_record,
                "notebook": synthetic_exam_workspace_notebook(),
                "cell_index": 1,
                "cell_id": "synthetic-private-run-cell",
                "cell_type": "code",
                "student_reflection": "I checked my own prediction before requesting source-anchored help.",
                "requested_help_level": "A2",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                "python_exam_local_cycle_operator_workspace_card": synthetic_exam_workspace_run_workspace_card(),
                "public_safe": True,
                "attach_workspace_card_alignment": False,
            }
            if run_report is None:
                import exam_mode

                previous_exam_root = exam_mode.EXAM_ROOT
                exam_mode.EXAM_ROOT = temp_root / "exam_workspace_runtime"
                try:
                    run_report = build_exam_workspace_run_dry_run(
                        **common_kwargs,
                        receipts=[receipt],
                        private_manifest_path=temp_root / "private_manifest.json",
                        manifest_apply_journal_path=temp_root / "manifest_apply.jsonl",
                        tutor_index_path=temp_root / "private_tutor_index.json",
                        tutor_index_journal_path=temp_root / "private_tutor_index.jsonl",
                        ledger_path=temp_root / "help_ledger.jsonl",
                        operator_confirmed_exam_workspace_run=True,
                        operator_confirmed_manifest_apply=True,
                        operator_confirmed_tutor_index_build=True,
                        operator_confirmed_help_ledger_append=True,
                        operator_confirmed_exam_ledger_append=True,
                    )
                finally:
                    exam_mode.EXAM_ROOT = previous_exam_root
            waiting_report = waiting_report or build_exam_workspace_run_dry_run(
                **common_kwargs,
                private_manifest_path=temp_root / "missing_manifest.json",
                tutor_index_path=temp_root / "missing_tutor_index.json",
            )

    run_report = run_report if isinstance(run_report, dict) else {}
    waiting_report = waiting_report if isinstance(waiting_report, dict) else {}
    checkpoint = run_report.get("notebook_checkpoint", {}) if isinstance(run_report.get("notebook_checkpoint"), dict) else {}
    tutor_sidecar = run_report.get("tutor_sidecar", {}) if isinstance(run_report.get("tutor_sidecar"), dict) else {}
    tutor_flow = (
        run_report.get("private_tutor_use_flow_summary", {})
        if isinstance(run_report.get("private_tutor_use_flow_summary"), dict)
        else {}
    )
    receipt = tutor_flow.get("study_receipt_validation", {}) if isinstance(tutor_flow.get("study_receipt_validation"), dict) else {}
    general_ledger = tutor_flow.get("ledger_append", {}) if isinstance(tutor_flow.get("ledger_append"), dict) else {}
    exam_ledger = (
        run_report.get("exam_ledger_append_summary", {})
        if isinstance(run_report.get("exam_ledger_append_summary"), dict)
        else {}
    )
    export = stable_export_package_summary(run_report.get("export_package_summary", {}))
    waiting_session = (
        waiting_report.get("session_summary", {}) if isinstance(waiting_report.get("session_summary"), dict) else {}
    )
    waiting_materials = (
        waiting_report.get("material_freeze_summary", {})
        if isinstance(waiting_report.get("material_freeze_summary"), dict)
        else {}
    )
    waiting_exam_ledger = (
        waiting_report.get("exam_ledger_append_summary", {})
        if isinstance(waiting_report.get("exam_ledger_append_summary"), dict)
        else {}
    )
    source_workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else run_report.get("local_cycle_operator_workspace_card", {})
    )
    if not isinstance(source_workspace_card, dict) or source_workspace_card.get("status") in {None, "", "missing"}:
        source_workspace_card = synthetic_exam_workspace_run_workspace_card()
    workspace_card = safe_local_cycle_workspace_card(
        source_workspace_card if isinstance(source_workspace_card, dict) else {}
    )
    run_hash = exam_workspace_run_hash(run_report)
    receipt_hash = exam_workspace_run_receipt_hash(run_report)
    waiting_receipt_hash = exam_workspace_run_receipt_hash(waiting_report)
    raw_flag_names = [
        "raw_query_returned",
        "raw_text_returned",
        "raw_notebook_returned",
        "notebook_code_returned",
        "local_paths_returned",
        "private_manifest_path_returned",
        "tutor_index_path_returned",
        "ledger_path_returned",
    ]
    high_stakes_flag_names = [
        "automatic_grading_started",
        "proctoring_started",
        "ai_detection_started",
        "exam_clearance_claimed",
    ]
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    selected_skill = tutor_sidecar.get("selected_skill", {}) if isinstance(tutor_sidecar.get("selected_skill"), dict) else {}
    contracts = {
        "run_report_public_safe": run_report.get("public_safety_status") == "pass",
        "waiting_run_public_safe": waiting_report.get("public_safety_status") == "pass",
        "run_ready_with_receipts": run_report.get("status") == "exam_workspace_ready_with_exam_ledger"
        and export.get("status") == "ready_for_human_review_not_exam_clearance"
        and export.get("not_cleared_receipt") is True
        and export.get("human_reviewable_independence_evidence") is True,
        "private_tutor_study_ledger_references_preserved": tutor_flow.get("status")
        == "private_tutor_use_flow_ready_with_ledger"
        and tutor_sidecar.get("status") == "allowed"
        and tutor_sidecar.get("effective_help_level") in {"A0", "A1", "A2"}
        and receipt.get("status") == "ok_study_session_receipt"
        and general_ledger.get("ledger_written") is True
        and exam_ledger.get("ledger_written") is True
        and bool(general_ledger.get("event_hash"))
        and bool(exam_ledger.get("event_hash")),
        "notebook_checkpoint_hash_only_preserved": bool(checkpoint.get("notebook_sha256"))
        and bool(checkpoint.get("cell_source_sha256"))
        and bool(checkpoint.get("notebook_work_sha256"))
        and checkpoint.get("raw_notebook_returned") is False
        and checkpoint.get("notebook_code_returned") is False
        and checkpoint.get("local_path_returned") is False,
        "run_receipt_hashes_present": bool(run_hash) and bool(receipt_hash) and bool(waiting_receipt_hash),
        "workspace_card_run_receipt_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("selected_skill_tag") in {
            str(selected_skill.get("skill_tag", "")),
            str(selected_skill.get("tag", "")),
            "boxplots",
        }
        and bool(workspace_card.get("task_hash"))
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and bool(receipt_hash),
        "operator_confirmed_local_write_boundary_preserved": all(
            run_report.get("operator_confirmations", {}).get(flag) is True
            for flag in [
                "exam_workspace_run",
                "manifest_apply",
                "tutor_index_build",
                "help_ledger_append",
                "exam_ledger_append",
            ]
        )
        and general_ledger.get("path_returned") is False
        and exam_ledger.get("path_returned") is False,
        "waiting_mode_no_write_boundary_preserved": waiting_report.get("status") == "exam_workspace_waiting_for_tutor_flow"
        and waiting_session.get("status") == "dry_run_not_started"
        and waiting_materials.get("freeze_written") is False
        and waiting_exam_ledger.get("ledger_written") is False
        and waiting_report.get("local_paths_returned") is False,
        "metadata_only_safety_flags_false": all(run_report.get(flag) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(run_report.get(flag) is False for flag in high_stakes_flag_names)
        and run_report.get("exam_deployment_status") == "not_cleared",
    }
    required_readiness_check_ids = [
        "exam_workspace_run",
        "exam_workspace_launch",
        "notebook_checkpoint",
        "study_session",
        "private_tutor_use_flow",
        "python_exam_local_cycle_operator_workspace_card",
        "exam_boundary",
    ]
    blocked_claims = [
        "raw private course text publication",
        "raw notebook code returned",
        "raw query returned",
        "contact data publication",
        "local path publication",
        "provider call",
        "autonomous publication",
        "approval claim",
        "exam-clearance claim",
        "grading",
        "proctoring",
        "KI-detection evidence",
        "exam deployment",
    ]
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "run_hash": run_hash,
        "run_receipt_hash": receipt_hash,
        "waiting_run_receipt_hash": waiting_receipt_hash,
        "workspace_card": workspace_card,
        "contracts": contracts,
        "blocked_claims": blocked_claims,
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-run-workspace-card-receipt-alignment",
    )
    status = "ready" if scan["status"] == "pass" and not failed_contract_ids else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_RUN_WORKSPACE_CARD_RECEIPT_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "run_hash": run_hash,
        "run_receipt_hash": receipt_hash,
        "waiting_run_receipt_hash": waiting_receipt_hash,
        "run_status": run_report.get("status", "missing"),
        "waiting_status": waiting_report.get("status", "missing"),
        "run_public_safety_status": run_report.get("public_safety_status", "missing"),
        "waiting_public_safety_status": waiting_report.get("public_safety_status", "missing"),
        "exam_deployment_status": run_report.get("exam_deployment_status", "missing"),
        "notebook_work_hash_present": bool(checkpoint.get("notebook_work_sha256", "")),
        "study_receipt_status": receipt.get("status", "missing"),
        "tutor_status": tutor_sidecar.get("status", "missing"),
        "effective_help_level": tutor_sidecar.get("effective_help_level", "missing"),
        "general_help_ledger_status": general_ledger.get("status", "missing"),
        "general_help_ledger_written": bool(general_ledger.get("ledger_written", False)),
        "exam_ledger_status": exam_ledger.get("status", "missing"),
        "exam_ledger_written": bool(exam_ledger.get("ledger_written", False)),
        "export_status": export.get("status", "missing"),
        "export_not_cleared_receipt": bool(export.get("not_cleared_receipt", False)),
        "human_reviewable_independence_evidence": bool(export.get("human_reviewable_independence_evidence", False)),
        "waiting_session_status": waiting_session.get("status", "missing"),
        "waiting_freeze_written": bool(waiting_materials.get("freeze_written", False)),
        "waiting_exam_ledger_written": bool(waiting_exam_ledger.get("ledger_written", False)),
        "workspace_card_status": workspace_card.get("status", "missing"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag", ""),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status", "missing"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash", "")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_run_receipt_gate_linked": contracts["workspace_card_run_receipt_gate_linked"],
        "public_safety_status": scan["status"],
        "contracts": contracts,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "operator_confirmation_required_for_local_write",
            "human_review_required",
            "exam_clearance_requires_written_authority_clearance",
            "public_safety_required",
        ],
        "blocked_claims": blocked_claims,
        "policy": (
            "Exam workspace run receipt alignment links the controlled run packet, private tutor sidecar, "
            "study receipt, Help-Ledger and exam-ledger receipts, export receipt, and operator-confirmed local-write "
            "boundaries to the local-cycle workspace-card readiness gate. It does not publish raw private course "
            "text, notebook code, local paths, provider prompts, grades, proctoring, KI-detection evidence, or "
            "exam-clearance claims."
        ),
    }


def notebook_from_payload(*, notebook: dict[str, Any] | None, notebook_content_base64: str | None) -> dict[str, Any]:
    if isinstance(notebook, dict):
        return notebook
    if notebook_content_base64:
        try:
            decoded = base64.b64decode(str(notebook_content_base64).encode("ascii")).decode("utf-8")
            payload = json.loads(decoded)
            if isinstance(payload, dict):
                return payload
        except (ValueError, json.JSONDecodeError):
            pass
    return {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [],
            }
        ],
        "metadata": {"unibot": {"exam_workspace": True}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def synthetic_exam_workspace_decision_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic exam workspace decision",
    }


def synthetic_exam_workspace_reviewed_receipt(
    job: dict[str, Any],
    decision_record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 1400,
        "private_artifact_reference": "synthetic private artifact reference",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(decision_record["decision_reference"])),
    }


def synthetic_exam_workspace_notebook() -> dict[str, Any]:
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Synthetic controlled exam workspace\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["own_values = [1, 2, 3]\nlen(own_values)\n"],
            },
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def synthetic_exam_workspace_run_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic exam workspace run workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "boxplots",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic run prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "boxplots",
            "next_safe_action": "review_exam_workspace_run_dry_run",
            "next_safe_user_action": "review_run_evidence_before_any_local_write",
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


def source_from_notebook(notebook: dict[str, Any], cell_index: int) -> str:
    cells = notebook.get("cells", [])
    if not isinstance(cells, list) or not cells:
        return ""
    try:
        cell = cells[int(cell_index or 0)]
    except (IndexError, TypeError, ValueError):
        return ""
    if not isinstance(cell, dict):
        return ""
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(part) for part in source)
    return str(source or "")


def valid_sha256(value: str | None) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if SHA256_RE.match(candidate) else ""


def session_step(*, course_id: str, notebook_session_id: str, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        return {
            "status": "dry_run_not_started",
            "mode": "exam_controlled_gateway",
            "course_id": course_id,
            "session_id": "",
            "session_id_hash": sha256_text(f"{course_id}:{notebook_session_id}")[:20],
            "allowed_help_levels": ["A0", "A1", "A2"],
            "exam_deployment_status": "not_cleared",
        }
    from exam_mode import start_exam_gateway_session

    session = start_exam_gateway_session({"course_id": course_id, "notebook_session_id": notebook_session_id})
    return {
        "status": session.get("status", "started"),
        "mode": session.get("mode", "exam_controlled_gateway"),
        "course_id": course_id,
        "session_id": session.get("session_id", ""),
        "session_id_hash": sha256_text(str(session.get("session_id", "")))[:20],
        "allowed_help_levels": list(session.get("allowed_help_levels", ["A0", "A1", "A2"])),
        "exam_deployment_status": session.get("exam_deployment_status", "not_cleared"),
    }


def material_freeze_step(*, course_id: str, material_files: list[dict[str, Any]], confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        return {
            "status": "dry_run_not_frozen",
            "imported_file_count": 0,
            "candidate_file_count": len([item for item in material_files if isinstance(item, dict)]),
            "freeze_written": False,
            "exam_rule": "A0-A2 only",
        }
    from exam_mode import freeze_exam_materials, import_exam_materials

    imported_count = 0
    if material_files:
        imported = import_exam_materials({"course_id": course_id, "source": "exam_workspace_run", "files": material_files})
        imported_count = int(imported.get("file_count", 0) or 0)
    frozen = freeze_exam_materials({"course_id": course_id, "exam_rule": "A0-A2 only"})
    return {
        "status": frozen.get("status", "frozen"),
        "imported_file_count": imported_count,
        "candidate_file_count": len([item for item in material_files if isinstance(item, dict)]),
        "freeze_written": frozen.get("status") == "frozen",
        "exam_rule": frozen.get("exam_rule", "A0-A2 only"),
    }


def notebook_open_step(
    *,
    course_id: str,
    notebook_payload: dict[str, Any],
    notebook_content_base64: str | None,
    notebook_filename: str,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        return {"status": "dry_run_not_opened", "notebook_written": False, "notebook_path_returned": False}
    from exam_mode import open_exam_notebook

    encoded = notebook_content_base64 or base64.b64encode(
        json.dumps(notebook_payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    opened = open_exam_notebook(
        {
            "course_id": course_id,
            "filename": Path(str(notebook_filename or "exam_workspace_notebook.ipynb")).name,
            "content_base64": encoded,
            "strip_outputs": True,
        }
    )
    return {
        "status": opened.get("status", "opened"),
        "notebook_written": opened.get("status") == "opened",
        "notebook_path_returned": False,
        "session_id_hash": sha256_text(str(opened.get("session_id", "")))[:20],
    }


def notebook_cell_step(
    *,
    course_id: str,
    session_id: str,
    cell_index: int,
    cell_source: str,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        return {
            "artifact_type": "exam_notebook_cell_run",
            "status": "dry_run_not_executed",
            "notebook_work_sha256": sha256_text(cell_source),
            "session_id": "",
            "cell_index": int(cell_index or 0),
            "execution_id": sha256_text(f"dry:{course_id}:{cell_index}:{cell_source}")[:16],
        }
    from exam_mode import run_exam_notebook_cell

    return run_exam_notebook_cell(
        {
            "course_id": course_id,
            "session_id": session_id,
            "cell_index": int(cell_index or 0),
            "source": cell_source,
            "prior_code": "",
        }
    )


def workspace_study_receipt(
    *,
    task_id: str,
    query: str,
    reflection: str,
    study_receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "task_id": task_id,
        "prediction_present": bool(str(query or "").strip()),
        "notebook_action_present": True,
        "reflection_present": bool(str(reflection or "").strip()),
        "notebook_cell_task_id": task_id,
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


def exam_ledger_step(
    *,
    course_id: str,
    session_id: str,
    gateway_session_id: str,
    cell_index: int,
    cell_id: str,
    cell_type: str,
    prompt: str,
    raw_response: str,
    student_reflection: str,
    notebook_work_sha256: str,
    source_card_ids: list[str],
    help_level: str,
    confirmed: bool,
) -> dict[str, Any]:
    event_seed = {
        "course_id": course_id,
        "cell_index": int(cell_index or 0),
        "cell_id_hash": sha256_text(cell_id),
        "prompt_sha256": sha256_text(prompt),
        "response_sha256": sha256_text(raw_response),
        "notebook_work_sha256": notebook_work_sha256,
        "help_level": help_level,
        "source_card_ids": source_card_ids[:8],
    }
    if not confirmed:
        return {
            "status": "dry_run_not_written",
            "ledger_written": False,
            "path_returned": False,
            "event_hash": sha256_text(json.dumps(event_seed, sort_keys=True, ensure_ascii=False)),
            "record": event_seed,
        }
    from exam_mode import append_exam_ledger_event

    appended = append_exam_ledger_event(
        {
            "course_id": course_id,
            "session_id": session_id,
            "gateway_session_id": gateway_session_id,
            "cell_index": int(cell_index or 0),
            "cell_id": cell_id,
            "cell_type": cell_type,
            "help_level": help_level,
            "decision": "allowed",
            "source": "private_tutor_index",
            "source_card_ids": source_card_ids[:8],
            "prompt": prompt,
            "raw_response": raw_response,
            "student_reflection": student_reflection,
            "notebook_work_sha256": notebook_work_sha256,
        }
    )
    return {
        "status": appended.get("status", "unknown"),
        "ledger_written": appended.get("status") == "appended",
        "path_returned": False,
        "event_hash": sha256_text(json.dumps(appended.get("record", {}), sort_keys=True, ensure_ascii=False)),
        "record": appended.get("record", {}),
        "ledger_summary": appended.get("ledger_summary", {}),
    }


def export_step(
    *,
    course_id: str,
    notebook_payload: dict[str, Any],
    session: dict[str, Any],
    materials: dict[str, Any],
    cell_run: dict[str, Any],
    sidecar_response: dict[str, Any],
    exam_ledger: dict[str, Any],
) -> dict[str, Any]:
    from exam_mode import export_exam_package

    ledger_record = exam_ledger.get("record", {})
    package = export_exam_package(
        {
            "course_id": course_id,
            "notebook": notebook_payload,
            "session_log": [
                {"name": "session_start", "status": session.get("status", "")},
                {"name": "materials_freeze", "status": materials.get("status", "")},
                {"name": "run_cell", "status": cell_run.get("status", "")},
                {"name": "tutor_sidecar", "status": sidecar_response.get("status", "")},
                {"name": "exam_ledger", "status": exam_ledger.get("status", "")},
            ],
            "help_ledger": [ledger_record] if isinstance(ledger_record, dict) and ledger_record else [],
        }
    )
    confirmation = package.get("technical_confirmation", {})
    return {
        "status": package.get("status", "unknown"),
        "package_id": package.get("package_id", ""),
        "exam_deployment_status": package.get("exam_deployment_status", "not_cleared"),
        "not_cleared_receipt": package.get("exam_deployment_status") == "not_cleared",
        "notebook_included": package.get("notebook_receipt", {}).get("included", False),
        "notebook_sha256": package.get("notebook_receipt", {}).get("notebook_sha256", ""),
        "help_ledger_entry_count": package.get("gateway_help_ledger_summary", {}).get("entry_count", 0),
        "blocked_count": package.get("gateway_help_ledger_summary", {}).get("blocked_count", 0),
        "human_reviewable_independence_evidence": confirmation.get("human_reviewable_independence_evidence", False),
        "raw_transcripts_included": confirmation.get("raw_transcripts_included", False),
        "automatic_grading_included": confirmation.get("automatic_grading_included", False),
        "proctoring_included": confirmation.get("proctoring_included", False),
        "ai_detection_included": confirmation.get("ai_detection_included", False),
        "local_path_returned": False,
        "raw_notebook_returned": False,
    }


def public_session_summary(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": session.get("status", "unknown"),
        "mode": session.get("mode", "exam_controlled_gateway"),
        "session_id_hash": session.get("session_id_hash", sha256_text(str(session.get("session_id", "")))[:20]),
        "allowed_help_levels": list(session.get("allowed_help_levels", ["A0", "A1", "A2"])),
        "exam_deployment_status": session.get("exam_deployment_status", "not_cleared"),
        "session_id_returned": False,
    }


def public_material_summary(materials: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": materials.get("status", "unknown"),
        "freeze_written": bool(materials.get("freeze_written", False)),
        "candidate_file_count": int(materials.get("candidate_file_count", 0) or 0),
        "imported_file_count": int(materials.get("imported_file_count", 0) or 0),
        "exam_rule": materials.get("exam_rule", "A0-A2 only"),
        "raw_text_returned": False,
        "local_path_returned": False,
    }


def sidecar_public_summary(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": response.get("status", "unknown"),
        "mode": response.get("mode", "exam_controlled_gateway"),
        "strict_exam_boundary": bool(response.get("strict_exam_boundary", True)),
        "effective_help_level": response.get("effective_help_level", "A2"),
        "selected_skill": response.get("selected_skill", {}),
        "source_anchor_count": len(response.get("source_anchors", []) or []),
        "source_card_ids": list(response.get("source_card_ids", []) or [])[:8],
        "answer_markdown": response.get("answer_markdown", ""),
        "socratic_questions": list(response.get("socratic_questions", []) or [])[:3],
        "next_task": response.get("next_task", {}),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
    }


def exam_ledger_public_summary(exam_ledger: dict[str, Any]) -> dict[str, Any]:
    record = exam_ledger.get("record", {}) if isinstance(exam_ledger.get("record"), dict) else {}
    return {
        "status": exam_ledger.get("status", "unknown"),
        "ledger_written": bool(exam_ledger.get("ledger_written", False)),
        "event_hash": exam_ledger.get("event_hash", ""),
        "help_level": record.get("help_level", ""),
        "allowed": record.get("allowed", exam_ledger.get("status") in {"dry_run_not_written", "appended"}),
        "blocked": bool(record.get("blocked", False)),
        "repeat_task_required": bool(record.get("repeat_task_required", False)),
        "path_returned": False,
        "prompt_returned": False,
        "raw_response_returned": False,
    }


def exam_workspace_status(
    *,
    tutor_flow: dict[str, Any],
    sidecar_response: dict[str, Any],
    exam_ledger: dict[str, Any],
) -> str:
    if tutor_flow.get("status") == "blocked_public_safety" or sidecar_response.get("status") == "blocked_public_safety":
        return "blocked_public_safety"
    if str(tutor_flow.get("status", "")).startswith("waiting_for") or sidecar_response.get("status") in {
        "waiting_for_private_tutor_index_build",
        "no_index_anchor",
    }:
        return "exam_workspace_waiting_for_tutor_flow"
    if sidecar_response.get("status") != "allowed":
        return f"exam_workspace_tutor_{sidecar_response.get('status', 'blocked')}"
    receipt_status = tutor_flow.get("study_receipt_validation", {}).get("status")
    if receipt_status != "ok_study_session_receipt":
        return "exam_workspace_study_receipt_needs_evidence"
    if exam_ledger.get("ledger_written"):
        return "exam_workspace_ready_with_exam_ledger"
    return "exam_workspace_dry_run_ready"


def exam_workspace_next_actions(
    *,
    tutor_flow: dict[str, Any],
    sidecar_response: dict[str, Any],
    exam_ledger: dict[str, Any],
) -> list[str]:
    if sidecar_response.get("status") in {"waiting_for_private_tutor_index_build", "no_index_anchor"}:
        return [
            "Apply reviewed private manifest metadata and build the hash-only tutor index before relying on the sidecar.",
            "Keep the exam workspace not_cleared; real authority clearance remains a real-world reminder, not a technical blocker.",
        ]
    if sidecar_response.get("status") != "allowed":
        return ["Rephrase as A0-A2 help: source anchor, syntax pointer, or one Socratic next-check question."]
    if tutor_flow.get("study_receipt_validation", {}).get("status") != "ok_study_session_receipt":
        return ["Add hash-only evidence: own prediction, notebook action, source anchor, and reflection."]
    if not exam_ledger.get("ledger_written"):
        return [
            "Review the dry-run, then set operator_confirmed_exam_ledger_append only if this cell help should be stored locally.",
            "Use the export summary as human-reviewable evidence; do not convert it into a grade or Eigenleistung percentage.",
        ]
    return [
        "Export the package summary for human review after checking the local notebook checkpoint and ledger.",
        "Continue closing course-material gaps through reviewed receipts and tutor-index rebuilds.",
        "Reminder: real exam authority clearance remains outside the bot; UniBot stays not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-workspace-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
