from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


PYTHON_EXAM_LIVE_CONTROL_SURFACE_SCHEMA_VERSION = "unibot-python-exam-live-control-surface-v1"
PYTHON_EXAM_LIVE_CONTROL_SURFACE_ENDPOINT = "/api/unibot/course/python-exam-live-control-surface"


ACTION_CONTRACTS: dict[str, dict[str, Any]] = {
    "select_skill": {
        "safe_action_id": "select_skill_refresh",
        "label": "Skill Drilldown aktualisieren",
        "endpoint": "/api/unibot/course/exam-skill-drilldown",
        "requires_operator_confirmation_for_local_writes": False,
        "local_write_confirmation_keys": [],
    },
    "readiness_check": {
        "safe_action_id": "readiness_refresh",
        "label": "Readiness neu pruefen",
        "endpoint": "/api/unibot/course/python-exam-readiness-console",
        "requires_operator_confirmation_for_local_writes": False,
        "local_write_confirmation_keys": [],
    },
    "start_exam_workspace_operator_dry_run": {
        "safe_action_id": "operator_dry_run",
        "label": "Operator Dry-Run starten",
        "endpoint": "/api/unibot/exam-workspace/operator-run",
        "requires_operator_confirmation_for_local_writes": True,
        "local_write_confirmation_keys": ["confirmExamWorkspaceRun"],
    },
    "session_console": {
        "safe_action_id": "session_console_refresh",
        "label": "Session Console aktualisieren",
        "endpoint": "/api/unibot/exam-workspace/session-console",
        "requires_operator_confirmation_for_local_writes": False,
        "local_write_confirmation_keys": [],
    },
    "notebook_checkpoint": {
        "safe_action_id": "notebook_checkpoint_hash",
        "label": "Notebook-Checkpoint hashen",
        "endpoint": "/api/unibot/exam-workspace/notebook-checkpoint/adapt",
        "requires_operator_confirmation_for_local_writes": True,
        "local_write_confirmation_keys": ["confirmCheckpointStore"],
    },
    "a0_a2_tutor_sidecar": {
        "safe_action_id": "a0_a2_tutor_sidecar_refresh",
        "label": "A0-A2 Tutorstatus pruefen",
        "endpoint": "/api/unibot/exam-workspace/session-console",
        "requires_operator_confirmation_for_local_writes": False,
        "local_write_confirmation_keys": [],
    },
    "help_exam_ledger_preview": {
        "safe_action_id": "ledger_preview_check",
        "label": "Ledger Preview pruefen",
        "endpoint": "/api/unibot/exam-workspace/session-console",
        "requires_operator_confirmation_for_local_writes": True,
        "local_write_confirmation_keys": ["confirmHelpLedgerAppend", "confirmExamLedgerAppend"],
    },
    "review_chain_integrity": {
        "safe_action_id": "review_chain_check",
        "label": "Review Chain Integrity pruefen",
        "endpoint": "/api/unibot/course/review-chain-integrity-check",
        "requires_operator_confirmation_for_local_writes": False,
        "local_write_confirmation_keys": [],
    },
    "export_receipt_summary": {
        "safe_action_id": "receipt_summary_refresh",
        "label": "Receipt Summary aktualisieren",
        "endpoint": "/api/unibot/course/timeline-export-receipt-journal/summary",
        "requires_operator_confirmation_for_local_writes": True,
        "local_write_confirmation_keys": ["confirmTimelineExportReceiptJournalAppend"],
    },
}


def build_python_exam_live_control_surface(
    *,
    python_exam_cockpit_flow: dict[str, Any] | None = None,
    python_exam_readiness_console: dict[str, Any] | None = None,
    exam_skill_drilldown: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    exam_workspace_operator_run: dict[str, Any] | None = None,
    exam_workspace_session_console: dict[str, Any] | None = None,
    notebook_checkpoint: dict[str, Any] | None = None,
    review_chain_integrity_check: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    cockpit = python_exam_cockpit_flow if isinstance(python_exam_cockpit_flow, dict) else {}
    readiness = python_exam_readiness_console if isinstance(python_exam_readiness_console, dict) else {}
    drilldown = exam_skill_drilldown if isinstance(exam_skill_drilldown, dict) else {}
    workspace_card = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    operator = exam_workspace_operator_run if isinstance(exam_workspace_operator_run, dict) else {}
    session = exam_workspace_session_console if isinstance(exam_workspace_session_console, dict) else {}
    checkpoint = notebook_checkpoint if isinstance(notebook_checkpoint, dict) else {}
    chain = review_chain_integrity_check if isinstance(review_chain_integrity_check, dict) else {}
    review = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else {}
    journal = timeline_export_receipt_journal_summary if isinstance(timeline_export_receipt_journal_summary, dict) else {}
    skill_tag = effective_skill_tag(selected_skill_tag, cockpit, readiness, drilldown, session, chain, journal)
    step_bar = [item for item in cockpit.get("step_bar", []) if isinstance(item, dict)]
    control_actions = build_control_actions(step_bar, cockpit)
    summary = control_summary(
        cockpit=cockpit,
        readiness=readiness,
        control_actions=control_actions,
        skill_tag=skill_tag,
    )
    workspace_card_summary_data = workspace_card_summary(workspace_card)
    lights = status_lights(
        summary=summary,
        cockpit=cockpit,
        readiness=readiness,
        chain=chain,
        journal=journal,
    )
    payload = {
        "schema_version": PYTHON_EXAM_LIVE_CONTROL_SURFACE_SCHEMA_VERSION,
        "artifact_type": "python_exam_live_control_surface",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Live Control Surface. It is a sidepanel-first, metadata-only action surface over the "
            "Python Exam Cockpit Flow. It offers direct safe actions for readiness refresh, operator dry-run, "
            "session console refresh, notebook checkpoint hashing, ledger preview review, review-chain integrity, "
            "and receipt summary refresh. It performs no local writes by itself; dry-run remains the default and "
            "every local write stays behind an explicit operator confirmation. It never returns raw queries, course "
            "raw text, notebook code, local paths, values, solutions, final interpretations, proctoring, AI "
            "detection, automatic assessment, or exam clearance."
        ),
        "sidepanel_first": True,
        "selected_skill_tag": skill_tag,
        "control_summary": summary,
        "status_lights": lights,
        "control_actions": control_actions,
        "local_cycle_operator_workspace_card": workspace_card_summary_data,
        "local_cycle_operator_workspace_card_source": safe_workspace_card_source(workspace_card),
        "operator_confirmation_status": operator_confirmation_status(cockpit, readiness, operator),
        "a0_a2_help_status": a0_a2_help_status(cockpit, readiness, session),
        "evidence_receipts": evidence_receipts(cockpit, readiness, operator, session, checkpoint, chain, review, journal),
        "next_safe_action": workspace_card_summary_data.get("next_safe_action") or summary["next_safe_action"],
        "real_world_clearance_reminder": (
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; die Live Control Surface bleibt not_cleared."
        ),
        "dry_run_default": True,
        "local_writes_executed_by_surface": False,
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


def build_control_actions(step_bar: list[dict[str, Any]], cockpit: dict[str, Any]) -> list[dict[str, Any]]:
    if not step_bar:
        step_bar = fallback_steps(cockpit)
    actions: list[dict[str, Any]] = []
    for index, step in enumerate(step_bar):
        step_id = str(step.get("step_id", ""))
        contract = ACTION_CONTRACTS.get(step_id, {})
        step_status = str(step.get("status", "waiting"))
        actions.append(
            {
                "safe_action_id": contract.get("safe_action_id", f"{step_id}_action"),
                "step_id": step_id,
                "label": contract.get("label", step.get("label", step_id)),
                "step_label": step.get("label", step_id),
                "method": "POST",
                "endpoint": contract.get("endpoint", ""),
                "status": step_status,
                "light": action_light(step_status),
                "enabled": bool(contract.get("endpoint")),
                "sequence_index": index + 1,
                "dry_run_default": True,
                "requires_operator_confirmation_for_local_writes": bool(
                    contract.get(
                        "requires_operator_confirmation_for_local_writes",
                        step.get("requires_operator_confirmation_for_local_writes", False),
                    )
                ),
                "local_write_confirmation_keys": list(contract.get("local_write_confirmation_keys", [])),
                "next_safe_action": step.get("next_safe_action", ""),
                "evidence": safe_evidence(step.get("evidence", {}) if isinstance(step.get("evidence"), dict) else {}),
                "exam_deployment_status": "not_cleared",
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "raw_notebook_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
                "values_returned": False,
                "solutions_returned": False,
                "final_interpretations_returned": False,
            }
        )
    return actions


def fallback_steps(cockpit: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(cockpit.get("status", "missing"))
    return [
        {
            "step_id": step_id,
            "label": contract["label"],
            "status": "waiting" if status == "missing" else "attention",
            "next_safe_action": "Build Python Exam Cockpit Flow before using the Live Control Surface.",
            "evidence": {},
        }
        for step_id, contract in ACTION_CONTRACTS.items()
    ]


def control_summary(
    *,
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    control_actions: list[dict[str, Any]],
    skill_tag: str,
) -> dict[str, Any]:
    attention_count = len([item for item in control_actions if item.get("status") == "attention"])
    waiting_count = len([item for item in control_actions if item.get("status") == "waiting"])
    enabled_count = len([item for item in control_actions if item.get("enabled")])
    confirmations = operator_confirmation_status(cockpit, readiness, {})
    current_step_id = first_text(
        nested(cockpit, "cockpit_summary", "current_step_id"),
        next((str(item.get("step_id", "")) for item in control_actions if item.get("status") != "complete"), ""),
    )
    cockpit_status = str(cockpit.get("status", "missing"))
    if attention_count or "attention" in cockpit_status:
        status = "python_exam_live_control_surface_attention"
    elif control_actions and waiting_count == 0 and cockpit_status == "python_exam_cockpit_flow_ready":
        status = "python_exam_live_control_surface_ready"
    else:
        status = "python_exam_live_control_surface_waiting"
    return {
        "status": status,
        "selected_skill_tag": skill_tag,
        "action_count": len(control_actions),
        "enabled_action_count": enabled_count,
        "attention_action_count": attention_count,
        "waiting_action_count": waiting_count,
        "current_step_id": current_step_id,
        "cockpit_status": cockpit_status,
        "readiness_status": readiness.get("status", "missing"),
        "open_operator_confirmation_count": confirmations["open_operator_confirmation_count"],
        "dry_run_default": True,
        "sidepanel_first": True,
        "local_writes_executed_by_surface": False,
        "exam_deployment_status": "not_cleared",
        "next_safe_action": live_next_safe_action(control_actions, status, cockpit),
    }


def status_lights(
    *,
    summary: dict[str, Any],
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    chain: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, str]:
    return {
        "overall": "green" if summary.get("status") == "python_exam_live_control_surface_ready" else ("amber" if summary.get("status") != "blocked_public_safety" else "red"),
        "readiness": "green" if readiness.get("status") == "python_exam_readiness_console_ready" else "amber",
        "operator_confirmations": "amber" if int(summary.get("open_operator_confirmation_count", 0) or 0) else "green",
        "a0_a2": "green" if a0_a2_help_status(cockpit, readiness, {}).get("status") == "a0_a2_only" else "red",
        "review_chain": "green" if chain.get("status") == "review_chain_integrity_pass" else "amber",
        "receipt_journal": "green" if int(journal.get("accepted_record_count", 0) or 0) >= 1 else "amber",
        "exam_deployment": "grey",
    }


def action_light(step_status: str) -> str:
    if step_status == "complete":
        return "green"
    if step_status == "attention":
        return "amber"
    return "grey"


def operator_confirmation_status(cockpit: dict[str, Any], readiness: dict[str, Any], operator: dict[str, Any]) -> dict[str, Any]:
    cockpit_confirmations = cockpit.get("operator_confirmation_status", {}) if isinstance(cockpit.get("operator_confirmation_status"), dict) else {}
    readiness_confirmations = readiness.get("operator_confirmation_status", {}) if isinstance(readiness.get("operator_confirmation_status"), dict) else {}
    matrix = operator.get("operator_confirmation_matrix", {}) if isinstance(operator.get("operator_confirmation_matrix"), dict) else {}
    confirmed = int(
        first_number(
            cockpit_confirmations.get("confirmed_local_write_step_count"),
            matrix.get("confirmed_count"),
            0,
        )
    )
    curated_open_count = max(
        int(cockpit_confirmations.get("open_operator_confirmation_count", 0) or 0),
        int(readiness_confirmations.get("open_operator_confirmation_count", 0) or 0),
        0,
    )
    matrix_open_count = max(int(matrix.get("write_step_count", 0) or 0) - confirmed, 0)
    open_count = curated_open_count if cockpit_confirmations or readiness_confirmations else matrix_open_count
    return {
        "status": "operator_confirmations_open" if open_count else "operator_confirmations_reviewed",
        "open_operator_confirmation_count": open_count,
        "confirmed_local_write_step_count": confirmed,
        "open_operator_confirmation_steps": list(cockpit_confirmations.get("open_operator_confirmation_steps", []) or []),
        "local_writes_require_confirmation": True,
        "dry_run_default": True,
    }


def a0_a2_help_status(cockpit: dict[str, Any], readiness: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    readiness_help = readiness.get("a0_a2_help_status", {}) if isinstance(readiness.get("a0_a2_help_status"), dict) else {}
    console = session.get("session_console", {}) if isinstance(session.get("session_console"), dict) else {}
    tutor = console.get("tutor_state", {}) if isinstance(console.get("tutor_state"), dict) else {}
    level = first_text(
        tutor.get("effective_help_level", ""),
        readiness_help.get("recommended_help_level", ""),
        "A2",
    )
    nonstandard = int(readiness_help.get("nonstandard_help_event_count", 0) or 0)
    allowed = str(level).startswith(("A0", "A1", "A2")) and nonstandard == 0
    return {
        "status": "a0_a2_only" if allowed else "nonstandard_help_attention",
        "effective_help_level": level,
        "observed_help_profile": readiness_help.get("observed_help_profile", {}),
        "nonstandard_help_event_count": nonstandard,
        "allowed_help_boundary": "A0-A2",
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def evidence_receipts(
    cockpit: dict[str, Any],
    readiness: dict[str, Any],
    operator: dict[str, Any],
    session: dict[str, Any],
    checkpoint: dict[str, Any],
    chain: dict[str, Any],
    review: dict[str, Any],
    journal: dict[str, Any],
) -> dict[str, Any]:
    cockpit_receipts = cockpit.get("evidence_receipts", {}) if isinstance(cockpit.get("evidence_receipts"), dict) else {}
    return {
        "readiness_status": first_text(cockpit_receipts.get("readiness_status"), readiness.get("status"), "missing"),
        "operator_receipt_id": first_text(cockpit_receipts.get("operator_receipt_id"), nested(operator, "dry_run_receipt", "receipt_id")),
        "session_receipt_id": first_text(cockpit_receipts.get("session_receipt_id"), nested(session, "session_console_receipt", "receipt_id")),
        "notebook_checkpoint_hash": first_text(
            cockpit_receipts.get("notebook_checkpoint_hash"),
            nested(session, "session_console", "notebook_checkpoint", "notebook_work_sha256"),
            checkpoint.get("notebook_work_sha256", ""),
            nested(checkpoint, "notebook_checkpoint", "notebook_work_sha256"),
        ),
        "review_chain_status": first_text(cockpit_receipts.get("review_chain_status"), chain.get("status"), "missing"),
        "review_receipt_id": first_text(cockpit_receipts.get("review_receipt_id"), nested(review, "local_export_receipt", "receipt_id")),
        "receipt_journal_record_count": int(first_number(cockpit_receipts.get("receipt_journal_record_count"), journal.get("record_count"), 0)),
        "receipt_journal_accepted_record_count": int(
            first_number(cockpit_receipts.get("receipt_journal_accepted_record_count"), journal.get("accepted_record_count"), 0)
        ),
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
    }


def live_next_safe_action(control_actions: list[dict[str, Any]], status: str, cockpit: dict[str, Any]) -> str:
    for item in control_actions:
        if item.get("status") == "attention":
            return str(item.get("next_safe_action") or "Resolve the highlighted Live Control action.")
    for item in control_actions:
        if item.get("status") == "waiting":
            return str(item.get("next_safe_action") or "Run the next safe Live Control action.")
    if status == "python_exam_live_control_surface_ready":
        return "Use the sidepanel actions for metadata-only review; keep dry-run, A0-A2, and not_cleared."
    return str(cockpit.get("next_safe_action", "Build Python Exam Cockpit Flow before continuing."))


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review Live Control Surface state."),
        "Use the enabled sidepanel action for the current step; dry-run remains default.",
        "Confirm local write steps individually before any future non-dry-run write.",
        "Keep A0-A2 help only and keep exam_deployment_status not_cleared.",
    ]


def workspace_card_summary(workspace_card: dict[str, Any]) -> dict[str, Any]:
    summary = (
        workspace_card.get("workspace_card_summary", {})
        if isinstance(workspace_card.get("workspace_card_summary"), dict)
        else {}
    )
    review = workspace_card.get("readiness_review", {}) if isinstance(workspace_card.get("readiness_review"), dict) else {}
    handoff = workspace_card.get("readiness_handoff", {}) if isinstance(workspace_card.get("readiness_handoff"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(workspace_card.get("selected_skill_tag", summary.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(summary.get("recommendation_reason", review.get("recommendation_reason", "missing_start_packet"))),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "open_confirmation_count": int(summary.get("open_confirmation_count", review.get("open_confirmation_count", 0)) or 0),
        "confirmed_count": int(summary.get("confirmed_count", review.get("confirmed_count", 0)) or 0),
        "task_hash": str(summary.get("task_hash", review.get("task_hash", ""))),
        "checkpoint_hash": str(summary.get("checkpoint_hash", review.get("checkpoint_hash", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "prefill_hash": str(handoff.get("prefill_hash", "")),
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", workspace_card.get("source_card_ids", [])) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", workspace_card.get("source_anchor_count", 0)) or 0),
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def safe_workspace_card_source(workspace_card: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": workspace_card.get("selected_skill_tag", ""),
        "readiness_review_status": workspace_card.get("readiness_review_status", ""),
        "readiness_handoff_status": workspace_card.get("readiness_handoff_status", ""),
        "help_ledger_preview_status": workspace_card.get("help_ledger_preview", {}).get("status", "") if isinstance(workspace_card.get("help_ledger_preview"), dict) else "",
        "operator_run_endpoint": workspace_card.get("operator_run_prefill", {}).get("endpoint", "") if isinstance(workspace_card.get("operator_run_prefill"), dict) else "",
        "exam_deployment_status": "not_cleared",
    }


def safe_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    safe = dict(evidence)
    safe.update(
        {
            "raw_query_returned": False,
            "raw_text_returned": False,
            "raw_cell_returned": False,
            "raw_notebook_returned": False,
            "notebook_code_returned": False,
            "local_paths_returned": False,
            "values_returned": False,
            "solutions_returned": False,
            "final_interpretations_returned": False,
        }
    )
    return safe


def effective_skill_tag(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for path in [
                ("selected_skill_tag",),
                ("control_summary", "selected_skill_tag"),
                ("cockpit_summary", "selected_skill_tag"),
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


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def first_number(*values: Any) -> int:
    for value in values:
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def nested(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-live-control-surface")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
