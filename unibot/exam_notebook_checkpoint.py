from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .materials import sha256_text
from .public_safety import scan_text
from .study_session import validate_study_session_receipt


EXAM_NOTEBOOK_CHECKPOINT_SCHEMA_VERSION = "unibot-exam-notebook-checkpoint-v1"
HEX_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
SOLUTION_MARKER_RE = re.compile(
    r"(solution[_ -]?key|final[_ -]?answer|finale? loesung|fertige loesung|abgabefertig|complete solution|inserted[_ -]?values)",
    re.IGNORECASE,
)
FORBIDDEN_CHECKPOINT_FIELDS = {
    "final_solution",
    "complete_code",
    "inserted_values",
    "raw_course_text",
    "raw_transcript",
    "raw_notebook",
    "local_path",
    "notebook_path",
}


def build_exam_notebook_checkpoint_adapter_dry_run(
    *,
    course_id: str = DEFAULT_COURSE_ID,
    task_id: str = "",
    skill_tag: str = "",
    source_card_ids: list[str] | None = None,
    source_anchor_id: str = "",
    cell_source: str = "",
    notebook_checkpoint: dict[str, Any] | None = None,
    cell_index: int = 0,
    cell_id: str = "",
    cell_type: str = "code",
    requested_help_level: str = "A2",
    prediction_present: bool = False,
    retrieval_response_present: bool = False,
    notebook_action_present: bool = False,
    reflection_present: bool = False,
    student_reflection: str = "",
    checkpoint_journal_path: str | Path | None = None,
    operator_confirmed_checkpoint_store: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    checkpoint = notebook_checkpoint if isinstance(notebook_checkpoint, dict) else {}
    source = str(cell_source or "")
    raw_source_supplied = bool(source)
    supplied_hash = first_valid_hash(
        checkpoint.get("notebook_work_sha256"),
        checkpoint.get("cell_source_sha256"),
        checkpoint.get("checkpoint_sha256"),
    )
    cell_source_hash = sha256_text(source) if raw_source_supplied else supplied_hash
    safe_task_id = str(task_id or checkpoint.get("task_id") or checkpoint.get("cell_task_id") or "local-notebook-checkpoint")
    safe_skill_tag = str(skill_tag or checkpoint.get("skill_tag") or "general_python")
    safe_cell_type = str(cell_type or checkpoint.get("cell_type") or "code")[:40]
    safe_cell_index = safe_int(cell_index if cell_index is not None else checkpoint.get("cell_index", 0), default=0)
    source_cards = [str(item) for item in (source_card_ids or checkpoint.get("source_card_ids", []) or [])[:8]]
    anchor_id = str(source_anchor_id or checkpoint.get("source_anchor_id", "") or default_source_anchor_id(safe_skill_tag, source_cards))
    final_solution_seen = bool(checkpoint.get("final_solution_seen")) or str(requested_help_level).strip().upper() == "A6"
    solution_marker_seen = bool(SOLUTION_MARKER_RE.search(source)) if source else bool(checkpoint.get("solution_marker_detected"))
    forbidden_fields = sorted(field for field in FORBIDDEN_CHECKPOINT_FIELDS if field in checkpoint)
    checkpoint_id = f"nbcp-{sha256_text(f'{safe_id}:{safe_task_id}:{safe_skill_tag}:{cell_source_hash}:{safe_cell_index}:{safe_cell_type}')[:16]}"

    receipt_payload = {
        "task_id": safe_task_id,
        "skill_tag": safe_skill_tag,
        "help_level": "A6" if final_solution_seen or solution_marker_seen else safe_help_level(requested_help_level),
        "source_anchor_id": anchor_id,
        "prediction_present": bool(prediction_present or checkpoint.get("prediction_present")),
        "retrieval_response_present": bool(retrieval_response_present or checkpoint.get("retrieval_response_present") or source_cards),
        "notebook_action_present": bool(notebook_action_present or checkpoint.get("notebook_action_present") or cell_source_hash),
        "reflection_present": bool(reflection_present or checkpoint.get("reflection_present") or str(student_reflection).strip()),
        "notebook_work_sha256": cell_source_hash,
        "notebook_checkpoint_id": checkpoint_id,
        "final_solution_seen": final_solution_seen or solution_marker_seen,
    }
    validation = validate_study_session_receipt(receipt_payload, public_safe=public_safe)
    status = checkpoint_status(
        cell_source_hash=cell_source_hash,
        validation=validation,
        forbidden_fields=forbidden_fields,
        final_solution_seen=final_solution_seen or solution_marker_seen,
    )
    event = checkpoint_event(
        safe_id=safe_id,
        checkpoint_id=checkpoint_id,
        task_id=safe_task_id,
        skill_tag=safe_skill_tag,
        source_cards=source_cards,
        cell_source_hash=cell_source_hash,
        cell_index=safe_cell_index,
        cell_type=safe_cell_type,
        validation=validation,
    )
    journal = maybe_append_checkpoint_event(
        event,
        checkpoint_journal_path=checkpoint_journal_path,
        operator_confirmed=operator_confirmed_checkpoint_store,
    )
    raw_scan_flags = raw_cell_scan_flags(source) if source else []
    report = {
        "schema_version": EXAM_NOTEBOOK_CHECKPOINT_SCHEMA_VERSION,
        "artifact_type": "exam_notebook_checkpoint_adapter_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_id,
        "status": status,
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Local notebook checkpoint adapter. It accepts a locally captured cell or hash-only checkpoint, "
            "turns it into hashes, validates study evidence, previews a Help-Ledger event, and writes only "
            "with operator confirmation. It never returns raw cell text, notebook code, local paths, complete "
            "solutions, inserted values, final interpretation, grading, proctoring, AI detection, or exam clearance."
        ),
        "notebook_checkpoint": {
            "checkpoint_id": checkpoint_id,
            "status": "ready" if cell_source_hash else "missing_local_cell_or_checkpoint_hash",
            "task_id": safe_task_id,
            "skill_tag": safe_skill_tag,
            "cell_index": safe_cell_index,
            "cell_type": safe_cell_type,
            "cell_id_hash": sha256_text(str(cell_id or checkpoint.get("cell_id", "") or checkpoint_id)),
            "cell_source_sha256": cell_source_hash,
            "notebook_work_sha256": cell_source_hash,
            "source_hash_supplied": bool(supplied_hash),
            "raw_cell_supplied": raw_source_supplied,
            "raw_cell_returned": False,
            "raw_notebook_returned": False,
            "notebook_code_returned": False,
            "local_path_returned": False,
        },
        "study_receipt_summary": validation,
        "help_ledger_preview": {
            "status": "preview_ready" if cell_source_hash else "waiting_for_local_checkpoint",
            "event_hash": sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False)),
            "help_level": validation.get("help_level", safe_help_level(requested_help_level)),
            "notebook_work_sha256": cell_source_hash,
            "source_card_ids": source_cards,
            "ledger_written": journal.get("checkpoint_journal_written", False),
            "raw_query_returned": False,
            "raw_response_returned": False,
            "raw_cell_returned": False,
            "local_path_returned": False,
            "eigenleistung_percentage_claimed": False,
        },
        "checkpoint_journal_summary": journal,
        "operator_confirmations": {
            "checkpoint_store": bool(operator_confirmed_checkpoint_store),
        },
        "solution_marker_detected": bool(solution_marker_seen),
        "forbidden_fields_present": forbidden_fields,
        "raw_cell_privacy_flags": raw_scan_flags,
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
        "next_actions": checkpoint_next_actions(status),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def first_valid_hash(*values: Any) -> str:
    for value in values:
        candidate = str(value or "").strip().lower()
        if HEX_SHA256_RE.match(candidate):
            return candidate
    return ""


def safe_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_help_level(value: Any) -> str:
    candidate = str(value or "A2").strip().upper()
    return candidate if candidate in {"A0", "A1", "A2"} else "A2"


def default_source_anchor_id(skill_tag: str, source_card_ids: list[str]) -> str:
    first_source = source_card_ids[0] if source_card_ids else "course-anchor"
    return f"checkpoint-source-anchor:{skill_tag}:{first_source}"


def raw_cell_scan_flags(source: str) -> list[str]:
    scan = scan_text(source, "local-notebook-cell-source")
    return sorted({str(finding.get("type", "")) for finding in scan.get("findings", []) if finding.get("type")})


def checkpoint_status(
    *,
    cell_source_hash: str,
    validation: dict[str, Any],
    forbidden_fields: list[str],
    final_solution_seen: bool,
) -> str:
    if final_solution_seen or validation.get("repeat_task_required"):
        return "notebook_checkpoint_repeat_task_required"
    if forbidden_fields:
        return "notebook_checkpoint_blocked_forbidden_fields"
    if not cell_source_hash:
        return "notebook_checkpoint_waiting_for_local_cell"
    if validation.get("status") != "ok_study_session_receipt":
        return "notebook_checkpoint_needs_study_receipt_evidence"
    return "notebook_checkpoint_ready"


def checkpoint_event(
    *,
    safe_id: str,
    checkpoint_id: str,
    task_id: str,
    skill_tag: str,
    source_cards: list[str],
    cell_source_hash: str,
    cell_index: int,
    cell_type: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": EXAM_NOTEBOOK_CHECKPOINT_SCHEMA_VERSION,
        "event_type": "exam_notebook_checkpoint",
        "course_id": safe_id,
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "skill_tag": skill_tag,
        "source_card_ids": source_cards,
        "cell_source_sha256": cell_source_hash,
        "notebook_work_sha256": cell_source_hash,
        "cell_index": cell_index,
        "cell_type": cell_type,
        "study_receipt_status": validation.get("status", "unknown"),
        "help_level": validation.get("help_level", "A2"),
        "exam_deployment_status": "not_cleared",
    }


def maybe_append_checkpoint_event(
    event: dict[str, Any],
    *,
    checkpoint_journal_path: str | Path | None,
    operator_confirmed: bool,
) -> dict[str, Any]:
    event_hash = sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False))
    if not operator_confirmed:
        return {
            "status": "dry_run_not_written",
            "checkpoint_journal_written": False,
            "event_hash": event_hash,
            "path_returned": False,
        }
    if not checkpoint_journal_path:
        return {
            "status": "blocked_missing_checkpoint_journal_path",
            "checkpoint_journal_written": False,
            "event_hash": event_hash,
            "path_returned": False,
        }
    path = Path(checkpoint_journal_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"status": "accepted", "event": event, "event_hash": event_hash}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "stored",
        "checkpoint_journal_written": True,
        "event_hash": event_hash,
        "path_returned": False,
    }


def checkpoint_next_actions(status: str) -> list[str]:
    if status == "notebook_checkpoint_ready":
        return [
            "Attach this checkpoint hash to the coverage-selected Exam-Workspace launch flow.",
            "Keep raw notebook code local; use only hashes, source anchors, reflection flags, and ledger preview in reports.",
        ]
    if status == "notebook_checkpoint_repeat_task_required":
        return ["Repeat the notebook task after final-solution/A6 exposure; do not use this checkpoint as Eigenleistung evidence."]
    if status == "notebook_checkpoint_needs_study_receipt_evidence":
        return ["Add missing evidence flags: own prediction, source anchor, notebook action, and reflection."]
    if status == "notebook_checkpoint_blocked_forbidden_fields":
        return ["Remove forbidden raw solution/private fields and submit only the local cell or hash-only checkpoint."]
    return ["Capture the local notebook cell or provide a notebook_work_sha256 checkpoint before launch."]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-notebook-checkpoint-adapter")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
