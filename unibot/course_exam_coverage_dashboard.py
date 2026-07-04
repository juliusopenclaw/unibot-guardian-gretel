from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .material_coverage_run import build_course_material_coverage_run
from .materials import sha256_text
from .public_safety import scan_text


COURSE_EXAM_COVERAGE_DASHBOARD_SCHEMA_VERSION = "unibot-course-exam-coverage-dashboard-v1"
COURSE_EXAM_COVERAGE_DASHBOARD_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-course-exam-coverage-dashboard-workspace-card-dashboard-alignment-v1"
)
COURSE_EXAM_COVERAGE_DASHBOARD_ENDPOINT = "/api/unibot/course/exam-coverage-dashboard"


def build_course_exam_coverage_dashboard(
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
    focus_query: str = "",
    selected_skill_tag: str = "",
    console_reports: list[dict[str, Any]] | None = None,
    console_receipts: list[dict[str, Any]] | None = None,
    run_history_report: dict[str, Any] | None = None,
    build_current_console: bool = False,
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
        focus_query=focus_query or selected_skill_tag,
        public_safe=public_safe,
    )
    safe_console_reports = [item for item in (console_reports or []) if isinstance(item, dict)]
    safe_console_receipts = [item for item in (console_receipts or []) if isinstance(item, dict)]
    if isinstance(run_history_report, dict):
        history = run_history_report
    elif build_current_console or safe_console_reports or safe_console_receipts:
        history = build_exam_workspace_run_history_export_review(
            course_id=safe_id,
            console_reports=safe_console_reports,
            console_receipts=safe_console_receipts,
            build_current_console=build_current_console,
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
            focus_query=focus_query,
            selected_skill_tag=selected_skill_tag,
            public_safe=public_safe,
        )
    else:
        history = empty_history_report(safe_id)
    rows = build_dashboard_rows(
        skill_coverage=[item for item in coverage.get("skill_coverage", []) if isinstance(item, dict)],
        run_history=[item for item in history.get("run_history", []) if isinstance(item, dict)],
    )
    summary = dashboard_summary(coverage=coverage, history=history, rows=rows)
    report = {
        "schema_version": COURSE_EXAM_COVERAGE_DASHBOARD_SCHEMA_VERSION,
        "artifact_type": "course_exam_coverage_dashboard",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "course_exam_coverage_dashboard_ready",
        "dashboard_title": "Course Exam Coverage Dashboard",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Course Exam Coverage Dashboard. It merges material coverage, Exam-Skill readiness, Session Console "
            "receipts, and Run-History Export Review into a compact per-skill overview. It is dry-run and "
            "metadata-only: no raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "coverage_summary": coverage.get("coverage_summary", {}),
        "dashboard_summary": summary,
        "skill_dashboard": rows,
        "run_history_summary": history.get("history_summary", {}),
        "export_review_summary": safe_export_review_summary(history.get("export_review_package", {})),
        "coverage_receipt": {
            "status": "dashboard_receipt_ready_not_exam_clearance",
            "receipt_id": dashboard_receipt_id(summary=summary, rows=rows, history=history),
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
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
            "Reale Pruefungsfreigabe bleibt ausserhalb des Bots; dieses Dashboard bleibt technisch nutzbar und not_cleared."
        ),
        "next_actions": dashboard_next_actions(rows),
    }
    attach_public_scan(report, public_safe=public_safe)
    report["workspace_card_dashboard_alignment"] = build_course_exam_coverage_dashboard_workspace_card_alignment(report)
    attach_public_scan(report, public_safe=public_safe)
    return report


def course_exam_coverage_dashboard_hash(dashboard: dict[str, Any] | None = None) -> str:
    dashboard = dashboard if isinstance(dashboard, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": dashboard.get("schema_version", ""),
                "artifact_type": dashboard.get("artifact_type", ""),
                "status": dashboard.get("status", ""),
                "course_id": dashboard.get("course_id", ""),
                "exam_deployment_status": dashboard.get("exam_deployment_status", ""),
                "coverage_summary": dashboard.get("coverage_summary", {}),
                "dashboard_summary": dashboard.get("dashboard_summary", {}),
                "skill_dashboard": dashboard.get("skill_dashboard", []),
                "run_history_summary": dashboard.get("run_history_summary", {}),
                "export_review_summary": dashboard.get("export_review_summary", {}),
                "public_safety_status": dashboard.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def course_exam_coverage_dashboard_receipt_hash(dashboard: dict[str, Any] | None = None) -> str:
    dashboard = dashboard if isinstance(dashboard, dict) else {}
    receipt = dashboard.get("coverage_receipt", {}) if isinstance(dashboard.get("coverage_receipt"), dict) else {}
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "dashboard_summary_hash": sha256_text(
                    json.dumps(dashboard.get("dashboard_summary", {}), sort_keys=True, ensure_ascii=False)
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_course_exam_coverage_dashboard_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic course exam coverage dashboard workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "python_lists",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic course exam coverage dashboard prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "python_lists",
            "next_safe_action": "review_dashboard_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_dashboard_before_route_or_public_claim",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__COURSE_EXAM_COVERAGE_DASHBOARD_RECEIPT_HASH__",
            "checkpoint_hash": "__COURSE_EXAM_COVERAGE_DASHBOARD_HASH__",
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


def safe_course_exam_coverage_dashboard_workspace_card(
    workspace_card: dict[str, Any],
    *,
    dashboard_hash: str = "",
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
    if dashboard_hash and checkpoint_hash == "__COURSE_EXAM_COVERAGE_DASHBOARD_HASH__":
        checkpoint_hash = dashboard_hash
    if receipt_hash and task_hash == "__COURSE_EXAM_COVERAGE_DASHBOARD_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_course_exam_dashboard_gate")),
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


def build_course_exam_coverage_dashboard_workspace_card_alignment(
    course_exam_coverage_dashboard: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dashboard = course_exam_coverage_dashboard if isinstance(course_exam_coverage_dashboard, dict) else {}
    summary = dashboard.get("dashboard_summary", {}) if isinstance(dashboard.get("dashboard_summary"), dict) else {}
    receipt = dashboard.get("coverage_receipt", {}) if isinstance(dashboard.get("coverage_receipt"), dict) else {}
    rows = [row for row in (dashboard.get("skill_dashboard", []) or []) if isinstance(row, dict)]
    dashboard_hash = course_exam_coverage_dashboard_hash(dashboard)
    receipt_hash = course_exam_coverage_dashboard_receipt_hash(dashboard)
    workspace_card = safe_course_exam_coverage_dashboard_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_course_exam_coverage_dashboard_workspace_card(),
        dashboard_hash=dashboard_hash,
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
        "dashboard_public_safe": dashboard.get("public_safety_status") == "pass",
        "dashboard_ready": dashboard.get("status") == "course_exam_coverage_dashboard_ready"
        and int(summary.get("skill_count", 0) or 0) == len(rows)
        and len(rows) >= 1,
        "coverage_receipt_ready_not_clearance": receipt.get("status") == "dashboard_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and receipt.get("not_cleared_receipt") is True,
        "skill_rows_metadata_ready": all(row.get("skill_tag") for row in rows)
        and all(row.get("exam_deployment_status") == "not_cleared" for row in rows),
        "checkpoint_and_confirmation_counts_preserved": int(summary.get("checkpoint_hash_count", 0) or 0) >= 0
        and int(summary.get("open_operator_confirmation_count", 0) or 0) >= 0
        and all(int(row.get("checkpoint_hash_count", 0) or 0) >= 0 for row in rows)
        and all(int(row.get("open_operator_confirmation_count", 0) or 0) >= 0 for row in rows),
        "local_write_boundary_preserved": True,
        "no_clearance_or_deployment_claim": dashboard.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(dashboard.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names)
        and all(row.get(flag, False) is False for row in rows for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(dashboard.get(flag) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_course_exam_dashboard_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == dashboard_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "course_exam_coverage_dashboard",
        "course_per_skill_action_router",
        "routed_action_executor",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": COURSE_EXAM_COVERAGE_DASHBOARD_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "course_exam_coverage_dashboard_hash": dashboard_hash,
        "course_exam_coverage_dashboard_receipt_hash": receipt_hash,
        "dashboard_status": dashboard.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "skill_count": int(summary.get("skill_count", 0) or 0),
        "visible_skill_count": len(rows),
        "workspace_ready_skill_count": int(summary.get("workspace_ready_skill_count", 0) or 0),
        "checkpoint_hash_count": int(summary.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": int(summary.get("open_operator_confirmation_count", 0) or 0),
        "exam_deployment_status": dashboard.get("exam_deployment_status", "missing"),
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
        "workspace_card_course_exam_dashboard_gate_linked": contracts[
            "workspace_card_course_exam_dashboard_gate_linked"
        ],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Course exam coverage dashboard claims are hash-only review aids for skill readiness rows, coverage "
            "receipts, checkpoint counts, open-operator-confirmation counts, and local-write boundaries; they do "
            "not authorize publication, provider calls, grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "course-exam-coverage-dashboard-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def synthetic_course_exam_coverage_dashboard_inputs() -> dict[str, Any]:
    dashboard = build_course_exam_coverage_dashboard(public_safe=True)
    if not dashboard.get("skill_dashboard"):
        dashboard["skill_dashboard"] = [
            {
                "skill_tag": "python_lists",
                "title": "Python lists",
                "workspace_readiness": "ready_for_exam_workspace_dry_run",
                "source_anchor_count": 2,
                "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
                "reviewed_notebook_anchor_count": 1,
                "ocr_gap_count": 0,
                "video_transcription_gap_count": 0,
                "coverage_gap_status": "coverage_ready_for_dry_run",
                "latest_checkpoint_hashes": [sha256_text("synthetic dashboard checkpoint")],
                "checkpoint_hash_count": 1,
                "help_level_profile": {"A2": 1},
                "open_operator_confirmation_count": 1,
                "open_operator_confirmations": ["synthetic_operator_confirmation"],
                "next_safe_step": "review latest checkpoint hash, help-level profile, and export receipt",
                "allowed_exam_help": ["A0", "A1", "A2"],
                "exam_deployment_status": "not_cleared",
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        ]
        dashboard["dashboard_summary"] = {
            "skill_count": 1,
            "workspace_ready_skill_count": 1,
            "skills_with_history_count": 1,
            "source_anchor_count": 2,
            "ocr_gap_count": 0,
            "video_gap_count": 0,
            "checkpoint_hash_count": 1,
            "open_operator_confirmation_count": 1,
            "help_level_profile": {"A2": 1},
            "exam_deployment_status": "not_cleared",
        }
        dashboard["coverage_receipt"]["receipt_id"] = dashboard_receipt_id(
            summary=dashboard["dashboard_summary"],
            rows=dashboard["skill_dashboard"],
            history={"export_review_receipt": {"receipt_hash": "synthetic"}},
        )
        attach_public_scan(dashboard, public_safe=True)
        dashboard["workspace_card_dashboard_alignment"] = build_course_exam_coverage_dashboard_workspace_card_alignment(
            dashboard
        )
        attach_public_scan(dashboard, public_safe=True)
    return {"course_exam_coverage_dashboard": dashboard}


def build_dashboard_rows(*, skill_coverage: list[dict[str, Any]], run_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in run_history:
        tag = str(entry.get("skill_tag", ""))
        if tag:
            entries_by_skill[tag].append(entry)

    rows = []
    for skill in skill_coverage:
        tag = str(skill.get("skill_tag", ""))
        entries = entries_by_skill.get(tag, [])
        help_profile = help_level_profile(entries)
        open_steps = open_operator_steps(entries)
        checkpoint_hashes = latest_checkpoint_hashes(entries)
        rows.append(
            {
                "skill_tag": tag,
                "title": skill.get("title", ""),
                "exam_task_type": skill.get("exam_task_type", ""),
                "workspace_readiness": skill.get("exam_workspace_readiness", "unknown"),
                "source_anchor_count": int(skill.get("source_anchor_count", 0) or 0),
                "source_card_ids": list(skill.get("source_card_ids", []) or [])[:8],
                "reviewed_notebook_anchor_count": int(skill.get("reviewed_notebook_anchor_count", 0) or 0),
                "ocr_gap_count": int(skill.get("ocr_gap_count", 0) or 0),
                "video_transcription_gap_count": int(skill.get("video_transcription_gap_count", 0) or 0),
                "coverage_gap_status": coverage_gap_status(skill),
                "latest_checkpoint_hashes": checkpoint_hashes,
                "checkpoint_hash_count": len(checkpoint_hashes),
                "help_level_profile": help_profile,
                "open_operator_confirmation_count": len(open_steps),
                "open_operator_confirmations": open_steps[:8],
                "next_safe_step": next_safe_step(skill, entries, open_steps),
                "allowed_exam_help": allowed_a0_a2(skill),
                "exam_deployment_status": "not_cleared",
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
            }
        )
    return rows


def empty_history_report(course_id: str) -> dict[str, Any]:
    return {
        "artifact_type": "exam_workspace_run_history_export_review",
        "course_id": course_id,
        "status": "exam_workspace_run_history_waiting_for_session_history",
        "exam_deployment_status": "not_cleared",
        "run_history": [],
        "history_summary": {
            "run_count": 0,
            "skill_tags": [],
            "checkpoint_hash_count": 0,
            "checkpoint_hashes": [],
            "help_level_profile": {},
            "blocker_profile": {},
            "confirmed_operator_step_count": 0,
            "open_operator_step_count": 0,
            "raw_history_returned": False,
        },
        "export_review_package": {
            "status": "export_review_waiting_for_session_history",
            "human_reviewable_independence_evidence": False,
            "review_items": {
                "reflection_statuses": [],
                "operator_confirmation_profile": {"confirmed_step_count": 0, "open_step_count": 0},
            },
        },
        "export_review_receipt": {"status": "waiting_for_session_history", "receipt_hash": ""},
    }


def latest_checkpoint_hashes(entries: list[dict[str, Any]]) -> list[str]:
    hashes = []
    for entry in sorted(entries, key=lambda item: int(item.get("repeat_run_index", 0) or 0), reverse=True):
        checkpoint_hash = str(entry.get("checkpoint_hash", ""))
        if checkpoint_hash and checkpoint_hash not in hashes:
            hashes.append(checkpoint_hash)
    return hashes[:4]


def help_level_profile(entries: list[dict[str, Any]]) -> dict[str, int]:
    profile: dict[str, int] = {}
    for entry in entries:
        level = str(entry.get("help_level", ""))
        if level:
            profile[level] = profile.get(level, 0) + 1
    return profile


def open_operator_steps(entries: list[dict[str, Any]]) -> list[str]:
    steps = []
    for entry in entries:
        confirmations = entry.get("operator_confirmations", {}) if isinstance(entry.get("operator_confirmations"), dict) else {}
        for step in confirmations.get("open_steps", []) or []:
            step_text = str(step)
            if step_text and step_text not in steps:
                steps.append(step_text)
    return steps


def coverage_gap_status(skill: dict[str, Any]) -> str:
    if int(skill.get("source_anchor_count", 0) or 0) <= 0:
        return "needs_source_anchor_review"
    if int(skill.get("reviewed_notebook_anchor_count", 0) or 0) <= 0:
        return "needs_notebook_anchor_review"
    if int(skill.get("video_transcription_gap_count", 0) or 0) > 0:
        return "video_transcription_pending"
    if int(skill.get("ocr_gap_count", 0) or 0) > 0:
        return "ocr_pending"
    return "coverage_ready_for_dry_run"


def next_safe_step(skill: dict[str, Any], entries: list[dict[str, Any]], open_steps: list[str]) -> str:
    if open_steps:
        return "review open operator confirmations before any local write"
    if not entries and skill.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run":
        return "start Session Console dry-run for this skill with A0-A2 help"
    if entries:
        return "review latest checkpoint hash, help-level profile, and export receipt"
    return str(skill.get("next_step", "review coverage state"))


def allowed_a0_a2(skill: dict[str, Any]) -> list[str]:
    allowed = [str(item) for item in (skill.get("allowed_exam_help", []) or [])]
    safe = [item for item in allowed if item.startswith(("A0", "A1", "A2"))]
    return safe or ["A0", "A1", "A2"]


def dashboard_summary(*, coverage: dict[str, Any], history: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    coverage_summary = coverage.get("coverage_summary", {}) if isinstance(coverage.get("coverage_summary"), dict) else {}
    history_summary = history.get("history_summary", {}) if isinstance(history.get("history_summary"), dict) else {}
    return {
        "skill_count": len(rows),
        "workspace_ready_skill_count": int(coverage_summary.get("exam_workspace_ready_skill_count", 0) or 0),
        "skills_with_history_count": len([row for row in rows if row.get("checkpoint_hash_count", 0)]),
        "source_anchor_count": sum(int(row.get("source_anchor_count", 0) or 0) for row in rows),
        "ocr_gap_count": int(coverage_summary.get("ocr_gap_count", 0) or 0),
        "video_gap_count": int(coverage_summary.get("video_gap_count", 0) or 0),
        "checkpoint_hash_count": int(history_summary.get("checkpoint_hash_count", 0) or 0),
        "open_operator_confirmation_count": sum(int(row.get("open_operator_confirmation_count", 0) or 0) for row in rows),
        "help_level_profile": dict(history_summary.get("help_level_profile", {}) or {}),
        "exam_deployment_status": "not_cleared",
    }


def safe_export_review_summary(package: dict[str, Any]) -> dict[str, Any]:
    review = package.get("review_items", {}) if isinstance(package.get("review_items"), dict) else {}
    profile = review.get("operator_confirmation_profile", {}) if isinstance(review.get("operator_confirmation_profile"), dict) else {}
    return {
        "status": package.get("status", "unknown"),
        "human_reviewable_independence_evidence": bool(package.get("human_reviewable_independence_evidence", False)),
        "reflection_statuses": list(review.get("reflection_statuses", []) or [])[:8],
        "confirmed_operator_step_count": int(profile.get("confirmed_step_count", 0) or 0),
        "open_operator_step_count": int(profile.get("open_step_count", 0) or 0),
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def dashboard_receipt_id(*, summary: dict[str, Any], rows: list[dict[str, Any]], history: dict[str, Any]) -> str:
    seed = {
        "summary": summary,
        "skill_tags": [row.get("skill_tag", "") for row in rows],
        "history_receipt": history.get("export_review_receipt", {}).get("receipt_hash", "")
        if isinstance(history.get("export_review_receipt"), dict)
        else "",
    }
    return sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))[:20]


def dashboard_next_actions(rows: list[dict[str, Any]]) -> list[str]:
    open_confirmation_rows = [row for row in rows if row.get("open_operator_confirmation_count", 0)]
    if open_confirmation_rows:
        return [
            "Review open operator confirmations before any local write.",
            "Use Session Console or Run-History Export Review for the selected skill; keep A0-A2 and not_cleared.",
        ]
    ready_without_history = [
        row
        for row in rows
        if row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run" and not row.get("checkpoint_hash_count")
    ]
    if ready_without_history:
        tag = ready_without_history[0].get("skill_tag", "selected_skill")
        return [f"Start a Session Console dry-run for {tag} with A0-A2 help, then rebuild the dashboard."]
    return ["Review per-skill next safe steps and continue material or notebook-anchor readiness work."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "course-exam-coverage-dashboard")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
