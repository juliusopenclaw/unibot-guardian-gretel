from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text
from .python_exam_drill_session_review_loop import build_python_exam_drill_session_review_loop
from .python_exam_drill_session_runner import build_python_exam_drill_session_runner


PYTHON_EXAM_DRILL_LOOP_CONTROL_PANEL_SCHEMA_VERSION = "unibot-python-exam-drill-loop-control-panel-v1"
PYTHON_EXAM_DRILL_LOOP_CONTROL_PANEL_ENDPOINT = "/api/unibot/course/python-exam-drill-loop-control-panel"


def build_python_exam_drill_loop_control_panel(
    *,
    python_exam_tutor_drill_pack: dict[str, Any] | None = None,
    skill_to_workspace_session_carryover: dict[str, Any] | None = None,
    python_exam_drill_session_runner: dict[str, Any] | None = None,
    python_exam_drill_session_review_loop: dict[str, Any] | None = None,
    previous_review_loops: list[dict[str, Any]] | None = None,
    selected_skill_tag: str = "",
    selected_task_id: str = "",
    selected_task_hash: str = "",
    cell_source: str = "",
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    student_reflection: str = "",
    checkpoint_journal_path: str | Path | None = None,
    operator_confirmed_checkpoint_store: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    pack = python_exam_tutor_drill_pack if isinstance(python_exam_tutor_drill_pack, dict) else {}
    carryover = skill_to_workspace_session_carryover if isinstance(skill_to_workspace_session_carryover, dict) else {}
    previous = [item for item in (previous_review_loops or []) if isinstance(item, dict)]
    selected = str(selected_skill_tag or pack.get("selected_skill_tag") or "general_python")
    task_target = task_target_from_inputs(
        pack=pack,
        previous_review_loop=python_exam_drill_session_review_loop,
        selected_task_id=selected_task_id,
        selected_task_hash=selected_task_hash,
        selected_skill_tag=selected,
    )
    session = (
        python_exam_drill_session_runner
        if isinstance(python_exam_drill_session_runner, dict)
        else build_session_if_possible(
            pack=pack,
            carryover=carryover,
            task_target=task_target,
            selected_skill_tag=selected,
            cell_source=cell_source,
            notebook_checkpoint=notebook_checkpoint,
            cell_index=cell_index,
            cell_id=cell_id,
            cell_type=cell_type,
            student_reflection=student_reflection,
            checkpoint_journal_path=checkpoint_journal_path,
            operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
            public_safe=public_safe,
        )
    )
    review = (
        python_exam_drill_session_review_loop
        if isinstance(python_exam_drill_session_review_loop, dict) and python_exam_drill_session_review_loop.get("artifact_type")
        else build_python_exam_drill_session_review_loop(
            python_exam_drill_session_runner=session,
            python_exam_tutor_drill_pack=pack,
            previous_review_loops=previous,
            selected_skill_tag=selected,
            public_safe=public_safe,
        )
    )
    summary = control_panel_summary(pack=pack, session=session, review=review)
    payload = {
        "schema_version": PYTHON_EXAM_DRILL_LOOP_CONTROL_PANEL_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_loop_control_panel",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Drill Loop Control Panel. It coordinates Tutor Drill Pack, Drill Session Runner, and "
            "Drill Session Review Loop as one metadata-only A0-A2 work cycle. It shows the selected skill, current "
            "microtask hash, checkpoint hash, source-card metadata, Help-Ledger preview, Carryover receipt, "
            "reflection status, next-step action, and not_cleared receipt. It never returns raw queries, course raw "
            "text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, "
            "rankings, grades, grading, proctoring, AI detection, or exam clearance."
        ),
        "selected_skill_tag": summary["selected_skill_tag"],
        "control_panel_summary": summary,
        "cycle_cards": cycle_cards(pack=pack, session=session, review=review),
        "current_microtask": current_microtask_view(session=session, review=review, task_target=task_target),
        "session_evidence_summary": safe_session_evidence(session),
        "next_step_recommendation": safe_next_step(review),
        "control_panel_artifacts": {
            "drill_session_runner": session,
            "drill_session_review_loop": review,
        },
        "control_panel_receipt": control_panel_receipt(summary, session, review),
        "dry_run_default": True,
        "local_writes_requested": False,
        "operator_confirmation_required_for_local_write": True,
        "operator_confirmations": {
            "checkpoint_store": bool(operator_confirmed_checkpoint_store),
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Drill Loop Control Panel bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def build_session_if_possible(
    *,
    pack: dict[str, Any],
    carryover: dict[str, Any],
    task_target: dict[str, str],
    selected_skill_tag: str,
    cell_source: str,
    notebook_checkpoint: dict[str, Any] | None,
    cell_index: int,
    cell_id: str,
    cell_type: str,
    student_reflection: str,
    checkpoint_journal_path: str | Path | None,
    operator_confirmed_checkpoint_store: bool,
    public_safe: bool,
) -> dict[str, Any]:
    return build_python_exam_drill_session_runner(
        python_exam_tutor_drill_pack=pack,
        skill_to_workspace_session_carryover=carryover,
        selected_skill_tag=selected_skill_tag,
        selected_task_id=task_target.get("task_id", ""),
        selected_task_hash=task_target.get("task_hash", ""),
        cell_source=cell_source,
        notebook_checkpoint=notebook_checkpoint,
        cell_index=cell_index,
        cell_id=cell_id,
        cell_type=cell_type,
        student_reflection=student_reflection,
        checkpoint_journal_path=checkpoint_journal_path,
        operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
        public_safe=public_safe,
    )


def task_target_from_inputs(
    *,
    pack: dict[str, Any],
    previous_review_loop: dict[str, Any] | None,
    selected_task_id: str,
    selected_task_hash: str,
    selected_skill_tag: str,
) -> dict[str, str]:
    if selected_task_hash or selected_task_id:
        return {"task_id": str(selected_task_id), "task_hash": str(selected_task_hash)}
    previous = previous_review_loop if isinstance(previous_review_loop, dict) else {}
    next_hash = nested(previous, "next_step_recommendation", "next_task_hash")
    next_id = nested(previous, "next_step_recommendation", "next_task_id")
    if next_hash or next_id:
        return {"task_id": str(next_id or ""), "task_hash": str(next_hash or "")}
    drill = choose_drill(pack, selected_skill_tag)
    tasks = [item for item in (drill.get("microtasks", []) or []) if isinstance(item, dict)]
    if tasks:
        return {"task_id": str(tasks[0].get("task_id", "")), "task_hash": str(tasks[0].get("task_hash", ""))}
    return {"task_id": "", "task_hash": ""}


def choose_drill(pack: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    drills = [item for item in (pack.get("skill_drills", []) or []) if isinstance(item, dict)]
    for drill in drills:
        if drill.get("skill_tag") == selected_skill_tag:
            return drill
    for drill in drills:
        if drill.get("selected"):
            return drill
    return drills[0] if drills else {}


def control_panel_summary(*, pack: dict[str, Any], session: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    pack_ready = pack.get("status") == "python_exam_source_grounded_tutor_drill_pack_ready"
    session_ready = session.get("status") == "python_exam_drill_session_runner_ready"
    review_ready = review.get("status") == "python_exam_drill_session_review_loop_ready"
    selected = str(
        review.get("selected_skill_tag")
        or session.get("selected_skill_tag")
        or pack.get("selected_skill_tag")
        or "general_python"
    )
    return {
        "status": "python_exam_drill_loop_control_panel_ready"
        if pack_ready and session_ready and review_ready
        else "python_exam_drill_loop_control_panel_attention",
        "selected_skill_tag": selected,
        "pack_status": pack.get("status", "missing"),
        "session_status": session.get("status", "missing"),
        "review_loop_status": review.get("status", "missing"),
        "current_task_hash": nested(session, "selected_microtask", "task_hash") or "",
        "checkpoint_hash": nested(session, "notebook_checkpoint_adapter_summary", "notebook_work_sha256") or "",
        "source_card_count": len(nested(session, "source_anchor_metadata", "source_card_ids") or []),
        "help_status": "a0_a2_only",
        "reflection_status": nested(review, "reflection_status", "status") or "missing",
        "next_step_action": nested(review, "next_step_recommendation", "action") or "missing",
        "next_step_status": nested(review, "next_step_recommendation", "status") or "missing",
        "next_task_hash": nested(review, "next_step_recommendation", "next_task_hash") or "",
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def cycle_cards(*, pack: dict[str, Any], session: dict[str, Any], review: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "card_id": "tutor_drill_pack",
            "label": "Tutor Drill Pack",
            "status": pack.get("status", "missing"),
            "receipt_id": nested(pack, "pack_receipt", "receipt_id") or "",
            "ready": pack.get("status") == "python_exam_source_grounded_tutor_drill_pack_ready",
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        {
            "card_id": "drill_session_runner",
            "label": "Drill Session Runner",
            "status": session.get("status", "missing"),
            "receipt_id": nested(session, "drill_session_receipt", "receipt_id") or "",
            "ready": session.get("status") == "python_exam_drill_session_runner_ready",
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
        {
            "card_id": "drill_session_review_loop",
            "label": "Drill Session Review Loop",
            "status": review.get("status", "missing"),
            "receipt_id": nested(review, "review_loop_receipt", "receipt_id") or "",
            "ready": review.get("status") == "python_exam_drill_session_review_loop_ready",
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        },
    ]


def current_microtask_view(*, session: dict[str, Any], review: dict[str, Any], task_target: dict[str, str]) -> dict[str, Any]:
    task = session.get("selected_microtask", {}) if isinstance(session.get("selected_microtask"), dict) else {}
    return {
        "task_id": str(task.get("task_id") or task_target.get("task_id", "")),
        "task_hash": str(task.get("task_hash") or task_target.get("task_hash", "")),
        "prompt_summary": str(task.get("prompt_summary", "")),
        "next_task_hash": nested(review, "next_step_recommendation", "next_task_hash") or "",
        "next_action": nested(review, "next_step_recommendation", "action") or "missing",
        "help_level": "A2",
        "raw_query_returned": False,
        "complete_code_returned": False,
        "solution_returned": False,
        "values_returned": False,
    }


def safe_session_evidence(session: dict[str, Any]) -> dict[str, Any]:
    source = session.get("source_anchor_metadata", {}) if isinstance(session.get("source_anchor_metadata"), dict) else {}
    ledger = session.get("help_ledger_preview", {}) if isinstance(session.get("help_ledger_preview"), dict) else {}
    carryover = session.get("carryover_reference", {}) if isinstance(session.get("carryover_reference"), dict) else {}
    return {
        "skill_tag": session.get("selected_skill_tag", ""),
        "microtask_hash": nested(session, "selected_microtask", "task_hash") or "",
        "checkpoint_hash": nested(session, "notebook_checkpoint_adapter_summary", "notebook_work_sha256") or "",
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "help_level": ledger.get("help_level", "A2"),
        "help_ledger_event_hash": ledger.get("event_hash", ""),
        "carryover_session_receipt_id": carryover.get("session_receipt_id", ""),
        "reflection_status": nested(session, "drill_session_summary", "study_receipt_status") or "missing",
        "not_cleared_receipt": bool(nested(session, "drill_session_receipt", "not_cleared_receipt")),
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def safe_next_step(review: dict[str, Any]) -> dict[str, Any]:
    next_step = review.get("next_step_recommendation", {}) if isinstance(review.get("next_step_recommendation"), dict) else {}
    return {
        "status": next_step.get("status", "missing"),
        "action": next_step.get("action", "missing"),
        "reason_code": next_step.get("reason_code", ""),
        "current_task_hash": next_step.get("current_task_hash", ""),
        "next_task_hash": next_step.get("next_task_hash", ""),
        "help_level": "A2",
        "dry_run_default": True,
        "score_returned": False,
        "grade_returned": False,
        "solution_returned": False,
        "raw_query_returned": False,
    }


def control_panel_receipt(summary: dict[str, Any], session: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "session_receipt_id": nested(session, "drill_session_receipt", "receipt_id"),
        "review_receipt_id": nested(review, "review_loop_receipt", "receipt_id"),
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "drill_loop_control_panel_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "percentage_returned": False,
        "grade_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") != "python_exam_drill_loop_control_panel_ready":
        return [
            "Prepare a ready Tutor Drill Pack and run the selected microtask with a local notebook checkpoint.",
            "Keep the control panel metadata-only and not_cleared.",
        ]
    action = summary.get("next_step_action")
    if action == "run_next_microtask":
        return [
            "Run the next safe microtask through the Control Panel cycle.",
            "Keep notebook work local and export only hashes, receipts, and A0-A2 metadata.",
        ]
    if action == "repeat_current_microtask":
        return [
            "Repeat the current microtask because safe evidence is incomplete.",
            "Do not infer scores, grades, rankings, percentages, or final interpretations.",
        ]
    return [
        "Return to the Course Exam Coverage Dashboard and select the next source-grounded skill.",
        "Keep exam_deployment_status not_cleared.",
    ]


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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-drill-loop-control-panel")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
