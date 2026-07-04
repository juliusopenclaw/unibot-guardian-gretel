from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_operator_run import build_exam_workspace_operator_run_dry_run
from .materials import build_material_manifest, sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_index import build_private_tutor_index_dry_run


EXAM_WORKSPACE_SESSION_CONSOLE_SCHEMA_VERSION = "unibot-exam-workspace-session-console-v1"
EXAM_WORKSPACE_SESSION_CONSOLE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-session-console-release-review-board-claim-alignment-v1"
)
SESSION_CONSOLE_ENDPOINT = "/api/unibot/exam-workspace/session-console"


def build_exam_workspace_session_console(
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
    previous_console_receipts: list[dict[str, Any]] | None = None,
    operator_confirmed_checkpoint_store: bool = False,
    operator_confirmed_exam_workspace_run: bool = False,
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    operator_confirmed_exam_ledger_append: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    skill_focus = str(selected_skill_tag or focus_query or query or "").strip()
    local_cycle_workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    operator = build_exam_workspace_operator_run_dry_run(
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
        focus_query=skill_focus,
        query=skill_focus,
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
        operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
        operator_confirmed_exam_workspace_run=operator_confirmed_exam_workspace_run,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        operator_confirmed_help_ledger_append=operator_confirmed_help_ledger_append,
        operator_confirmed_exam_ledger_append=operator_confirmed_exam_ledger_append,
        public_safe=public_safe,
    )
    console = session_console_view(operator=operator, repeat_run_index=repeat_run_index)
    receipt = session_console_receipt(
        course_id=safe_id,
        operator=operator,
        console=console,
        repeat_run_index=repeat_run_index,
        previous_console_receipts=previous_console_receipts or [],
    )
    report = {
        "schema_version": EXAM_WORKSPACE_SESSION_CONSOLE_SCHEMA_VERSION,
        "artifact_type": "exam_workspace_session_console",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": session_console_status(operator),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Exam Workspace Session Console. It summarizes the selected skill, workspace status, hash-only notebook "
            "checkpoint, A0-A2 tutor state, Help-Ledger preview, export receipt, and open operator confirmations. "
            "It supports repeated dry-runs for the same skill, but never returns raw queries, course raw text, "
            "notebook code, local paths, values, final interpretations, grading, proctoring, AI detection, or "
            "exam clearance."
        ),
        "session_console": console,
        "session_console_markdown": session_console_markdown(console),
        "session_console_receipt": receipt,
        "operator_summary": operator_summary(operator),
        "operator_confirmation_matrix": operator.get("operator_confirmation_matrix", {}),
        "local_cycle_operator_workspace_card": safe_local_cycle_workspace_card(local_cycle_workspace_card),
        "local_cycle_operator_workspace_card_source": safe_local_cycle_workspace_card_source(local_cycle_workspace_card),
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; die Session Console bleibt not_cleared."
        ),
        "next_actions": session_console_next_actions(operator),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_exam_workspace_session_console_release_claim_alignment(
    ready_report: dict[str, Any] | None = None,
    repeat_report: dict[str, Any] | None = None,
    workspace_card_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ready_report is None or repeat_report is None or workspace_card_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_session_console_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            manifest_path = temp_root / "private_manifest.json"
            index_path = temp_root / "private_tutor_index.json"
            index_journal_path = temp_root / "index_journal.jsonl"
            write_synthetic_session_console_fixture(materials_root)
            write_synthetic_session_console_manifest(manifest_path)
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )
            workspace_card_report = workspace_card_report or synthetic_session_console_workspace_card()
            common_kwargs = {
                "base_path": str(materials_root),
                "review_policy": "local_private_tutor",
                "decision_record": synthetic_session_console_decision_record(),
                "private_manifest_path": manifest_path,
                "tutor_index_path": index_path,
                "tutor_index_journal_path": index_journal_path,
                "selected_skill_tag": "pandas",
                "focus_query": "pandas groupby",
                "query": "synthetic private session-console question",
                "requested_help_level": "A2",
                "student_reflection": "I checked my own prediction before asking for the next hint.",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                "python_exam_local_cycle_operator_workspace_card": workspace_card_report,
                "public_safe": True,
            }
            ready_report = ready_report or build_exam_workspace_session_console(
                **common_kwargs,
                cell_source="own_groupby_checkpoint = None\n# local checkpoint only\n",
                cell_index=1,
                cell_id="synthetic-private-session-console-cell",
            )
            repeat_report = repeat_report or build_exam_workspace_session_console(
                **common_kwargs,
                cell_source="# final answer: complete solution\n",
                cell_index=2,
                cell_id="synthetic-private-session-console-repeat-cell",
                repeat_run_index=2,
                previous_console_receipts=[ready_report["session_console_receipt"]],
            )

    sections = [
        {
            "section_id": "session_console_receipt_trace",
            "summary_claim": "session console summarizes selected skill, workspace state, and receipt evidence without raw private data",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "exam_workspace_session_console",
                "exam_workspace_operator_run",
                "exam_workspace_run_history",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "workspace_card_reflection_trace",
            "summary_claim": "session console preserves local-cycle workspace-card and reflection evidence as hash/status metadata",
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "exam_workspace_session_console",
                "python_exam_local_cycle_operator_workspace_card",
                "study_session",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "operator_boundary_trace",
            "summary_claim": "session console links back to operator-run dry-run confirmations and keeps local writes unconfirmed by default",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "exam_workspace_session_console",
                "exam_workspace_operator_run",
                "python_exam_local_cycle_operator_workspace_card",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "session console does not publish notebooks, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "exam_workspace_session_console",
                "external_decision_state",
                "evaluation_packet",
                "exam_boundary",
            ],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    console = ready_report.get("session_console", {}) if isinstance(ready_report.get("session_console"), dict) else {}
    selected = console.get("selected_skill", {}) if isinstance(console.get("selected_skill"), dict) else {}
    workspace = console.get("workspace_status", {}) if isinstance(console.get("workspace_status"), dict) else {}
    checkpoint = (
        console.get("notebook_checkpoint", {}) if isinstance(console.get("notebook_checkpoint"), dict) else {}
    )
    tutor = console.get("tutor_state", {}) if isinstance(console.get("tutor_state"), dict) else {}
    ledger = (
        console.get("help_ledger_preview", {}) if isinstance(console.get("help_ledger_preview"), dict) else {}
    )
    export = console.get("export_receipt", {}) if isinstance(console.get("export_receipt"), dict) else {}
    confirmations = (
        console.get("operator_confirmations", {}) if isinstance(console.get("operator_confirmations"), dict) else {}
    )
    receipt = (
        ready_report.get("session_console_receipt", {})
        if isinstance(ready_report.get("session_console_receipt"), dict)
        else {}
    )
    operator_summary_report = (
        ready_report.get("operator_summary", {}) if isinstance(ready_report.get("operator_summary"), dict) else {}
    )
    workspace_card = (
        ready_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(ready_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    workspace_card_source = (
        ready_report.get("local_cycle_operator_workspace_card_source", {})
        if isinstance(ready_report.get("local_cycle_operator_workspace_card_source"), dict)
        else {}
    )
    repeat_console = (
        repeat_report.get("session_console", {}) if isinstance(repeat_report.get("session_console"), dict) else {}
    )
    repeat_checkpoint = (
        repeat_console.get("notebook_checkpoint", {})
        if isinstance(repeat_console.get("notebook_checkpoint"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
        "raw run history returned",
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
    markdown = str(ready_report.get("session_console_markdown", ""))
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "console_public_safe": ready_report.get("public_safety_status") == "pass",
        "repeat_public_safe": repeat_report.get("public_safety_status") == "pass",
        "session_console_receipt_hash_only_ready": ready_report.get("status") == "exam_workspace_session_console_ready"
        and console.get("status") == "ready_dry_run"
        and receipt.get("status") == "session_console_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_hash"))
        and bool(receipt.get("operator_receipt_id"))
        and receipt.get("not_cleared_receipt") is True
        and receipt.get("raw_query_returned") is False
        and receipt.get("raw_text_returned") is False
        and receipt.get("raw_cell_returned") is False
        and receipt.get("notebook_code_returned") is False
        and receipt.get("local_paths_returned") is False
        and checkpoint.get("status") == "notebook_checkpoint_ready"
        and bool(checkpoint.get("notebook_work_sha256")),
        "operator_run_receipt_linked": operator_summary_report.get("artifact_type") == "exam_workspace_operator_run_dry_run"
        and operator_summary_report.get("status") == "exam_workspace_operator_dry_run_ready"
        and operator_summary_report.get("receipt_id") == receipt.get("operator_receipt_id")
        and operator_summary_report.get("not_cleared_receipt") is True
        and confirmations.get("status") == "all_steps_dry_run"
        and confirmations.get("local_writes_requested") is False
        and int(confirmations.get("confirmed_count", -1) or 0) == 0,
        "workspace_card_and_reflection_preserved": workspace_card.get("status")
        == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("selected_skill_tag") == selected.get("skill_tag")
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card_source.get("artifact_type") == "python_exam_local_cycle_operator_workspace_card"
        and workspace_card_source.get("schema_version")
        == "unibot-python-exam-local-cycle-operator-workspace-card-v1"
        and tutor.get("study_receipt_status") == "ok_study_session_receipt"
        and tutor.get("tutor_status") == "allowed"
        and tutor.get("allowed_help_boundary") == "A0-A2"
        and ledger.get("status") == "preview_ready"
        and ledger.get("raw_help_text_returned") is False,
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card_source.get("artifact_type") == "python_exam_local_cycle_operator_workspace_card"
        and workspace_card_source.get("schema_version")
        == "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "repeat_task_blocks_console_ready": repeat_report.get("status")
        == "exam_workspace_session_console_repeat_task_required"
        and repeat_console.get("status") == "repeat_task_required"
        and repeat_checkpoint.get("status") == "notebook_checkpoint_repeat_task_required",
        "public_outputs_hide_private_console_data": ready_report.get("raw_query_returned") is False
        and ready_report.get("raw_text_returned") is False
        and ready_report.get("raw_cell_returned") is False
        and ready_report.get("raw_notebook_returned") is False
        and ready_report.get("notebook_code_returned") is False
        and ready_report.get("local_paths_returned") is False
        and "never returns" in boundary
        and "raw queries" in boundary
        and "notebook code" in boundary
        and "local paths" in boundary
        and "Exam Deployment: not_cleared" in markdown,
        "high_stakes_actions_not_started": ready_report.get("automatic_grading_started") is False
        and ready_report.get("proctoring_started") is False
        and ready_report.get("ai_detection_started") is False
        and ready_report.get("exam_clearance_claimed") is False
        and ready_report.get("exam_deployment_status") == "not_cleared"
        and workspace.get("exam_deployment_status") == "not_cleared"
        and selected.get("raw_source_text_returned") is False
        and export.get("raw_export_returned") is False,
        "not_cleared_receipt_present": receipt.get("not_cleared_receipt") is True
        and export.get("not_cleared_receipt") is True
        and ready_report.get("exam_deployment_status") == "not_cleared"
        and ready_report.get("exam_clearance_claimed") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "ready_status": ready_report.get("status"),
        "repeat_status": repeat_report.get("status"),
        "selected_skill_tag": selected.get("skill_tag"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-session-console-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_SESSION_CONSOLE_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "console_status": ready_report.get("status"),
        "console_public_safety_status": ready_report.get("public_safety_status"),
        "repeat_status": repeat_report.get("status"),
        "repeat_public_safety_status": repeat_report.get("public_safety_status"),
        "exam_deployment_status": ready_report.get("exam_deployment_status"),
        "session_console_status": console.get("status"),
        "selected_skill_tag": selected.get("skill_tag"),
        "workspace_status": workspace.get("workspace_run_status"),
        "operator_status": operator_summary_report.get("status"),
        "operator_receipt_id": receipt.get("operator_receipt_id"),
        "receipt_status": receipt.get("status"),
        "receipt_not_cleared": bool(receipt.get("not_cleared_receipt", False)),
        "receipt_hash_present": bool(receipt.get("receipt_hash")),
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_hash_present": bool(checkpoint.get("notebook_work_sha256")),
        "tutor_status": tutor.get("tutor_status"),
        "study_receipt_status": tutor.get("study_receipt_status"),
        "help_ledger_preview_status": ledger.get("status"),
        "export_status": export.get("status"),
        "export_not_cleared_receipt": bool(export.get("not_cleared_receipt", False)),
        "confirmation_status": confirmations.get("status"),
        "confirmed_count": confirmations.get("confirmed_count", 0),
        "write_step_count": confirmations.get("write_step_count", 0),
        "local_writes_requested": bool(confirmations.get("local_writes_requested", False)),
        "reflection_status": tutor.get("study_receipt_status"),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", False)),
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
            "Exam workspace session console is a status-and-receipt surface for repeated dry-runs. It may show "
            "hashes, counts, selected-skill metadata, local-cycle workspace-card status, and reflection receipt "
            "state, but it does not publish raw notebook/query data, perform unconfirmed writes, grade, proctor, "
            "detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


def session_console_status(operator: dict[str, Any]) -> str:
    status = str(operator.get("status", "unknown"))
    if status == "exam_workspace_operator_dry_run_ready":
        return "exam_workspace_session_console_ready"
    if status == "exam_workspace_operator_ready_with_confirmed_local_writes":
        return "exam_workspace_session_console_ready_with_confirmed_local_writes"
    if status == "exam_workspace_operator_repeat_task_required":
        return "exam_workspace_session_console_repeat_task_required"
    if status == "exam_workspace_operator_waiting_for_required_evidence":
        return "exam_workspace_session_console_waiting_for_required_evidence"
    return "exam_workspace_session_console_review_required"


def session_console_view(
    *,
    operator: dict[str, Any],
    repeat_run_index: int,
    local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = operator.get("dry_run_receipt", {}) if isinstance(operator.get("dry_run_receipt"), dict) else {}
    coverage = operator.get("coverage_summary", {}) if isinstance(operator.get("coverage_summary"), dict) else {}
    start = coverage.get("start_point", {}) if isinstance(coverage.get("start_point"), dict) else {}
    checkpoint = operator.get("local_notebook_checkpoint", {}) if isinstance(operator.get("local_notebook_checkpoint"), dict) else {}
    workspace = operator.get("exam_workspace_run_summary", {}) if isinstance(operator.get("exam_workspace_run_summary"), dict) else {}
    ledger = operator.get("help_ledger_preview", {}) if isinstance(operator.get("help_ledger_preview"), dict) else {}
    export = operator.get("export_receipt", {}) if isinstance(operator.get("export_receipt"), dict) else {}
    confirmations = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    steps = confirmations.get("steps", {}) if isinstance(confirmations.get("steps"), dict) else {}
    open_steps = [key for key, step in steps.items() if isinstance(step, dict) and not step.get("confirmed")]
    workspace_card = safe_local_cycle_workspace_card(local_cycle_operator_workspace_card or {})
    return {
        "title": "Exam Workspace Session Console",
        "status": console_view_status(operator),
        "mode": "exam_controlled_gateway",
        "exam_deployment_status": "not_cleared",
        "selected_skill": {
            "skill_tag": receipt.get("selected_skill_tag", start.get("skill_tag", "")),
            "start_point_status": receipt.get("start_point_status", start.get("status", "unknown")),
            "source_anchor_count": start.get("source_anchor_count", 0),
            "raw_source_text_returned": False,
        },
        "workspace_status": {
            "operator_status": operator.get("status", "unknown"),
            "launch_status": operator.get("launch_status", "unknown"),
            "workspace_run_status": workspace.get("status", "unknown"),
            "session_status": workspace.get("session_status", "dry_run_not_started"),
            "exam_deployment_status": "not_cleared",
        },
        "notebook_checkpoint": {
            "status": checkpoint.get("status", "not_provided"),
            "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
            "checkpoint_journal_written": bool(checkpoint.get("checkpoint_journal_written", False)),
            "raw_cell_returned": False,
            "notebook_code_returned": False,
        },
        "tutor_state": {
            "tutor_status": workspace.get("tutor_status", "unknown"),
            "effective_help_level": receipt.get("effective_help_level", ledger.get("help_level", "A2")),
            "study_receipt_status": receipt.get("study_receipt_status", workspace.get("study_receipt_status", "unknown")),
            "allowed_help_boundary": "A0-A2",
            "automatic_grading_started": False,
        },
        "help_ledger_preview": {
            "status": ledger.get("status", "unknown"),
            "help_level": ledger.get("help_level", "A2"),
            "general_help_ledger_written": bool(ledger.get("general_help_ledger_written", False)),
            "exam_ledger_written": bool(ledger.get("exam_ledger_written", False)),
            "event_hash": ledger.get("event_hash", ""),
            "raw_help_text_returned": False,
        },
        "local_cycle_operator_workspace_card": workspace_card,
        "export_receipt": {
            "status": export.get("status", "unknown"),
            "package_id": export.get("package_id", ""),
            "not_cleared_receipt": bool(export.get("not_cleared_receipt", True)),
            "human_reviewable_independence_evidence": bool(export.get("human_reviewable_independence_evidence", False)),
            "raw_export_returned": False,
        },
        "operator_confirmations": {
            "status": confirmations.get("status", "unknown"),
            "confirmed_count": confirmations.get("confirmed_count", 0),
            "write_step_count": confirmations.get("write_step_count", 0),
            "open_steps": open_steps,
            "local_writes_requested": bool(confirmations.get("local_writes_requested", False)),
            "default_policy": confirmations.get("default_policy", "dry_run_until_individual_operator_confirmation"),
        },
        "repeat_dry_run": {
            "supported": True,
            "repeat_run_index": max(1, int(repeat_run_index or 1)),
            "same_skill_repeat_allowed": True,
            "local_write_default": False,
        },
    }


def console_view_status(operator: dict[str, Any]) -> str:
    status = session_console_status(operator)
    if status == "exam_workspace_session_console_ready":
        return "ready_dry_run"
    if status == "exam_workspace_session_console_ready_with_confirmed_local_writes":
        return "ready_with_confirmed_local_writes"
    if status == "exam_workspace_session_console_repeat_task_required":
        return "repeat_task_required"
    if status == "exam_workspace_session_console_waiting_for_required_evidence":
        return "waiting_for_required_evidence"
    return "review_required"


def session_console_receipt(
    *,
    course_id: str,
    operator: dict[str, Any],
    console: dict[str, Any],
    repeat_run_index: int,
    previous_console_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    operator_receipt = operator.get("dry_run_receipt", {}) if isinstance(operator.get("dry_run_receipt"), dict) else {}
    selected = console.get("selected_skill", {}) if isinstance(console.get("selected_skill"), dict) else {}
    checkpoint = console.get("notebook_checkpoint", {}) if isinstance(console.get("notebook_checkpoint"), dict) else {}
    workspace_card = console.get("local_cycle_operator_workspace_card", {}) if isinstance(console.get("local_cycle_operator_workspace_card"), dict) else {}
    workspace_card_hash = (
        str(workspace_card.get("help_ledger_preview_hash", ""))
        or str(workspace_card.get("task_hash", ""))
        or str(workspace_card.get("checkpoint_hash", ""))
        or str(workspace_card.get("status", ""))
    )
    previous_hashes = [
        str(item.get("receipt_hash", item.get("receipt_id", "")))
        for item in previous_console_receipts
        if isinstance(item, dict)
    ][:12]
    seed = {
        "course_id": course_id,
        "skill_tag": selected.get("skill_tag", ""),
        "checkpoint_hash": checkpoint.get("notebook_work_sha256", ""),
        "operator_receipt_id": operator_receipt.get("receipt_id", ""),
        "workspace_card_hash": workspace_card_hash,
        "repeat_run_index": max(1, int(repeat_run_index or 1)),
        "previous_hashes": previous_hashes,
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "session_console_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "operator_receipt_id": operator_receipt.get("receipt_id", ""),
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "selected_skill_tag": selected.get("skill_tag", ""),
        "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
        "repeat_run_index": max(1, int(repeat_run_index or 1)),
        "previous_console_receipt_count": len(previous_console_receipts),
        "previous_console_receipt_hashes_returned": previous_hashes,
        "supports_repeated_dry_runs": True,
        "workspace_card_hash": workspace_card_hash,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def operator_summary(operator: dict[str, Any]) -> dict[str, Any]:
    receipt = operator.get("dry_run_receipt", {}) if isinstance(operator.get("dry_run_receipt"), dict) else {}
    return {
        "artifact_type": operator.get("artifact_type", ""),
        "status": operator.get("status", "unknown"),
        "receipt_id": receipt.get("receipt_id", ""),
        "selected_skill_tag": receipt.get("selected_skill_tag", ""),
        "effective_help_level": receipt.get("effective_help_level", "A2"),
        "not_cleared_receipt": bool(receipt.get("not_cleared_receipt", True)),
        "raw_operator_report_embedded": False,
    }


def session_console_markdown(console: dict[str, Any]) -> str:
    selected = console.get("selected_skill", {}) if isinstance(console.get("selected_skill"), dict) else {}
    workspace = console.get("workspace_status", {}) if isinstance(console.get("workspace_status"), dict) else {}
    checkpoint = console.get("notebook_checkpoint", {}) if isinstance(console.get("notebook_checkpoint"), dict) else {}
    tutor = console.get("tutor_state", {}) if isinstance(console.get("tutor_state"), dict) else {}
    confirmations = console.get("operator_confirmations", {}) if isinstance(console.get("operator_confirmations"), dict) else {}
    workspace_card = console.get("local_cycle_operator_workspace_card", {}) if isinstance(console.get("local_cycle_operator_workspace_card"), dict) else {}
    return "\n".join(
        [
            "# Exam Workspace Session Console",
            f"- Status: {console.get('status', 'unknown')}",
            f"- Exam Deployment: {console.get('exam_deployment_status', 'not_cleared')}",
            f"- Skill: {selected.get('skill_tag', '')}",
            f"- Workspace: {workspace.get('workspace_run_status', 'unknown')}",
            f"- Checkpoint Hash: {checkpoint.get('notebook_work_sha256', '')}",
            f"- Tutor Help: {tutor.get('effective_help_level', 'A2')}",
            f"- Confirmations: {confirmations.get('confirmed_count', 0)}/{confirmations.get('write_step_count', 0)}",
            f"- Local Cycle Workspace Card: {workspace_card.get('status', 'missing')}; {workspace_card.get('help_ledger_preview_status', 'no-ledger')}; next={workspace_card.get('next_safe_action', '') or 'review_skill_readiness'}",
        ]
    )


def session_console_next_actions(operator: dict[str, Any]) -> list[str]:
    status = session_console_status(operator)
    if status == "exam_workspace_session_console_ready":
        return [
            "Repeat the dry-run for the same skill after the next local notebook checkpoint if needed.",
            "Keep local writes behind individual operator confirmations and keep exam_deployment_status not_cleared.",
        ]
    if status == "exam_workspace_session_console_repeat_task_required":
        return ["Remove final-solution-like notebook content and repeat with an own prediction/checkpoint."]
    return operator.get("next_actions", ["Review the selected skill coverage before continuing."])


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-workspace-session-console")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


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
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(summary.get("recommendation_reason", review.get("recommendation_reason", "missing_start_packet"))),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
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
    }


def safe_local_cycle_workspace_card_source(workspace_card: dict[str, Any]) -> dict[str, Any]:
    if not workspace_card:
        return {"status": "missing", "artifact_type": "missing", "schema_version": "", "exam_deployment_status": "not_cleared"}
    return {
        "status": str(workspace_card.get("status", "missing")),
        "artifact_type": str(workspace_card.get("artifact_type", "python_exam_local_cycle_operator_workspace_card")),
        "schema_version": str(workspace_card.get("schema_version", "")),
        "selected_skill_tag": str(workspace_card.get("selected_skill_tag", "")),
        "exam_deployment_status": "not_cleared",
    }


def write_synthetic_session_console_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_groupby.md").write_text(
        "pandas DataFrame groupby aggregate filter debugging notebook",
        encoding="utf-8",
    )


def synthetic_session_console_manifest_record() -> dict[str, Any]:
    return {
        "material_id": "synthetic-session-console-pandas-notebook",
        "title": "Synthetic session console pandas notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["pandas"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "synthetic week 01",
        "sha256": sha256_text("synthetic session console pandas notebook reviewed locally"),
    }


def write_synthetic_session_console_manifest(path: Path) -> None:
    manifest = build_material_manifest([synthetic_session_console_manifest_record()])
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def synthetic_session_console_decision_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic session console decision",
    }


def synthetic_session_console_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic session console workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic local-cycle prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "open_operator_run_dry_run",
            "next_safe_user_action": "review_session_console_before_any_local_write",
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
