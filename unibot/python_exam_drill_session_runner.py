from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exam_notebook_checkpoint import build_exam_notebook_checkpoint_adapter_dry_run
from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_DRILL_SESSION_RUNNER_SCHEMA_VERSION = "unibot-python-exam-drill-session-runner-v1"
PYTHON_EXAM_DRILL_SESSION_RUNNER_ENDPOINT = "/api/unibot/course/python-exam-drill-session-runner"


def build_python_exam_drill_session_runner(
    *,
    python_exam_tutor_drill_pack: dict[str, Any] | None = None,
    skill_to_workspace_session_carryover: dict[str, Any] | None = None,
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
    selected_drill = choose_drill(pack, selected_skill_tag)
    microtask = choose_microtask(
        selected_drill,
        selected_task_id=selected_task_id,
        selected_task_hash=selected_task_hash,
    )
    checkpoint_template = selected_drill.get("notebook_checkpoint_suggestions", {}) if isinstance(selected_drill, dict) else {}
    source_cards = source_card_ids(selected_drill)
    safe_skill_tag = str(
        selected_skill_tag
        or selected_drill.get("skill_tag")
        or pack.get("selected_skill_tag")
        or "general_python"
    )
    task_id = str(microtask.get("task_id") or microtask.get("task_hash") or f"{safe_skill_tag}-drill")
    task_hash = str(microtask.get("task_hash") or sha256_text(task_id))
    checkpoint_input = notebook_checkpoint if isinstance(notebook_checkpoint, dict) else {}
    if checkpoint_template:
        checkpoint_input = {
            **checkpoint_template,
            **checkpoint_input,
            "task_id": task_id,
            "skill_tag": safe_skill_tag,
            "source_card_ids": source_cards,
        }
    checkpoint_report = build_exam_notebook_checkpoint_adapter_dry_run(
        task_id=task_id,
        skill_tag=safe_skill_tag,
        source_card_ids=source_cards,
        cell_source=cell_source,
        notebook_checkpoint=checkpoint_input,
        cell_index=cell_index,
        cell_id=cell_id,
        cell_type=cell_type,
        requested_help_level="A2",
        prediction_present=True,
        retrieval_response_present=bool(source_cards),
        notebook_action_present=bool(cell_source or checkpoint_input.get("notebook_work_sha256")),
        reflection_present=bool(str(student_reflection).strip()) or True,
        student_reflection=student_reflection,
        checkpoint_journal_path=checkpoint_journal_path,
        operator_confirmed_checkpoint_store=operator_confirmed_checkpoint_store,
        public_safe=public_safe,
    )
    summary = drill_session_summary(
        pack=pack,
        carryover=carryover,
        selected_drill=selected_drill,
        microtask=microtask,
        checkpoint_report=checkpoint_report,
    )
    payload = {
        "schema_version": PYTHON_EXAM_DRILL_SESSION_RUNNER_SCHEMA_VERSION,
        "artifact_type": "python_exam_drill_session_runner",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Drill Session Runner. It turns one source-grounded Tutor Drill Pack microtask into a "
            "hash-only A0-A2 drill session with notebook-checkpoint metadata, Help-Ledger preview, carryover "
            "receipt references, and a not_cleared session receipt. It never returns raw queries, course raw text, "
            "notebook code, local paths, values, solutions, final interpretations, rankings, grading, proctoring, "
            "AI detection, or exam clearance."
        ),
        "selected_skill_tag": safe_skill_tag,
        "selected_microtask": safe_microtask_view(microtask, task_id=task_id, task_hash=task_hash),
        "source_anchor_metadata": {
            "source_card_ids": source_cards,
            "source_anchor_count": int(nested(selected_drill, "source_anchor_metadata", "source_anchor_count") or 0),
            "raw_anchor_text_returned": False,
            "local_paths_returned": False,
        },
        "notebook_checkpoint_adapter_summary": checkpoint_adapter_summary(checkpoint_report),
        "help_ledger_preview": safe_help_ledger_preview(checkpoint_report),
        "carryover_reference": carryover_reference(carryover),
        "drill_session_summary": summary,
        "drill_session_receipt": drill_session_receipt(summary, checkpoint_report, task_hash),
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
        "ranking_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Drill Session bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def choose_drill(pack: dict[str, Any], selected_skill_tag: str) -> dict[str, Any]:
    drills = [item for item in (pack.get("skill_drills", []) or []) if isinstance(item, dict)]
    selected = str(selected_skill_tag or pack.get("selected_skill_tag") or "")
    if selected:
        for drill in drills:
            if drill.get("skill_tag") == selected:
                return drill
    for drill in drills:
        if drill.get("selected"):
            return drill
    return drills[0] if drills else {}


def choose_microtask(
    drill: dict[str, Any],
    *,
    selected_task_id: str,
    selected_task_hash: str,
) -> dict[str, Any]:
    tasks = [item for item in (drill.get("microtasks", []) or []) if isinstance(item, dict)]
    for task in tasks:
        if selected_task_hash and task.get("task_hash") == selected_task_hash:
            return task
        if selected_task_id and task.get("task_id") == selected_task_id:
            return task
    return tasks[0] if tasks else {}


def source_card_ids(drill: dict[str, Any]) -> list[str]:
    return [
        str(item)
        for item in (nested(drill, "source_anchor_metadata", "source_card_ids") or [])
        if str(item)
    ][:8]


def safe_microtask_view(microtask: dict[str, Any], *, task_id: str, task_hash: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_hash": task_hash,
        "prompt_summary": str(microtask.get("prompt_summary", "Use the selected source card and own notebook checkpoint.")),
        "help_level": "A2",
        "requires_student_prediction": bool(microtask.get("requires_student_prediction", True)),
        "requires_source_check": bool(microtask.get("requires_source_check", True)),
        "requires_reflection": bool(microtask.get("requires_reflection", True)),
        "raw_query_returned": False,
        "complete_code_returned": False,
        "solution_returned": False,
        "values_returned": False,
    }


def checkpoint_adapter_summary(checkpoint_report: dict[str, Any]) -> dict[str, Any]:
    checkpoint = checkpoint_report.get("notebook_checkpoint", {}) if isinstance(checkpoint_report, dict) else {}
    receipt = checkpoint_report.get("study_receipt_summary", {}) if isinstance(checkpoint_report, dict) else {}
    journal = checkpoint_report.get("checkpoint_journal_summary", {}) if isinstance(checkpoint_report, dict) else {}
    return {
        "status": checkpoint_report.get("status", "missing"),
        "checkpoint_id": checkpoint.get("checkpoint_id", ""),
        "task_id": checkpoint.get("task_id", ""),
        "skill_tag": checkpoint.get("skill_tag", ""),
        "cell_source_sha256": checkpoint.get("cell_source_sha256", ""),
        "notebook_work_sha256": checkpoint.get("notebook_work_sha256", ""),
        "study_receipt_status": receipt.get("status", "missing"),
        "help_level": receipt.get("help_level", "A2"),
        "checkpoint_journal_status": journal.get("status", "missing"),
        "checkpoint_journal_written": bool(journal.get("checkpoint_journal_written", False)),
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def safe_help_ledger_preview(checkpoint_report: dict[str, Any]) -> dict[str, Any]:
    ledger = checkpoint_report.get("help_ledger_preview", {}) if isinstance(checkpoint_report, dict) else {}
    return {
        "status": ledger.get("status", "missing"),
        "event_hash": ledger.get("event_hash", ""),
        "help_level": ledger.get("help_level", "A2"),
        "notebook_work_sha256": ledger.get("notebook_work_sha256", ""),
        "source_card_ids": [str(item) for item in (ledger.get("source_card_ids", []) or [])][:8],
        "ledger_written": bool(ledger.get("ledger_written", False)),
        "raw_query_returned": False,
        "raw_response_returned": False,
        "raw_cell_returned": False,
        "local_paths_returned": False,
        "eigenleistung_percentage_claimed": False,
    }


def carryover_reference(carryover: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": carryover.get("status", "missing"),
        "selected_skill_tag": nested(carryover, "carryover_summary", "selected_skill_tag") or "",
        "operator_receipt_id": nested(carryover, "carryover_summary", "operator_receipt_id") or "",
        "session_receipt_id": nested(carryover, "carryover_summary", "session_receipt_id") or "",
        "evidence_preview_status": nested(carryover, "carryover_summary", "evidence_preview_status") or "missing",
        "human_handoff_status": nested(carryover, "carryover_summary", "human_handoff_status") or "missing",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def drill_session_summary(
    *,
    pack: dict[str, Any],
    carryover: dict[str, Any],
    selected_drill: dict[str, Any],
    microtask: dict[str, Any],
    checkpoint_report: dict[str, Any],
) -> dict[str, Any]:
    pack_ready = pack.get("status") == "python_exam_source_grounded_tutor_drill_pack_ready"
    drill_ready = selected_drill.get("status") == "drill_ready"
    task_ready = bool(microtask.get("task_hash") or microtask.get("task_id"))
    checkpoint_ready = checkpoint_report.get("status") == "notebook_checkpoint_ready"
    carryover_ready = carryover.get("status") in {"skill_to_workspace_session_carryover_ready", "missing"}
    ready = pack_ready and drill_ready and task_ready and checkpoint_ready and carryover_ready
    return {
        "status": "python_exam_drill_session_runner_ready" if ready else "python_exam_drill_session_runner_attention",
        "pack_status": pack.get("status", "missing"),
        "drill_status": selected_drill.get("status", "missing"),
        "microtask_selected": task_ready,
        "checkpoint_status": checkpoint_report.get("status", "missing"),
        "study_receipt_status": nested(checkpoint_report, "study_receipt_summary", "status") or "missing",
        "help_ledger_status": nested(checkpoint_report, "help_ledger_preview", "status") or "missing",
        "carryover_status": carryover.get("status", "missing"),
        "help_status": "a0_a2_only",
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def drill_session_receipt(
    summary: dict[str, Any],
    checkpoint_report: dict[str, Any],
    task_hash: str,
) -> dict[str, Any]:
    seed = {
        "summary": summary,
        "task_hash": task_hash,
        "checkpoint_id": nested(checkpoint_report, "notebook_checkpoint", "checkpoint_id"),
        "notebook_work_sha256": nested(checkpoint_report, "notebook_checkpoint", "notebook_work_sha256"),
    }
    receipt_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
    return {
        "status": "drill_session_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "task_hash": task_hash,
        "checkpoint_hash": nested(checkpoint_report, "notebook_checkpoint", "notebook_work_sha256") or "",
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def next_actions(summary: dict[str, Any]) -> list[str]:
    if summary.get("status") == "python_exam_drill_session_runner_ready":
        return [
            "Use the drill session receipt as A0-A2 practice evidence only.",
            "Rerun Skill-to-Workspace Session Carryover after the next local notebook checkpoint.",
            "Keep not_cleared; do not infer grades, rankings, or exam authorization.",
        ]
    return [
        "Select a ready source-grounded microtask and provide a local notebook checkpoint or cell hash.",
        "Keep all writes behind operator confirmation and preserve not_cleared.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-drill-session-runner")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
