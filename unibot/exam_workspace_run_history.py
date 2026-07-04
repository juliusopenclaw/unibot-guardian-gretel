from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_session_console import build_exam_workspace_session_console
from .materials import build_material_manifest, sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_index import build_private_tutor_index_dry_run


EXAM_WORKSPACE_RUN_HISTORY_SCHEMA_VERSION = "unibot-exam-workspace-run-history-v1"
EXAM_WORKSPACE_RUN_HISTORY_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-exam-workspace-run-history-release-review-board-claim-alignment-v1"
)
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


def build_exam_workspace_run_history_release_claim_alignment(
    history_report: dict[str, Any] | None = None,
    waiting_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if history_report is None or waiting_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_exam_workspace_run_history_alignment_") as temp_dir:
            temp_root = Path(temp_dir)
            materials_root = temp_root / "materials"
            manifest_path = temp_root / "private_manifest.json"
            index_path = temp_root / "private_tutor_index.json"
            write_synthetic_history_fixture(materials_root)
            write_synthetic_history_manifest(manifest_path)
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                operator_confirmed_tutor_index_build=True,
            )
            workspace_card = synthetic_history_workspace_card()
            first = build_exam_workspace_session_console(
                base_path=str(materials_root),
                review_policy="local_private_tutor",
                decision_record=synthetic_history_decision_record(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                cell_source="own_checkpoint = []\n",
                repeat_run_index=1,
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )
            second = build_exam_workspace_session_console(
                base_path=str(materials_root),
                review_policy="local_private_tutor",
                decision_record=synthetic_history_decision_record(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                cell_source="own_checkpoint = ['next']\n",
                repeat_run_index=2,
                previous_console_receipts=[first["session_console_receipt"]],
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )
            history_report = history_report or build_exam_workspace_run_history_export_review(
                console_reports=[first, second],
                console_receipts=[first["session_console_receipt"]],
                build_current_console=False,
                public_safe=True,
            )
            waiting_report = waiting_report or build_empty_history_waiting_report(
                course_id="exam-workspace-run-history-alignment"
            )

    sections = [
        {
            "section_id": "run_receipt_history_trace",
            "summary_claim": "run history aggregates only session-console receipt ids, hashes, skill tags, and checkpoint hashes",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["exam_workspace_run_history", "exam_workspace_run", "exam_workspace_launch"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "operator_reflection_export_trace",
            "summary_claim": "history export preserves operator-confirmation state, blockers, and reflection evidence for human review",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "exam_workspace_run_history",
                "python_exam_local_cycle_operator_workspace_card",
                "study_session",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "not_cleared_export_receipt_trace",
            "summary_claim": "history export receipt is human-reviewable evidence and remains not exam clearance",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "exam_workspace_run_history",
                "python_exam_local_cycle_operator_workspace_card",
                "external_decision_state",
                "exam_boundary",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "run history does not publish raw notebook data, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["exam_workspace_run_history", "evaluation_packet", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    entries = [item for item in history_report.get("run_history", []) or [] if isinstance(item, dict)]
    summary = history_report.get("history_summary", {}) if isinstance(history_report.get("history_summary"), dict) else {}
    package = (
        history_report.get("export_review_package", {})
        if isinstance(history_report.get("export_review_package"), dict)
        else {}
    )
    review_items = package.get("review_items", {}) if isinstance(package.get("review_items"), dict) else {}
    receipt = (
        history_report.get("export_review_receipt", {})
        if isinstance(history_report.get("export_review_receipt"), dict)
        else {}
    )
    waiting_summary = (
        waiting_report.get("history_summary", {})
        if isinstance(waiting_report.get("history_summary"), dict)
        else {}
    )
    waiting_package = (
        waiting_report.get("export_review_package", {})
        if isinstance(waiting_report.get("export_review_package"), dict)
        else {}
    )
    waiting_receipt = (
        waiting_report.get("export_review_receipt", {})
        if isinstance(waiting_report.get("export_review_receipt"), dict)
        else {}
    )
    session_report_entries = [entry for entry in entries if entry.get("entry_type") == "session_console_report"]
    workspace_card_entries = [
        entry.get("local_cycle_operator_workspace_card", {})
        for entry in session_report_entries
        if isinstance(entry.get("local_cycle_operator_workspace_card"), dict)
    ]
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    ready_workspace_card_entries = [
        card
        for card in workspace_card_entries
        if card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and card.get("ready_for_operator_prefill") is True
    ]
    workspace_card_help_ledger_hash_count = len(
        [card for card in workspace_card_entries if bool(card.get("help_ledger_preview_hash"))]
    )
    blocked_claims = [
        "raw query returned",
        "raw history returned",
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
    boundary = str(history_report.get("execution_boundary", ""))
    contracts = {
        "history_public_safe": history_report.get("public_safety_status") == "pass",
        "waiting_history_public_safe": waiting_report.get("public_safety_status") == "pass",
        "run_history_hash_only_ready": history_report.get("status") == "exam_workspace_run_history_export_review_ready"
        and int(summary.get("run_count", 0) or 0) >= 2
        and int(summary.get("checkpoint_hash_count", 0) or 0) >= 2
        and summary.get("raw_history_returned") is False
        and all(entry.get("raw_query_returned") is False for entry in entries)
        and all(entry.get("raw_text_returned") is False for entry in entries)
        and all(entry.get("raw_cell_returned") is False for entry in entries)
        and all(entry.get("notebook_code_returned") is False for entry in entries)
        and all(entry.get("local_paths_returned") is False for entry in entries),
        "operator_reflection_and_blockers_preserved": "reflection_evidence_present"
        in set(review_items.get("reflection_statuses", []) or [])
        and "operator_confirmations_open" in dict(summary.get("blocker_profile", {}) or {})
        and int(summary.get("open_operator_step_count", 0) or 0) >= 1,
        "workspace_card_review_gate_linked": workspace_card_readiness_gate_linked
        and bool(workspace_card_entries)
        and len(ready_workspace_card_entries) == len(workspace_card_entries)
        and workspace_card_help_ledger_hash_count == len(workspace_card_entries)
        and all(
            entry.get("local_cycle_operator_workspace_card", {}).get("selected_skill_tag") == entry.get("skill_tag")
            for entry in session_report_entries
            if isinstance(entry.get("local_cycle_operator_workspace_card"), dict)
        )
        and all(card.get("not_cleared_receipt") is True for card in workspace_card_entries)
        and "python_exam_local_cycle_operator_workspace_card_ready"
        in dict(review_items.get("workspace_card_profile", {}) or {}),
        "export_review_package_human_reviewable": package.get("status") == "export_review_ready"
        and package.get("human_reviewable_independence_evidence") is True
        and package.get("raw_query_returned") is False
        and package.get("raw_text_returned") is False
        and package.get("raw_cell_returned") is False
        and package.get("notebook_code_returned") is False
        and package.get("local_paths_returned") is False
        and package.get("automatic_grading_started") is False
        and all(
            item.get("not_cleared_receipt") is True
            for item in (review_items.get("export_receipts", []) or [])
            if isinstance(item, dict)
        ),
        "export_review_receipt_not_exam_clearance": receipt.get("status")
        == "export_review_receipt_ready_not_exam_clearance"
        and receipt.get("exam_deployment_status") == "not_cleared"
        and receipt.get("not_cleared_receipt") is True
        and int(receipt.get("run_count", 0) or 0) == int(summary.get("run_count", 0) or 0)
        and receipt.get("raw_query_returned") is False
        and receipt.get("raw_text_returned") is False
        and receipt.get("raw_cell_returned") is False
        and receipt.get("notebook_code_returned") is False
        and receipt.get("local_paths_returned") is False,
        "waiting_history_has_no_reviewable_export": waiting_report.get("status")
        == "exam_workspace_run_history_waiting_for_session_history"
        and int(waiting_summary.get("run_count", 0) or 0) == 0
        and waiting_package.get("status") == "export_review_waiting_for_session_history"
        and waiting_package.get("human_reviewable_independence_evidence") is False
        and int(waiting_receipt.get("run_count", 0) or 0) == 0,
        "public_outputs_hide_private_history_data": history_report.get("raw_query_returned") is False
        and history_report.get("raw_text_returned") is False
        and history_report.get("raw_cell_returned") is False
        and history_report.get("raw_notebook_returned") is False
        and history_report.get("notebook_code_returned") is False
        and history_report.get("local_paths_returned") is False
        and "never returns raw queries" in boundary
        and "notebook code" in boundary
        and "local paths" in boundary,
        "high_stakes_actions_not_started": history_report.get("exam_deployment_status") == "not_cleared"
        and history_report.get("automatic_grading_started") is False
        and history_report.get("proctoring_started") is False
        and history_report.get("ai_detection_started") is False
        and history_report.get("exam_clearance_claimed") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "history_status": history_report.get("status"),
        "waiting_status": waiting_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "exam-workspace-run-history-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_WORKSPACE_RUN_HISTORY_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "history_status": history_report.get("status"),
        "history_public_safety_status": history_report.get("public_safety_status"),
        "waiting_status": waiting_report.get("status"),
        "waiting_public_safety_status": waiting_report.get("public_safety_status"),
        "exam_deployment_status": history_report.get("exam_deployment_status"),
        "run_count": summary.get("run_count", 0),
        "checkpoint_hash_count": summary.get("checkpoint_hash_count", 0),
        "skill_tags": list(summary.get("skill_tags", []) or [])[:8],
        "help_level_profile": dict(summary.get("help_level_profile", {}) or {}),
        "blocker_profile": dict(summary.get("blocker_profile", {}) or {}),
        "open_operator_step_count": summary.get("open_operator_step_count", 0),
        "workspace_card_profile": dict(summary.get("workspace_card_profile", {}) or {}),
        "workspace_card_ready_entry_count": len(ready_workspace_card_entries),
        "workspace_card_help_ledger_hash_count": workspace_card_help_ledger_hash_count,
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "export_review_status": package.get("status"),
        "human_reviewable_independence_evidence": bool(package.get("human_reviewable_independence_evidence", False)),
        "reflection_evidence_present": "reflection_evidence_present"
        in set(review_items.get("reflection_statuses", []) or []),
        "export_receipt_status": receipt.get("status"),
        "export_receipt_not_cleared": bool(receipt.get("not_cleared_receipt", False)),
        "waiting_run_count": waiting_summary.get("run_count", 0),
        "waiting_export_status": waiting_package.get("status"),
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
            "Exam workspace run history is a hash-only export-review surface. It may aggregate session-console "
            "receipt ids, checkpoint hashes, help-level profiles, blockers, operator-confirmation state, reflection "
            "status, and not-cleared export receipts for human review, but it does not return raw private data, grade, "
            "proctor, detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


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
        workspace_card = (
            console.get("local_cycle_operator_workspace_card", {})
            if isinstance(console.get("local_cycle_operator_workspace_card"), dict)
            and console.get("local_cycle_operator_workspace_card", {}).get("status") != "missing"
            else report.get("local_cycle_operator_workspace_card", {})
        )
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
                workspace_card if isinstance(workspace_card, dict) else {}
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


def write_synthetic_history_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "lists_intro.md").write_text(
        "Python lists dictionary tuple index slice loop function notebook",
        encoding="utf-8",
    )


def synthetic_history_manifest_record() -> dict[str, Any]:
    return {
        "material_id": "synthetic-history-python-lists-notebook",
        "title": "Synthetic history Python lists notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["python_lists", "control_flow", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "synthetic week 01",
        "sha256": sha256_text("synthetic history python lists notebook reviewed locally"),
    }


def write_synthetic_history_manifest(path: Path) -> None:
    manifest = build_material_manifest([synthetic_history_manifest_record()])
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def synthetic_history_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic history workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic local-cycle prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "open_operator_run_dry_run",
            "next_safe_user_action": "review_run_history_before_any_local_write",
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


def synthetic_history_decision_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic history review decision",
    }


def build_empty_history_waiting_report(*, course_id: str) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    entries: list[dict[str, Any]] = []
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
            "Exam Workspace Run History waiting state. It has no session history and therefore no reviewable "
            "independence evidence. It never returns raw queries, course raw text, notebook code, local paths, "
            "grading, proctoring, AI detection, or exam clearance."
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
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": history_next_actions(entries),
    }
    attach_public_scan(report, public_safe=True)
    return report


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
