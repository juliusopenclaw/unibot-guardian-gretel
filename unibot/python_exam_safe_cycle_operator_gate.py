from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_SAFE_CYCLE_OPERATOR_GATE_SCHEMA_VERSION = "unibot-python-exam-safe-cycle-operator-gate-v1"
PYTHON_EXAM_SAFE_CYCLE_OPERATOR_GATE_ENDPOINT = "/api/unibot/course/python-exam-safe-cycle-operator-gate"


def build_python_exam_safe_cycle_operator_gate(
    *,
    python_exam_safe_cycle_console: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    console = python_exam_safe_cycle_console if isinstance(python_exam_safe_cycle_console, dict) else {}
    cycle = console.get("current_cycle_view", {}) if isinstance(console.get("current_cycle_view"), dict) else {}
    preview = cycle.get("preview", {}) if isinstance(cycle.get("preview"), dict) else {}
    receipts = cycle.get("receipts", {}) if isinstance(cycle.get("receipts"), dict) else {}
    matrix = cycle.get("operator_confirmation_matrix", {}) if isinstance(cycle.get("operator_confirmation_matrix"), dict) else {}
    selected = selected_skill_tag or nested(console, "safe_cycle_summary", "selected_skill_tag") or preview.get("selected_skill_tag") or "general_python"
    cards = confirmation_cards(selected_skill_tag=str(selected), preview=preview, receipts=receipts)
    summary = gate_summary(console=console, preview=preview, matrix=matrix, cards=cards, selected_skill_tag=str(selected))
    payload = {
        "schema_version": PYTHON_EXAM_SAFE_CYCLE_OPERATOR_GATE_SCHEMA_VERSION,
        "artifact_type": "python_exam_safe_cycle_operator_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_safe_cycle_operator_gate_ready" if summary["ready"] else "python_exam_safe_cycle_operator_gate_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Safe Cycle Operator Gate. It turns the Safe Cycle Console into separate human-reviewable "
            "confirmation cards before any local exam work cycle is started or continued. Cards cover opening the "
            "Control Panel, preparing a local notebook checkpoint, using A0-A2 help, reviewing Help-Ledger preview, "
            "and preparing Progress-Journal append. It uses only Safe-Cycle metadata, skill tag, task/checkpoint "
            "hashes, Source-Card anchors, A0-A2 help level, receipts, and operator-confirmation status. All "
            "confirmations default to false and no local writes start automatically. It never returns raw queries, "
            "course raw text, notebook code, local paths, values, solutions, final interpretations, scores, "
            "percentages, rankings, grades, proctoring, AI detection, automatic grading, or exam clearance."
        ),
        "operator_gate_endpoint": PYTHON_EXAM_SAFE_CYCLE_OPERATOR_GATE_ENDPOINT,
        "selected_skill_tag": str(selected),
        "operator_gate_summary": summary,
        "confirmation_cards": cards,
        "operator_confirmation_matrix": gate_matrix(cards),
        "operator_gate_receipt": gate_receipt(summary, cards),
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; das Operator Gate bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def confirmation_cards(*, selected_skill_tag: str, preview: dict[str, Any], receipts: dict[str, Any]) -> list[dict[str, Any]]:
    base = safe_base(selected_skill_tag=selected_skill_tag, preview=preview, receipts=receipts)
    specs = [
        (
            "open_control_panel",
            "Control Panel öffnen",
            "review_control_panel_preview",
            "Prepares the Control Panel preview for the selected safe action without opening local files.",
        ),
        (
            "prepare_notebook_checkpoint",
            "Lokalen Notebook-Checkpoint vorbereiten",
            "prepare_checkpoint_hash_only",
            "Prepares a local checkpoint step; the gate returns only checkpoint hash metadata.",
        ),
        (
            "use_a0_a2_help",
            "A0-A2-Hilfe nutzen",
            "use_a0_a2_help_only",
            "Allows only A0-A2 assistance metadata; no values, code, solution, or final interpretation.",
        ),
        (
            "review_help_ledger_preview",
            "Help-Ledger-Preview prüfen",
            "review_help_ledger_preview",
            "Reviews the Help-Ledger event hash before any append decision.",
        ),
        (
            "prepare_progress_journal_append",
            "Progress-Journal-Append vorbereiten",
            "prepare_progress_append_preview",
            "Prepares Progress Journal append as preview only; append remains unconfirmed.",
        ),
    ]
    cards = []
    for step_id, label, action, description in specs:
        seed = {**base, "step_id": step_id, "action": action}
        cards.append(
            {
                "step_id": step_id,
                "label": label,
                "status": "operator_confirmation_required_dry_run",
                "description": description,
                "action": action,
                **base,
                "confirmation_required": True,
                "operator_confirmed": False,
                "write_started": False,
                "local_write_preview_only": True,
                "card_hash": sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False)),
                "raw_query_returned": False,
                "raw_text_returned": False,
                "raw_cell_returned": False,
                "notebook_code_returned": False,
                "local_paths_returned": False,
                "solutions_returned": False,
                "score_returned": False,
                "grade_returned": False,
            }
        )
    return cards


def safe_base(*, selected_skill_tag: str, preview: dict[str, Any], receipts: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_skill_tag": selected_skill_tag,
        "next_safe_action": safe_action(str(preview.get("action", ""))),
        "route": str(preview.get("route", "missing")),
        "endpoint": str(preview.get("endpoint", "")),
        "selected_task_hash": str(preview.get("selected_task_hash", "")),
        "checkpoint_hash": str(preview.get("checkpoint_hash", "")),
        "source_card_ids": [str(item) for item in (preview.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(preview.get("source_anchor_count", 0) or 0),
        "help_level": safe_help_level(str(preview.get("help_level", "A2"))),
        "help_ledger_event_hash": str(receipts.get("help_ledger_event_hash", "")),
        "review_loop_receipt_id": str(receipts.get("review_loop_receipt_id", "")),
        "progress_entry_hash": str(receipts.get("progress_entry_hash", "")),
        "control_panel_receipt_id": str(receipts.get("control_panel_receipt_id", "")),
        "execution_bridge_receipt_id": str(receipts.get("execution_bridge_receipt_id", "")),
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def gate_summary(
    *,
    console: dict[str, Any],
    preview: dict[str, Any],
    matrix: dict[str, Any],
    cards: list[dict[str, Any]],
    selected_skill_tag: str,
) -> dict[str, Any]:
    ready = (
        console.get("status") == "python_exam_safe_cycle_console_ready"
        and bool(preview.get("ready"))
        and len(cards) == 5
        and all(card.get("operator_confirmed") is False for card in cards)
        and int(matrix.get("confirmed_count", 0) or 0) == 0
    )
    return {
        "selected_skill_tag": selected_skill_tag,
        "safe_cycle_status": console.get("status", "missing"),
        "cycle_status": nested(console, "safe_cycle_summary", "cycle_status") or "missing",
        "ready": ready,
        "gate_status": "operator_gate_ready_for_human_review" if ready else "operator_gate_attention",
        "next_safe_action": safe_action(str(preview.get("action", ""))),
        "route": str(preview.get("route", "missing")),
        "endpoint": str(preview.get("endpoint", "")),
        "selected_task_hash": str(preview.get("selected_task_hash", "")),
        "checkpoint_hash": str(preview.get("checkpoint_hash", "")),
        "source_card_count": len(preview.get("source_card_ids", []) or []),
        "help_level": safe_help_level(str(preview.get("help_level", "A2"))),
        "confirmation_card_count": len(cards),
        "confirmed_count": 0,
        "local_writes_started": False,
        "a0_a2_only": True,
        "dry_run_default": True,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def gate_matrix(cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "all_steps_waiting_for_operator_confirmation",
        "confirmed_count": 0,
        "local_writes_requested": False,
        "steps": [
            {
                "step_id": card.get("step_id", ""),
                "required_before_write": True,
                "confirmed": False,
                "write_started": False,
            }
            for card in cards
        ],
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def gate_receipt(summary: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "cards": cards}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "safe_cycle_operator_gate_receipt_ready_not_exam_clearance",
        "receipt_id": receipt_hash[:20],
        "receipt_hash": receipt_hash,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
        "score_returned": False,
        "grade_returned": False,
    }


def safe_action(action: str) -> str:
    if action in {
        "run_next_microtask",
        "repeat_current_microtask",
        "start_first_microtask",
        "return_to_skill_dashboard",
        "review_skill_readiness",
    }:
        return action
    return "review_skill_readiness"


def safe_help_level(help_level: str) -> str:
    value = str(help_level or "A2").upper()
    return value if value in {"A0", "A1", "A2"} else "A2"


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        "Review each Operator Gate card before starting the local cycle.",
        "Keep all confirmations false until the human operator explicitly confirms one local step.",
        "Use only A0-A2 help and keep exam_deployment_status not_cleared.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-safe-cycle-operator-gate")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
