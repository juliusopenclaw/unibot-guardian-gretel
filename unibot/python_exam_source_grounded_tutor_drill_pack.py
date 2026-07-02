from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .course_tutor import SKILL_PITFALLS, SKILL_PRACTICE_TASKS, SKILL_PROFILES
from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_SOURCE_GROUNDED_TUTOR_DRILL_PACK_SCHEMA_VERSION = "unibot-python-exam-source-grounded-tutor-drill-pack-v1"
PYTHON_EXAM_SOURCE_GROUNDED_TUTOR_DRILL_PACK_ENDPOINT = "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack"


def build_python_exam_source_grounded_tutor_drill_pack(
    *,
    course_exam_coverage_dashboard: dict[str, Any] | None = None,
    exam_skill_drilldown: dict[str, Any] | None = None,
    skill_to_workspace_session_carryover: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    max_drills: int = 12,
    public_safe: bool = True,
) -> dict[str, Any]:
    dashboard = course_exam_coverage_dashboard if isinstance(course_exam_coverage_dashboard, dict) else {}
    drilldown = exam_skill_drilldown if isinstance(exam_skill_drilldown, dict) else {}
    carryover = skill_to_workspace_session_carryover if isinstance(skill_to_workspace_session_carryover, dict) else {}
    selected = effective_skill_tag(selected_skill_tag, carryover, drilldown, dashboard)
    rows = source_skill_rows(dashboard, drilldown, selected=selected, max_drills=max_drills)
    drills = [build_skill_drill(row, carryover=carryover, selected=selected) for row in rows]
    summary = drill_pack_summary(drills, dashboard, drilldown, carryover)
    payload = {
        "schema_version": PYTHON_EXAM_SOURCE_GROUNDED_TUTOR_DRILL_PACK_SCHEMA_VERSION,
        "artifact_type": "python_exam_source_grounded_tutor_drill_pack",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Source-Grounded Tutor Drill Pack. It turns Course Exam Coverage Dashboard, "
            "Exam-Skill-Drilldown, and Skill-to-Workspace Session Carryover metadata into A0-A2-only tutor drills: "
            "safe microtasks, retrieval questions, notebook checkpoint templates, typical-error hints, source-card "
            "anchors, Help-Ledger previews, and not_cleared receipts. It never returns raw queries, course raw text, "
            "notebook code, values, solutions, final interpretations, rankings, grading, proctoring, AI detection, "
            "or exam clearance."
        ),
        "selected_skill_tag": selected,
        "drill_pack_summary": summary,
        "skill_drills": drills,
        "pack_receipt": pack_receipt(summary, drills),
        "dry_run_default": True,
        "local_writes_requested": False,
        "operator_confirmation_required_for_local_write": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "ranking_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Tutor Drill Pack bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def source_skill_rows(
    dashboard: dict[str, Any],
    drilldown: dict[str, Any],
    *,
    selected: str,
    max_drills: int,
) -> list[dict[str, Any]]:
    rows = [normalize_dashboard_row(item) for item in (dashboard.get("skill_dashboard", []) or []) if isinstance(item, dict)]
    if not rows:
        rows = [normalize_drilldown_card(item) for item in (drilldown.get("skill_map", []) or []) if isinstance(item, dict)]
    if not rows and isinstance(drilldown.get("selected_skill"), dict):
        rows = [normalize_drilldown_card(drilldown["selected_skill"])]
    rows = [row for row in rows if row.get("skill_tag")]
    rows.sort(key=lambda row: skill_sort_key(row, selected))
    return rows[: max(1, int(max_drills or 12))]


def normalize_dashboard_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(row.get("skill_tag", "")),
        "title": str(row.get("title", "")),
        "exam_task_type": str(row.get("exam_task_type", "")),
        "workspace_readiness": str(row.get("workspace_readiness", "unknown")),
        "source_anchor_count": int(row.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(row.get("reviewed_notebook_anchor_count", 0) or 0),
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "checkpoint_hash_count": int(row.get("checkpoint_hash_count", 0) or 0),
        "help_level_profile": row.get("help_level_profile", {}) if isinstance(row.get("help_level_profile"), dict) else {},
        "open_operator_confirmation_count": int(row.get("open_operator_confirmation_count", 0) or 0),
        "allowed_exam_help": [str(item) for item in (row.get("allowed_exam_help", []) or [])][:6],
    }


def normalize_drilldown_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(card.get("skill_tag", "")),
        "title": str(card.get("title", "")),
        "exam_task_type": str(card.get("exam_task_type", "")),
        "workspace_readiness": str(card.get("exam_workspace_readiness", card.get("workspace_readiness", "unknown"))),
        "source_anchor_count": int(card.get("source_anchor_count", 0) or 0),
        "reviewed_notebook_anchor_count": int(card.get("reviewed_notebook_anchor_count", 0) or 0),
        "source_card_ids": [str(item) for item in (card.get("source_card_ids", []) or [])][:8],
        "checkpoint_hash_count": 0,
        "help_level_profile": {},
        "open_operator_confirmation_count": 0,
        "allowed_exam_help": [str(item) for item in (card.get("allowed_exam_help", []) or [])][:6],
    }


def skill_sort_key(row: dict[str, Any], selected: str) -> tuple[int, int, int, str]:
    selected_rank = 0 if row.get("skill_tag") == selected else 1
    ready_rank = 0 if row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run" else 1
    anchors = -int(row.get("source_anchor_count", 0) or 0)
    return (selected_rank, ready_rank, anchors, str(row.get("skill_tag", "")))


def build_skill_drill(row: dict[str, Any], *, carryover: dict[str, Any], selected: str) -> dict[str, Any]:
    tag = str(row.get("skill_tag", ""))
    source_card_ids = [str(item) for item in (row.get("source_card_ids", []) or [])][:8]
    source_anchor_count = int(row.get("source_anchor_count", 0) or 0)
    checkpoint_template = notebook_checkpoint_template(row, carryover)
    task_seed = {
        "skill_tag": tag,
        "source_card_ids": source_card_ids,
        "source_anchor_count": source_anchor_count,
        "checkpoint_template_hash": checkpoint_template["checkpoint_template_hash"],
    }
    return {
        "skill_tag": tag,
        "title": row.get("title") or profile_title(tag),
        "selected": bool(tag and tag == selected),
        "status": "drill_ready" if source_card_ids and source_anchor_count >= 1 else "drill_attention_needs_source_anchor",
        "exam_deployment_status": "not_cleared",
        "a0_a2_help_level": "A2",
        "allowed_help_levels": allowed_help_levels(row),
        "source_anchor_metadata": {
            "source_card_ids": source_card_ids,
            "source_anchor_count": source_anchor_count,
            "reviewed_notebook_anchor_count": int(row.get("reviewed_notebook_anchor_count", 0) or 0),
            "source_anchor_ids_returned": False,
            "raw_anchor_text_returned": False,
            "local_paths_returned": False,
        },
        "microtasks": microtasks_for_skill(tag, task_seed),
        "retrieval_questions": retrieval_questions_for_skill(tag, source_card_ids),
        "notebook_checkpoint_suggestions": checkpoint_template,
        "typical_error_hints": typical_error_hints(tag),
        "help_ledger_preview": help_ledger_preview(row, checkpoint_template),
        "drill_receipt": drill_receipt(row, checkpoint_template),
        "dry_run_default": True,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "ranking_returned": False,
    }


def microtasks_for_skill(skill_tag: str, seed: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = list(SKILL_PRACTICE_TASKS.get(skill_tag, ()))[:3] or [
        "Name the concept boundary, expected own check, and one uncertainty before using the notebook.",
        "Write a short reflection on which source card supports the next step.",
    ]
    result = []
    for index, prompt in enumerate(tasks, start=1):
        task_seed = {**seed, "index": index, "prompt": prompt}
        result.append(
            {
                "task_id": sha256_text(json.dumps(task_seed, sort_keys=True, ensure_ascii=False))[:16],
                "task_hash": sha256_text(json.dumps(task_seed, sort_keys=True, ensure_ascii=False)),
                "prompt_summary": prompt,
                "help_level": "A2",
                "requires_student_prediction": True,
                "requires_source_check": True,
                "requires_reflection": True,
                "complete_code_returned": False,
                "solution_returned": False,
                "values_returned": False,
            }
        )
    return result


def retrieval_questions_for_skill(skill_tag: str, source_card_ids: list[str]) -> list[dict[str, Any]]:
    cards = source_card_ids[:3] or profile_source_cards(skill_tag)[:3]
    questions = []
    for index, source_id in enumerate(cards, start=1):
        seed = {"skill_tag": skill_tag, "source_id": source_id, "index": index}
        questions.append(
            {
                "question_id": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))[:16],
                "source_card_id": source_id,
                "question": f"Which boundary or concept from source card {source_id} should I check before the next {skill_tag} notebook step?",
                "help_level": "A1",
                "raw_source_text_returned": False,
                "raw_query_returned": False,
            }
        )
    return questions


def notebook_checkpoint_template(row: dict[str, Any], carryover: dict[str, Any]) -> dict[str, Any]:
    tag = str(row.get("skill_tag", ""))
    checkpoint_hash = first_text(
        nested(carryover, "carryover_summary", "checkpoint_hash"),
        nested(carryover, "carryover_packet", "session_receipt", "checkpoint_hash"),
    )
    template_seed = {
        "skill_tag": tag,
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "checkpoint_hash_present": bool(checkpoint_hash),
        "help_level": "A2",
    }
    return {
        "status": "checkpoint_template_ready",
        "skill_tag": tag,
        "checkpoint_template_hash": sha256_text(json.dumps(template_seed, sort_keys=True, ensure_ascii=False)),
        "latest_checkpoint_hash": checkpoint_hash,
        "cell_index_default": 0,
        "cell_type_default": "code",
        "requires_prediction": True,
        "requires_notebook_action": True,
        "requires_reflection": True,
        "raw_cell_template_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def typical_error_hints(skill_tag: str) -> list[dict[str, Any]]:
    hints = list(SKILL_PITFALLS.get(skill_tag, ()))[:3] or [
        "The next action is chosen before the relevant source or notebook state is checked.",
        "A final conclusion is written before the student's own checkpoint exists.",
    ]
    return [
        {
            "hint_hash": sha256_text(json.dumps({"skill_tag": skill_tag, "hint": hint}, sort_keys=True, ensure_ascii=False)),
            "hint": hint,
            "help_level": "A2",
            "solution_returned": False,
            "final_interpretation_returned": False,
        }
        for hint in hints
    ]


def help_ledger_preview(row: dict[str, Any], checkpoint_template: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "help_ledger_preview_ready",
        "skill_tags": [row.get("skill_tag", "")],
        "help_level": "A2",
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "checkpoint_template_hash": checkpoint_template.get("checkpoint_template_hash", ""),
        "write_default": False,
        "requires_operator_confirmation": True,
        "raw_help_text_returned": False,
        "raw_query_returned": False,
        "local_paths_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def drill_receipt(row: dict[str, Any], checkpoint_template: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "skill_tag": row.get("skill_tag", ""),
        "source_card_ids": [str(item) for item in (row.get("source_card_ids", []) or [])][:8],
        "checkpoint_template_hash": checkpoint_template.get("checkpoint_template_hash", ""),
        "exam_deployment_status": "not_cleared",
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "drill_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def drill_pack_summary(
    drills: list[dict[str, Any]],
    dashboard: dict[str, Any],
    drilldown: dict[str, Any],
    carryover: dict[str, Any],
) -> dict[str, Any]:
    ready_count = len([item for item in drills if item.get("status") == "drill_ready"])
    task_count = sum(len(item.get("microtasks", []) or []) for item in drills)
    return {
        "status": "python_exam_source_grounded_tutor_drill_pack_ready" if drills and ready_count == len(drills) else "python_exam_source_grounded_tutor_drill_pack_attention",
        "skill_count": len(drills),
        "ready_drill_count": ready_count,
        "microtask_count": task_count,
        "retrieval_question_count": sum(len(item.get("retrieval_questions", []) or []) for item in drills),
        "checkpoint_template_count": len([item for item in drills if item.get("notebook_checkpoint_suggestions")]),
        "help_status": "a0_a2_only",
        "selected_skill_tag": effective_skill_tag("", carryover, drilldown, dashboard),
        "carryover_status": carryover.get("status", "missing"),
        "dashboard_status": dashboard.get("status", "missing"),
        "drilldown_status": drilldown.get("status", "missing"),
        "not_cleared_receipt": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "exam_deployment_status": "not_cleared",
    }


def pack_receipt(summary: dict[str, Any], drills: list[dict[str, Any]]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "drill_receipts": [nested(item, "drill_receipt", "receipt_hash") for item in drills],
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "tutor_drill_pack_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "skill_count": summary.get("skill_count", 0),
        "microtask_count": summary.get("microtask_count", 0),
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def allowed_help_levels(row: dict[str, Any]) -> list[str]:
    allowed = " ".join(str(item) for item in (row.get("allowed_exam_help", []) or []))
    levels = [level for level in ["A0", "A1", "A2"] if level in allowed]
    return levels or ["A0", "A1", "A2"]


def profile_title(skill_tag: str) -> str:
    for profile in SKILL_PROFILES:
        if profile.skill_tag == skill_tag:
            return profile.title
    return skill_tag or "Python skill"


def profile_source_cards(skill_tag: str) -> list[str]:
    for profile in SKILL_PROFILES:
        if profile.skill_tag == skill_tag:
            return list(profile.source_card_ids)
    return []


def effective_skill_tag(selected_skill_tag: str, *values: Any) -> str:
    if selected_skill_tag:
        return str(selected_skill_tag)
    for value in values:
        if isinstance(value, dict):
            for path in [
                ("carryover_summary", "selected_skill_tag"),
                ("selected_skill_tag",),
                ("selected_skill", "skill_tag"),
                ("dashboard_summary", "selected_skill_tag"),
            ]:
                found = nested(value, *path)
                if found:
                    return str(found)
    return "python_skill"


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "python_exam_source_grounded_tutor_drill_pack_ready":
        return [
            "Use the drill pack for A0-A2 practice and checkpoint preparation only.",
            "Run Skill-to-Workspace Carryover again after the next notebook checkpoint.",
            "Keep not_cleared; do not infer grades, rankings, or exam authorization.",
        ]
    return [
        "Review source-anchor coverage before relying on all drills.",
        "Keep drills A0-A2 and metadata-only while closing material gaps.",
    ]


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-source-grounded-tutor-drill-pack")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
