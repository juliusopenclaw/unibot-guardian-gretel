from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import (
    DEFAULT_COURSE_ID,
    SKILL_PROFILES,
    build_course_exam_scope,
    safe_course_id,
    scan_course_intake,
)
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .public_safety import scan_text


TUTOR_COVERAGE_SCHEMA_VERSION = "unibot-course-tutor-coverage-plan-v1"


def build_course_tutor_coverage_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    scan = scan_course_intake(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    current_records = [item for item in scan.get("records", []) if isinstance(item, dict)]
    current_scope = build_course_exam_scope(
        course_id,
        records=current_records,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    manifest_plan = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts or [],
        public_safe=public_safe,
    )
    candidates = [
        item
        for item in manifest_plan.get("manifest_update_candidates", [])
        if isinstance(item, dict) and item.get("validation_status") == "ok"
    ]
    projected_records = apply_candidate_metadata_preview(current_records, candidates)
    projected_scope = build_course_exam_scope(
        course_id,
        records=projected_records,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    skill_coverage = build_skill_coverage(current_scope, projected_scope, candidates)
    plan = {
        "schema_version": TUTOR_COVERAGE_SCHEMA_VERSION,
        "artifact_type": "course_tutor_coverage_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": coverage_status(manifest_plan, current_scope, projected_scope, candidates),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "This is a forecast-only tutor coverage plan. It does not write manifests, "
            "does not run OCR or transcription, and does not expose raw course text or local paths."
        ),
        "intake_status": scan.get("status", "unknown"),
        "manifest_update_status": manifest_plan.get("status"),
        "manifest_candidate_summary": manifest_plan.get("candidate_summary", {}),
        "current_scope_summary": scope_summary(current_scope),
        "projected_scope_summary": projected_scope_summary(current_scope, projected_scope, candidates),
        "skill_coverage": skill_coverage,
        "priority_skill_gaps": priority_skill_gaps(skill_coverage),
        "coverage_policy": {
            "ready_means": "at least one reviewed private tutor anchor for the skill",
            "forecast_rule": "projected coverage counts only validated reviewed receipt metadata candidates",
            "not_allowed": [
                "raw course text",
                "local paths",
                "automatic grading",
                "exam clearance",
                "public release of private material",
            ],
        },
        "next_actions": coverage_next_actions(manifest_plan, skill_coverage, candidates),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="course-tutor-coverage-plan")
    return plan


def apply_candidate_metadata_preview(
    records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(record.get("material_id", "")): dict(record) for record in records if record.get("material_id")}
    for candidate in candidates:
        material_id = str(candidate.get("material_id", ""))
        if not material_id:
            continue
        current = by_id.get(material_id, {"material_id": material_id, "title": f"Reviewed extraction {material_id}"})
        updated = dict(current)
        updated.update(
            {
                "source_kind": candidate.get("source_kind_after_review", current.get("source_kind", "document")),
                "permission_status": candidate.get("permission_status_after_review", "private_course_use_only"),
                "publish_policy": candidate.get("publish_policy_after_review", "private_only"),
                "extraction_status": candidate.get("extraction_status_after_review", "text_extracted"),
                "review_status": candidate.get("review_status_after_review", "reviewed_for_private_tutor"),
                "sha256": candidate.get("sha256_after_review", current.get("sha256", "")),
                "skill_tags": list(candidate.get("skill_tags", []) or current.get("skill_tags", []) or [])[:6],
                "source_card_ids": list(
                    candidate.get("source_card_ids", []) or current.get("source_card_ids", []) or []
                )[:6],
                "notes": "forecast_from_reviewed_private_extraction_receipt",
            }
        )
        by_id[material_id] = updated
    return list(by_id.values())


def scope_summary(scope: dict[str, Any]) -> dict[str, Any]:
    skills = [item for item in scope.get("skills", []) if isinstance(item, dict)]
    return {
        "status": scope.get("status"),
        "material_summary": scope.get("material_summary", {}),
        "ready_skill_count": len([item for item in skills if item.get("readiness") == "ready_for_private_tutor"]),
        "needs_review_skill_count": len([item for item in skills if item.get("readiness") == "needs_review"]),
        "no_course_anchor_skill_count": len([item for item in skills if item.get("readiness") == "no_course_anchor"]),
        "skill_count": len(skills),
    }


def projected_scope_summary(
    current_scope: dict[str, Any],
    projected_scope: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    current = scope_summary(current_scope)
    projected = scope_summary(projected_scope)
    return {
        **projected,
        "candidate_material_count": len(candidates),
        "ready_skill_uplift": max(0, projected["ready_skill_count"] - current["ready_skill_count"]),
        "needs_review_reduction": max(0, current["needs_review_skill_count"] - projected["needs_review_skill_count"]),
    }


def build_skill_coverage(
    current_scope: dict[str, Any],
    projected_scope: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_by_tag = {item.get("skill_tag"): item for item in current_scope.get("skills", []) if isinstance(item, dict)}
    projected_by_tag = {item.get("skill_tag"): item for item in projected_scope.get("skills", []) if isinstance(item, dict)}
    candidate_counts: dict[str, int] = {}
    for candidate in candidates:
        for tag in candidate.get("skill_tags", []) or []:
            candidate_counts[str(tag)] = candidate_counts.get(str(tag), 0) + 1
    coverage = []
    for profile in SKILL_PROFILES:
        current = current_by_tag.get(profile.skill_tag, {})
        projected = projected_by_tag.get(profile.skill_tag, {})
        coverage.append(
            {
                "skill_tag": profile.skill_tag,
                "title": profile.title,
                "current_readiness": current.get("readiness", "no_course_anchor"),
                "projected_readiness": projected.get("readiness", "no_course_anchor"),
                "current_material_count": current.get("material_count", 0),
                "projected_material_count": projected.get("material_count", 0),
                "current_tutor_usable_count": current.get("tutor_usable_count", 0),
                "projected_tutor_usable_count": projected.get("tutor_usable_count", 0),
                "candidate_count": candidate_counts.get(profile.skill_tag, 0),
                "source_card_ids": list(profile.source_card_ids),
                "coverage_delta": int(projected.get("tutor_usable_count", 0) or 0)
                - int(current.get("tutor_usable_count", 0) or 0),
            }
        )
    return coverage


def priority_skill_gaps(skill_coverage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = [
        item
        for item in skill_coverage
        if item.get("projected_readiness") != "ready_for_private_tutor"
    ]
    gaps.sort(key=lambda item: (item.get("candidate_count", 0), item.get("current_material_count", 0)), reverse=True)
    return [
        {
            "skill_tag": item.get("skill_tag", ""),
            "title": item.get("title", ""),
            "current_readiness": item.get("current_readiness", ""),
            "projected_readiness": item.get("projected_readiness", ""),
            "candidate_count": item.get("candidate_count", 0),
            "next_review_need": "review candidate receipts" if item.get("candidate_count", 0) else "add or extract a course anchor",
        }
        for item in gaps[:8]
    ]


def coverage_status(
    manifest_plan: dict[str, Any],
    current_scope: dict[str, Any],
    projected_scope: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> str:
    manifest_status = str(manifest_plan.get("status", ""))
    if manifest_status.startswith("blocked"):
        return manifest_status
    if not current_scope.get("skills"):
        return "needs_scope_map"
    current_ready = scope_summary(current_scope)["ready_skill_count"]
    projected_ready = scope_summary(projected_scope)["ready_skill_count"]
    if candidates and projected_ready > current_ready:
        return "coverage_uplift_ready_after_private_manifest_update"
    if candidates:
        return "candidate_metadata_ready_no_new_skill_uplift"
    return "waiting_for_reviewed_manifest_candidates"


def coverage_next_actions(
    manifest_plan: dict[str, Any],
    skill_coverage: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[str]:
    status = str(manifest_plan.get("status", ""))
    if status == "blocked_until_valid_rights_privacy_decision":
        return ["Validate the rights/privacy decision before expecting course coverage uplift from extracted materials."]
    if status.startswith("blocked"):
        return ["Fix the blocked manifest update plan before using coverage forecasts."]
    if candidates:
        gaps = priority_skill_gaps(skill_coverage)
        next_gap = gaps[0]["skill_tag"] if gaps else "none"
        return [
            "Apply reviewed private manifest metadata, rebuild ExamScopeMap, then rerun course tutor eval.",
            f"After applying candidates, prioritize remaining gap: {next_gap}.",
        ]
    return ["Complete human review for extracted materials, then regenerate this coverage plan."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
