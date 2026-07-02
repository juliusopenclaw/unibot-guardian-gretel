from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


PYTHON_EXAM_OPERATOR_GATE_DECISION_RECEIPT_SCHEMA_VERSION = "unibot-python-exam-operator-gate-decision-receipt-v1"
PYTHON_EXAM_OPERATOR_GATE_DECISION_RECEIPT_ENDPOINT = "/api/unibot/course/python-exam-operator-gate-decision-receipt"


def build_python_exam_operator_gate_decision_receipt(
    *,
    python_exam_safe_cycle_operator_gate: dict[str, Any] | None = None,
    confirmed_step_ids: list[str] | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    gate = python_exam_safe_cycle_operator_gate if isinstance(python_exam_safe_cycle_operator_gate, dict) else {}
    cards = safe_cards(gate.get("confirmation_cards", []) if isinstance(gate.get("confirmation_cards"), list) else [])
    confirmed = safe_confirmed_steps(confirmed_step_ids, cards)
    selected = selected_skill_tag or nested(gate, "operator_gate_summary", "selected_skill_tag") or "general_python"
    card_status = decision_card_status(cards=cards, confirmed_step_ids=confirmed)
    summary = decision_summary(gate=gate, card_status=card_status, selected_skill_tag=str(selected))
    payload = {
        "schema_version": PYTHON_EXAM_OPERATOR_GATE_DECISION_RECEIPT_SCHEMA_VERSION,
        "artifact_type": "python_exam_operator_gate_decision_receipt",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "python_exam_operator_gate_decision_receipt_ready" if summary["ready"] else "python_exam_operator_gate_decision_receipt_attention",
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Python Exam Operator Gate Decision Receipt. It turns Safe Cycle Operator Gate cards into a "
            "human-reviewable decision receipt that documents which steps remain unconfirmed and which local "
            "confirmation action would be next, without executing it. It uses only Operator-Gate metadata, skill "
            "tag, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, gate-card hashes, receipts, and "
            "confirmation status. Confirmed steps, when provided later, mirror only hash metadata. It never starts "
            "local writes and never returns raw queries, course raw text, notebook code, local paths, values, "
            "solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, "
            "automatic grading, or exam clearance."
        ),
        "decision_receipt_endpoint": PYTHON_EXAM_OPERATOR_GATE_DECISION_RECEIPT_ENDPOINT,
        "selected_skill_tag": str(selected),
        "decision_receipt_summary": summary,
        "card_decision_status": card_status,
        "unconfirmed_steps": [item for item in card_status if item["operator_confirmed"] is False],
        "confirmed_step_hash_metadata": [item for item in card_status if item["operator_confirmed"] is True],
        "next_allowed_local_action": next_allowed_local_action(card_status),
        "operator_decision_receipt": decision_receipt(summary, card_status),
        "dry_run_default": True,
        "local_writes_requested": False,
        "local_writes_started": False,
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
            "Reale Pruefungsfreigabe bleibt echte-Welt-Reminder; der Decision Receipt bleibt not_cleared."
        ),
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def safe_cards(cards: list[Any]) -> list[dict[str, Any]]:
    safe = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        safe.append(
            {
                "step_id": str(item.get("step_id", "")),
                "label": str(item.get("label", "")),
                "action": str(item.get("action", "")),
                "selected_skill_tag": str(item.get("selected_skill_tag", "")),
                "next_safe_action": safe_action(str(item.get("next_safe_action", ""))),
                "route": str(item.get("route", "missing")),
                "endpoint": str(item.get("endpoint", "")),
                "selected_task_hash": str(item.get("selected_task_hash", "")),
                "checkpoint_hash": str(item.get("checkpoint_hash", "")),
                "source_card_ids": [str(value) for value in (item.get("source_card_ids", []) or [])][:8],
                "source_anchor_count": int(item.get("source_anchor_count", 0) or 0),
                "help_level": safe_help_level(str(item.get("help_level", "A2"))),
                "help_ledger_event_hash": str(item.get("help_ledger_event_hash", "")),
                "review_loop_receipt_id": str(item.get("review_loop_receipt_id", "")),
                "progress_entry_hash": str(item.get("progress_entry_hash", "")),
                "control_panel_receipt_id": str(item.get("control_panel_receipt_id", "")),
                "execution_bridge_receipt_id": str(item.get("execution_bridge_receipt_id", "")),
                "card_hash": str(item.get("card_hash", "")),
                "operator_confirmed": bool(item.get("operator_confirmed", False)),
                "write_started": False,
                "local_writes_requested": False,
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
            }
        )
    return safe


def safe_confirmed_steps(confirmed_step_ids: list[str] | None, cards: list[dict[str, Any]]) -> set[str]:
    known = {card["step_id"] for card in cards}
    return {str(step) for step in (confirmed_step_ids or []) if str(step) in known}


def decision_card_status(*, cards: list[dict[str, Any]], confirmed_step_ids: set[str]) -> list[dict[str, Any]]:
    status = []
    for index, card in enumerate(cards):
        confirmed = card["step_id"] in confirmed_step_ids or bool(card.get("operator_confirmed", False))
        status.append(
            {
                "step_id": card["step_id"],
                "label": card["label"],
                "action": card["action"],
                "order": index + 1,
                "operator_confirmed": confirmed,
                "write_started": False,
                "next_confirmable": False,
                "card_hash": card["card_hash"],
                "selected_skill_tag": card["selected_skill_tag"],
                "selected_task_hash": card["selected_task_hash"],
                "checkpoint_hash": card["checkpoint_hash"],
                "source_card_ids": card["source_card_ids"],
                "source_anchor_count": card["source_anchor_count"],
                "help_level": card["help_level"],
                "help_ledger_event_hash": card["help_ledger_event_hash"],
                "review_loop_receipt_id": card["review_loop_receipt_id"],
                "progress_entry_hash": card["progress_entry_hash"],
                "control_panel_receipt_id": card["control_panel_receipt_id"],
                "execution_bridge_receipt_id": card["execution_bridge_receipt_id"],
                "local_writes_requested": False,
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
            }
        )
    for item in status:
        if item["operator_confirmed"] is False:
            item["next_confirmable"] = True
            break
    return status


def decision_summary(*, gate: dict[str, Any], card_status: list[dict[str, Any]], selected_skill_tag: str) -> dict[str, Any]:
    confirmed_count = len([item for item in card_status if item["operator_confirmed"] is True])
    unconfirmed_count = len(card_status) - confirmed_count
    ready = gate.get("status") == "python_exam_safe_cycle_operator_gate_ready" and len(card_status) == 5
    next_action = next_allowed_local_action(card_status)
    return {
        "selected_skill_tag": selected_skill_tag,
        "operator_gate_status": gate.get("status", "missing"),
        "gate_status": nested(gate, "operator_gate_summary", "gate_status") or "missing",
        "ready": ready,
        "decision_status": "decision_receipt_ready_for_human_review" if ready else "decision_receipt_attention",
        "card_count": len(card_status),
        "confirmed_count": confirmed_count,
        "unconfirmed_count": unconfirmed_count,
        "next_confirmable_step_id": next_action.get("step_id", ""),
        "next_allowed_local_action": next_action.get("action", "review_operator_gate_cards"),
        "local_action_execution_started": False,
        "local_writes_requested": False,
        "local_writes_started": False,
        "a0_a2_only": True,
        "dry_run_default": True,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def next_allowed_local_action(card_status: list[dict[str, Any]]) -> dict[str, Any]:
    for item in card_status:
        if item["operator_confirmed"] is False:
            return {
                "status": "awaiting_operator_confirmation",
                "step_id": item["step_id"],
                "action": item["action"],
                "card_hash": item["card_hash"],
                "execution_started": False,
                "local_writes_requested": False,
                "not_cleared_receipt": True,
                "exam_deployment_status": "not_cleared",
            }
    return {
        "status": "all_gate_cards_confirmed_review_before_local_cycle",
        "step_id": "review_confirmed_gate_receipt",
        "action": "review_confirmed_gate_receipt",
        "card_hash": "",
        "execution_started": False,
        "local_writes_requested": False,
        "not_cleared_receipt": True,
        "exam_deployment_status": "not_cleared",
    }


def decision_receipt(summary: dict[str, Any], card_status: list[dict[str, Any]]) -> dict[str, Any]:
    receipt_hash = sha256_text(json.dumps({"summary": summary, "cards": card_status}, sort_keys=True, ensure_ascii=False))
    return {
        "status": "operator_gate_decision_receipt_ready_not_exam_clearance",
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
        "Review the Decision Receipt before confirming any Operator Gate card.",
        "Confirm only one local step at a time and keep the receipt hash-only.",
        "Do not start local writes from the receipt; stay A0-A2 and not_cleared.",
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
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "python-exam-operator-gate-decision-receipt")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
