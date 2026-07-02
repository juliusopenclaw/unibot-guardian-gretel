from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


PYTHON_EXAM_COCKPIT_FLOW_SCHEMA_VERSION = "unibot-python-exam-cockpit-flow-v1"
PYTHON_EXAM_COCKPIT_FLOW_ENDPOINT = "/api/unibot/course/python-exam-cockpit-flow"


def build_python_exam_cockpit_flow(
    *,
    python_exam_readiness_console: dict[str, Any] | None = None,
    exam_skill_drilldown: dict[str, Any] | None = None,
    exam_workspace_operator_run: dict[str, Any] | None = None,
    exam_workspace_session_console: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    readiness = python_exam_readiness_console if isinstance(python_exam_readiness_console, dict) else {}
    drilldown = exam_skill_drilldown if isinstance(exam_skill_drilldown, dict) else {}
    operator = exam_workspace_operator_run if isinstance(exam_workspace_operator_run, dict) else {}
    session = exam_workspace_session_console if isinstance(exam_workspace_session_console, dict) else {}
    checkpoint = notebook_checkpoint if isinstance(notebook_checkpoint, dict) else {}
    chain = review_chain_integrity_check if isinstance(review_chain_integrity_check, dict) else {}
    review = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else {}
    journal = timeline_export_receipt_journal_summary if isinstance(timeline_export_receipt_journal_summary, dict) else {}
    skill_tag = effective_skill_tag(selected_skill_tag, readiness, drilldown, session, chain, journal)
    steps = cockpit_steps(
        skill_tag=skill_tag,
        readiness=readiness,
        drilldown=drilldown,
        operator=operator,
        session=session,
        checkpoint=checkpoint,
        chain=chain,
        review=review,
        journal=journal,
    )
    summary = cockpit_summary(steps=steps, readiness=readiness, operator=operator, chain=chain, journal=journal)
    payload = {
        "schema_version": PYTHON_EXAM_COCKPIT_FLOW_SCHEMA_VERSION,
        "artifact_type": "python_exam_cockpit_flow",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Cockpit Flow. It presents a guided, metadata-only step bar from skill selection and "
            "readiness through Start Exam Workspace Operator Dry-Run, Session Console, Notebook Checkpoint, "
            "A0-A2 Tutor Sidecar, Help-/Exam-Ledger Preview, Review Chain Integrity, and Export/Receipt Summary. "
            "It does not execute local writes by itself; local write steps remain behind explicit operator "
            "confirmations and dry-run remains the default. It never returns raw queries, course raw text, notebook "
            "code, local paths, values, solutions, final interpretations, proctoring, AI detection, automatic "
            "assessment, or exam clearance."
        ),
        "cockpit_summary": summary,
        "selected_skill_tag": skill_tag,
        "step_bar": steps,
        "operator_confirmation_status": operator_confirmation_status(operator, readiness),
        "evidence_receipts": evidence_receipts(readiness, operator, session, checkpoint, chain, review, journal),
        "next_safe_action": summary["next_safe_action"],
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Cockpit Flow bleibt not_cleared."
        ),
        "dry_run_default": True,
        "local_writes_executed_by_cockpit": False,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "values_returned": False,
        "solutions_returned": False,
        "final_interpretations_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def cockpit_steps(
    *,
    skill_tag: str,
    readiness: dict[str, Any],
    drilldown: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
    chain: dict[str, Any],
    review: dict[str, Any],
    journal: dict[str, Any],
) -> list[dict[str, Any]]:
    console = session.get("session_console", {}) if isinstance(session.get("session_console"), dict) else {}
    console_checkpoint = console.get("notebook_checkpoint", {}) if isinstance(console.get("notebook_checkpoint"), dict) else {}
    tutor = console.get("tutor_state", {}) if isinstance(console.get("tutor_state"), dict) else {}
    ledger = console.get("help_ledger_preview", {}) if isinstance(console.get("help_ledger_preview"), dict) else {}
    export = console.get("export_receipt", {}) if isinstance(console.get("export_receipt"), dict) else {}
    checkpoint_hash = first_text(
        console_checkpoint.get("notebook_work_sha256", ""),
        checkpoint.get("notebook_work_sha256", ""),
        checkpoint.get("notebook_checkpoint", {}).get("notebook_work_sha256", "")
        if isinstance(checkpoint.get("notebook_checkpoint"), dict)
        else "",
        readiness.get("readiness_summary", {}).get("latest_notebook_checkpoint_hash", "")
        if isinstance(readiness.get("readiness_summary"), dict)
        else "",
    )
    return [
        step(
            "select_skill",
            "Skill auswaehlen",
            complete=bool(skill_tag and drilldown.get("artifact_type") == "exam_skill_drilldown"),
            attention=False,
            source="exam_skill_drilldown",
            evidence={"skill_tag": skill_tag, "start_enabled": bool(drilldown.get("workspace_start_action", {}).get("status") == "ready") if isinstance(drilldown.get("workspace_start_action"), dict) else False},
            next_action="Build Exam-Skill Drilldown for the selected Python skill.",
        ),
        step(
            "readiness_check",
            "Readiness pruefen",
            complete=readiness.get("status") == "python_exam_readiness_console_ready",
            attention=bool(readiness and readiness.get("status") != "python_exam_readiness_console_ready"),
            source="python_exam_readiness_console",
            evidence=readiness_evidence(readiness),
            next_action=readiness_next_action(readiness),
        ),
        step(
            "start_exam_workspace_operator_dry_run",
            "Start Exam Workspace Operator Dry-Run",
            complete=operator.get("artifact_type") == "exam_workspace_operator_run_dry_run",
            attention=bool(operator and operator.get("status") not in {"exam_workspace_operator_dry_run_ready", "exam_workspace_operator_ready_with_confirmed_local_writes"}),
            source="exam_workspace_operator_run",
            evidence=operator_evidence(operator),
            next_action="Run Start Exam Workspace Operator Dry-Run with all write confirmations off by default.",
        ),
        step(
            "session_console",
            "Session Console",
            complete=session.get("artifact_type") == "exam_workspace_session_console",
            attention=bool(session and "ready" not in str(session.get("status", ""))),
            source="exam_workspace_session_console",
            evidence=session_evidence(session),
            next_action="Open Session Console for the selected skill and inspect hash-only evidence.",
        ),
        step(
            "notebook_checkpoint",
            "Notebook Checkpoint",
            complete=bool(checkpoint_hash),
            attention=False,
            source="notebook_checkpoint",
            evidence={"latest_notebook_checkpoint_hash": checkpoint_hash, "raw_cell_returned": False, "notebook_code_returned": False},
            next_action="Create or review the hash-only notebook checkpoint.",
        ),
        step(
            "a0_a2_tutor_sidecar",
            "A0-A2 Tutor Sidecar",
            complete=is_a0_a2(tutor.get("effective_help_level", readiness.get("a0_a2_help_status", {}).get("recommended_help_level", "A2") if isinstance(readiness.get("a0_a2_help_status"), dict) else "A2")),
            attention=not is_a0_a2(tutor.get("effective_help_level", "A2")),
            source="session_console",
            evidence={
                "tutor_status": tutor.get("tutor_status", "unknown"),
                "effective_help_level": tutor.get("effective_help_level", "A2"),
                "allowed_help_boundary": "A0-A2",
            },
            next_action="Keep tutor help inside A0-A2; block solution-like help.",
        ),
        step(
            "help_exam_ledger_preview",
            "Help-/Exam-Ledger Preview",
            complete=bool(ledger.get("status") or operator.get("help_ledger_preview")),
            attention=False,
            source="session_console",
            evidence={
                "ledger_status": ledger.get("status", operator.get("help_ledger_preview", {}).get("status", "missing") if isinstance(operator.get("help_ledger_preview"), dict) else "missing"),
                "general_help_ledger_written": bool(ledger.get("general_help_ledger_written", False)),
                "exam_ledger_written": bool(ledger.get("exam_ledger_written", False)),
                "event_hash": ledger.get("event_hash", ""),
            },
            next_action="Preview Help-/Exam-Ledger evidence; write only after explicit operator confirmation.",
        ),
        step(
            "review_chain_integrity",
            "Review Chain Integrity",
            complete=chain.get("status") == "review_chain_integrity_pass",
            attention=bool(chain and chain.get("status") != "review_chain_integrity_pass"),
            source="review_chain_integrity_check",
            evidence=chain_evidence(chain),
            next_action=chain.get("chain_integrity_summary", {}).get("next_safe_action", "Build Review Chain Integrity Check.") if isinstance(chain.get("chain_integrity_summary"), dict) else "Build Review Chain Integrity Check.",
        ),
        step(
            "export_receipt_summary",
            "Export/Receipt Summary",
            complete=int(journal.get("accepted_record_count", 0) or 0) >= 1,
            attention=bool(journal and int(journal.get("accepted_record_count", 0) or 0) < 1),
            source="timeline_export_receipt_journal_summary",
            evidence={
                "review_packet_status": review.get("status", "missing"),
                "export_receipt_status": export.get("status", review.get("local_export_receipt", {}).get("status", "missing") if isinstance(review.get("local_export_receipt"), dict) else "missing"),
                "journal_status": journal.get("status", "missing"),
                "accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
                "record_count": int(journal.get("record_count", 0) or 0),
            },
            next_action="Review export receipt summary with human review; it is not exam clearance.",
        ),
    ]


def step(
    step_id: str,
    label: str,
    *,
    complete: bool,
    attention: bool,
    source: str,
    evidence: dict[str, Any],
    next_action: str,
) -> dict[str, Any]:
    status = "complete" if complete and not attention else ("attention" if attention else "waiting")
    return {
        "step_id": step_id,
        "label": label,
        "status": status,
        "source": source,
        "evidence": safe_evidence(evidence),
        "next_safe_action": next_action,
        "exam_deployment_status": "not_cleared",
        "dry_run_default": True,
        "requires_operator_confirmation_for_local_writes": step_id in {
            "start_exam_workspace_operator_dry_run",
            "notebook_checkpoint",
            "help_exam_ledger_preview",
            "export_receipt_summary",
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def cockpit_summary(
    *,
    steps: list[dict[str, Any]],
    readiness: dict[str, Any],
    operator: dict[str, Any],
    chain: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    complete_count = len([item for item in steps if item.get("status") == "complete"])
    attention_count = len([item for item in steps if item.get("status") == "attention"])
    waiting_count = len([item for item in steps if item.get("status") == "waiting"])
    confirmations = operator_confirmation_status(operator, readiness)
    if attention_count:
        status = "python_exam_cockpit_flow_attention"
    elif complete_count == len(steps):
        status = "python_exam_cockpit_flow_ready"
    else:
        status = "python_exam_cockpit_flow_waiting"
    return {
        "status": status,
        "step_count": len(steps),
        "complete_step_count": complete_count,
        "attention_step_count": attention_count,
        "waiting_step_count": waiting_count,
        "current_step_id": next((item["step_id"] for item in steps if item.get("status") != "complete"), steps[-1]["step_id"] if steps else ""),
        "readiness_status": readiness.get("status", "missing"),
        "review_chain_status": chain.get("status", "missing"),
        "receipt_journal_status": journal.get("status", "missing"),
        "open_operator_confirmation_count": confirmations["open_operator_confirmation_count"],
        "confirmed_local_write_step_count": confirmations["confirmed_local_write_step_count"],
        "dry_run_default": True,
        "local_writes_executed_by_cockpit": False,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": next_safe_action(steps, status),
    }


def operator_confirmation_status(operator: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    matrix = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    steps = matrix.get("steps", {}) if isinstance(matrix.get("steps"), dict) else {}
    confirmed = [key for key, item in steps.items() if isinstance(item, dict) and item.get("confirmed")]
    open_steps = [key for key, item in steps.items() if isinstance(item, dict) and item.get("writes_local") and not item.get("confirmed")]
    readiness_confirmations = readiness.get("operator_confirmation_status", {}) if isinstance(readiness.get("operator_confirmation_status"), dict) else {}
    return {
        "status": "operator_confirmations_present" if confirmed else "dry_run_default_no_cockpit_writes",
        "confirmed_local_write_step_count": len(confirmed),
        "confirmed_local_write_steps": confirmed,
        "open_operator_confirmation_count": max(len(open_steps), int(readiness_confirmations.get("open_operator_confirmation_count", 0) or 0)),
        "open_operator_confirmation_steps": open_steps,
        "local_writes_require_confirmation": True,
        "dry_run_default": True,
    }


def evidence_receipts(
    readiness: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
    chain: dict[str, Any],
    review: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    return {
        "readiness_status": readiness.get("status", "missing"),
        "operator_receipt_id": nested(operator, "dry_run_receipt", "receipt_id"),
        "session_receipt_id": nested(session, "session_console_receipt", "receipt_id"),
        "notebook_checkpoint_hash": first_text(
            nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256"),
            checkpoint.get("notebook_work_sha256", ""),
            nested(checkpoint, "notebook_checkpoint", "notebook_work_sha256"),
        ),
        "review_chain_status": chain.get("status", "missing"),
        "review_receipt_id": nested(review, "local_export_receipt", "receipt_id"),
        "receipt_journal_record_count": int(journal.get("record_count", 0) or 0),
        "receipt_journal_accepted_record_count": int(journal.get("accepted_record_count", 0) or 0),
        "exam_deployment_status": "not_cleared",
    }


def readiness_evidence(readiness: dict[str, Any]) -> dict[str, Any]:
    summary = readiness.get("readiness_summary", {}) if isinstance(readiness.get("readiness_summary"), dict) else {}
    return {
        "status": readiness.get("status", "missing"),
        "skill_ready_for_workspace": bool(summary.get("skill_ready_for_workspace", False)),
        "review_chain_pass": bool(summary.get("review_chain_pass", False)),
        "receipt_journal_ready": bool(summary.get("receipt_journal_ready", False)),
        "next_safe_action": summary.get("next_safe_action", ""),
    }


def operator_evidence(operator: dict[str, Any]) -> dict[str, Any]:
    receipt = operator.get("dry_run_receipt", {}) if isinstance(operator.get("dry_run_receipt"), dict) else {}
    matrix = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    return {
        "status": operator.get("status", "missing"),
        "receipt_id": receipt.get("receipt_id", ""),
        "selected_skill_tag": receipt.get("selected_skill_tag", ""),
        "effective_help_level": receipt.get("effective_help_level", "A2"),
        "confirmed_count": int(matrix.get("confirmed_count", 0) or 0),
        "write_step_count": int(matrix.get("write_step_count", 0) or 0),
    }


def session_evidence(session: dict[str, Any]) -> dict[str, Any]:
    receipt = session.get("session_console_receipt", {}) if isinstance(session.get("session_console_receipt"), dict) else {}
    console = session.get("session_console", {}) if isinstance(session.get("session_console"), dict) else {}
    return {
        "status": session.get("status", "missing"),
        "receipt_id": receipt.get("receipt_id", ""),
        "repeat_run_index": int(receipt.get("repeat_run_index", 0) or 0),
        "console_status": console.get("status", "missing"),
    }


def chain_evidence(chain: dict[str, Any]) -> dict[str, Any]:
    summary = chain.get("chain_integrity_summary", {}) if isinstance(chain.get("chain_integrity_summary"), dict) else {}
    return {
        "status": chain.get("status", "missing"),
        "issue_count": int(summary.get("issue_count", 0) or 0),
        "checked_link_count": int(summary.get("checked_link_count", 0) or 0),
        "next_safe_action": summary.get("next_safe_action", ""),
    }


def next_safe_action(steps: list[dict[str, Any]], status: str) -> str:
    for item in steps:
        if item.get("status") == "attention":
            return str(item.get("next_safe_action", "Resolve the cockpit attention item."))
    for item in steps:
        if item.get("status") == "waiting":
            return str(item.get("next_safe_action", "Continue the next cockpit step."))
    if status == "python_exam_cockpit_flow_ready":
        return "Proceed with the metadata-only cockpit evidence review; keep A0-A2 and not_cleared."
    return "Review cockpit step status before continuing."


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review cockpit step status."),
        "Use the step bar in order; local writes remain behind explicit operator confirmations.",
        "Keep A0-A2 help only and keep exam_deployment_status not_cleared.",
    ]


def readiness_next_action(readiness: dict[str, Any]) -> str:
    summary = readiness.get("readiness_summary", {}) if isinstance(readiness.get("readiness_summary"), dict) else {}
    return str(summary.get("next_safe_action", "Build Python Exam Readiness Console."))


def effective_skill_tag(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for path in [
                ("readiness_summary", "selected_skill_tag"),
                ("selected_skill_readiness", "skill_tag"),
                ("selected_skill", "skill_tag"),
                ("session_console", "selected_skill", "skill_tag"),
                ("chain_integrity_summary", "skill_tags"),
                ("skill_tags",),
            ]:
                found = nested(value, *path)
                if isinstance(found, list) and found:
                    return str(found[0])
                if isinstance(found, str) and found:
                    return found
    return "python_skill"


def safe_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    safe = dict(evidence)
    safe.update(
        {
            "raw_query_returned": False,
            "raw_text_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
        }
    )
    return safe


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def nested(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def is_a0_a2(level: Any) -> bool:
    return str(level or "").startswith(("A0", "A1", "A2"))


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-cockpit-flow")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
