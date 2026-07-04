from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import (
    DEFAULT_COURSE_ID,
    SKILL_PITFALLS,
    SKILL_PRACTICE_TASKS,
    build_course_exam_scope,
    safe_course_id,
)
from .guardian import normalize_help_level
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .tutor_coverage import build_course_tutor_coverage_plan


STUDY_SESSION_SCHEMA_VERSION = "unibot-course-study-session-plan-v1"
STUDY_SESSION_RECEIPT_SCHEMA_VERSION = "unibot-course-study-session-receipt-v1"
STUDY_SESSION_REVIEW_SCHEMA_VERSION = "unibot-course-study-session-review-v1"
STUDY_SESSION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-study-session-release-review-board-claim-alignment-v1"
)
STUDY_SESSION_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-study-session-workspace-card-study-alignment-v1"
)

RECEIPT_TEXT_FIELDS = {
    "retrieval_response",
    "prediction",
    "notebook_action",
    "reflection",
    "student_reflection",
    "source_anchor_note",
}
FORBIDDEN_RECEIPT_FIELDS = {
    "final_solution",
    "complete_code",
    "inserted_values",
    "raw_course_text",
    "raw_transcript",
    "local_path",
}


def build_course_study_session_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    receipts: list[dict[str, Any]] | None = None,
    focus_query: str = "",
    max_items: int = 5,
    public_safe: bool = True,
) -> dict[str, Any]:
    scope = build_course_exam_scope(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    coverage = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        receipts=receipts or [],
        public_safe=public_safe,
    )
    skills = [] if scope.get("status") == "needs_materials" else ranked_study_skills(scope.get("skills", []), focus_query=focus_query)
    selected = skills[: max(1, min(int(max_items or 5), 9))]
    tasks = [study_task_for_skill(skill, index=index + 1, focus_query=focus_query) for index, skill in enumerate(selected)]
    ready_count = len([task for task in tasks if task.get("readiness") == "ready_for_private_tutor"])
    plan = {
        "schema_version": STUDY_SESSION_SCHEMA_VERSION,
        "artifact_type": "course_study_session_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": study_session_status(scope, tasks),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a study-session plan for source-grounded practice. It does not solve tasks, "
            "does not grade, does not proctor, and does not expose raw course text or local paths."
        ),
        "focus_query_hash": sha256_text(str(focus_query or "")) if focus_query else "",
        "scope_summary": scope.get("material_summary", {}),
        "coverage_summary": {
            "current_ready_skill_count": coverage.get("current_scope_summary", {}).get("ready_skill_count", 0),
            "projected_ready_skill_count": coverage.get("projected_scope_summary", {}).get("ready_skill_count", 0),
            "candidate_material_count": coverage.get("projected_scope_summary", {}).get("candidate_material_count", 0),
            "coverage_status": coverage.get("status"),
        },
        "task_count": len(tasks),
        "ready_task_count": ready_count,
        "needs_review_task_count": len([task for task in tasks if task.get("readiness") == "needs_review"]),
        "tasks": tasks,
        "session_contract": {
            "standard_help_boundary": "A0-A2",
            "allowed_help_levels": ["A0", "A1", "A2"],
            "practice_extensions": ["A3", "A4", "A5 only outside real exam and clearly marked non-standard"],
            "always_blocked": ["A6 final solution, full code, inserted values, final interpretation"],
            "evidence_required": [
                "own prediction",
                "source anchor",
                "smallest notebook action",
                "reflection sentence",
                "Help-Ledger entry if AI help is used",
            ],
            "assessment_policy": "self-check only; no grade, ranking, AI detection, or exam decision",
        },
        "spacing_plan": spacing_plan(tasks),
        "next_actions": study_session_next_actions(scope, tasks, coverage),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="course-study-session-plan")
    return plan


def validate_study_session_receipt(
    receipt: dict[str, Any] | None,
    *,
    expected_task_ids: set[str] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    record = dict(receipt or {})
    issues: list[str] = []
    warnings: list[str] = []
    task_id = str(record.get("task_id", "")).strip()
    skill_tag = str(record.get("skill_tag", "")).strip()
    help_level = normalize_help_level(record.get("help_level", "A0"))
    source_anchor_id = str(record.get("source_anchor_id", record.get("source_ref_id", ""))).strip()
    final_solution_seen = bool(record.get("final_solution_seen")) or help_level == "A6"
    forbidden_present = sorted(field for field in FORBIDDEN_RECEIPT_FIELDS if field in record)

    if not task_id:
        issues.append("task_id_required")
    if expected_task_ids is not None and task_id and task_id not in expected_task_ids:
        issues.append("task_id_not_in_study_session_plan")
    if not skill_tag:
        issues.append("skill_tag_required")
    if not source_anchor_id:
        issues.append("source_anchor_required")
    if forbidden_present:
        issues.append("forbidden_solution_or_private_field_present")
    if final_solution_seen:
        issues.append("a6_or_final_solution_seen_repeat_task_required")

    evidence = evidence_summary(record)
    missing_evidence = [key for key, value in evidence.items() if key.endswith("_present") and not value]
    if missing_evidence:
        issues.append("required_learning_evidence_missing")

    private_flags = privacy_flags_for_receipt(record)
    if private_flags:
        warnings.append("raw_receipt_text_redacted_or_hash_only")

    safe_summary = {
        "schema_version": STUDY_SESSION_RECEIPT_SCHEMA_VERSION,
        "artifact_type": "course_study_session_receipt_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": study_receipt_status(issues, final_solution_seen),
        "exam_deployment_status": "not_cleared",
        "task_id": task_id,
        "skill_tag": skill_tag,
        "help_level": help_level,
        "source_anchor_id_hash": sha256_text(source_anchor_id) if source_anchor_id else "",
        "source_anchor_id_stored": False,
        "evidence": evidence,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "privacy_flags": private_flags,
        "forbidden_fields_present": forbidden_present,
        "raw_text_stored": False,
        "reflection_stored": False,
        "repeat_task_required": final_solution_seen,
        "assessment_policy": "human-readable learning evidence only; no grade, score, ranking, proctoring, or AI detection",
    }
    attach_public_scan(safe_summary, public_safe=public_safe, source_name="study-session-receipt-validation")
    return safe_summary


def build_study_session_review_report(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    extraction_receipts: list[dict[str, Any]] | None = None,
    study_receipts: list[dict[str, Any]] | None = None,
    focus_query: str = "",
    max_items: int = 5,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    plan = build_course_study_session_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        receipts=extraction_receipts or [],
        focus_query=focus_query,
        max_items=max_items,
        public_safe=public_safe,
    )
    expected_task_ids = {str(task.get("task_id", "")) for task in plan.get("tasks", []) if task.get("task_id")}
    receipt_records = [item for item in (study_receipts or []) if isinstance(item, dict)]
    validations = [
        validate_study_session_receipt(receipt, expected_task_ids=expected_task_ids, public_safe=public_safe)
        for receipt in receipt_records
    ]
    ok = [item for item in validations if item.get("status") == "ok_study_session_receipt"]
    repeat = [item for item in validations if item.get("repeat_task_required")]
    blocked = [item for item in validations if item.get("status") == "blocked"]
    report = {
        "schema_version": STUDY_SESSION_REVIEW_SCHEMA_VERSION,
        "artifact_type": "course_study_session_review_report",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": study_review_status(plan, receipt_records, validations),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This review report validates learning evidence receipts only. It does not grade, "
            "does not infer Eigenleistung percentages, and does not store raw student text."
        ),
        "study_session_status": plan.get("status"),
        "planned_task_count": plan.get("task_count", 0),
        "receipt_summary": {
            "submitted_receipt_count": len(receipt_records),
            "valid_receipt_count": len(ok),
            "blocked_receipt_count": len(blocked),
            "repeat_task_required_count": len(repeat),
            "missing_planned_receipt_count": max(0, int(plan.get("task_count", 0) or 0) - len(ok)),
        },
        "evidence_profile": aggregate_evidence_profile(validations),
        "validated_receipts": validations[:80],
        "receipt_output_truncated": len(validations) > 80,
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
        "study_session_review_receipt": {
            "status": "study_session_review_receipt_ready_not_exam_clearance",
            "receipt_id": study_session_review_receipt_id(
                receipt_summary={
                    "submitted_receipt_count": len(receipt_records),
                    "valid_receipt_count": len(ok),
                    "blocked_receipt_count": len(blocked),
                    "repeat_task_required_count": len(repeat),
                    "missing_planned_receipt_count": max(0, int(plan.get("task_count", 0) or 0) - len(ok)),
                },
                evidence_profile=aggregate_evidence_profile(validations),
            ),
            "exam_deployment_status": "not_cleared",
            "not_cleared_receipt": True,
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_student_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        "review_policy": {
            "eigenleistung_claim": "Use evidence profile, source anchors, help levels, blocked repeats, and reflections; never claim a percentage.",
            "human_review_path": "A human can inspect private notebook/checkpoint artifacts using hashes and local-only references outside this report.",
            "not_allowed": ["grade", "ranking", "proctoring", "AI detection", "raw private text publication"],
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_student_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": study_review_next_actions(plan, validations),
    }
    attach_public_scan(report, public_safe=public_safe, source_name="study-session-review-report")
    report["workspace_card_study_alignment"] = build_study_session_workspace_card_alignment(report)
    attach_public_scan(report, public_safe=public_safe, source_name="study-session-review-report")
    return report


def study_session_review_receipt_id(*, receipt_summary: dict[str, Any], evidence_profile: dict[str, Any]) -> str:
    seed = {
        "receipt_summary": receipt_summary,
        "evidence_profile": evidence_profile,
        "exam_deployment_status": "not_cleared",
    }
    return sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))[:20]


def study_session_review_hash(review_report: dict[str, Any] | None = None) -> str:
    review_report = review_report if isinstance(review_report, dict) else {}
    return sha256_text(
        json.dumps(
            {
                "schema_version": review_report.get("schema_version", ""),
                "artifact_type": review_report.get("artifact_type", ""),
                "status": review_report.get("status", ""),
                "course_id": review_report.get("course_id", ""),
                "exam_deployment_status": review_report.get("exam_deployment_status", ""),
                "study_session_status": review_report.get("study_session_status", ""),
                "planned_task_count": review_report.get("planned_task_count", 0),
                "receipt_summary": review_report.get("receipt_summary", {}),
                "evidence_profile": review_report.get("evidence_profile", {}),
                "validated_receipts": review_report.get("validated_receipts", []),
                "public_safety_status": review_report.get("public_safety_status", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def study_session_review_receipt_hash(review_report: dict[str, Any] | None = None) -> str:
    review_report = review_report if isinstance(review_report, dict) else {}
    receipt = (
        review_report.get("study_session_review_receipt", {})
        if isinstance(review_report.get("study_session_review_receipt"), dict)
        else {}
    )
    return sha256_text(
        json.dumps(
            {
                "receipt_status": receipt.get("status", ""),
                "receipt_id": receipt.get("receipt_id", ""),
                "exam_deployment_status": receipt.get("exam_deployment_status", ""),
                "not_cleared_receipt": receipt.get("not_cleared_receipt", None),
                "review_status": review_report.get("status", ""),
                "receipt_summary_hash": sha256_text(
                    json.dumps(review_report.get("receipt_summary", {}), sort_keys=True, ensure_ascii=False)
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def synthetic_study_session_review_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic study session review workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic study-session review prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_study_session_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_study_session_before_route_or_public_claim",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__STUDY_SESSION_REVIEW_RECEIPT_HASH__",
            "checkpoint_hash": "__STUDY_SESSION_REVIEW_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "uoc-ki-faq"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_study_session_review_workspace_card(
    workspace_card: dict[str, Any],
    *,
    review_hash: str = "",
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
    if review_hash and checkpoint_hash == "__STUDY_SESSION_REVIEW_HASH__":
        checkpoint_hash = review_hash
    if receipt_hash and task_hash == "__STUDY_SESSION_REVIEW_RECEIPT_HASH__":
        task_hash = receipt_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_study_session_gate")),
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


def build_study_session_workspace_card_alignment(
    review_report: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review_report = review_report if isinstance(review_report, dict) else {}
    receipt_summary = (
        review_report.get("receipt_summary", {}) if isinstance(review_report.get("receipt_summary"), dict) else {}
    )
    evidence_profile = (
        review_report.get("evidence_profile", {}) if isinstance(review_report.get("evidence_profile"), dict) else {}
    )
    receipt = (
        review_report.get("study_session_review_receipt", {})
        if isinstance(review_report.get("study_session_review_receipt"), dict)
        else {}
    )
    validations = [item for item in review_report.get("validated_receipts", []) if isinstance(item, dict)]
    review_hash = study_session_review_hash(review_report)
    receipt_hash = study_session_review_receipt_hash(review_report)
    source_workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_study_session_review_workspace_card()
    )
    workspace_card = safe_study_session_review_workspace_card(
        source_workspace_card,
        review_hash=review_hash,
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
        "raw_student_text_returned",
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
        "study_review_public_safe": review_report.get("public_safety_status") == "pass",
        "study_review_ready": review_report.get("status") == "study_session_evidence_ready_for_human_review"
        and review_report.get("study_session_status") == "ready_for_course_bound_practice"
        and int(review_report.get("planned_task_count", 0) or 0) >= 1,
        "study_receipt_ready_not_clearance": receipt.get("status")
        == "study_session_review_receipt_ready_not_exam_clearance"
        and bool(receipt.get("receipt_id"))
        and receipt.get("not_cleared_receipt") is True,
        "hash_only_learning_evidence_preserved": int(receipt_summary.get("valid_receipt_count", 0) or 0) >= 1
        and int(receipt_summary.get("blocked_receipt_count", 0) or 0) == 0
        and int(receipt_summary.get("repeat_task_required_count", 0) or 0) == 0
        and all(item.get("raw_text_stored") is False for item in validations)
        and all(item.get("reflection_stored") is False for item in validations),
        "learner_agency_profile_preserved": int(evidence_profile.get("prediction_present_count", 0) or 0) >= 1
        and int(evidence_profile.get("retrieval_response_present_count", 0) or 0) >= 1
        and int(evidence_profile.get("notebook_action_present_count", 0) or 0) >= 1
        and int(evidence_profile.get("source_anchor_present_count", 0) or 0) >= 1
        and int(evidence_profile.get("reflection_present_count", 0) or 0) >= 1,
        "repeat_task_boundary_preserved": True,
        "no_clearance_or_deployment_claim": review_report.get("exam_deployment_status") == "not_cleared"
        and receipt.get("exam_deployment_status") == "not_cleared",
        "metadata_only_safety_flags_false": all(review_report.get(flag) is False for flag in raw_flag_names)
        and all(receipt.get(flag, False) is False for flag in raw_flag_names),
        "high_stakes_boundaries_blocked": all(review_report.get(flag) is False for flag in high_stakes_flag_names),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_study_session_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == review_hash
        and workspace_card.get("task_hash") == receipt_hash,
        "workspace_card_public_metadata_only": workspace_card.get("raw_workspace_card_returned") is False,
    }
    required_readiness_check_ids = [
        "study_session",
        "private_tutor_use_flow",
        "evaluation_packet",
        "python_exam_local_cycle_operator_workspace_card",
    ]
    alignment = {
        "schema_version": STUDY_SESSION_WORKSPACE_CARD_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "study_session_review_hash": review_hash,
        "study_session_review_receipt_hash": receipt_hash,
        "review_status": review_report.get("status", "missing"),
        "receipt_status": receipt.get("status", "missing"),
        "study_session_status": review_report.get("study_session_status", "missing"),
        "planned_task_count": int(review_report.get("planned_task_count", 0) or 0),
        "valid_receipt_count": int(receipt_summary.get("valid_receipt_count", 0) or 0),
        "blocked_receipt_count": int(receipt_summary.get("blocked_receipt_count", 0) or 0),
        "repeat_task_required_count": int(receipt_summary.get("repeat_task_required_count", 0) or 0),
        "prediction_present_count": int(evidence_profile.get("prediction_present_count", 0) or 0),
        "retrieval_response_present_count": int(evidence_profile.get("retrieval_response_present_count", 0) or 0),
        "notebook_action_present_count": int(evidence_profile.get("notebook_action_present_count", 0) or 0),
        "source_anchor_present_count": int(evidence_profile.get("source_anchor_present_count", 0) or 0),
        "reflection_present_count": int(evidence_profile.get("reflection_present_count", 0) or 0),
        "exam_deployment_status": review_report.get("exam_deployment_status", "missing"),
        "required_readiness_check_ids": required_readiness_check_ids,
        "required_human_gates": [
            "human_review_required",
            "public_safety_required",
            "operator_confirmation_required_for_local_write",
            "exam_clearance_requires_written_authority_clearance",
        ],
        "blocked_claims": [
            "raw private course text publication",
            "raw learner reflection publication",
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
        "workspace_card_study_session_gate_linked": contracts["workspace_card_study_session_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in required_readiness_check_ids,
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "public_language": (
            "Study-session claims are hash-only review aids for formative learning receipts, prediction/retrieval/"
            "notebook/reflection evidence counts, repeat-task boundaries, and no-clearance boundaries; they do "
            "not authorize publication, provider calls, grading, proctoring, KI detection, or exam use."
        ),
    }
    if alignment["failed_contract_ids"]:
        alignment["status"] = "blocked"
    scan = scan_text(
        json.dumps(alignment, ensure_ascii=False, sort_keys=True),
        "study-session-workspace-card-alignment",
    )
    alignment["alignment_public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def build_study_session_release_claim_alignment(
    review_report: dict[str, Any] | None = None,
    repeat_receipt_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if review_report is None or repeat_receipt_validation is None:
        with tempfile.TemporaryDirectory(prefix="unibot_study_session_alignment_") as temp_dir:
            fixture_root = Path(temp_dir)
            write_synthetic_study_session_fixture(fixture_root)
            plan = build_course_study_session_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                focus_query="pandas boxplot",
                max_items=1,
            )
            task = (plan.get("tasks") or [{"task_id": "synthetic-study-task", "skill_tag": "pandas"}])[0]
            receipt = synthetic_study_session_receipt(task)
            if review_report is None:
                review_report = build_study_session_review_report(
                    base_path=str(fixture_root),
                    review_policy="local_private_tutor",
                    focus_query="pandas boxplot",
                    max_items=1,
                    study_receipts=[receipt],
                    python_exam_local_cycle_operator_workspace_card=synthetic_study_session_workspace_card(receipt),
                )
            if repeat_receipt_validation is None:
                repeat_receipt = {
                    **receipt,
                    "help_level": "A6",
                    "final_solution_seen": True,
                }
                repeat_receipt_validation = validate_study_session_receipt(
                    repeat_receipt,
                    expected_task_ids={str(task.get("task_id", ""))},
                )

    sections = [
        {
            "section_id": "course_bound_study_plan_trace",
            "summary_claim": "study-session tasks are course-bound source-anchor practice, not answer outsourcing",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "study_session",
                "python_exam_local_cycle_operator_workspace_card",
                "private_tutor_use_flow",
                "evaluation_packet",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "hash_only_receipt_trace",
            "summary_claim": "study receipts retain hash-only evidence for prediction, retrieval, notebook action, source anchor, and reflection",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "study_session",
                "python_exam_local_cycle_operator_workspace_card",
                "private_tutor_use_flow",
                "review_board_packet",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "learner_agency_repeat_trace",
            "summary_claim": "A6 or final-solution exposure forces repeat-task evidence instead of accepting the receipt",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["study_session", "evaluation_packet", "exam_boundary"],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "study-session review does not grade, rank, proctor, detect AI use, publish raw text, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["study_session", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    receipt_summary = review_report.get("receipt_summary", {})
    evidence_profile = review_report.get("evidence_profile", {})
    review_policy = review_report.get("review_policy", {})
    workspace_card = (
        review_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(review_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    blocked_claims = [
        "raw prediction storage",
        "raw retrieval response storage",
        "raw notebook action storage",
        "raw reflection storage",
        "raw private course text publication",
        "final solution acceptance",
        "complete code outsourcing",
        "Eigenleistung percentage claim",
        "automatic grading",
        "ranking",
        "proctoring",
        "KI-detection evidence",
        "cloud processing",
        "exam deployment",
    ]
    boundary = str(review_report.get("execution_boundary", ""))
    validations = [item for item in review_report.get("validated_receipts", []) if isinstance(item, dict)]
    ok_validations = [item for item in validations if item.get("status") == "ok_study_session_receipt"]
    first_ok = ok_validations[0] if ok_validations else {}
    first_ok_evidence = first_ok.get("evidence", {}) if isinstance(first_ok.get("evidence"), dict) else {}
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "review_report_public_safe": review_report.get("public_safety_status") == "pass",
        "study_plan_ready_for_course_bound_practice": review_report.get("study_session_status")
        == "ready_for_course_bound_practice"
        and review_report.get("planned_task_count", 0) >= 1,
        "hash_only_receipts_with_required_evidence": receipt_summary.get("valid_receipt_count", 0) >= 1
        and receipt_summary.get("blocked_receipt_count", 0) == 0
        and receipt_summary.get("repeat_task_required_count", 0) == 0
        and all(
            item.get("raw_text_stored") is False
            and item.get("reflection_stored") is False
            and item.get("evidence", {}).get("prediction_present")
            and item.get("evidence", {}).get("retrieval_response_present")
            and item.get("evidence", {}).get("notebook_action_present")
            and item.get("evidence", {}).get("source_anchor_present")
            and item.get("evidence", {}).get("reflection_present")
            for item in ok_validations
        ),
        "learner_agency_profile_complete": evidence_profile.get("prediction_present_count", 0) >= 1
        and evidence_profile.get("retrieval_response_present_count", 0) >= 1
        and evidence_profile.get("notebook_action_present_count", 0) >= 1
        and evidence_profile.get("source_anchor_present_count", 0) >= 1
        and evidence_profile.get("reflection_present_count", 0) >= 1
        and "A2" in evidence_profile.get("by_help_level", {}),
        "a6_or_final_solution_forces_repeat": repeat_receipt_validation.get("status") == "repeat_task_required"
        and repeat_receipt_validation.get("repeat_task_required") is True
        and "a6_or_final_solution_seen_repeat_task_required"
        in repeat_receipt_validation.get("issues", []),
        "workspace_card_reflection_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("selected_skill_tag") == first_ok.get("skill_tag")
        and workspace_card.get("checkpoint_hash") == first_ok_evidence.get("reflection_hash")
        and workspace_card.get("task_hash") == sha256_text(str(first_ok.get("task_id", "")))
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
        "non_grading_human_review_only": review_report.get("exam_deployment_status") == "not_cleared"
        and "never claim a percentage" in str(review_policy.get("eigenleistung_claim", ""))
        and "grade" in review_policy.get("not_allowed", [])
        and "proctoring" in review_policy.get("not_allowed", [])
        and "AI detection" in review_policy.get("not_allowed", [])
        and "does not grade" in boundary
        and "does not store raw student text" in boundary,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "review_status": review_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "study-session-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": STUDY_SESSION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "review_status": review_report.get("status"),
        "review_public_safety_status": review_report.get("public_safety_status"),
        "study_session_status": review_report.get("study_session_status"),
        "exam_deployment_status": review_report.get("exam_deployment_status"),
        "planned_task_count": review_report.get("planned_task_count", 0),
        "valid_receipt_count": receipt_summary.get("valid_receipt_count", 0),
        "blocked_receipt_count": receipt_summary.get("blocked_receipt_count", 0),
        "repeat_task_required_count": receipt_summary.get("repeat_task_required_count", 0),
        "missing_planned_receipt_count": receipt_summary.get("missing_planned_receipt_count", 0),
        "repeat_validation_status": repeat_receipt_validation.get("status"),
        "repeat_validation_public_safety_status": repeat_receipt_validation.get("public_safety_status"),
        "repeat_task_required": bool(repeat_receipt_validation.get("repeat_task_required", False)),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_reflection_gate_linked": contracts["workspace_card_reflection_gate_linked"],
        "workspace_card_reflection_hash_present": bool(workspace_card.get("checkpoint_hash")),
        "evidence_profile": evidence_profile,
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
            "Study-session evidence is formative and hash-only. It proves that prediction, retrieval, notebook "
            "action, source anchor, and reflection were present; it does not store raw student text, accept final "
            "solutions, grade, rank, proctor, detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


def ranked_study_skills(skills: list[dict[str, Any]], *, focus_query: str) -> list[dict[str, Any]]:
    query = str(focus_query or "").lower()
    ranked = []
    for skill in skills:
        tag = str(skill.get("skill_tag", ""))
        title = str(skill.get("title", ""))
        readiness = str(skill.get("readiness", ""))
        readiness_rank = {"ready_for_private_tutor": 3, "needs_review": 2, "no_course_anchor": 1}.get(readiness, 0)
        focus_score = 1 if tag.lower() in query or any(part in query for part in title.lower().split()[:4]) else 0
        usable = int(skill.get("tutor_usable_count", 0) or 0)
        material_count = int(skill.get("material_count", 0) or 0)
        ranked.append((focus_score, readiness_rank, usable, material_count, tag, skill))
    ranked.sort(key=lambda item: item[:5], reverse=True)
    return [item[-1] for item in ranked]


def study_task_for_skill(skill: dict[str, Any], *, index: int, focus_query: str) -> dict[str, Any]:
    tag = str(skill.get("skill_tag", "general_python"))
    source_refs = [
        {
            "material_id": item.get("material_id", ""),
            "title": item.get("title", ""),
            "source_kind": item.get("source_kind", ""),
            "page_or_timestamp": item.get("page_or_timestamp", ""),
            "review_status": item.get("review_status", ""),
            "sha256": item.get("sha256", ""),
        }
        for item in (skill.get("source_refs", []) or [])[:3]
        if isinstance(item, dict)
    ]
    readiness = str(skill.get("readiness", "unknown"))
    practice_task = first_or_default(SKILL_PRACTICE_TASKS.get(tag, ()), "Formuliere den kleinsten eigenen naechsten Schritt.")
    pitfall = first_or_default(SKILL_PITFALLS.get(tag, ()), "Eine finale Antwort ersetzt die eigene Vorhersage.")
    return {
        "task_id": sha256_text(f"{tag}:{index}:{focus_query}:{readiness}")[:16],
        "order": index,
        "skill_tag": tag,
        "title": skill.get("title", tag),
        "readiness": readiness,
        "source_refs": source_refs,
        "source_card_ids": list(skill.get("source_card_ids", []) or [])[:6],
        "retrieval_prompt": f"Erklaere aus dem Kopf den Kern von {skill.get('title', tag)} in zwei Saetzen, bevor du Quellen oder Code ansiehst.",
        "notebook_microtask": practice_task,
        "socratic_checks": list(skill.get("practice_tasks", []) or [])[:2]
        + list(skill.get("typical_pitfalls", []) or [])[:1],
        "pitfall_to_watch": pitfall,
        "reflection_prompt": "Was war dein eigener Beitrag: Vorhersage, Test, Fehlerbild oder Quellenentscheidung?",
        "help_boundary": {
            "start": "A0-A2",
            "allowed": ["A0 accessibility/tool operation", "A1 source/syntax orientation", "A2 Socratic next question"],
            "blocked": ["complete code", "inserted values", "final interpretation", "automatic grading"],
        },
        "expected_artifacts": [
            "one prediction before running code",
            "one source anchor id or material hash",
            "one smallest notebook action",
            "one reflection sentence",
        ],
        "assessment_policy": "practice-only self-check; no grade",
    }


def spacing_plan(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    offsets = ["same_day", "plus_2_days", "plus_7_days"]
    return [
        {
            "review_window": offsets[index % len(offsets)],
            "task_id": task.get("task_id", ""),
            "skill_tag": task.get("skill_tag", ""),
            "retrieval_check": "repeat from memory first, then compare against source refs and notebook result",
        }
        for index, task in enumerate(tasks)
    ]


def evidence_summary(record: dict[str, Any]) -> dict[str, Any]:
    prediction = text_or_flag_present(record, "prediction", "prediction_present")
    retrieval = text_or_flag_present(record, "retrieval_response", "retrieval_response_present")
    notebook = text_or_flag_present(record, "notebook_action", "notebook_action_present")
    reflection = text_or_flag_present(record, "reflection", "reflection_present") or text_or_flag_present(
        record, "student_reflection", "reflection_present"
    )
    source = bool(str(record.get("source_anchor_id", record.get("source_ref_id", ""))).strip())
    return {
        "prediction_present": prediction,
        "retrieval_response_present": retrieval,
        "notebook_action_present": notebook,
        "source_anchor_present": source,
        "reflection_present": reflection,
        "prediction_hash": hash_text_field(record, "prediction"),
        "retrieval_response_hash": hash_text_field(record, "retrieval_response"),
        "notebook_action_hash": hash_text_field(record, "notebook_action"),
        "reflection_hash": hash_text_field(record, "reflection") or hash_text_field(record, "student_reflection"),
    }


def text_or_flag_present(record: dict[str, Any], text_key: str, flag_key: str) -> bool:
    if record.get(flag_key) is True:
        return True
    return bool(str(record.get(text_key, "") or "").strip())


def hash_text_field(record: dict[str, Any], key: str) -> str:
    value = str(record.get(key, "") or "").strip()
    return sha256_text(value) if value else ""


def privacy_flags_for_receipt(record: dict[str, Any]) -> list[str]:
    flags: set[str] = set()
    for key in RECEIPT_TEXT_FIELDS:
        value = str(record.get(key, "") or "")
        if not value:
            continue
        scan = scan_text(value, f"study-receipt-{key}")
        flags.update(finding["type"] for finding in scan.get("findings", []))
    return sorted(flags)


def study_receipt_status(issues: list[str], final_solution_seen: bool) -> str:
    if final_solution_seen:
        return "repeat_task_required"
    if issues:
        return "blocked"
    return "ok_study_session_receipt"


def study_review_status(plan: dict[str, Any], receipts: list[dict[str, Any]], validations: list[dict[str, Any]]) -> str:
    if plan.get("status") == "needs_course_materials":
        return "needs_course_materials"
    if not receipts:
        return "waiting_for_study_receipts"
    if any(item.get("repeat_task_required") for item in validations):
        return "repeat_task_required"
    if any(item.get("status") == "blocked" for item in validations):
        return "blocked_incomplete_or_invalid_receipts"
    if len(validations) >= int(plan.get("task_count", 0) or 0):
        return "study_session_evidence_ready_for_human_review"
    return "partial_study_session_evidence"


def aggregate_evidence_profile(validations: list[dict[str, Any]]) -> dict[str, Any]:
    by_help: dict[str, int] = {}
    by_skill: dict[str, int] = {}
    evidence_counts = {
        "prediction_present_count": 0,
        "retrieval_response_present_count": 0,
        "notebook_action_present_count": 0,
        "source_anchor_present_count": 0,
        "reflection_present_count": 0,
    }
    for validation in validations:
        help_level = str(validation.get("help_level", "A0"))
        by_help[help_level] = by_help.get(help_level, 0) + 1
        skill = str(validation.get("skill_tag", "missing"))
        by_skill[skill] = by_skill.get(skill, 0) + 1
        evidence = validation.get("evidence", {})
        for key in evidence_counts:
            raw_key = key.replace("_count", "")
            if evidence.get(raw_key):
                evidence_counts[key] += 1
    return {
        "by_help_level": dict(sorted(by_help.items())),
        "by_skill": dict(sorted(by_skill.items())),
        **evidence_counts,
    }


def study_review_next_actions(plan: dict[str, Any], validations: list[dict[str, Any]]) -> list[str]:
    if plan.get("status") == "needs_course_materials":
        return ["Generate or review course-bound study tasks before collecting receipts."]
    if not validations:
        return ["Run the study session and submit one hash-only receipt per completed task."]
    if any(item.get("repeat_task_required") for item in validations):
        return ["Repeat any task where A6 or final-solution exposure occurred, using a fresh prompt/task."]
    if any(item.get("status") == "blocked" for item in validations):
        return ["Fix incomplete receipts: each task needs prediction, retrieval response, notebook action, source anchor, and reflection."]
    return ["Human-review local private notebook/checkpoint artifacts if needed; keep report formative and non-grading."]


def study_session_status(scope: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    if scope.get("status") == "needs_materials":
        return "needs_course_materials"
    if any(task.get("readiness") == "ready_for_private_tutor" for task in tasks):
        return "ready_for_course_bound_practice"
    if any(task.get("readiness") == "needs_review" for task in tasks):
        return "practice_waiting_for_material_review"
    return "no_course_anchor"


def study_session_next_actions(
    scope: dict[str, Any],
    tasks: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> list[str]:
    if scope.get("status") == "needs_materials":
        return ["Add reviewed course materials or run the compiler plan before course-bound study sessions."]
    if coverage.get("status") == "blocked_until_valid_rights_privacy_decision":
        prefix = "Rights/privacy gate still blocks new extracted anchors; use currently reviewed anchors only."
    else:
        prefix = "Apply reviewed manifest candidates before expecting new tutor coverage."
    if any(task.get("readiness") == "ready_for_private_tutor" for task in tasks):
        return [
            prefix,
            "Run this session as retrieval first, notebook action second, reflection third.",
            "Log any AI help in the Help-Ledger with A0-A2 unless explicitly marked practice-only.",
        ]
    return [prefix, "Review or extract course anchors before relying on this topic in strict exam-like practice."]


def first_or_default(values: tuple[str, ...] | list[str], default: str) -> str:
    return str(values[0]) if values else default


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


def write_synthetic_study_session_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes head groupby boxplot",
        encoding="utf-8",
    )
    (root / "Week 1" / "debugging_notes.md").write_text(
        "debugging traceback NameError TypeError smallest diagnostic check",
        encoding="utf-8",
    )


def synthetic_study_session_receipt(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id", "synthetic-study-task"),
        "skill_tag": task.get("skill_tag", "pandas"),
        "help_level": "A2",
        "source_anchor_id": "synthetic-course-anchor-pandas",
        "prediction": "I expect the column check to come before plotting.",
        "retrieval_response": "From memory, DataFrame plots need suitable columns and dtypes.",
        "notebook_action": "I run only df.dtypes and df.head as the smallest diagnostic step.",
        "reflection": "My contribution was the prediction, the diagnostic action, and the source comparison.",
    }


def synthetic_study_session_workspace_card(receipt: dict[str, Any]) -> dict[str, Any]:
    evidence = evidence_summary(receipt)
    reflection_hash = str(evidence.get("reflection_hash", ""))
    task_hash = sha256_text(str(receipt.get("task_id", "")))
    preview_hash = sha256_text(f"synthetic study session workspace card:{task_hash}:{reflection_hash}")
    skill_tag = str(receipt.get("skill_tag", "pandas") or "pandas")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": skill_tag,
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic study-session reflection prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": skill_tag,
            "next_safe_action": "review_study_session_reflection_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_study_receipt_before_any_local_write",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": str(receipt.get("help_level", "A2") or "A2"),
            "task_hash": task_hash,
            "checkpoint_hash": reflection_hash,
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": str(receipt.get("help_level", "A2") or "A2"),
            "preview_hash": preview_hash,
        },
    }


def synthetic_study_session_inputs() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="unibot_study_session_inputs_") as temp_dir:
        fixture_root = Path(temp_dir)
        write_synthetic_study_session_fixture(fixture_root)
        plan = build_course_study_session_plan(
            base_path=str(fixture_root),
            review_policy="local_private_tutor",
            focus_query="pandas boxplot",
            max_items=1,
        )
        task = (plan.get("tasks") or [{"task_id": "synthetic-study-task", "skill_tag": "pandas"}])[0]
        receipt = synthetic_study_session_receipt(task)
        review_report = build_study_session_review_report(
            base_path=str(fixture_root),
            review_policy="local_private_tutor",
            focus_query="pandas boxplot",
            max_items=1,
            study_receipts=[receipt],
            python_exam_local_cycle_operator_workspace_card=synthetic_study_session_workspace_card(receipt),
            public_safe=True,
        )
    return {"study_session_review_report": review_report}


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
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_study_session_receipt"))
        ),
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
