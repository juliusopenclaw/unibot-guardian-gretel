from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, SKILL_PROFILES, safe_course_id
from .material_coverage_run import build_course_material_coverage_run
from .materials import sha256_text
from .public_safety import scan_text


EXAM_SKILL_DRILLDOWN_SCHEMA_VERSION = "unibot-exam-skill-drilldown-v1"
DRILLDOWN_ENDPOINT = "/api/unibot/course/exam-skill-drilldown"
OPERATOR_RUN_ENDPOINT = "/api/unibot/exam-workspace/operator-run"


def build_exam_skill_drilldown(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | None = None,
    private_manifest_path: str | None = None,
    manifest_apply_journal_path: str | None = None,
    tutor_index_path: str | None = None,
    tutor_index_journal_path: str | None = None,
    focus_query: str = "",
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    effective_focus = selected_skill_tag or focus_query
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
        focus_query=effective_focus,
        public_safe=public_safe,
    )
    skills = [item for item in coverage.get("skill_coverage", []) if isinstance(item, dict)]
    selected = select_skill(skills, selected_skill_tag=selected_skill_tag, focus_query=focus_query)
    cards = [skill_card(item, selected_skill_tag=str(selected.get("skill_tag", ""))) for item in skills]
    ready_cards = [item for item in cards if item.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run"]
    gap_cards = [item for item in cards if item.get("exam_workspace_readiness") != "ready_for_exam_workspace_dry_run"]
    selected_card = skill_card(selected, selected_skill_tag=str(selected.get("skill_tag", ""))) if selected else {}
    selected_ready = selected_card.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run"
    report = {
        "schema_version": EXAM_SKILL_DRILLDOWN_SCHEMA_VERSION,
        "artifact_type": "exam_skill_drilldown",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": "exam_skill_drilldown_ready_for_workspace" if selected_ready else "exam_skill_drilldown_needs_material_work",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Course-exam skill drilldown. It turns the metadata-only material coverage report into a selectable "
            "Python exam skill map and prepares a dry-run Start Exam Workspace action. It does not return raw "
            "course text, raw queries, notebook code, local paths, values, final interpretations, grading, "
            "proctoring, AI detection, or exam clearance."
        ),
        "coverage_summary": {
            **coverage.get("coverage_summary", {}),
            "ready_skill_tags": [item.get("skill_tag", "") for item in ready_cards],
            "gap_skill_tags": [item.get("skill_tag", "") for item in gap_cards],
        },
        "selected_skill": selected_card,
        "skill_map": cards,
        "workspace_start_action": workspace_start_action(selected_card, ready=selected_ready),
        "operator_payload_template": operator_payload_template(
            course_id=safe_id,
            selected_skill=selected_card,
            ready=selected_ready,
        ),
        "notebook_checkpoint_template": notebook_checkpoint_template(selected_card, ready=selected_ready),
        "help_ledger_preview_template": help_ledger_preview_template(selected_card, ready=selected_ready),
        "skill_to_workspace_live_flow": skill_to_workspace_live_flow(selected_card, ready=selected_ready),
        "material_gap_queue": material_gap_queue(gap_cards),
        "coverage_receipt": {
            "coverage_status": coverage.get("status", "unknown"),
            "coverage_hash": sha256_text(json.dumps(safe_coverage_receipt_source(coverage), sort_keys=True, ensure_ascii=False)),
            "source_report_type": coverage.get("artifact_type", ""),
            "raw_material_returned": False,
            "local_paths_returned": False,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Drilldown liefert nur technische Bot-Navigation."
        ),
        "next_actions": drilldown_next_actions(selected_card, ready=selected_ready, gap_cards=gap_cards),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def select_skill(skills: list[dict[str, Any]], *, selected_skill_tag: str, focus_query: str) -> dict[str, Any]:
    if not skills:
        return {}
    tag = str(selected_skill_tag or "").strip().lower()
    if tag:
        for skill in skills:
            if str(skill.get("skill_tag", "")).lower() == tag:
                return skill
    focus = str(focus_query or "").lower()
    if focus:
        focused = [
            skill
            for skill in skills
            if str(skill.get("skill_tag", "")).lower() in focus
            or any(part and part in focus for part in str(skill.get("title", "")).lower().split()[:5])
        ]
        if focused:
            return sorted(focused, key=skill_priority_key)[0]
    ready = [skill for skill in skills if skill.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run"]
    if ready:
        return sorted(ready, key=skill_priority_key)[0]
    return sorted(skills, key=skill_priority_key)[0]


def skill_priority_key(skill: dict[str, Any]) -> tuple[int, int, int, str]:
    ready_rank = 0 if skill.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run" else 1
    core_rank = 0 if skill.get("skill_tag") in {"python_lists", "control_flow", "pandas", "debugging"} else 1
    anchors = -int(skill.get("source_anchor_count", 0) or 0)
    return (ready_rank, core_rank, anchors, str(skill.get("skill_tag", "")))


def skill_card(skill: dict[str, Any], *, selected_skill_tag: str) -> dict[str, Any]:
    tag = str(skill.get("skill_tag", ""))
    notebook = skill.get("notebook_exercise", {}) if isinstance(skill.get("notebook_exercise"), dict) else {}
    return {
        "skill_tag": tag,
        "title": skill.get("title", ""),
        "selected": bool(tag and tag == selected_skill_tag),
        "exam_task_type": skill.get("exam_task_type", ""),
        "exam_workspace_readiness": skill.get("exam_workspace_readiness", "unknown"),
        "current_readiness": skill.get("current_readiness", "unknown"),
        "projected_readiness": skill.get("projected_readiness", "unknown"),
        "private_index_readiness": skill.get("private_index_readiness", "unknown"),
        "source_anchor_count": skill.get("source_anchor_count", 0),
        "reviewed_notebook_anchor_count": skill.get("reviewed_notebook_anchor_count", 0),
        "material_count": skill.get("material_count", 0),
        "tutor_usable_count": skill.get("tutor_usable_count", 0),
        "ocr_gap_count": skill.get("ocr_gap_count", 0),
        "video_transcription_gap_count": skill.get("video_transcription_gap_count", 0),
        "queued_job_count": skill.get("queued_job_count", 0),
        "source_card_ids": list(skill.get("source_card_ids", []) or [])[:8],
        "source_anchor_metadata": {
            "source_anchor_count": skill.get("source_anchor_count", 0),
            "reviewed_notebook_anchor_count": skill.get("reviewed_notebook_anchor_count", 0),
            "source_card_ids": list(skill.get("source_card_ids", []) or [])[:8],
            "source_anchor_ids_returned": False,
            "raw_anchor_text_returned": False,
        },
        "notebook_exercise": {
            "status": notebook.get("status", "unknown"),
            "task_id": notebook.get("task_id", ""),
            "notebook_microtask_hash": notebook.get("notebook_microtask_hash", ""),
            "raw_task_text_returned": False,
        },
        "allowed_exam_help": list(skill.get("allowed_exam_help", []) or [])[:4],
        "blocked_help": list(skill.get("blocked_help", []) or [])[:6],
        "next_step": skill.get("next_step", "review coverage state"),
        "recommended_operator_endpoint": OPERATOR_RUN_ENDPOINT,
        "recommended_help_level": "A2",
        "start_button_enabled": skill.get("exam_workspace_readiness") == "ready_for_exam_workspace_dry_run",
    }


def workspace_start_action(selected_skill: dict[str, Any], *, ready: bool) -> dict[str, Any]:
    tag = str(selected_skill.get("skill_tag", ""))
    title = str(selected_skill.get("title", tag or "selected skill"))
    return {
        "status": "ready" if ready else "not_ready",
        "label": f"Start Workspace: {title}" if ready else f"Prepare Skill: {title}",
        "skill_tag": tag,
        "endpoint": OPERATOR_RUN_ENDPOINT if ready else "",
        "method": "POST" if ready else "",
        "recommended_help_level": "A2",
        "focus_query_template": tag,
        "requires_operator_confirmation_for_writes": True,
        "dry_run_default": True,
        "exam_deployment_status": "not_cleared",
    }


def operator_payload_template(*, course_id: str, selected_skill: dict[str, Any], ready: bool) -> dict[str, Any]:
    notebook = selected_skill.get("notebook_exercise", {}) if isinstance(selected_skill.get("notebook_exercise"), dict) else {}
    return {
        "status": "template_ready" if ready else "blocked_until_skill_ready",
        "endpoint": OPERATOR_RUN_ENDPOINT if ready else "",
        "course_id": course_id,
        "selected_skill_tag": selected_skill.get("skill_tag", ""),
        "focus_query": selected_skill.get("skill_tag", ""),
        "query": selected_skill.get("skill_tag", ""),
        "task_id": notebook.get("task_id", ""),
        "source_card_ids": list(selected_skill.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": selected_skill.get("source_anchor_count", 0),
        "notebook_checkpoint_template_hash": sha256_text(
            json.dumps(notebook_checkpoint_template(selected_skill, ready=ready), sort_keys=True, ensure_ascii=False)
        ),
        "requested_help_level": "A2",
        "exam_status": "strict",
        "operator_confirmations_default": "all_false_dry_run",
        "study_receipt_defaults": {
            "prediction_present": False,
            "notebook_action_present": False,
            "reflection_present": False,
        },
        "local_journal_paths_supplied_by_client": True,
        "raw_query_included": False,
        "raw_cell_included": False,
        "raw_source_text_included": False,
        "notebook_code_included": False,
        "local_paths_returned": False,
    }


def notebook_checkpoint_template(selected_skill: dict[str, Any], *, ready: bool) -> dict[str, Any]:
    notebook = selected_skill.get("notebook_exercise", {}) if isinstance(selected_skill.get("notebook_exercise"), dict) else {}
    return {
        "status": "template_ready" if ready else "blocked_until_skill_ready",
        "skill_tag": selected_skill.get("skill_tag", ""),
        "task_id": notebook.get("task_id", ""),
        "source_card_ids": list(selected_skill.get("source_card_ids", []) or [])[:8],
        "source_anchor_count": selected_skill.get("source_anchor_count", 0),
        "cell_index_default": 0,
        "cell_type_default": "code",
        "requested_help_level": "A2",
        "requires_prediction": True,
        "requires_notebook_action": True,
        "requires_reflection": True,
        "raw_cell_template_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def help_ledger_preview_template(selected_skill: dict[str, Any], *, ready: bool) -> dict[str, Any]:
    return {
        "status": "template_ready" if ready else "blocked_until_skill_ready",
        "skill_tags": [selected_skill.get("skill_tag", "")] if selected_skill.get("skill_tag") else [],
        "help_level": "A2",
        "allowed_help": list(selected_skill.get("allowed_exam_help", []) or [])[:4],
        "blocked_help": list(selected_skill.get("blocked_help", []) or [])[:6],
        "source_card_ids": list(selected_skill.get("source_card_ids", []) or [])[:8],
        "write_default": False,
        "requires_operator_confirmation": True,
        "raw_help_text_returned": False,
        "raw_query_returned": False,
        "local_paths_returned": False,
    }


def skill_to_workspace_live_flow(selected_skill: dict[str, Any], *, ready: bool) -> dict[str, Any]:
    return {
        "status": "ready_to_execute_operator_dry_run" if ready else "waiting_for_skill_material_readiness",
        "selected_skill_tag": selected_skill.get("skill_tag", ""),
        "drilldown_endpoint": DRILLDOWN_ENDPOINT,
        "operator_endpoint": OPERATOR_RUN_ENDPOINT if ready else "",
        "flow_order": [
            "exam_skill_drilldown",
            "prefill_operator_payload_from_selected_skill",
            "start_exam_workspace_operator_run_dry_run",
            "review_receipt_before_any_local_write",
        ],
        "dry_run_default": True,
        "operator_confirmations_default": "all_false",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def material_gap_queue(gap_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for item in sorted(gap_cards, key=lambda card: (-int(card.get("queued_job_count", 0) or 0), str(card.get("skill_tag", ""))))[:8]:
        queue.append(
            {
                "skill_tag": item.get("skill_tag", ""),
                "title": item.get("title", ""),
                "readiness": item.get("exam_workspace_readiness", "unknown"),
                "ocr_gap_count": item.get("ocr_gap_count", 0),
                "video_transcription_gap_count": item.get("video_transcription_gap_count", 0),
                "next_step": item.get("next_step", ""),
            }
        )
    return queue


def safe_coverage_receipt_source(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": coverage.get("status", ""),
        "coverage_summary": coverage.get("coverage_summary", {}),
        "next_exam_workspace_start_point": coverage.get("next_exam_workspace_start_point", {}),
        "skill_count": len([item for item in coverage.get("skill_coverage", []) if isinstance(item, dict)]),
    }


def drilldown_next_actions(selected_skill: dict[str, Any], *, ready: bool, gap_cards: list[dict[str, Any]]) -> list[str]:
    if ready:
        return [
            f"Start the dry-run Exam Workspace for {selected_skill.get('skill_tag', 'the selected skill')} with A2 help.",
            "Keep all local writes behind individual operator confirmations and keep exam_deployment_status not_cleared.",
        ]
    if selected_skill:
        return [str(selected_skill.get("next_step", "Review the selected skill coverage before workspace use."))]
    if gap_cards:
        return [str(gap_cards[0].get("next_step", "Review the next course-material gap."))]
    return ["Add or review local course material before starting an exam workspace."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-skill-drilldown")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
