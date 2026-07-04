from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .study_session import validate_study_session_receipt


EXAM_NOTEBOOK_CHECKPOINT_SCHEMA_VERSION = "unibot-exam-notebook-checkpoint-v1"
EXAM_NOTEBOOK_CHECKPOINT_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-notebook-checkpoint-release-review-board-claim-alignment-v1"
)
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
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    operator_confirmed_checkpoint_store: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    safe_id = safe_course_id(course_id)
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
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
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
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


def build_notebook_checkpoint_release_claim_alignment(
    ready_report: dict[str, Any] | None = None,
    stored_report: dict[str, Any] | None = None,
    repeat_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if ready_report is None or stored_report is None or repeat_report is None:
        with tempfile.TemporaryDirectory(prefix="unibot_notebook_checkpoint_alignment_") as temp_dir:
            journal_path = Path(temp_dir) / "checkpoints.jsonl"
            ready_report = ready_report or build_exam_notebook_checkpoint_adapter_dry_run(
                task_id="synthetic-checkpoint-task",
                skill_tag="pandas",
                source_card_ids=["dfg-gwp", "uoc-ki-faq"],
                cell_source="own_values = [1, 2, 3]\nlen(own_values)\n",
                cell_index=2,
                cell_id="synthetic-private-cell",
                requested_help_level="A2",
                prediction_present=True,
                retrieval_response_present=True,
                notebook_action_present=True,
                reflection_present=True,
                checkpoint_journal_path=journal_path,
                python_exam_local_cycle_operator_workspace_card=synthetic_notebook_checkpoint_workspace_card(),
            )
            stored_report = stored_report or build_exam_notebook_checkpoint_adapter_dry_run(
                task_id="synthetic-checkpoint-task",
                skill_tag="python_lists",
                source_card_ids=["dfg-gwp"],
                cell_source="result = sum([1, 2, 3])\n",
                prediction_present=True,
                retrieval_response_present=True,
                notebook_action_present=True,
                reflection_present=True,
                checkpoint_journal_path=journal_path,
                operator_confirmed_checkpoint_store=True,
            )
            repeat_report = repeat_report or build_exam_notebook_checkpoint_adapter_dry_run(
                task_id="synthetic-repeat-task",
                skill_tag="pandas",
                source_card_ids=["dfg-gwp"],
                cell_source="# final answer: use this exact completed solution\n",
                prediction_present=True,
                retrieval_response_present=True,
                notebook_action_present=True,
                reflection_present=True,
            )

    sections = [
        {
            "section_id": "hash_only_checkpoint_trace",
            "summary_claim": "notebook checkpoints turn local cell work into hashes and never return raw notebook code",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "notebook_checkpoint",
                "python_exam_local_cycle_operator_workspace_card",
                "study_session",
                "private_tutor_use_flow",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "operator_confirmed_checkpoint_journal_trace",
            "summary_claim": "checkpoint journal writes are hash-only and require explicit operator confirmation",
            "source_card_ids": ["dfg-gwp", "dsk-ai-privacy-2024"],
            "readiness_check_ids": [
                "notebook_checkpoint",
                "python_exam_local_cycle_operator_workspace_card",
                "study_session",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "learner_agency_repeat_trace",
            "summary_claim": "final-solution or A6 exposure forces repeat-task handling instead of accepting the checkpoint",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["notebook_checkpoint", "study_session", "evaluation_packet"],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "notebook checkpoints do not publish raw code, grade, proctor, detect AI use, or clear exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["notebook_checkpoint", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    ready_checkpoint = ready_report.get("notebook_checkpoint", {})
    ready_receipt = ready_report.get("study_receipt_summary", {})
    workspace_card = (
        ready_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(ready_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    stored_journal = stored_report.get("checkpoint_journal_summary", {})
    repeat_receipt = repeat_report.get("study_receipt_summary", {})
    blocked_claims = [
        "raw notebook code returned",
        "raw cell text returned",
        "raw notebook returned",
        "local path returned",
        "checkpoint journal write without operator confirmation",
        "final solution acceptance",
        "complete code outsourcing",
        "inserted values",
        "final interpretation",
        "automatic grading",
        "proctoring",
        "KI-detection evidence",
        "Eigenleistung percentage claim",
        "cloud processing",
        "exam deployment",
    ]
    ready_boundary = str(ready_report.get("execution_boundary", ""))
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "ready_checkpoint_public_safe": ready_report.get("public_safety_status") == "pass",
        "stored_checkpoint_public_safe": stored_report.get("public_safety_status") == "pass",
        "repeat_checkpoint_public_safe": repeat_report.get("public_safety_status") == "pass",
        "hash_only_checkpoint_ready": ready_report.get("status") == "notebook_checkpoint_ready"
        and bool(ready_checkpoint.get("cell_source_sha256"))
        and ready_checkpoint.get("raw_cell_returned") is False
        and ready_checkpoint.get("raw_notebook_returned") is False
        and ready_checkpoint.get("notebook_code_returned") is False
        and ready_checkpoint.get("local_path_returned") is False
        and ready_receipt.get("status") == "ok_study_session_receipt",
        "operator_confirmed_journal_hash_only": stored_report.get("status") == "notebook_checkpoint_ready"
        and stored_report.get("operator_confirmations", {}).get("checkpoint_store") is True
        and stored_journal.get("status") == "stored"
        and stored_journal.get("checkpoint_journal_written") is True
        and stored_journal.get("path_returned") is False
        and bool(stored_journal.get("event_hash")),
        "a6_or_final_solution_forces_repeat": repeat_report.get("status") == "notebook_checkpoint_repeat_task_required"
        and repeat_report.get("solution_marker_detected") is True
        and repeat_receipt.get("status") == "repeat_task_required"
        and repeat_receipt.get("repeat_task_required") is True,
        "workspace_card_checkpoint_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and bool(workspace_card.get("help_ledger_preview_hash"))
        and workspace_card.get("selected_skill_tag") == ready_checkpoint.get("skill_tag")
        and workspace_card.get("checkpoint_hash") == ready_checkpoint.get("notebook_work_sha256")
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
        "public_outputs_hide_private_notebook_data": ready_report.get("raw_cell_returned") is False
        and ready_report.get("raw_text_returned") is False
        and ready_report.get("raw_notebook_returned") is False
        and ready_report.get("notebook_code_returned") is False
        and ready_report.get("local_paths_returned") is False
        and "never returns raw cell text" in ready_boundary
        and "notebook code" in ready_boundary
        and "local paths" in ready_boundary,
        "high_stakes_actions_not_started": ready_report.get("exam_deployment_status") == "not_cleared"
        and ready_report.get("automatic_grading_started") is False
        and ready_report.get("proctoring_started") is False
        and ready_report.get("ai_detection_started") is False
        and ready_report.get("exam_clearance_claimed") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "ready_status": ready_report.get("status"),
        "stored_status": stored_report.get("status"),
        "repeat_status": repeat_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "notebook-checkpoint-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": EXAM_NOTEBOOK_CHECKPOINT_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "ready_checkpoint_status": ready_report.get("status"),
        "ready_public_safety_status": ready_report.get("public_safety_status"),
        "stored_checkpoint_status": stored_report.get("status"),
        "stored_public_safety_status": stored_report.get("public_safety_status"),
        "repeat_checkpoint_status": repeat_report.get("status"),
        "repeat_public_safety_status": repeat_report.get("public_safety_status"),
        "exam_deployment_status": ready_report.get("exam_deployment_status"),
        "study_receipt_status": ready_receipt.get("status"),
        "checkpoint_hash_present": bool(ready_checkpoint.get("notebook_work_sha256")),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_checkpoint_gate_linked": contracts["workspace_card_checkpoint_gate_linked"],
        "checkpoint_journal_status": stored_journal.get("status"),
        "checkpoint_journal_written": bool(stored_journal.get("checkpoint_journal_written", False)),
        "repeat_receipt_status": repeat_receipt.get("status"),
        "repeat_task_required": bool(repeat_receipt.get("repeat_task_required", False)),
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
            "Notebook checkpoints are hash-only local learning evidence. They can record checkpoint hashes and "
            "operator-confirmed journal events, but they do not return raw code or paths, accept final solutions, "
            "grade, proctor, detect AI use, claim Eigenleistung percentages, or clear exams."
        ),
    }


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


def synthetic_notebook_checkpoint_workspace_card() -> dict[str, Any]:
    cell_source = "own_values = [1, 2, 3]\nlen(own_values)\n"
    checkpoint_hash = sha256_text(cell_source)
    preview_hash = sha256_text(f"synthetic notebook checkpoint workspace card:{checkpoint_hash}")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic notebook checkpoint prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_notebook_checkpoint_before_workspace_prefill",
            "next_safe_user_action": "review_checkpoint_hash_before_any_local_write",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": preview_hash,
            "checkpoint_hash": checkpoint_hash,
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


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
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_notebook_checkpoint"))
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


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "exam-notebook-checkpoint-adapter")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
