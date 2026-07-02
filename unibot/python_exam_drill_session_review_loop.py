from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_DRILL_SESSION_REVIEW_LOOP_SCHEMA_VERSION = "unibot-python-exam-drill-session-review-loop-v1"
PYTHON_EXAM_DRILL_SESSION_REVIEW_LOOP_ENDPOINT = "/api/unibot/course/python-exam-drill-session-review-loop"


def build_python_exam_drill_session_review_loop(
    *,
    python_exam_drill_session_runner: dict[str, Any] | None = None,
    python_exam_tutor_drill_pack: dict[str, Any] | None = None,
    previous_review_loops: list[dict[str, Any]] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    session = python_exam_drill_session_runner if isinstance(python_exam_drill_session_runner, dict) else {}
    pack = python_exam_tutor_drill_pack if isinstance(python_exam_tutor_drill_pack, dict) else {}
    previous = [item for item in (previous_review_loops or []) if isinstance(item, dict)]
    selected = str(selected_skill_tag or session.get("selected_skill_tag") or pack.get("selected_skill_tag") or "general_python")
    current_task_hash = str(nested(session, "selected_microtask", "task_hash") or "")
    current_drill = choose_drill(pack, selected)
    microtasks = safe_microtasks(current_drill)
    next_step = next_step_recommendation(session, microtasks, current_task_hash)
    summary = review_summary(session=session, pack=pack, previous=previous, next_step=next_step)
    payload = {
        "schema_version": PYTHON_EXAM_DRILL_SESSION_REVIEW_LOOP_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_session_review_loop",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Drill Session Review Loop. It reviews one completed Drill Session using only hash and "
            "metadata-safe evidence, then suggests either the next safe microtask or a repeat. It never returns "
            "raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, "
            "scores, percentages, rankings, grades, grading, proctoring, AI detection, or exam clearance."
        ),
        "selected_skill_tag": selected,
        "review_loop_summary": summary,
        "session_evidence_summary": session_evidence_summary(session),
        "source_anchor_metadata": source_anchor_metadata(session),
        "help_ledger_preview": help_ledger_preview(session),
        "carryover_reference": carryover_reference(session),
        "reflection_status": reflection_status(session),
        "next_step_recommendation": next_step,
        "review_loop_receipt": review_loop_receipt(summary, session, next_step),
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
        "score_returned": False,
        "percentage_returned": False,
        "ranking_returned": False,
        "grade_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Review Loop bleibt not_cleared."
        ),
        "next_actions": next_actions(summary, next_step),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def choose_drill(pack: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    drills = [item for item in (pack.get("skill_drills", []) or []) if isinstance(item, dict)]
    for drill in drills:
        if drill.get("skill_tag") == selected_skill_tag:
            return drill
    for drill in drills:
        if drill.get("selected"):
            return drill
    return drills[0] if drills else {}


def safe_microtasks(drill: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in (drill.get("microtasks", []) or []):
        if isinstance(item, dict):
            result.append(
                {
                    "task_id": str(item.get("task_id", "")),
                    "task_hash": str(item.get("task_hash", "")),
                    "prompt_summary": str(item.get("prompt_summary", "")),
                    "help_level": "A2",
                    "complete_code_returned": False,
                    "solution_returned": False,
                    "values_returned": False,
                }
            )
    return result


def next_step_recommendation(
    session: dict[str, Any],
    microtasks: list[dict[str, Any]],
    current_task_hash: str,
) -> dict[str, Any]:
    session_ready = session.get("status") == "python_exam_drill_session_runner_ready"
    checkpoint_ready = nested(session, "drill_session_summary", "checkpoint_status") == "notebook_checkpoint_ready"
    study_receipt_ready = nested(session, "drill_session_summary", "study_receipt_status") == "ok_study_session_receipt"
    reflection_ready = reflection_status(session)["status"] == "reflection_metadata_present"
    if not (session_ready and checkpoint_ready and study_receipt_ready and reflection_ready):
        return {
            "status": "repeat_current_microtask_required",
            "action": "repeat_current_microtask",
            "reason_code": "missing_safe_evidence",
            "current_task_hash": current_task_hash,
            "next_task_hash": current_task_hash,
            "help_level": "A2",
            "dry_run_default": True,
            "raw_query_returned": False,
            "solution_returned": False,
            "score_returned": False,
            "grade_returned": False,
        }
    hashes = [item.get("task_hash", "") for item in microtasks]
    try:
        index = hashes.index(current_task_hash)
    except ValueError:
        index = -1
    if index >= 0 and index + 1 < len(microtasks):
        next_task = microtasks[index + 1]
        return {
            "status": "next_microtask_ready",
            "action": "run_next_microtask",
            "reason_code": "safe_checkpoint_receipt_present",
            "current_task_hash": current_task_hash,
            "next_task_id": next_task.get("task_id", ""),
            "next_task_hash": next_task.get("task_hash", ""),
            "next_prompt_summary": next_task.get("prompt_summary", ""),
            "help_level": "A2",
            "dry_run_default": True,
            "raw_query_returned": False,
            "solution_returned": False,
            "score_returned": False,
            "grade_returned": False,
        }
    return {
        "status": "skill_drill_cycle_complete",
        "action": "return_to_skill_dashboard",
        "reason_code": "no_remaining_safe_microtask_in_pack",
        "current_task_hash": current_task_hash,
        "next_task_hash": "",
        "help_level": "A2",
        "dry_run_default": True,
        "raw_query_returned": False,
        "solution_returned": False,
        "score_returned": False,
        "grade_returned": False,
    }


def review_summary(
    *,
    session: dict[str, Any],
    pack: dict[str, Any],
    previous: list[dict[str, Any]],
    next_step: dict[str, Any],
) -> dict[str, Any]:
    session_ready = session.get("status") == "python_exam_drill_session_runner_ready"
    pack_ready = pack.get("status") in {"python_exam_source_grounded_tutor_drill_pack_ready", "missing"}
    next_ready = next_step.get("status") in {
        "next_microtask_ready",
        "repeat_current_microtask_required",
        "skill_drill_cycle_complete",
    }
    return {
        "status": "python_exam_drill_session_review_loop_ready" if session_ready and pack_ready and next_ready else "python_exam_drill_session_review_loop_attention",
        "session_status": session.get("status", "missing"),
        "pack_status": pack.get("status", "missing"),
        "review_loop_index": len(previous) + 1,
        "current_task_hash": nested(session, "selected_microtask", "task_hash") or "",
        "checkpoint_hash": nested(session, "notebook_checkpoint_adapter_summary", "notebook_work_sha256") or "",
        "help_status": "a0_a2_only",
        "next_step_status": next_step.get("status", "missing"),
        "next_step_action": next_step.get("action", "missing"),
        "no_score_or_grade": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def session_evidence_summary(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": session.get("selected_skill_tag", ""),
        "microtask_hash": nested(session, "selected_microtask", "task_hash") or "",
        "checkpoint_hash": nested(session, "notebook_checkpoint_adapter_summary", "notebook_work_sha256") or "",
        "checkpoint_status": nested(session, "drill_session_summary", "checkpoint_status") or "missing",
        "study_receipt_status": nested(session, "drill_session_summary", "study_receipt_status") or "missing",
        "session_receipt_id": nested(session, "drill_session_receipt", "receipt_id") or "",
        "not_cleared_receipt": bool(nested(session, "drill_session_receipt", "not_cleared_receipt")),
        "raw_cell_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def source_anchor_metadata(session: dict[str, Any]) -> dict[str, Any]:
    source = session.get("source_anchor_metadata", {}) if isinstance(session.get("source_anchor_metadata"), dict) else {}
    return {
        "source_card_ids": [str(item) for item in (source.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(source.get("source_anchor_count", 0) or 0),
        "raw_anchor_text_returned": False,
        "local_paths_returned": False,
    }


def help_ledger_preview(session: dict[str, Any]) -> dict[str, Any]:
    ledger = session.get("help_ledger_preview", {}) if isinstance(session.get("help_ledger_preview"), dict) else {}
    return {
        "status": ledger.get("status", "missing"),
        "event_hash": ledger.get("event_hash", ""),
        "help_level": ledger.get("help_level", "A2"),
        "source_card_ids": [str(item) for item in (ledger.get("source_card_ids", []) or [])][:8],
        "ledger_written": bool(ledger.get("ledger_written", False)),
        "raw_query_returned": False,
        "raw_response_returned": False,
        "raw_cell_returned": False,
        "local_paths_returned": False,
        "eigenleistung_percentage_claimed": False,
    }


def carryover_reference(session: dict[str, Any]) -> dict[str, Any]:
    carryover = session.get("carryover_reference", {}) if isinstance(session.get("carryover_reference"), dict) else {}
    return {
        "status": carryover.get("status", "missing"),
        "operator_receipt_id": carryover.get("operator_receipt_id", ""),
        "session_receipt_id": carryover.get("session_receipt_id", ""),
        "evidence_preview_status": carryover.get("evidence_preview_status", "missing"),
        "human_handoff_status": carryover.get("human_handoff_status", "missing"),
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def reflection_status(session: dict[str, Any]) -> dict[str, Any]:
    study_status = nested(session, "drill_session_summary", "study_receipt_status")
    checkpoint_hash = nested(session, "notebook_checkpoint_adapter_summary", "notebook_work_sha256")
    present = study_status == "ok_study_session_receipt" and bool(checkpoint_hash)
    return {
        "status": "reflection_metadata_present" if present else "reflection_metadata_missing_or_unverified",
        "study_receipt_status": study_status or "missing",
        "checkpoint_hash_present": bool(checkpoint_hash),
        "raw_reflection_returned": False,
        "percentage_claimed": False,
        "score_returned": False,
        "grade_returned": False,
    }


def review_loop_receipt(
    summary: dict[str, Any],
    session: dict[str, Any],
    next_step: dict[str, Any],
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "session_receipt_id": nested(session, "drill_session_receipt", "receipt_id"),
        "next_step": {
            "status": next_step.get("status"),
            "action": next_step.get("action"),
            "current_task_hash": next_step.get("current_task_hash"),
            "next_task_hash": next_step.get("next_task_hash"),
        },
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "drill_session_review_loop_receipt_ready_not_exam_clearance",
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


def next_actions(summary: dict[str, Any], next_step: dict[str, Any]) -> list[str]:
    if summary.get("status") != "python_exam_drill_session_review_loop_ready":
        return [
            "Rerun a source-grounded Drill Session with checkpoint hash, study receipt, and reflection metadata.",
            "Keep the loop metadata-only and not_cleared.",
        ]
    if next_step.get("action") == "run_next_microtask":
        return [
            "Run the next safe microtask through Python Exam Drill Session Runner.",
            "Keep local notebook work private; export only hashes and receipts.",
        ]
    if next_step.get("action") == "repeat_current_microtask":
        return [
            "Repeat the current microtask because safe evidence is incomplete.",
            "Do not infer a score, grade, ranking, percentage, or final interpretation.",
        ]
    return [
        "Return to the skill dashboard and select the next source-grounded Python skill.",
        "Keep not_cleared until a separate real-world decision changes deployment status.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-drill-session-review-loop")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
