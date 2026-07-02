from __future__ import annotations

import json
from datetime import datetime, timezone
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
from .tutor_coverage import build_course_tutor_coverage_plan


STUDY_SESSION_SCHEMA_VERSION = "unibot-course-study-session-plan-v1"
STUDY_SESSION_RECEIPT_SCHEMA_VERSION = "unibot-course-study-session-receipt-v1"
STUDY_SESSION_REVIEW_SCHEMA_VERSION = "unibot-course-study-session-review-v1"

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
    public_safe: bool = True,
) -> dict[str, Any]:
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
        "review_policy": {
            "eigenleistung_claim": "Use evidence profile, source anchors, help levels, blocked repeats, and reflections; never claim a percentage.",
            "human_review_path": "A human can inspect private notebook/checkpoint artifacts using hashes and local-only references outside this report.",
            "not_allowed": ["grade", "ranking", "proctoring", "AI detection", "raw private text publication"],
        },
        "next_actions": study_review_next_actions(plan, validations),
    }
    attach_public_scan(report, public_safe=public_safe, source_name="study-session-review-report")
    return report


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
